from pathlib import Path
import os

# ======================
# Базовые пути проекта
# ======================
BASE_DIR = Path(__file__).resolve().parent.parent  # Корневая директория проекта

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'app.log'),
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# ======================
# Настройки безопасности
# ======================
SECRET_KEY = 'django-insecure-r(7$cl^h@lcto@88ms5(imlfk4dz@-mxjp*0h*6ihpp=3&352w'  # Ключ должен быть изменен в продакшене
DEBUG = True  # Режим отладки - только для разработки!
ALLOWED_HOSTS = []  # Разрешенные хосты (пусто - только localhost)

# ======================
# Пользовательская модель
# ======================
AUTH_USER_MODEL = 'core.User'  # Кастомная модель пользователя

# ======================
# Установленные приложения
# ======================
INSTALLED_APPS = [
    # Стандартные приложения Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Сторонние приложения
    'mptt',  # Для работы с деревьями (Modified Preorder Tree Traversal)
    
    # Локальные приложения
    'core',  # Основное приложение проекта
]

# ======================
# Промежуточное ПО (Middleware)
# ======================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',  # Безопасность
    'django.contrib.sessions.middleware.SessionMiddleware',  # Сессии
    'django.middleware.common.CommonMiddleware',  # Базовые HTTP операции
    'django.middleware.csrf.CsrfViewMiddleware',  # Защита от CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Аутентификация
    'django.contrib.messages.middleware.MessageMiddleware',  # Система сообщений
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Защита от clickjacking
]

# Основные URL и аутентификация
ROOT_URLCONF = 'backend.urls'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'  # Перенаправление после успешного входа
LOGOUT_REDIRECT_URL = '/login/'  # Перенаправление после выхода
TELEGRAM_BOT_TOKEN = "7977098735:AAGOfWoe0LT0VL_ru32MU8qoRDs0MGyqr-I"

# Настройки безопасности сессий
SESSION_COOKIE_AGE = 24 * 60 * 60  # Время жизни сессии - 1 день
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True  # Передача cookies только через HTTPS
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Закрытие сессии при завершении браузера
SESSION_COOKIE_SAMESITE = 'Lax'  # Защита от CSRF атак

# Настройки шаблонов
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'core/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI приложение
WSGI_APPLICATION = 'backend.wsgi.application'

# Настройки базы данных PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gulfstream',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Валидация паролей
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Локализация и время
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Статические файлы
STATIC_URL = 'static/'

# Первичный ключ по умолчанию
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'