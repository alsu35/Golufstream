from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Organization, OrganizationLocation, User, Role, Profile,
    Status, Request
)
from mptt.admin import DraggableMPTTAdmin
from mptt.admin import MPTTModelAdmin

@admin.register(Organization)
class OrganizationAdmin(MPTTModelAdmin):
    list_display = ('name', 'full_name', 'parent', 'inn')
    list_filter = ('name', 'full_name', 'parent')
    search_fields = ('name', 'full_name', 'parent', 'inn')
    mptt_level_indent = 20


@admin.register(OrganizationLocation)
class OrganizationLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

# --- Роли ---
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# --- Пользователи и Профили ---
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fk_name = 'user'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'get_role', 'get_organization', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('username',)

    def get_role(self, obj):
        return obj.profile.role.name if hasattr(obj, 'profile') and obj.profile.role else "-"
    get_role.short_description = 'Роль'

    def get_organization(self, obj):
        return obj.profile.department.organization.name if hasattr(obj, 'profile') and obj.profile.department else "-"
    get_organization.short_description = 'Организация'

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'is_active')
    list_filter = ('is_active', 'role', 'location')
    search_fields = ('last_name', 'first_name', 'middle_name', 'user__username')
    raw_id_fields = ('user',)

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'ФИО'

# --- Статусы ---
@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# --- Заявки ---
@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'get_status', 'get_customer', 'date_start', 'date_end', 'break_time', 'is_completed_fact')
    list_filter = ('status', 'equipment_category')
    search_fields = ('customer__last_name', 'responsible__last_name', 'comment')
    date_hierarchy = 'created_at'
    autocomplete_fields = ('customer', 'responsible', 'status')
    readonly_fields = ('created_at',)
    save_on_top = True

    def get_customer(self, obj):
        return obj.customer.full_name
    get_customer.short_description = 'Заказчик'

    def get_status(self, obj):
        return obj.status.name
    get_status.short_description = 'Статус'

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        user = request.user
        if not hasattr(user, 'profile') or user.profile.role.name != 'Логист':
            fields.append('status')
        return fields
    
