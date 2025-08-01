from django.urls import path
from .views import login_view, custom_logout_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', custom_logout_view, name='logout'),
]
