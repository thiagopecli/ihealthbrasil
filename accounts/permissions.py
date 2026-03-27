from rest_framework.permissions import BasePermission


class HasAnyProfile(BasePermission):
    """Permite acesso somente para usuarios com perfis definidos na view."""

    def has_permission(self, request, view):
        allowed_profiles = getattr(view, "allowed_profiles", [])
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.profile in allowed_profiles
