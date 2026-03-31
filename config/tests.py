from django.test import TestCase
from django.urls import reverse


class ApiDocsUrlsTests(TestCase):
    def test_schema_endpoint_available(self):
        response = self.client.get(reverse("api_schema"))

        self.assertEqual(response.status_code, 200)

    def test_swagger_endpoint_available(self):
        response = self.client.get(reverse("swagger_ui"))

        self.assertEqual(response.status_code, 200)
