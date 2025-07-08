import json
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, HttpResponseServerError, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import logout, authenticate, login
from django.db import transaction

from .models import Request, Status, OrganizationLocation, Category, Profile
from .forms import RequestForm, LoginForm

# ———————— Helpers ————————
def _get_cached(key, queryset_fn, timeout=60*15):
    """Общая обёртка для кэша списков справочников."""
    data = cache.get(key)
    if data is None:
        data = list(queryset_fn())
        cache.set(key, data, timeout)
    return data

def get_cached_statuses():
    return _get_cached('status_choices', lambda: Status.objects.only('code', 'name'))

def get_cached_categories():
    return _get_cached('category_choices', lambda: Category.objects.only('code', 'name'))

def get_cached_locations():
    return _get_cached('location_choices', lambda: OrganizationLocation.objects.only('code', 'name'))


def _has_role(user, role_code):
    """Удобный чек на роль через профиль."""
    profile = getattr(user, 'profile', None)
    return profile and profile.role.code == role_code


# ———————— Auth Views ————————
def login_view(request):
    form = LoginForm(request.POST or None)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        user = authenticate(request, username=username, password=password)
        if user:
                    login(request, user)
                    request.session.set_expiry(24 * 60 * 60 if remember else 0)
                    
                    if user.is_superuser or _has_role(user, 'admin'):
                        return redirect('/admin/')

                    return redirect('request_list')
        messages.error(request, "Неверный логин или пароль")

    return render(request, 'registration/login.html', {'form': form})

@login_required
def custom_logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def redirect_after_login_view(request):
    user = request.user
    if user.is_superuser or _has_role(user, 'admin'):
        return redirect('/admin/')
    return redirect('request_list')


# ———————— CRUD для Request ————————
import json

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import (
    JsonResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from core.models import (
    Request,
    Profile,
    Status,
    OrganizationLocation,
    Category,
)
from django.utils.decorators import decorator_from_middleware
from django.middleware.csrf import CsrfViewMiddleware

csrfmiddlewareexempt = decorator_from_middleware(CsrfViewMiddleware)


@login_required
def request_list_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    # Базовый QuerySet
    qs = Request.objects.select_related(
        'status',
        'location',
        'equipment_category',
        'customer__department__organization',
        'responsible',
    )

    if profile and profile.location:
        qs = qs.filter(location=profile.location)

    responsibles = None
    if profile and profile.role.code == 'operator' and profile.location:
        # Берём всех сотрудников в этой локации, но исключаем админов
        responsibles = Profile.objects.filter(
            location=profile.location
        ).exclude(
            role__code='admin'
        )

    return render(request, 'requests/request_list.html', {
        'requests': qs,
        'statuses': Status.objects.all(),
        'locations': OrganizationLocation.objects.all(),
        'categories': Category.objects.all(),
        'profile': profile,
        'responsibles': responsibles,
    })

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

from .models import Request, Status, User

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
        return HttpResponseForbidden("Можно просматривать только свои заявки")

    # сотрудник — заявки своей организации
    if _has_role(user, 'employee'):
        if req.customer.department.organization == profile.department.organization:
            return render(request, 'requests/request_detail.html', {'req': req})
        return HttpResponseForbidden("Можно просматривать только заявки своей организации")

    # без профиля — как сотрудник
    if not profile:
        return render(request, 'requests/request_detail.html', {'req': req})

    return HttpResponseForbidden("Нет прав на просмотр заявки")

@login_required
def request_create_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    if not any([user.is_superuser, _has_role(user, 'admin'), _has_role(user, 'operator'), _has_role(user, 'customer')]):
        return HttpResponseForbidden("Нет прав на создание заявки")

    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            if not profile:
                return HttpResponseForbidden("Профиль не найден")
            
            req.customer = profile
            req.location = profile.location
            
            # Очищаем поля для подъемных сооружений, если категория не "lifting"
            if req.equipment_category.code != 'lifting':
                req.responsible_certificate = None
                req.rigger_name = None
                req.rigger_certificates = None
            
            try:
                req.status = Status.objects.get(code='new')
            except Status.DoesNotExist:
                return HttpResponseServerError("Статус 'new' не найден")
            
            req.save()
            return redirect('request_list')
    else:
        initial_data = {}
        if profile:
            initial_data['location'] = profile.location_id
        
        form = RequestForm(initial=initial_data)
        
        if profile:
            form.fields['location'].widget.attrs['readonly'] = True

    return render(request, 'requests/request_form.html', {
        'form': form,
        'show_lifting_fields': False 
    })


@login_required
def request_update_view(request, pk):
    user = request.user
    profile = getattr(user, 'profile', None)

    if not any([user.is_superuser, _has_role(user, 'admin'), _has_role(user, 'operator'), _has_role(user, 'customer')]):
        return HttpResponseForbidden("Нет прав на редактирование")

    req = get_object_or_404(
        Request.objects.select_related(
            'customer', 'location', 'status', 'customer__department__organization'
        ),
        pk=pk
    )

    # operator – только по локации
    if _has_role(user, 'operator') and req.location != profile.location:
        return HttpResponseForbidden("Можно редактировать только по своей локации")

    # customer – только свои и не в работе
    if _has_role(user, 'customer'):
        if req.customer != profile:
            return HttpResponseForbidden("Можно редактировать только свои заявки")
        if req.status.code == 'work':
            return HttpResponseForbidden("Заявка в статусе 'work' не изменяется")

    form = RequestForm(request.POST or None, instance=req, user=user)

    # ограничиваем права заказчика
    if _has_role(user, 'customer'):
        form.fields.pop('status', None)
        for f in list(form.fields):
            if f not in ('is_completed_fact', 'comment'):
                form.fields[f].widget.attrs['readonly'] = True
                form.fields[f].required = False

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Заявка обновлена')
            return redirect('request_detail', pk=pk)
        messages.error(request, 'Проверьте корректность полей')

    return render(request, 'requests/request_form.html', {
        'form': form,
        'update': True,
        'req': req,
        'profile': profile,
    })


@login_required
def request_cancel_view(request, pk):
    user = request.user
    profile = getattr(user, 'profile', None)

    if not profile or profile.role.code not in ('operator', 'customer'):
        return HttpResponseForbidden("Нет прав на отмену")

    req = get_object_or_404(Request.objects.select_related('status'), pk=pk)

    # customer – только свои
    if profile.role.code == 'customer' and req.customer != profile:
        return HttpResponseForbidden("Можно отменять только свои заявки")

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
def request_double(request, pk):
    original = get_object_or_404(Request, pk=pk)

    original.pk = None 
    original.id = None           
    original._state.adding = True 
    original.save()

    return redirect('request_update', pk=original.pk)

# ———————— Ошибки ————————
def custom_400(request, exception=None):
    return render(request, 'errors/400.html', status=400)

def custom_401(request, exception=None):
    return render(request, 'errors/401.html', status=401)

def custom_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def custom_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def custom_405(request, exception=None):
    return render(request, 'errors/405.html', status=405)

def custom_500(request):
    return render(request, 'errors/500.html', status=500)
