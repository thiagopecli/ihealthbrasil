from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import HasAnyProfile
from .serializers import LogoutSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


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

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_raw = serializer.validated_data.get("refresh")

        try:
            refresh_token = RefreshToken(str(refresh_raw))
            refresh_token.blacklist()
        except TokenError:
            return Response({"detail": "Refresh token invalido ou expirado."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_205_RESET_CONTENT)


class AdminOnlyView(APIView):
    permission_classes = [IsAuthenticated, HasAnyProfile]
    allowed_profiles = ["ADMIN"]

    def get(self, _request, *args, **kwargs):
        return Response({"detail": "Acesso permitido para ADMIN."})


class ProviderOrAdminView(APIView):
    permission_classes = [IsAuthenticated, HasAnyProfile]
    allowed_profiles = ["PROVIDER", "ADMIN"]

    def get(self, _request, *args, **kwargs):
        return Response({"detail": "Acesso permitido para PROVIDER ou ADMIN."})
