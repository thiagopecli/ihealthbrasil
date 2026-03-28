from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AccountsAPITests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.password = "StrongPass@123"

        self.admin_user = self.user_model.objects.create_user(
            username="admin_user",
            email="admin@example.com",
            password=self.password,
            profile=self.user_model.Profile.ADMIN,
            is_staff=True,
        )

        self.provider_user = self.user_model.objects.create_user(
            username="provider_user",
            email="provider@example.com",
            password=self.password,
            profile=self.user_model.Profile.PROVIDER,
        )

        self.patient_user = self.user_model.objects.create_user(
            username="patient_user",
            email="patient@example.com",
            password=self.password,
            profile=self.user_model.Profile.PATIENT,
        )

    def _login(self, username, password):
        url = reverse("token_obtain_pair")
        response = self.client.post(url, {"username": username, "password": password}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        return response.data

    def test_register_public_user_success(self):
        url = reverse("register")
        payload = {
            "username": "new_user",
            "email": "new_user@example.com",
            "password": self.password,
            "first_name": "Novo",
            "last_name": "Usuario",
            "profile": self.user_model.Profile.PATIENT,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.user_model.objects.filter(username="new_user").exists())

    def test_register_admin_profile_forbidden(self):
        url = reverse("register")
        payload = {
            "username": "new_admin",
            "email": "new_admin@example.com",
            "password": self.password,
            "profile": self.user_model.Profile.ADMIN,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile", response.data)

    def test_me_requires_auth_and_returns_authenticated_user(self):
        me_url = reverse("me")

        unauth_response = self.client.get(me_url)
        self.assertEqual(unauth_response.status_code, status.HTTP_401_UNAUTHORIZED)

        tokens = self._login("patient_user", self.password)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        auth_response = self.client.get(me_url)
        self.assertEqual(auth_response.status_code, status.HTTP_200_OK)
        self.assertEqual(auth_response.data["username"], "patient_user")

    def test_logout_blacklists_refresh_token(self):
        tokens = self._login("patient_user", self.password)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        logout_url = reverse("logout")
        logout_response = self.client.post(logout_url, {"refresh": tokens["refresh"]}, format="json")

        self.assertEqual(logout_response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_rbac_admin_only(self):
        url = reverse("rbac_admin_only")

        patient_tokens = self._login("patient_user", self.password)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {patient_tokens['access']}")
        denied_response = self.client.get(url)
        self.assertEqual(denied_response.status_code, status.HTTP_403_FORBIDDEN)

        admin_tokens = self._login("admin_user", self.password)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_tokens['access']}")
        allowed_response = self.client.get(url)
        self.assertEqual(allowed_response.status_code, status.HTTP_200_OK)

    def test_rbac_provider_or_admin(self):
        url = reverse("rbac_provider_or_admin")

        provider_tokens = self._login("provider_user", self.password)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {provider_tokens['access']}")
        provider_response = self.client.get(url)
        self.assertEqual(provider_response.status_code, status.HTTP_200_OK)

        patient_tokens = self._login("patient_user", self.password)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {patient_tokens['access']}")
        patient_response = self.client.get(url)
        self.assertEqual(patient_response.status_code, status.HTTP_403_FORBIDDEN)
