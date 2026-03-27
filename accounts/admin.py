from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Perfil", {"fields": ("profile",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Perfil", {"fields": ("profile",)}),)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "profile",
        "is_staff",
        "is_active",
    )
    list_filter = UserAdmin.list_filter + ("profile",)
