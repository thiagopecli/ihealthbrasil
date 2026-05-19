from django.contrib.auth import get_user_model
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name", "profile", "phone_number")

    def validate_profile(self, value):
        if value == User.Profile.ADMIN:
            raise serializers.ValidationError("Perfil ADMIN nao pode ser definido no registro publico.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "profile",
            "phone_number",
            "is_active",
            "date_joined",
        )
        read_only_fields = fields


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class DetailMessageSerializer(serializers.Serializer):
    detail = serializers.CharField()


class GoogleOAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)
    client_id = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            id_token_value = data.get("id_token")
            client_id = data.get("client_id")

            request_obj = requests.Request()
            idinfo = id_token.verify_oauth2_token(id_token_value, request_obj, client_id)

            if idinfo.get("aud") != client_id:
                raise serializers.ValidationError("Token audience mismatch.")

            data["idinfo"] = idinfo
        except Exception as e:
            raise serializers.ValidationError(f"Invalid token: {str(e)}")

        return data

    def create(self, validated_data):
        idinfo = validated_data.get("idinfo")
        email = idinfo.get("email")
        name = idinfo.get("name", "").split(" ", 1)
        first_name = name[0] if name else ""
        last_name = name[1] if len(name) > 1 else ""

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": first_name,
                "last_name": last_name,
                "profile": User.Profile.PATIENT,
            },
        )

        if not created:
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            user.save()

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }
