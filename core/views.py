from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseServerError
from django.contrib import messages
from .models import Request, Status, OrganizationLocation
from .forms import RequestForm
from django.contrib.auth import logout, authenticate, login

def custom_logout_view(request):
    logout(request)
    return redirect('login') 

def _has_basic_access(user, profile):
    return (profile is None and not user.is_superuser) or (
        profile and profile.role and profile.role.code == 'employee'
    )

def _has_master_access(user, profile):
    return profile and profile.role and profile.role.code == 'master'

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            
            if remember:
                request.session.set_expiry(24*60*60)
            else:
                request.session.set_expiry(0)

            return redirect('request_list')
        else:
            messages.error(request, "Неверный логин или пароль")
        
    return render(request, 'login.html')

@login_required
def redirect_after_login_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    if user.is_superuser:
        return redirect('/admin/')
    
    if _has_basic_access(user, profile):
        return redirect('request_list')
    
    if _has_master_access(user, profile):
        return redirect('request_list')
    
    return render(request, 'errors/403.html', status=403)


@login_required
def request_create_view(request):
    if not request.user.has_perm('core.add_request'):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            # Установка профиля пользователя
            if hasattr(request.user, 'profile'):
                req.customer = request.user.profile
            else:
                return HttpResponseForbidden("Нет профиля пользователя")

            # Автоустановка статуса
            try:
                req.status = Status.objects.get(code='new')
            except Status.DoesNotExist:
                return HttpResponseServerError("Статус с кодом 'new' не найден")

            req.save()
            return redirect('request_list')
    else:
        form = RequestForm()

    return render(request, 'requests/request_form.html', {'form': form})

@login_required
def request_update_view(request, pk):
    user = request.user
    profile = getattr(user, 'profile', None)

    if not (_has_basic_access(user, profile) or _has_master_access(user, profile) or user.is_superuser):
        return HttpResponseForbidden()

    req = get_object_or_404(Request, pk=pk)

    if _has_basic_access(user, profile) and req.customer_id != profile.id:
        return HttpResponseForbidden()

    form = RequestForm(request.POST or None, instance=req)

    # Мастер может редактировать только is_completed_fact
    if _has_master_access(user, profile):
        allowed = {'is_completed_fact'}
        for field in list(form.fields):
            if field not in allowed:
                form.fields.pop(field)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Заявка обновлена.')
        return redirect('request_detail', pk=pk)

    return render(request, 'requests/request_form.html', {'form': form, 'update': True})


@login_required
def request_list_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    if not (_has_basic_access(user, profile) or _has_master_access(user, profile) or user.is_superuser):
        return HttpResponseForbidden()

    # Если пользователь имеет базовый доступ, но нет профиля — показываем все заявки
    if _has_basic_access(user, profile) and profile:
        qs = Request.objects.filter(customer=profile)
    else:
        qs = Request.objects.all()

    statuses = Status.objects.all()
    locations = OrganizationLocation.objects.all()
    qs = qs.select_related('status', 'location')

    return render(request, 'requests/request_list.html', {
        'requests': qs,
        'statuses': statuses,
        'locations': locations
    })

@login_required
def request_detail_view(request, pk):
    user = request.user
    profile = getattr(user, 'profile', None)

    if not (_has_basic_access(user, profile) or _has_master_access(user, profile) or user.is_superuser):
        return HttpResponseForbidden()

    req = get_object_or_404(Request.objects.select_related('customer', 'status', 'location'), pk=pk)

    if _has_basic_access(user, profile) and req.customer_id != profile.id:
        return HttpResponseForbidden()

    return render(request, 'requests/request_detail.html', {'req': req})

# ошибки
def custom_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def custom_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def custom_405(request, exception=None):
    return render(request, 'errors/405.html', status=405)

def custom_401(request, exception=None):
    return render(request, 'errors/401.html', status=401)

def custom_500(request):
    return render(request, 'errors/500.html', status=500)

def custom_400(request, exception=None):
    return render(request, 'errors/400.html', status=400)


#  ("logist1",  "Логистов",  "Логист",  "logist@example.com",  "logist"),
#     ("employee1","Сотрудников","Сотрудник","emp@example.com",     "employee"),
#     ("master1",  "Мастеров",  "Мастер",  "master@example.com",    "admin"), 
# 'master2' 'master2'
# http://127.0.0.1:8000/accounts/login/


# Status.objects.create(code="new", name="Новая")
# Status.objects.create(code="assigned", name="Назначена")
# Status.objects.create(code="work", name="В работе")
# Status.objects.create(code="done", name="Выполнена")
# Status.objects.create(code="cancel", name="Отменена")

        # 