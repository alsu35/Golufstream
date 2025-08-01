from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS += [
    'debug_toolbar',
    'sslserver',
]

MIDDLEWARE.insert(
    MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
    'debug_toolbar.middleware.DebugToolbarMiddleware'
)

INTERNAL_IPS = ['127.0.0.1']
