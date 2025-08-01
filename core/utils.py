from django.core.cache import cache
from core.views import get_cached_categories, get_cached_locations, get_cached_statuses
from users.models import Profile
from core.models import OrganizationLocation, Category, Status

def _has_role(user, role_code):
    """
    Проверить наличие конкретной роли у пользователя через профиль.
    """
    profile = getattr(user, 'profile', None)
    return profile and profile.role.code == role_code

def get_reference_data():
    """
    Возвращает:
        - locations_qs, categories_qs, statuses_qs  
        - statuses_dict, category_codes           
    """
    locations_qs  = OrganizationLocation.objects.order_by('name')
    categories_qs = Category.objects.order_by('name')
    statuses_qs   = Status.objects.order_by('name')

    # Кэшируем только словари для быстрого lookup
    statuses_dict = cache.get_or_set(
        'ref_statuses_dict',
        lambda: {s.code: s for s in statuses_qs},
        10 * 60
    )
    category_codes = cache.get_or_set(
        'ref_category_codes',
        lambda: {c.id: c.code for c in categories_qs},
        10 * 60
    )

    return {
        'locations':      locations_qs,    
        'categories':     categories_qs,   
        'statuses':       statuses_qs,     
        'statuses_dict':  statuses_dict,    
        'category_codes': category_codes,  
    }

def get_profile_and_people(user):
    base_qs = Profile.objects.select_related(
        'user', 'department__organization', 'location', 'role'
    )

    try:
        profile = base_qs.get(user=user)
    except Profile.DoesNotExist:
        return None, [], []

    responsibles = list(
        base_qs
        .filter(location=profile.location)
        .exclude(role__code__in=['operator', 'admin'])
    )

    customers = []
    if profile.role.code == 'operator':
        customers = list(
            base_qs.filter(
                role__code='customer',
                department__organization=profile.department.organization
            )
        )

    return profile, responsibles, customers
