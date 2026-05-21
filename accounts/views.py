from typing import Any, cast

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from .audit import log_auth_event
from .models import AuthAuditEvent
from .permissions import HasAnyProfile
from .serializers import (
    DetailMessageSerializer,
    GoogleOAuthSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class AuditTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-login"

    def post(self, request, *args, **kwargs):
        request_data = cast(dict[str, Any], request.data)
        # Allow login with email: if username looks like an email, try to resolve the
        # actual username for authentication. This keeps compatibility with existing
        # frontend which posts 'username' as the email address.
        username = request_data.get("username", "")
        # Create a mutable copy of the data for serializer input
        mutable_data = dict(request.data)
        if username and "@" in username:
            user_by_email = User.objects.filter(email__iexact=username).first()
            if user_by_email:
                mutable_data["username"] = user_by_email.username

        user = User.objects.filter(username=mutable_data.get("username", "")).first()
        serializer = self.get_serializer(data=mutable_data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            log_auth_event(
                request=request,
                event_type=AuthAuditEvent.EventType.LOGIN,
                status=AuthAuditEvent.Status.FAILED,
                user=user,
                username=username,
                details={"reason": "invalid_credentials"},
            )
            raise

        if user:
            log_auth_event(
                request=request,
                event_type=AuthAuditEvent.EventType.LOGIN,
                status=AuthAuditEvent.Status.SUCCESS,
                user=user,
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-register"


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> Any:
        return self.request.user


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-logout"

    @extend_schema(request=LogoutSerializer, responses={205: None, 400: DetailMessageSerializer})
    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = cast(dict[str, Any], serializer.validated_data)
        refresh_raw = validated_data.get("refresh")

        try:
            refresh_token = RefreshToken(cast(Any, refresh_raw))
            refresh_token.blacklist()
        except TokenError:
            log_auth_event(
                request=request,
                event_type=AuthAuditEvent.EventType.LOGOUT,
                status=AuthAuditEvent.Status.FAILED,
                user=request.user,
                details={"reason": "invalid_or_expired_refresh"},
            )
            return Response({"detail": "Refresh token invalido ou expirado."}, status=status.HTTP_400_BAD_REQUEST)

        log_auth_event(
            request=request,
            event_type=AuthAuditEvent.EventType.LOGOUT,
            status=AuthAuditEvent.Status.SUCCESS,
            user=request.user,
        )

        return Response(status=status.HTTP_205_RESET_CONTENT)


class AdminOnlyView(APIView):
    permission_classes = [IsAuthenticated, HasAnyProfile]
    allowed_profiles = ["ADMIN"]
    serializer_class = DetailMessageSerializer

    @extend_schema(responses={200: DetailMessageSerializer})
    def get(self, _request, *args, **kwargs):
        return Response({"detail": "Acesso permitido para ADMIN."})


class ProviderOrAdminView(APIView):
    permission_classes = [IsAuthenticated, HasAnyProfile]
    allowed_profiles = ["PROVIDER", "ADMIN"]
    serializer_class = DetailMessageSerializer

    @extend_schema(responses={200: DetailMessageSerializer})
    def get(self, _request, *args, **kwargs):
        return Response({"detail": "Acesso permitido para PROVIDER ou ADMIN."})


class GoogleOAuthView(generics.CreateAPIView):
    serializer_class = GoogleOAuthSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-google"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        user = User.objects.get(email=serializer.validated_data["idinfo"]["email"])
        log_auth_event(
            request=request,
            event_type=AuthAuditEvent.EventType.LOGIN,
            status=AuthAuditEvent.Status.SUCCESS,
            user=user,
            details={"method": "google_oauth"},
        )

        return Response(result, status=status.HTTP_200_OK)


class AuditTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-refresh"


class AuditTokenVerifyView(TokenVerifyView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-verify"
