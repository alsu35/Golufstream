from django.shortcuts import render
from django.core.cache import cache
from core.models import Category, OrganizationLocation, Status

import logging
logger = logging.getLogger('core')

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

# ———————— Ошибки ————————
def custom_400(request, exception=None):
    return render(request, 'errors/400.html', status=400)

def custom_401(request, exception=None):
    return render(request, 'errors/401.html', status=401)

def custom_403(request, exception=None):
    msg = f"403 Forbidden: path={request.path} user={request.user!r} reason={exception!r}"
    logger.warning(msg)

    return render(request, 'errors/403.html', status=403)

def custom_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def custom_405(request, exception=None):
    return render(request, 'errors/405.html', status=405)

def custom_500(request):
    return render(request, 'errors/500.html', status=500)
