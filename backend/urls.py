# backend/urls.py

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from core.views import (
    custom_logout_view,
    redirect_after_login_view,
    request_list_view,
    request_detail_view,
    request_create_view,
    request_update_view,
    custom_405,
    custom_401,
    custom_404,   
    custom_403,
    custom_500,
    custom_400,
)

urlpatterns = [
    path('', redirect_after_login_view, name='index'),
    path('admin/', admin.site.urls),

    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('accounts/logout/', custom_logout_view, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),

    path('requests/', request_list_view, name='request_list'),
    path('requests/<int:pk>/', request_detail_view, name='request_detail'),
    path('requests/create/', request_create_view, name='request_create'),
    path('requests/<int:pk>/edit/', request_update_view, name='request_update'),
]

handler405 = 'core.views.custom_405'
handler401 = 'core.views.custom_401'
handler404 = 'core.views.custom_404'
handler403 = 'core.views.custom_403'
handler500 = 'core.views.custom_500'
handler400 = 'core.views.custom_400'
