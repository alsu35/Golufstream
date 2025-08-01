from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from django.views.generic.base import RedirectView
from users.views import redirect_after_login_view
from core import views as core_views

# Обработчики ошибок
handler400 = core_views.custom_400
handler401 = core_views.custom_401
handler403 = core_views.custom_403
handler404 = core_views.custom_404
handler405 = core_views.custom_405
handler500 = core_views.custom_500

urlpatterns = [
    path('', redirect_after_login_view, name='index'),
    
    path('admin/', admin.site.urls),
    path('admin/logout/', RedirectView.as_view(url='/logout/', permanent=False)),

    # заявки
    path('requests/', include('myrequests.urls')),

    # аутентификация
    path('accounts/', include('users.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
