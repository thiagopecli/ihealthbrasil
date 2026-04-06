from django.test import TestCase
from django.urls import reverse


class ApiDocsUrlsTests(TestCase):
    def test_schema_endpoint_available(self):
        response = self.client.get(reverse("api_schema"))

        self.assertEqual(response.status_code, 200)

    def test_swagger_endpoint_available(self):
        response = self.client.get(reverse("swagger_ui"))

        self.assertEqual(response.status_code, 200)


class ObservabilityEndpointsTests(TestCase):
    def test_healthcheck_returns_correlation_and_trace_headers(self):
        response = self.client.get(
            reverse("healthcheck"),
            HTTP_X_CORRELATION_ID="corr-health-123",
            HTTP_TRACEPARENT="00-0123456789abcdef0123456789abcdef-0123456789abcdef-01",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Correlation-ID"], "corr-health-123")
        self.assertEqual(response["X-Trace-Id"], "0123456789abcdef0123456789abcdef")
        self.assertIn("Traceparent", response)

    def test_metrics_endpoint_exposes_prometheus_text(self):
        response = self.client.get(reverse("metrics"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; version=0.0.4")
        self.assertIn("ihealthbrasil_http_requests_total", response.content.decode())
