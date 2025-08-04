from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from core.utils import _has_role
from users.forms import LoginForm, RegisterForm

import logging
logger = logging.getLogger('users')

# ———————————— Auth Views ————————————
def login_view(request: HttpRequest) -> HttpResponse:
    """
    Обработка входа пользователя с поддержкой 'запомнить меня' и редиректом по ролям.
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember = form.cleaned_data.get('remember')

            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                request.session.set_expiry(24 * 60 * 60 if remember else 0)

                return redirect_after_login_view(request)

            else:
                form.add_error(None, "Неверный логин или пароль")
    else:
        form = LoginForm()

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

def register_view(request: HttpRequest) -> HttpResponse:
    """
    Представление для регистрации нового пользователя.
    Создаёт пользователя и профиль, затем автоматически авторизует.
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=True)
                logger.info(f"Новый пользователь зарегистрирован: {user.email}")

                # Автоматический вход после регистрации
                username = user.get_username()
                auth_user = authenticate(
                    request,
                    username=username,
                    password=form.cleaned_data['password1']
                )
                if auth_user is not None:
                    login(request, auth_user)
                    logger.info(f"Автоматический вход после регистрации: {username}")
                    return redirect_after_login_view(request)
                else:
                    return redirect('login')

            except Exception as e:
                logger.error(f"Ошибка при сохранении пользователя: {e}")
                form.add_error(None, "Произошла ошибка при регистрации. Попробуйте позже.")
        else:
            logger.warning("Форма регистрации заполнена некорректно.")
    else:
        form = RegisterForm()

    return render(request, 'users/register.html', {'form': form})