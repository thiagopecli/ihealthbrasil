from typing import Any

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .audit import log_auth_event
from .models import AuthAuditEvent
from .permissions import HasAnyProfile
from .serializers import DetailMessageSerializer, LogoutSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


class AuditTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get("username", "")
        user = User.objects.filter(username=username).first()
        serializer = self.get_serializer(data=request.data)

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


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> Any:
        return self.request.user


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(request=LogoutSerializer, responses={205: None, 400: DetailMessageSerializer})
    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_raw = serializer.validated_data.get("refresh")

        try:
            refresh_token = RefreshToken(str(refresh_raw))
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
