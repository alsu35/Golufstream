from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from core.utils import _has_role
from users.forms import LoginForm

import logging
logger = logging.getLogger('users')

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
            
    return render(request, 'users/login.html', {'form': form})

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
