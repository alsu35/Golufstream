from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Q
import json

from core.utils import _has_role, get_profile_and_people, get_reference_data
from core.models import Category, OrganizationLocation, Status
from myrequests.models import Request
from users.models import Profile
from myrequests.forms import RequestForm

import logging
logger = logging.getLogger('myrequests')

@login_required
def request_list_view(request):
    """
    Список заявок с фильтрацией по ролям и сериализацией периодов перерывов.
    """
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
    now = timezone.now()

    for req in qs:
        req.break_periods_json = json.dumps(req.break_periods or [])

        # Добавляем флаги для шаблона
        req.start_dt = timezone.make_aware(datetime.combine(req.date_start, req.time_start)) if req.date_start and req.time_start else None
        req.end_dt = timezone.make_aware(datetime.combine(req.date_end, req.time_end)) if req.date_end and req.time_end else None

        req.can_change_status_assigned = req.status.code == 'assigned' and req.start_dt and now > req.start_dt
        req.can_change_status_work = req.status.code == 'work' and req.end_dt and now > req.end_dt
        req.can_change_status_new = req.status.code == 'new' and req.start_dt and now < req.start_dt

        requests_with_serialized_breaks.append(req)

    # Данные для фильтров
    statuses = Status.objects.all()
    locations = OrganizationLocation.objects.all()
    categories = Category.objects.all()

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
        'statuses': statuses,
        'locations': locations,
        'categories': categories,
        'profile': profile,
        'responsibles': responsibles,
    })

@csrf_exempt
@require_POST
def update_status(request):
    """
    AJAX: обновление статуса заявки в зависимости от роли.
    """
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
            now = timezone.now()

            # Комбинируем дату и время старта/окончания
            start_dt = timezone.make_aware(datetime.combine(req.date_start, req.time_start)) if req.date_start and req.time_start else None
            end_dt = timezone.make_aware(datetime.combine(req.date_end, req.time_end)) if req.date_end and req.time_end else None

            if req.status.code == 'assigned' and start_dt and now > start_dt:
                can_update = new_status.code in ['assigned', 'work', 'cancel']

            elif req.status.code == 'work' and end_dt and now > end_dt:
                can_update = new_status.code in ['work', 'done', 'cancel']

            elif req.status.code == 'new' and start_dt and now < start_dt:
                can_update = new_status.code in ['new', 'cancel']


        req.status = new_status
        req.save(update_fields=['status'])

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
@require_POST
def update_responsible(request):
    """
    AJAX: переназначение ответственного за заявку (только для оператора).
    """
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
    """
    Просмотр деталей заявки с проверкой прав доступа по ролям.
    """
    req = get_object_or_404(
        Request.objects.select_related(
            # === Заказчик (customer) ===
            'customer__user', 
            'customer__department__organization',
            'customer__location',

            # === Ответственный (responsible) ===
            'responsible__user', 
            'responsible__department__organization', 
            'responsible__location', 

            # === Прямые связи ===
            'status', 
            'equipment_category',
            'location', 
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
    """
    Создание новой заявки с предустановленным статусом и локацией.
    """
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
    """
    Обновление существующей заявки с проверкой доступа и корректировкой полей для customer.
    """
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
                        'req': req,
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
            profile=profile,
            locations=ref['locations'],
            categories=ref['categories'],
            statuses=ref['statuses'],
            new_status=None
        )
        # для template JS
        cat_id = req.equipment_category_id

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
        'req': req,
    })

@login_required
def request_double_view(request, pk):
    """
    Дублирование существующей заявки для быстрого создания похожей.
    """
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
            profile=profile,
            locations=ref['locations'],
            categories=ref['categories'],
            statuses=ref['statuses'],
            new_status=None
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
            profile=profile,
            locations=ref['locations'],
            categories=ref['categories'],
            statuses=ref['statuses'],
            new_status=None
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
