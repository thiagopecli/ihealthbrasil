from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuthAuditEvent, User


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


@admin.register(AuthAuditEvent)
class AuthAuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "event_type",
        "status",
        "username_snapshot",
        "profile_snapshot",
        "ip_address",
    )
    list_filter = ("event_type", "status", "profile_snapshot", "created_at")
    search_fields = ("username_snapshot", "user__username", "ip_address")
    readonly_fields = (
        "user",
        "username_snapshot",
        "profile_snapshot",
        "event_type",
        "status",
        "ip_address",
        "user_agent",
        "details",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
