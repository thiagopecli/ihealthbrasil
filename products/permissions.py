from rest_framework.permissions import BasePermission


class IsAdminOrReadOnly(BasePermission):
    """Permite leitura para todos, escrita apenas para admins."""

    def has_permission(self, request, view):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return request.user and request.user.is_staff


class IsProviderOrAdminProfile(BasePermission):
    """Permite apenas perfis de fornecedor/admin (ou staff) para painel parceiro."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_staff:
            return True

        return getattr(user, "profile", None) in ["PROVIDER", "ADMIN"]
