# Стандартные библиотеки
from datetime import timezone
import json

# Django core
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.contrib.auth import logout, authenticate, login
from django.db import transaction
from django.utils.decorators import decorator_from_middleware
from django.middleware.csrf import CsrfViewMiddleware
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.exceptions import PermissionDenied, ValidationError
import logging

from core.utils import get_profile_and_people, get_reference_data
# Формы
from .forms import RequestForm, LoginForm

# Модели
from .models import (
    Request,
    Status,
    OrganizationLocation,
    Category,
    Profile,
    User,
)
from core.models import (
    Request as CoreRequest,
    Profile as CoreProfile,
    Status as CoreStatus,
    OrganizationLocation as CoreOrgLocation,
    Category as CoreCategory,
)

# ———————————— Caching Helpers ————————————
def _get_cached(key, queryset_fn, timeout=60 * 15):
    """
    Универсальный кэширующий декоратор для справочников.
    Возвращает закэшированные данные или выполняет и кэширует queryset.
    """
    data = cache.get(key)
    if data is None:
        data = list(queryset_fn())
        cache.set(key, data, timeout)
    return data


# ———————————— Cached Dictionaries ————————————
def get_cached_statuses():
    """Получить закэшированный список статусов (code, name)."""
    return _get_cached('status_choices', lambda: Status.objects.only('code', 'name'))

def get_cached_categories():
    """Получить закэшированный список категорий (code, name)."""
    return _get_cached('category_choices', lambda: Category.objects.only('code', 'name'))

def get_cached_locations():
    """Получить закэшированный список локаций (code, name)."""
    return _get_cached('location_choices', lambda: OrganizationLocation.objects.only('code', 'name'))


# ———————————— Role Helpers ————————————
def _has_role(user, role_code):
    """
    Проверить наличие конкретной роли у пользователя через профиль.
    """
    profile = getattr(user, 'profile', None)
    return profile and profile.role.code == role_code

# ———————————— Auth Views ————————————
def login_view(request):
    """
    Обработка входа пользователя с поддержкой 'запомнить меня' и редиректом по ролям.
    """
    form = LoginForm(request.POST or None)

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            # Установка времени жизни сессии (1 день если "запомнить меня")
            request.session.set_expiry(24 * 60 * 60 if remember else 0)
            
            # Редирект для админов и обычных пользователей
            if user.is_superuser or _has_role(user, 'admin'):
                return redirect('/admin/')
            return redirect('request_list')
        else:
            form.add_error(None, "Неверный логин или пароль")
            
    return render(request, 'registration/login.html', {'form': form})

@login_required
def custom_logout_view(request):
    """
    Выход пользователя с последующим редиректом на страницу входа.
    """
    logout(request)
    return redirect('login')

@login_required
def redirect_after_login_view(request):
    """
    Унифицированный редирект после входа в зависимости от роли пользователя.
    """
    user = request.user
    if user.is_superuser or _has_role(user, 'admin'):
        return redirect('/admin/')
    return redirect('request_list')

# ———————— CRUD для Request ————————
csrfmiddlewareexempt = decorator_from_middleware(CsrfViewMiddleware)

@login_required
def request_list_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    # Базовый queryset
    qs = Request.objects.select_related(
        'status',
        'location',
        'equipment_category',
        'customer__user',
        'customer__department__organization',
        'responsible',
    )

    # --- Фильтрация по ролям ---
    if profile:
        role_code = profile.role.code

        if role_code == 'customer':
            # Только свои заявки (как заказчик)
            qs = qs.filter(customer=profile)

        elif role_code == 'employee':
            # Где он ответственный или заявки по его организации и локации
            qs = qs.filter(
                Q(responsible=profile) |
                Q(
                    customer__department__organization=profile.department.organization,
                    location=profile.location
                )
            )

        elif role_code == 'operator':
            # Все заявки по его локации
            qs = qs.filter(location=profile.location)
        
    # --- сериализацию break_periods ---
    requests_with_serialized_breaks = []
    for req in qs:
        req.break_periods_json = req.break_periods or []
        requests_with_serialized_breaks.append(req)

    locations = OrganizationLocation.objects.all()

    # --- Ответственные (только для оператора) ---
    responsibles = None
    if profile and profile.role.code == 'operator' and profile.location:
        responsibles = Profile.objects.filter(
            location=profile.location
        ).exclude(
            role__code__in=['admin', 'operator']
        ).select_related('user')

    return render(request, 'requests/request_list.html', {
        'requests': requests_with_serialized_breaks,
        'statuses': Status.objects.all(),
        'locations': OrganizationLocation.objects.all(),
        'categories': Category.objects.all(),
        'profile': profile,
        'responsibles': responsibles,
    })

