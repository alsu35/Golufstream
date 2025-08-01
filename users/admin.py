from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import Department, Organization, Profile, User

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

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fk_name = 'user'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('email', 'get_role', 'get_organization', 'is_staff', 'is_superuser')
    search_fields = ('email',)
    ordering = ('email',)

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
    search_fields = ('last_name', 'first_name', 'middle_name', 'user__email')
    raw_id_fields = ('user',)
    list_select_related = ('department', 'department__organization', 'role', 'location')

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'ФИО'
