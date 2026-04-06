from django.test import SimpleTestCase

from products.audit import _sanitize_payload
from products.notifications import mask_email_address


class LgpdSanitizationTests(SimpleTestCase):
    def test_mask_email_address_masks_local_part(self):
        masked = mask_email_address("paciente.teste@example.com")

        self.assertEqual(masked, "p***e@example.com")

    def test_sanitize_payload_redacts_contact_fields(self):
        payload = {
            "recipient": "paciente.teste@example.com",
            "phone_number": "+5511999999999",
            "nested": {
                "email": "medico@example.com",
            },
        }

        sanitized = _sanitize_payload(payload)

        self.assertEqual(sanitized["recipient"], "[REDACTED]")
        self.assertEqual(sanitized["phone_number"], "[REDACTED]")
        self.assertEqual(sanitized["nested"]["email"], "[REDACTED]")
