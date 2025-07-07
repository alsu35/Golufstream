from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError
from .models import (
    Organization, OrganizationLocation, User, Role, Profile,
    Status, Request, Department, Category
)

@admin.register(OrganizationLocation)
class OrganizationLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin): 
    list_display = ('name', 'full_name', 'inn')
    list_filter = ('name', 'full_name', 'inn')
    search_fields = ('name', 'full_name', 'inn')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization')
    list_filter = ('organization',)
    search_fields = ('name', 'organization__name')
    raw_id_fields = ('organization',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    list_filter = ('code',)


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
        return obj.profile.role.name if hasattr(obj, 'profile') and obj.profile.role else '-'
    get_role.short_description = 'Роль'

    def get_organization(self, obj):
        dept = getattr(obj.profile, 'department', None)
        return dept.organization.name if dept and dept.organization else '-'
    get_organization.short_description = 'Организация'

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'is_active')
    list_filter = ('is_active', 'role', 'location')
    search_fields = ('last_name', 'first_name', 'middle_name', 'user__username')
    raw_id_fields = ('user',)
    list_select_related = ('department', 'department__organization', 'role', 'location')

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'ФИО'

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'created_at', 'get_status', 'get_customer',
        'date_start', 'date_end', 'break_periods', 'is_completed_fact'
    )
    list_filter = ('status', 'equipment_category')
    search_fields = ('customer__last_name', 'responsible__last_name', 'comment')
    date_hierarchy = 'created_at'
    autocomplete_fields = ('customer', 'responsible')
    readonly_fields = ('created_at',)
    save_on_top = True

    def get_status(self, obj):
        return obj.status.name
    get_status.short_description = 'Статус'

    def get_customer(self, obj):
        return obj.customer.full_name
    get_customer.short_description = 'Заказчик'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'status', 'customer__department__organization', 'equipment_category'
        )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and not request.user.groups.filter(name='admin').exists():
            readonly.append('status')
        return readonly

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser and not request.user.groups.filter(name='admin').exists():
            try:
                obj.status = Status.objects.get(code='new')
            except Status.DoesNotExist:
                raise ValidationError("Статус 'new' не найден")
        super().save_model(request, obj, form, change)
