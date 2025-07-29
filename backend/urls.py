from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView
from core.views import (
    login_view, 
    custom_logout_view,
    redirect_after_login_view,
    request_list_view,
    request_detail_view,
    request_create_view,
    request_update_view,
    update_status,
    update_responsible,
    request_double_view,
    custom_405,
    custom_401,
    custom_404,   
    custom_403,
    custom_500,
    custom_400,
)
from debug_toolbar.toolbar import debug_toolbar_urls


urlpatterns = [
    path('', redirect_after_login_view, name='index'),
    path('admin/', admin.site.urls),

    path('login/', login_view, name='login'),
    path('admin/logout/', RedirectView.as_view(url='/custom-logout/', permanent=False)),  
    path('logout/', custom_logout_view, name='logout'),

    # Заявки
    path('requests/', request_list_view, name='request_list'),
    path('requests/<int:pk>/', request_detail_view, name='request_detail'),
    path('requests/create/', request_create_view, name='request_create'),
    path('requests/<int:pk>/edit/', request_update_view, name='request_update'),
    path('requests/double/<int:pk>/', request_double_view, name='request_double'),
    path('requests/update/<int:pk>/', request_update_view, name='request_update'),
    path('api/update_status/', update_status, name='update_status'),
    path('api/update_responsible/', update_responsible, name='update_responsible'),
] + debug_toolbar_urls()

# Обработчики ошибок
handler405 = 'core.views.custom_405'
handler401 = 'core.views.custom_401'
handler404 = 'core.views.custom_404'
handler403 = 'core.views.custom_403'
handler500 = 'core.views.custom_500'
handler400 = 'core.views.custom_400'