@csrf_exempt
@require_POST
def update_status(request):
    try:
        data = json.loads(request.body)
        request_id = data.get('request_id')
        status_id = data.get('status_id')

        req = Request.objects.select_related('status').get(id=request_id)
        new_status = Status.objects.get(id=status_id)

        profile = request.user.profile
        role_code = profile.role.code

        can_update = False

        if role_code == 'operator':
            can_update = True
        elif role_code == 'customer':
            if req.status.code == 'assigned' and req.date_start_ended_allowed:
                can_update = new_status.code in ['assigned', 'work', 'cancel']
            elif req.status.code == 'work' and req.date_end_ended_allowed:
                can_update = new_status.code in ['work', 'done', 'cancel']

        req.status = new_status
        req.save(update_fields=['status'])

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def update_responsible(request):
    try:
        data = json.loads(request.body)
        req = Request.objects.get(id=data['request_id'])
        
        # теперь profile_id, а не user_id
        profile = request.user.profile
        if profile.role.code == 'operator':
            if req.status.code not in ['new', 'assigned']:
                return JsonResponse({
                    'success': False,
                    'error': 'Вы можете изменить ответственного только для заявок со статусом "Новая" или "Назначена"'
                }, status=403)

        # Назначение ответственного
        prof = Profile.objects.get(id=data['responsible_id'])
        req.responsible = prof
        req.save(update_fields=['responsible'])

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def request_detail_view(request, pk):
    req = get_object_or_404(
        Request.objects.select_related(
            # === Заказчик (customer) ===
            'customer__user',  # для full_name
            'customer__department__organization',  # для department.name и organization
            'customer__location',  # для location (OrganizationLocation)

            # === Ответственный (responsible) ===
            'responsible__user',  # для full_name
            'responsible__department__organization',  # для department.name
            'responsible__location',  # для location

            # === Прямые связи ===
            'status',      # статус заявки
            'equipment_category',    # категория техники
            'location',    # локация из заявки (OrganizationLocation)
        ),
        pk=pk
    )
    user = request.user
    profile = getattr(user, 'profile', None)

    # Проверка прав доступа
    if user.is_superuser or _has_role(user, 'admin'):
        pass  # разрешено
    elif _has_role(user, 'operator'):
        pass  # разрешено
    elif _has_role(user, 'customer'):
        if req.customer != profile:
            raise PermissionDenied("You can only view your applications")
    elif _has_role(user, 'employee'):
        if req.customer.department.organization != profile.department.organization:
            raise PermissionDenied("You can only view your organization's applications")
    elif not profile:
        pass  # разрешено (без профиля)
    else:
        raise PermissionDenied("No rights to view the application")

    return render(request, 'requests/request_detail.html', {'req': req})

