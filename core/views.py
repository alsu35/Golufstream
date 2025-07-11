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
from django.core.cache import cache
from django.contrib.auth import logout, authenticate, login
from django.db import transaction
from django.utils.decorators import decorator_from_middleware
from django.middleware.csrf import CsrfViewMiddleware
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.exceptions import PermissionDenied
import logging
from django.core.exceptions import PermissionDenied

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
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Установка времени жизни сессии (1 день если "запомнить меня")
            request.session.set_expiry(24 * 60 * 60 if remember else 0)
            
            # Редирект для админов и обычных пользователей
            if user.is_superuser or _has_role(user, 'admin'):
                return redirect('/admin/')
            return redirect('request_list')
        
        messages.error(request, "Неверный логин или пароль")

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

    # --- Ответственные (только для оператора) ---
    responsibles = None
    if profile and profile.role.code == 'operator' and profile.location:
        responsibles = Profile.objects.filter(
            location=profile.location
        ).exclude(
            role__code__in=['admin', 'operator']
        ).select_related('user')

    return render(request, 'requests/request_list.html', {
        'requests': qs,
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

        req = Request.objects.get(id=request_id)
        status = Status.objects.get(id=status_id)

        req.status = status
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
        prof = Profile.objects.get(id=data['responsible_id'])
        req.responsible = prof
        req.save(update_fields=['responsible'])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def request_detail_view(request, pk):
    req = get_object_or_404(
        Request.objects.select_related('customer__department__organization'),
        pk=pk
    )
    user = request.user
    profile = getattr(user, 'profile', None)

    # суперпользователь и админ
    if user.is_superuser or _has_role(user, 'admin'):
        return render(request, 'requests/request_detail.html', {'req': req})

    # оператор = полный доступ (только просмотр)
    if _has_role(user, 'operator'):
        return render(request, 'requests/request_detail.html', {'req': req})

    # заказчик — только свои заявки
    if _has_role(user, 'customer'):
        if req.customer == profile:
            return render(request, 'requests/request_detail.html', {'req': req})
        raise PermissionDenied("You can only view your applications")

    # сотрудник — заявки своей организации
    if _has_role(user, 'employee'):
        if req.customer.department.organization == profile.department.organization:
            return render(request, 'requests/request_detail.html', {'req': req})
        raise PermissionDenied("You can only view your organization's applications")

    # без профиля — как сотрудник
    if not profile:
        return render(request, 'requests/request_detail.html', {'req': req})

    raise PermissionDenied("No rights to view the application")

@login_required
def request_create_view(request):
    user    = request.user
    profile = getattr(user, 'profile', None)
    categories = Category.objects.all()
    # --- Список заказчиков (роль customer в той же локации) ---
    customers = Profile.objects.filter(
        location=profile.location,
        role__code='customer'
    ).select_related('user')

    # --- Список ответственных ---
    if profile and profile.role.code == 'customer':
        responsibles = Profile.objects.filter(
            department__organization=profile.department.organization,
            location=profile.location
        ).exclude(role__code__in=['operator', 'admin']).select_related('user')
    else:
        responsibles = Profile.objects.filter(
            location=profile.location
        ).exclude(role__code__in=['operator', 'admin']).select_related('user')

    # --- Проверка прав: superuser, admin, operator или customer ---
    allowed = (
        user.is_superuser
        or (profile and profile.role.code in ('admin', 'operator', 'customer'))
    )
    if not allowed:
        raise PermissionDenied("No rights to create an application")

    show_lifting = False

    if request.method == 'POST':
        form = RequestForm(request.POST, user=user)

        # Если оператор, требуем выбор заказчика
        if profile and profile.role.code == 'operator' and not request.POST.get('customer'):
            form.add_error('customer', 'Выберите заказчика')

        # Если форма невалидна — рендерим с ошибками
        if not form.is_valid():
            # Определяем, показывать ли блок подъёмных сооружений
            cat_id = request.POST.get('equipment_category')
            show_lifting = (
                Category.objects.filter(pk=cat_id)
                .values_list('code', flat=True)
                .first() == 'lifting'
            )
            return render(request, 'requests/request_form.html', {
                'form': form,
                'categories':categories,
                'show_lifting_fields': show_lifting,
                'responsibles': responsibles,
                'customers': customers,
                'profile': profile,
            })

        # Форма валидна — сохраняем
        req = form.save(commit=False)

        # Заполняем заказчика
        if profile and profile.role.code == 'operator':
            req.customer = form.cleaned_data['customer']
        else:
            req.customer = profile

        # Локация
        req.location = profile.location

        # Статус new
        try:
            req.status = Status.objects.get(code='new')
        except Status.DoesNotExist:
            return HttpResponseServerError("Статус 'new' не найден")

        req.save()
        return redirect('request_list')

    else:
        # GET-запрос — инициализируем пустую форму
        initial = {}
        if profile:
            initial['location'] = profile.location_id

        form = RequestForm(initial=initial, user=user)
        if profile:
            form.fields['location'].widget.attrs['readonly'] = True

    return render(request, 'requests/request_form.html', {
        'form': form,
        'show_lifting_fields': show_lifting,
        'categories': categories,
        'responsibles': responsibles,
        'customers': customers,
        'profile': profile,
    })

@login_required
def request_cancel_view(request, pk):
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or profile.role.code not in ('operator', 'customer'):
        raise PermissionDenied("No cancellation rights")

    req = get_object_or_404(Request.objects.select_related('status'), pk=pk)

    # customer – только свои
    if profile.role.code == 'customer' and req.customer != profile:
        raise PermissionDenied("You can only cancel your applications")

    if req.status.code == 'work':
        messages.error(request, "Нельзя отменить заявку в работе")
        return redirect('request_detail', pk=pk)

    try:
        cancel = Status.objects.get(code='cancel')
        req.status = cancel
        req.save()
        messages.success(request, "Заявка отменена")
    except Status.DoesNotExist:
        messages.error(request, "Статус 'cancel' не найден")
        return redirect('request_list')

    return redirect('request_detail', pk=pk)

@login_required
def request_update_view(request, pk=None):
    user = request.user
    profile = getattr(user, 'profile', None)
    categories = Category.objects.all()

    # responsables…
    responsibles = Profile.objects.filter(
        location=profile.location
    ).exclude(role__code__in=['operator', 'admin']).select_related('user')

    # проверка прав
    if not any([user.is_superuser,
                _has_role(user, 'admin'),
                _has_role(user, 'operator'),
                _has_role(user, 'customer')]):
        raise PermissionDenied("No editing rights")

    # получаем request
    req = None
    if pk:
        req = get_object_or_404(Request.objects.select_related(
            'customer', 'location', 'status', 'customer__department__organization'
        ), pk=pk)

        # оператор может только по своей локации
        if _has_role(user, 'operator') and req.location != profile.location:
            raise PermissionDenied("You can edit only by your location")

        # customer: только свои заявки и не в работе
        if _has_role(user, 'customer') and (req.customer != profile or req.status.code == 'work'):
            raise PermissionDenied("No rights to edit this application")

    # работа с формой
    if request.method == 'POST':
        form = RequestForm(request.POST, instance=req, user=user)
        if form.is_valid():
            new_req = form.save(commit=False)
            new_req.customer = profile
            # сохраняем
            new_req.save()
            messages.success(request, 'Заявка успешно сохранена')
            return redirect('request_detail', pk=new_req.pk)
        else:
            messages.error(request, 'Проверьте корректность полей')

        # для невалидного POST определяем lifting из POST
        cat_id = request.POST.get('equipment_category')
    else:
        # GET
        form = RequestForm(instance=req, user=user) if req else RequestForm(user=user)
        # для customer делаем readonly…
        if _has_role(user, 'customer'):
            form.fields.pop('status', None)
            editable = {
                'is_completed_fact',
                'comment',
                'work_type',
                'transport_type',
                'work_object',
            }
            for fname in list(form.fields):
                if fname not in editable:
                    form.fields[fname].widget.attrs['readonly'] = True
                    form.fields[fname].required = False

        # для GET берем категорию из instance
        cat_id = req.equipment_category_id if req else None

    # вычисляем, показывать ли lifting-поля
    show_lifting = False
    if cat_id:
        try:
            cat = Category.objects.get(pk=cat_id)
            show_lifting = (cat.code == 'lifting')
        except Category.DoesNotExist:
            show_lifting = False

    return render(request, 'requests/request_form.html', {
        'form': form,
        'update': bool(req),
        'responsibles': responsibles,
        'profile': profile,
        'is_duplicate': 'original_pk' in request.GET,
        'show_lifting_fields': show_lifting,
        'categories': categories,
    })

@login_required
def request_double(request, pk):
    """Создаёт дубликат (черновик) заявки и обрабатывает его сохранение."""
    original = get_object_or_404(Request, pk=pk)
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile:
        raise PermissionDenied("Нет профиля")

    # Готовим начальный объект (без сохранения в БД)
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
        customer=profile,
        is_completed_fact=original.is_completed_fact,
    )
    # дефолтный статус
    duplicate.status = Status.objects.filter(code="new").first()

    # подготовка списка ответственных (для выпадашки)
    responsibles = Profile.objects.filter(
        location=profile.location
    ).exclude(role__code__in=['operator', 'admin']).select_related('user')
    categories = Category.objects.all()

    if request.method == 'POST':
        # принимаем данные и валидируем
        form = RequestForm(request.POST, instance=duplicate, user=user)
        if form.is_valid():
            new_req = form.save(commit=False)
            new_req.customer = profile
            # статус уже задан в форме.save()
            new_req.save()
            messages.success(request, "Дубликат заявки успешно сохранён")
            return redirect('request_detail', pk=new_req.pk)
        else:
            messages.error(request, "Проверьте правильность заполнения полей")
        # для невалидного POST нужно определить, показывать ли lifting‑блок
        cat_id = request.POST.get('equipment_category')
    else:
        # GET: просто показываем форму с начальным экземпляром
        form = RequestForm(instance=duplicate, user=user)
        # lifting‑блок по instance
        cat_id = duplicate.equipment_category_id

    # включаем/выключаем поля для категории lifting
    show_lifting = False
    if cat_id:
        try:
            show_lifting = (Category.objects.get(pk=cat_id).code == 'lifting')
        except Category.DoesNotExist:
            pass

    return render(request, 'requests/request_form.html', {
        'form': form,
        'is_duplicate': True,
        'original_pk': pk,
        'responsibles': responsibles,
        'profile': profile,
        'duplicated': True,
        'show_lifting_fields': show_lifting,
        'categories': categories,
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
