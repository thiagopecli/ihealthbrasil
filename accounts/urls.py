from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import AdminOnlyView, AuditTokenObtainPairView, LogoutView, MeView, ProviderOrAdminView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", AuditTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("rbac/admin-only/", AdminOnlyView.as_view(), name="rbac_admin_only"),
    path("rbac/provider-or-admin/", ProviderOrAdminView.as_view(), name="rbac_provider_or_admin"),
]
