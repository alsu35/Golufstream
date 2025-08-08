from django.urls import path
from .views import (
    add_responsible_view, request_list_view, request_detail_view, request_create_view,
    request_update_view, update_status, update_responsible,
    request_double_view,
)

urlpatterns = [
    path('', request_list_view, name='request_list'),
    path('create/', request_create_view, name='request_create'),
    path('<int:pk>/', request_detail_view, name='request_detail'),
    path('<int:pk>/edit/', request_update_view, name='request_update'),
    path('double/<int:pk>/', request_double_view, name='request_double'),
    path('update_status/', update_status, name='update_status'),
    path('update_responsible/', update_responsible, name='update_responsible'),
    path('responsible/add/', add_responsible_view, name='add_responsible'),
]
