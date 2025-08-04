from django.urls import path
from .views import login_view, custom_logout_view, register_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', custom_logout_view, name='logout'),
]
