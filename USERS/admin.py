from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    pass
#    list_display = ("email", "username", "first_name", "last_name", "role", "is_active", "is_staff")
#    list_filter = ("role", "is_active", "is_staff", "is_superuser")
#    search_fields = ("email", "username", "first_name", "last_name")

#    fieldsets = (
#        (None, {'fields': ('username', 'password')}),
#        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'role')}),
#        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
#        ('Important dates', {'fields': ('last_login', 'date_joined')}),
#    )
    
#    add_fieldsets = (
#        (None, {
#            'classes': ('wide',),
#            'fields': ('username', 'email', 'password', 'role'),
#        }),
#    )