@login_required
def request_create_view(request):
    user = request.user
    profile, responsibles, customers = get_profile_and_people(user)
    ref = get_reference_data()

    # Только superuser/admin/operator/customer
    if not (user.is_superuser or (profile and profile.role.code in ('admin','operator','customer'))):
        raise PermissionDenied()

    # Всегда дефолтный статус = 'new' и локация = профильная
    new_status = ref['statuses_dict']['new']
    initial = {
        'status':   new_status.id,
        'location': profile.location.id if profile else None,
    }

    form = RequestForm(
        data=request.POST or None,
        initial=initial,
        profile=profile,
        locations=ref['locations'],
        categories=ref['categories'],
        statuses=ref['statuses'],
        new_status=new_status,
    )

    # вычисляем show_lifting сразу из incoming данных
    cat = form.data.get('equipment_category') or form.initial.get('equipment_category')
    show_lifting = bool(cat and ref['category_codes'].get(int(cat)) == 'lifting')

    if request.method == 'POST' and form.is_valid():
        req = form.save(commit=False)

        # customer: оператор выбирает, остальные — свой профиль
        if profile and profile.role.code == 'operator':
            customer = form.cleaned_data.get('customer')
            req.customer = customer
        else:
            req.customer = profile

        req.save()
        messages.success(request, "Заявка создана")
        return redirect('request_list')

    return render(request, 'requests/request_form.html', {
        'form':               form,
        'locations':          ref['locations'],
        'categories':         ref['categories'],
        'statuses':           ref['statuses'],
        'category_codes':     ref['category_codes'],
        'responsibles':       responsibles,
        'customers':          customers,
        'profile':            profile,
        'current_category_id': cat, 
    })

@login_required
def request_update_view(request, pk):
    user = request.user
    profile, responsibles, customers = get_profile_and_people(user)
    ref = get_reference_data()

    # Проверка доступа
    if not any([
        user.is_superuser,
        _has_role(user, 'admin'),
        _has_role(user, 'operator'),
        _has_role(user, 'customer'),
    ]):
        raise PermissionDenied("Нет прав для редактирования")

    # Загружаем заявку
    req = get_object_or_404(
        Request.objects.select_related(
            'customer__user', 'customer__department__organization', 'customer__location', 'customer__role',
            'responsible__user', 'responsible__department__organization', 'responsible__location', 'responsible__role',
            'status', 'equipment_category', 'location'
        ),
        pk=pk
    )

    # Доступ по локации/статусу
    if _has_role(user, 'operator') and req.location != profile.location:
        raise PermissionDenied("Редактировать можно только по своей локации")
    if _has_role(user, 'customer') and (req.customer != profile or req.status.code == 'work'):
        raise PermissionDenied("Редактировать можно только свои черновики")

    # Обработка POST
    if request.method == 'POST':
        form = RequestForm(
            request.POST,
            instance=req,
            user=user,
            profile=profile,
            locations=ref['locations'],
            categories=ref['categories'],
            statuses=ref['statuses'],
        )
        if form.is_valid():
            updated = form.save(commit=False)

            # Устанавливаем customer до валидации модели
            if profile.role.code == 'operator':
                customer = form.cleaned_data.get('customer')
                if not customer:
                    form.add_error('customer', 'Укажите заказчика')
                    # заново отрисуем форму с ошибкой, не вызывая save()
                    return render(request, 'requests/request_form.html', {
                        'form': form,
                        'update': True,
                        'responsibles': responsibles,
                        'customers': customers,
                        'profile': profile,
                        'is_duplicate': 'original_pk' in request.GET,
                        'show_lifting_fields': show_lifting,
                        'locations': ref['locations'],
                        'categories': ref['categories'],
                        'statuses': ref['statuses'],
                        'category_codes': ref['category_codes'],
                        'current_category_id': cat_id,
                    })
                updated.customer = customer
            else:
                # заказчик или админ
                updated.customer = profile

            # Теперь можно сохранить
            updated.save()
            messages.success(request, "Заявка обновлена")
            return redirect('request_detail', pk=updated.pk)
        else:
            messages.error(request, "Проверьте корректность полей")

        cat_id = request.POST.get('equipment_category')

    else:
        form = RequestForm(
            instance=req,
            user=user,
            locations=ref['locations'],
            categories=ref['categories'],
            statuses=ref['statuses'],
        )
        # для template JS
        cat_id = req.equipment_category_id
        # customer не может менять статус
        if _has_role(user, 'customer'):
            form.fields.pop('status', None)
            editable = {'is_completed_fact', 'comment', 'work_type', 'transport_type', 'work_object'}
            for fname in list(form.fields):
                if fname not in editable:
                    form.fields[fname].widget.attrs['readonly'] = True
                    form.fields[fname].required = False

    show_lifting = bool(cat_id and ref['category_codes'].get(int(cat_id)) == 'lifting')

    return render(request, 'requests/request_form.html', {
        'form': form,
        'update': True,
        'responsibles': responsibles,
        'customers': customers,
        'profile': profile,
        'is_duplicate': 'original_pk' in request.GET,
        'show_lifting_fields': show_lifting,
        'locations': ref['locations'],
        'categories': ref['categories'],
        'statuses': ref['statuses'],
        'category_codes': ref['category_codes'],
        'current_category_id': cat_id,
    })

@login_required
def request_double_view(request, pk):
    user = request.user
    profile, responsibles, customers = get_profile_and_people(user)
    ref = get_reference_data()

    # 1. Загружаем оригинал
    original = get_object_or_404(
        Request.objects.select_related(
            'customer__user', 'customer__department__organization', 'customer__location',
            'responsible__user', 'responsible__department__organization', 'responsible__location',
            'status', 'equipment_category', 'location',
        ),
        pk=pk
    )

    # 2. Создаём дубликат без сохранения
    duplicate = Request(
        location=original.location,
        date_start=original.date_start,
        date_end=original.date_end,
        time_start=original.time_start,
        time_end=original.time_end,
        work_object=original.work_object,
        work_type=original.work_type,
        transport_type=original.transport_type,
        equipment_category=original.equipment_category,
        break_periods=original.break_periods,
        comment=original.comment,
        responsible=original.responsible,
        responsible_certificate=original.responsible_certificate,
        rigger_name=original.rigger_name,
        rigger_certificates=original.rigger_certificates,
        customer=original.customer,
        is_completed_fact=original.is_completed_fact,
        status=ref['statuses_dict'].get('new'),
    )

    # 3. Обработка формы
    if request.method == 'POST':
        form = RequestForm(
            request.POST,
            instance=duplicate,
            user=user,
            locations=ref['locations'],
            categories=ref['categories'],
            statuses=ref['statuses'],
        )
        cat_id = request.POST.get('equipment_category')

        if form.is_valid():
            new_req = form.save(commit=False)
            # Оператор может указать заказчика, остальные — берут текущий профиль
            if profile and profile.role.code == 'operator':
                customer_id = request.POST.get('customer')
                if customer_id:
                    new_req.customer_id = int(customer_id)
            else:
                new_req.customer = profile

            new_req.save()
            messages.success(request, "Дубликат заявки сохранён")
            return redirect('request_detail', pk=new_req.pk)
        else:
            messages.error(request, "Проверьте корректность заполнения полей")
    else:
        form = RequestForm(
            instance=duplicate,
            user=user,
            locations=ref['locations'],
            categories=ref['categories'],
            statuses=ref['statuses'],
        )
        cat_id = duplicate.equipment_category_id

    # 4. Логика показа lifting‑блоков
    show_lifting = bool(cat_id and ref['category_codes'].get(int(cat_id)) == 'lifting')

    return render(request, 'requests/request_form.html', {
        'form': form,
        'is_duplicate': True,
        'original_pk': pk,
        'responsibles': responsibles,
        'customers': customers,
        'profile': profile,
        'show_lifting_fields': show_lifting,
        'locations': ref['locations'],
        'categories': ref['categories'],
        'statuses': ref['statuses'],
        'category_codes': ref['category_codes'],
        'current_category_id': cat_id,
    })

# ———————— Ошибки ————————
def custom_400(request, exception=None):
    return render(request, 'errors/400.html', status=400)

def custom_401(request, exception=None):
    return render(request, 'errors/401.html', status=401)

logger = logging.getLogger('django.request')

def custom_403(request, exception=None):
    # логируем URL и причину отказа
    msg = f"403 Forbidden: path={request.path} user={request.user!r} reason={exception!r}"
    logger.warning(msg)

    return render(request, 'errors/403.html', status=403)

def custom_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def custom_405(request, exception=None):
    return render(request, 'errors/405.html', status=405)

def custom_500(request):
    return render(request, 'errors/500.html', status=500)
