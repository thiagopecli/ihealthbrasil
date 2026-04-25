# pyright: reportAttributeAccessIssue=false

import hashlib
import hmac
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from config.observability import bind_observability_context
from products.models import (
    Cart,
    Category,
    MedicalPrescription,
    Order,
    PaymentConnectedAccount,
    PaymentCustomer,
    PaymentIntent,
    PaymentTransaction,
    PaymentWebhookEvent,
    PrescriptionAccessAudit,
    Product,
    ProductDosage,
    ProductPackageInsert,
    ProductPrice,
    ProductVariation,
    SalesRestriction,
)
from products.tasks import enqueue_order_status_sms

WEBHOOK_TEST_SECRET = "webhook-test-secret"


class ProductsAPITests(APITestCase):
    def setUp(self):
        user_model: Any = get_user_model()
        self.client: Any = self.client
        self.user = user_model.objects.create_user(
            username="catalog_user",
            email="catalog_user@example.com",
            profile=user_model.Profile.PATIENT,
            is_staff=False,
        )

        self.admin = user_model.objects.create_user(
            username="catalog_admin",
            email="catalog_admin@example.com",
            profile=user_model.Profile.ADMIN,
            is_staff=True,
        )

        self.category = Category.objects.create(name="Analgésicos", description="Dor e febre")

        self.product = Product.objects.create(
            category=self.category,
            name="Dipirona 500mg",
            description="Medicamento para dor e febre",
            price=Decimal("10.90"),
            requires_prescription=False,
            active_ingredient="Dipirona",
            controlled_substance_class="",
            min_age_required=12,
            max_age_allowed=0,
            stock=50,
            sku="DIP-500",
            is_active=True,
        )

        self.product_rx = Product.objects.create(
            category=self.category,
            name="Antibiótico X",
            description="Uso com prescrição",
            price=Decimal("89.90"),
            requires_prescription=True,
            active_ingredient="Amoxicilina",
            controlled_substance_class="C1",
            min_age_required=18,
            max_age_allowed=0,
            stock=10,
            sku="ATB-100",
            is_active=True,
        )

        ProductVariation.objects.create(
            product=self.product,
            name="Concentração",
            value="500mg",
            sku_suffix="500",
            price_modifier=Decimal("0.00"),
            stock=50,
        )

        ProductDosage.objects.create(
            product=self.product,
            strength="500",
            unit="mg",
            frequency_recommendation="8/8h",
            is_default=True,
        )

        ProductPackageInsert.objects.create(
            product=self.product,
            language="pt_BR",
            title="Bula Dipirona",
            content="Conteúdo da bula",
            requires_prescription_note=False,
        )
        ProductPackageInsert.objects.create(
            product=self.product,
            language="en_US",
            title="Dipyrone Package Insert",
            content="Package insert content",
            requires_prescription_note=False,
        )
        ProductPackageInsert.objects.create(
            product=self.product,
            language="es_ES",
            title="Prospecto Dipirona",
            content="Contenido del prospecto",
            requires_prescription_note=False,
        )
        ProductPackageInsert.objects.create(
            product=self.product,
            language="fr_FR",
            title="Notice Dipyrone",
            content="Contenu de la notice",
            requires_prescription_note=False,
        )

        ProductPrice.objects.create(product=self.product, country_code="BR", currency="BRL", amount=Decimal("10.90"))
        ProductPrice.objects.create(product=self.product, country_code="US", currency="USD", amount=Decimal("2.10"))
        ProductPrice.objects.create(product=self.product, country_code="ES", currency="EUR", amount=Decimal("1.95"))

        SalesRestriction.objects.create(
            product=self.product,
            restriction_type="age_min",
            description="Apenas acima de 12 anos",
            detail="Uso pediátrico com avaliação médica",
            is_active=True,
        )

    def test_category_list_public_and_create_requires_admin(self):
        list_response = self.client.get("/api/categories/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        payload = {"name": "Vitaminas", "description": "Suplementação"}
        denied_response = self.client.post("/api/categories/", payload, format="json")
        self.assertEqual(denied_response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.admin)
        allowed_response = self.client.post("/api/categories/", payload, format="json")
        self.assertEqual(allowed_response.status_code, status.HTTP_201_CREATED)

    def test_products_list_supports_search_filter_ordering_and_pagination(self):
        response = self.client.get(
            "/api/products/?search=dipirona&category_slug=analgesicos&ordering=price&page=1&page_size=10"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.product.slug)

    def test_requires_prescription_endpoint(self):
        response = self.client.get("/api/products/requires_prescription/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.product_rx.slug)

    def test_nested_product_endpoints(self):
        response = self.client.get(f"/api/products/{self.product.slug}/variations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["variations"]), 1)

        response = self.client.get(f"/api/products/{self.product.slug}/dosages/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["dosages"]), 1)

        response = self.client.get(f"/api/products/{self.product.slug}/package_inserts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["package_inserts"]), 1)
        self.assertEqual(response.data["package_inserts"][0]["language"], "pt_BR")

        response = self.client.get(f"/api/products/{self.product.slug}/restrictions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["restrictions"]), 1)

    def test_package_inserts_uses_accept_language_with_fallback(self):
        response = self.client.get(
            f"/api/products/{self.product.slug}/package_inserts/",
            HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["package_inserts"]), 1)
        self.assertEqual(response.data["package_inserts"][0]["language"], "en_US")

        response = self.client.get(
            f"/api/products/{self.product.slug}/package_inserts/",
            HTTP_ACCEPT_LANGUAGE="de-DE,de;q=0.9",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["package_inserts"][0]["language"], "pt_BR")

    def test_catalog_price_changes_by_country_and_currency(self):
        response = self.client.get(
            "/api/products/",
            HTTP_X_COUNTRY="US",
            HTTP_X_CURRENCY="USD",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target_product = next(item for item in response.data["results"] if item["slug"] == self.product.slug)
        self.assertEqual(target_product["price_currency"], "USD")
        self.assertEqual(target_product["price_country"], "US")

        response_fallback = self.client.get(
            "/api/products/",
            HTTP_X_COUNTRY="DE",
            HTTP_X_CURRENCY="EUR",
        )
        self.assertEqual(response_fallback.status_code, status.HTTP_200_OK)
        fallback_product = next(item for item in response_fallback.data["results"] if item["slug"] == self.product.slug)
        self.assertEqual(fallback_product["price_currency"], "EUR")
        self.assertEqual(fallback_product["price_is_fallback"], False)

    def test_product_detail_returns_localized_insert_and_price(self):
        response = self.client.get(
            f"/api/products/{self.product.slug}/",
            HTTP_ACCEPT_LANGUAGE="es-ES,es;q=0.9",
            HTTP_X_COUNTRY="ES",
            HTTP_X_CURRENCY="EUR",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["price_currency"], "EUR")
        self.assertEqual(response.data["price_country"], "ES")
        self.assertEqual(len(response.data["package_inserts"]), 1)
        self.assertEqual(response.data["package_inserts"][0]["language"], "es_ES")

    def test_package_inserts_supports_french_language(self):
        response = self.client.get(
            f"/api/products/{self.product.slug}/package_inserts/",
            HTTP_ACCEPT_LANGUAGE="fr-FR,fr;q=0.9",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["package_inserts"]), 1)
        self.assertEqual(response.data["package_inserts"][0]["language"], "fr_FR")

    def test_variations_dosages_package_inserts_and_restrictions_filter_by_product_slug(self):
        variation_response = self.client.get(f"/api/variations/?product_slug={self.product.slug}")
        self.assertEqual(variation_response.status_code, status.HTTP_200_OK)
        self.assertEqual(variation_response.data["count"], 1)

        dosage_response = self.client.get(f"/api/dosages/?product_slug={self.product.slug}")
        self.assertEqual(dosage_response.status_code, status.HTTP_200_OK)
        self.assertEqual(dosage_response.data["count"], 1)

        insert_response = self.client.get(f"/api/package-inserts/?product_slug={self.product.slug}")
        self.assertEqual(insert_response.status_code, status.HTTP_200_OK)
        self.assertEqual(insert_response.data["count"], 1)

        restriction_response = self.client.get(f"/api/sales-restrictions/?product_slug={self.product.slug}")
        self.assertEqual(restriction_response.status_code, status.HTTP_200_OK)
        self.assertEqual(restriction_response.data["count"], 1)

    def test_catalog_write_requires_admin_for_all_resources(self):
        write_targets = [
            ("/api/categories/", {"name": "Fitoterapia", "description": "Produtos naturais"}),
            (
                "/api/products/",
                {
                    "name": "Melatonina 3mg",
                    "description": "Auxiliar no sono",
                    "price": "49.90",
                    "requires_prescription": False,
                    "active_ingredient": "Melatonina",
                    "controlled_substance_class": "",
                    "min_age_required": 18,
                    "max_age_allowed": 0,
                    "stock": 20,
                    "sku": "MEL-3MG",
                    "category": self.category.id,
                    "is_active": True,
                },
            ),
            ("/api/variations/", {"name": "Concentracao", "value": "3mg", "sku_suffix": "3MG", "stock": 5}),
            ("/api/dosages/", {"strength": "3", "unit": "mg", "is_default": True}),
            (
                "/api/package-inserts/",
                {
                    "language": "pt_BR",
                    "title": "Bula Melatonina",
                    "content": "Conteudo",
                    "requires_prescription_note": False,
                },
            ),
            (
                "/api/sales-restrictions/",
                {
                    "restriction_type": "age_min",
                    "description": "Somente maiores de 18",
                    "detail": "Validacao por documento",
                    "is_active": True,
                },
            ),
        ]

        for url, payload in write_targets:
            anonymous_response = self.client.post(url, payload, format="json")
            self.assertEqual(anonymous_response.status_code, status.HTTP_401_UNAUTHORIZED)

            self.client.force_authenticate(user=self.user)
            non_admin_response = self.client.post(url, payload, format="json")
            self.assertEqual(non_admin_response.status_code, status.HTTP_403_FORBIDDEN)
            self.client.force_authenticate(user=None)

    def test_category_and_product_create_allowed_for_admin(self):
        self.client.force_authenticate(user=self.admin)

        category_payload = {"name": "Suplementos", "description": "Produtos de suporte nutricional"}
        category_response = self.client.post("/api/categories/", category_payload, format="json")
        self.assertEqual(category_response.status_code, status.HTTP_201_CREATED)

        product_payload = {
            "name": "Vitamina D 2000UI",
            "description": "Suplementacao diaria",
            "price": "39.90",
            "requires_prescription": False,
            "active_ingredient": "Colecalciferol",
            "controlled_substance_class": "",
            "min_age_required": 12,
            "max_age_allowed": 0,
            "stock": 80,
            "sku": "VITD-2000",
            "category": self.category.id,
            "is_active": True,
        }

        product_response = self.client.post("/api/products/", product_payload, format="json")
        self.assertEqual(product_response.status_code, status.HTTP_201_CREATED)


class OrderAPITests(APITestCase):
    """Testes para gerenciamento de pedidos (Sprint 4/5)."""

    def setUp(self):
        user_model = get_user_model()
        self.patient = user_model.objects.create_user(
            username="patient_user",
            email="patient@example.com",
            profile=user_model.Profile.PATIENT,
        )

        self.admin = user_model.objects.create_user(
            username="order_admin",
            email="admin@example.com",
            profile=user_model.Profile.ADMIN,
            is_staff=True,
        )

        self.category = Category.objects.create(name="Medicamentos", description="Diversos")
        self.product = Product.objects.create(
            category=self.category,
            name="Teste Meds",
            description="Para testes",
            price=Decimal("50.00"),
            requires_prescription=False,
            stock=10,
            sku="TST-001",
        )

    def test_patient_can_list_own_orders_only(self):
        """Paciente vê apenas seus pedidos."""
        Order.objects.create(user=self.patient, total_price=Decimal("100.00"))
        Order.objects.create(user=self.admin, total_price=Decimal("200.00"))  # Pedido de outro usuário

        self.client.force_authenticate(user=self.patient)
        response = self.client.get("/api/orders/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["user"], self.patient.username)

    def test_admin_can_list_all_orders(self):
        """Admin vê todos os pedidos."""
        Order.objects.create(user=self.patient, total_price=Decimal("100.00"))
        Order.objects.create(user=self.admin, total_price=Decimal("200.00"))

        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/orders/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_unauthenticated_cannot_access_orders(self):
        """Acesso não autenticado retorna 401."""
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CartCheckoutAPITests(APITestCase):
    """Testes de carrinho persistente e checkout (Sprint 4)."""

    def setUp(self):
        user_model = get_user_model()
        self.patient = user_model.objects.create_user(
            username="cart_patient",
            email="cart_patient@example.com",
            profile=user_model.Profile.PATIENT,
        )

        self.provider = user_model.objects.create_user(
            username="cart_provider",
            email="cart_provider@example.com",
            profile=user_model.Profile.PROVIDER,
        )

        self.category = Category.objects.create(name="Carrinho", description="Produtos para testes de carrinho")
        self.product = Product.objects.create(
            category=self.category,
            provider=self.provider,
            name="Produto Carrinho",
            description="Produto base para testes",
            price=Decimal("19.90"),
            requires_prescription=False,
            stock=10,
            sku="CRT-001",
            is_active=True,
        )

        self.product_variation = ProductVariation.objects.create(
            product=self.product,
            name="Dose",
            value="500mg",
            sku_suffix="500",
            price_modifier=Decimal("2.00"),
            stock=8,
        )

    def test_authenticated_user_gets_persistent_cart(self):
        self.client.force_authenticate(user=self.patient)
        response = self.client.get("/api/carts/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(response.data["total_price"], "0.00")

    def test_add_update_remove_and_clear_cart_items(self):
        self.client.force_authenticate(user=self.patient)

        add_response = self.client.post(
            "/api/carts/items/",
            {
                "product_id": self.product.id,
                "product_variation_id": self.product_variation.id,
                "quantity": 2,
            },
            format="json",
        )
        self.assertEqual(add_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(add_response.data["items"]), 1)
        self.assertEqual(add_response.data["total_price"], "43.80")

        item_id = add_response.data["items"][0]["id"]
        patch_response = self.client.patch(
            f"/api/carts/items/{item_id}/",
            {"quantity": 3},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["items"][0]["quantity"], 3)
        self.assertEqual(patch_response.data["total_price"], "65.70")

        remove_response = self.client.delete(f"/api/carts/items/{item_id}/")
        self.assertEqual(remove_response.status_code, status.HTTP_200_OK)
        self.assertEqual(remove_response.data["items"], [])
        self.assertEqual(remove_response.data["total_price"], "0.00")

        self.client.post(
            "/api/carts/items/",
            {
                "product_id": self.product.id,
                "quantity": 1,
            },
            format="json",
        )
        clear_response = self.client.delete("/api/carts/clear/")
        self.assertEqual(clear_response.status_code, status.HTTP_200_OK)
        self.assertEqual(clear_response.data["items"], [])
        self.assertEqual(clear_response.data["total_price"], "0.00")

    def test_checkout_creates_order_and_order_items_and_clears_cart(self):
        self.client.force_authenticate(user=self.patient)

        self.client.post(
            "/api/carts/items/",
            {
                "product_id": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        checkout_response = self.client.post(
            "/api/carts/checkout/",
            {
                "shipping_address": "Rua A, 123 - Sao Paulo/SP",
                "notes": "Entregar no periodo da tarde",
            },
            format="json",
        )

        self.assertEqual(checkout_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(checkout_response.data["total_price"], "39.80")
        self.assertEqual(len(checkout_response.data["items"]), 1)
        self.assertEqual(checkout_response.data["items"][0]["quantity"], 2)

        order = Order.objects.get(id=checkout_response.data["id"])
        self.assertEqual(order.user_id, self.patient.id)
        self.assertEqual(order.provider_id, self.provider.id)
        self.assertEqual(order.total_price, Decimal("39.80"))

        cart = Cart.objects.get(user=self.patient)
        self.assertEqual(cart.items.count(), 0)
        self.assertEqual(cart.total_price, Decimal("0.00"))

    def test_checkout_with_empty_cart_returns_400(self):
        self.client.force_authenticate(user=self.patient)
        response = self.client.post("/api/carts/checkout/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Carrinho vazio.")

    def test_add_item_above_stock_returns_400(self):
        self.client.force_authenticate(user=self.patient)
        response = self.client.post(
            "/api/carts/items/",
            {
                "product_id": self.product.id,
                "quantity": 999,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)


@override_settings(SHIPPING_PROVIDER="mock", SHIPPING_ORIGIN_CEP="01001000")
class ShippingQuoteAPITests(APITestCase):
    """Testes da cotacao de frete por carrinho."""

    def setUp(self):
        user_model = get_user_model()
        self.patient = user_model.objects.create_user(
            username="shipping_patient",
            email="shipping_patient@example.com",
            profile=user_model.Profile.PATIENT,
        )

        self.provider = user_model.objects.create_user(
            username="shipping_provider",
            email="shipping_provider@example.com",
            profile=user_model.Profile.PROVIDER,
        )

        self.category = Category.objects.create(name="Frete", description="Produtos para teste de frete")
        self.product = Product.objects.create(
            category=self.category,
            provider=self.provider,
            name="Produto Frete",
            description="Produto base para teste de frete",
            price=Decimal("39.90"),
            requires_prescription=False,
            stock=10,
            sku="FRT-001",
            is_active=True,
        )

    def test_shipping_quote_returns_options_for_cart(self):
        self.client.force_authenticate(user=self.patient)

        self.client.post(
            "/api/carts/items/",
            {
                "product_id": self.product.id,
                "quantity": 2,
            },
            format="json",
        )

        response = self.client.post(
            "/api/carts/shipping-quote/",
            {"cep": "01310-100"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["provider_name"], "mock")
        self.assertEqual(response.data["origin_cep"], "01001000")
        self.assertEqual(response.data["destination_cep"], "01310100")
        self.assertEqual(len(response.data["services"]), 2)
        self.assertEqual({service["service_code"] for service in response.data["services"]}, {"04014", "04510"})

    def test_shipping_quote_rejects_invalid_cep(self):
        self.client.force_authenticate(user=self.patient)

        self.client.post(
            "/api/carts/items/",
            {
                "product_id": self.product.id,
                "quantity": 1,
            },
            format="json",
        )

        response = self.client.post(
            "/api/carts/shipping-quote/",
            {"cep": "123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cep", response.data)

    def test_shipping_quote_with_empty_cart_returns_400(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(
            "/api/carts/shipping-quote/",
            {"cep": "01310-100"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Carrinho vazio.")


class MedicalPrescriptionAPITests(APITestCase):
    """Testes de upload e auditoria de receitas (Sprint 5)."""

    def setUp(self):
        from io import BytesIO

        user_model = get_user_model()
        self.patient = user_model.objects.create_user(
            username="rx_patient",
            email="patient_rx@example.com",
            profile=user_model.Profile.PATIENT,
        )

        self.admin = user_model.objects.create_user(
            username="rx_admin",
            email="admin_rx@example.com",
            profile=user_model.Profile.ADMIN,
            is_staff=True,
        )

        self.category = Category.objects.create(name="Controlados", description="Medicamentos controlados")
        self.product_rx = Product.objects.create(
            category=self.category,
            name="Med Controlado",
            description="Uso com receita",
            price=Decimal("150.00"),
            requires_prescription=True,
            controlled_substance_class="C2",
            stock=5,
            sku="CTR-001",
        )

        self.order = Order.objects.create(user=self.patient, status=Order.Status.PENDING, total_price=Decimal("150.00"))

        # Criar um arquivo mock para testes
        self.prescription_file_content = BytesIO(b"PDF prescription data - mock")
        self.prescription_file_content.name = "prescription.pdf"

    def test_patient_can_upload_prescription(self):
        """Paciente pode fazer upload de receita para seu pedido."""
        self.client.force_authenticate(user=self.patient)

        from io import BytesIO

        file_content = BytesIO(b"Mock prescription PDF")
        file_content.name = "my_prescription.pdf"

        payload = {
            "order": self.order.id,
            "prescription_type": "DIGITAL_PHOTO",
            "file": file_content,
            "prescriber_name": "Dr. Silva",
            "prescription_date": "2026-04-01",
        }

        response = self.client.post("/api/prescriptions/", payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], MedicalPrescription.Status.SUBMITTED)

        # Verificar se log de auditoria foi criado
        self.assertTrue(PrescriptionAccessAudit.objects.filter(action="UPLOADED").exists())

    def test_prescription_access_audit_log_created_on_download(self):
        """Log de auditoria é criado quando receita é baixada."""
        upload = SimpleUploadedFile("prescription.pdf", b"PDF prescription data - mock", content_type="application/pdf")
        prescription = MedicalPrescription.objects.create(
            order=self.order,
            prescription_type="DIGITAL_PHOTO",
            status=MedicalPrescription.Status.VERIFIED,
            file=upload,
        )

        self.client.force_authenticate(user=self.patient)
        signed_response = self.client.get(f"/api/prescriptions/{prescription.id}/download/")

        self.assertEqual(signed_response.status_code, status.HTTP_200_OK)
        self.assertIn("download_url", signed_response.data)
        parsed = urlparse(signed_response.data["download_url"])
        token = parse_qs(parsed.query).get("token", [None])[0]
        self.assertIsNotNone(token)

        response = self.client.get(f"/api/prescriptions/secure-download/?token={token}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get("Content-Type"), "application/pdf")
        # Verificar log criado
        log = PrescriptionAccessAudit.objects.filter(
            prescription=prescription, action=PrescriptionAccessAudit.Action.DOWNLOADED
        ).first()
        self.assertIsNotNone(log)

    def test_only_admin_can_verify_prescription(self):
        """Apenas admin pode aprovar receita."""
        prescription = MedicalPrescription.objects.create(
            order=self.order,
            prescription_type="DIGITAL_PHOTO",
            status=MedicalPrescription.Status.SUBMITTED,
        )
        prescription.file.name = "prescription.pdf"
        prescription.save()

        # Paciente tenta verificar - deve falhar
        self.client.force_authenticate(user=self.patient)
        response = self.client.post(
            f"/api/orders/{self.order.id}/approve_prescription/", {"notes": "Approved"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin verifica - deve funcionar
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/orders/{self.order.id}/approve_prescription/", {"notes": "Approved by admin"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_prescription_access_logs_endpoint_admin_only(self):
        """Endpoint de auditoria de receita é apenas para admin."""
        MedicalPrescription.objects.create(
            order=self.order,
            prescription_type="DIGITAL_PHOTO",
            status=MedicalPrescription.Status.VERIFIED,
        )

        self.client.force_authenticate(user=self.patient)
        response = self.client.get("/api/prescription-audit/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/prescription-audit/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@override_settings(PAYMENT_GATEWAY_PROVIDER="mock")
class OrderPaymentIntentAPITests(APITestCase):
    """Testes de pagamento/split (Sprint 6)."""

    def setUp(self):
        user_model = get_user_model()
        self.patient = user_model.objects.create_user(
            username="payment_patient",
            email="payment_patient@example.com",
            profile=user_model.Profile.PATIENT,
        )
        self.provider = user_model.objects.create_user(
            username="payment_provider",
            email="payment_provider@example.com",
            profile=user_model.Profile.PROVIDER,
        )
        self.admin = user_model.objects.create_user(
            username="payment_admin",
            email="payment_admin@example.com",
            profile=user_model.Profile.ADMIN,
            is_staff=True,
        )

        self.order = Order.objects.create(
            user=self.patient,
            status=Order.Status.PENDING,
            total_price=Decimal("199.90"),
        )

    def test_patient_can_create_payment_intent_for_own_order(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(
            f"/api/orders/{self.order.id}/payment-intent/",
            {"currency": "brl"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["gateway"], "mock")
        self.assertIn("gateway_payment_intent_id", response.data)
        self.assertIn("client_secret", response.data)
        self.assertIn("checkout_url", response.data)
        self.assertTrue(PaymentIntent.objects.filter(order=self.order).exists())
        self.assertTrue(PaymentCustomer.objects.filter(user=self.patient, gateway="mock").exists())

    def test_create_payment_intent_with_provider_creates_connected_account(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(
            f"/api/orders/{self.order.id}/payment-intent/",
            {"provider_user_id": self.provider.id, "currency": "brl"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["metadata"]["provider_user_id"], self.provider.id)
        self.assertTrue(PaymentConnectedAccount.objects.filter(user=self.provider, gateway="mock").exists())

    def test_patient_cannot_create_payment_intent_for_other_user_order(self):
        other_order = Order.objects.create(
            user=self.admin,
            status=Order.Status.PENDING,
            total_price=Decimal("350.00"),
        )
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(f"/api/orders/{other_order.id}/payment-intent/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_currency_message_is_localized(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(
            f"/api/orders/{self.order.id}/payment-intent/",
            {"currency": "1$2"},
            format="json",
            HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("currency", response.data)
        self.assertIn("Currency must contain letters only", response.data["currency"][0])

    def test_invalid_currency_message_is_localized_in_french(self):
        self.client.force_authenticate(user=self.patient)

        response = self.client.post(
            f"/api/orders/{self.order.id}/payment-intent/",
            {"currency": "1$2"},
            format="json",
            HTTP_ACCEPT_LANGUAGE="fr-FR,fr;q=0.9",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("currency", response.data)
        self.assertIn("La devise doit contenir uniquement des lettres", response.data["currency"][0])


@override_settings(PAYMENT_WEBHOOK_SECRET=WEBHOOK_TEST_SECRET, CELERY_TASK_ALWAYS_EAGER=True)  # nosec B106
class PaymentWebhookAPITests(APITestCase):
    """Testes para split de pagamento e webhook de atualização de status."""

    webhook_url = "/api/payments/webhooks/gateway/"

    def setUp(self):
        user_model = get_user_model()
        self.patient = user_model.objects.create_user(
            username="payment_patient_webhook",
            email="payment_patient_webhook@example.com",
            profile=user_model.Profile.PATIENT,
        )
        self.provider = user_model.objects.create_user(
            username="payment_provider_webhook",
            email="payment_provider_webhook@example.com",
            profile=user_model.Profile.PROVIDER,
        )

        self.order = Order.objects.create(
            user=self.patient,
            provider=self.provider,
            total_price=Decimal("100.00"),
            commission_rate=Decimal("15.00"),
            gateway_reference="ORD-100",
        )

    @staticmethod
    def _signed_request_payload(payload: dict, secret: str):
        raw_payload = json.dumps(payload, separators=(",", ":"))
        signature = hmac.new(secret.encode("utf-8"), raw_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return raw_payload, signature

    @patch("products.views.enqueue_order_status_sms")
    def test_webhook_pagamento_aprovado_calcula_split_e_muda_pedido_para_pago(self, mock_enqueue):
        payload = {
            "event_id": "evt-approved-1",
            "event": "payment.approved",
            "data": {
                "order_id": self.order.id,
                "transaction_id": "tx-approved-1",
                "payment_method": "PIX",
                "gateway": "asaas",
            },
        }
        raw_payload, signature = self._signed_request_payload(payload, WEBHOOK_TEST_SECRET)

        response = self.client.post(
            self.webhook_url,
            data=raw_payload,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
            HTTP_X_CORRELATION_ID="corr-webhook-123",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["X-Correlation-ID"], "corr-webhook-123")
        self.assertTrue(response.data["processed"])

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)

        payment = self.order.payment
        self.assertEqual(payment.gateway_status, "APPROVED")
        self.assertEqual(payment.gross_amount, Decimal("100.00"))
        self.assertEqual(payment.provider_amount, Decimal("85.00"))
        self.assertEqual(payment.ihealth_commission_amount, Decimal("15.00"))
        self.assertTrue(payment.is_split_calculated)
        mock_enqueue.assert_called_once_with(
            order_id=self.order.id,
            event_name="payment.approved",
            status_value=Order.Status.PAID,
        )
        event = PaymentWebhookEvent.objects.get(event_id="evt-approved-1")
        self.assertEqual(event.payload["observability"]["correlation_id"], "corr-webhook-123")

    def test_webhook_boleto_vencido_cancela_pedido(self):
        payload = {
            "event_id": "evt-expired-1",
            "event": "boleto.expired",
            "data": {
                "order_id": self.order.id,
                "transaction_id": "tx-expired-1",
                "payment_method": "BOLETO",
            },
        }
        raw_payload, signature = self._signed_request_payload(payload, WEBHOOK_TEST_SECRET)

        response = self.client.post(
            self.webhook_url,
            data=raw_payload,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.order.payment.gateway_status, "EXPIRED")

    @patch("products.views.enqueue_order_status_sms")
    def test_webhook_evento_duplicado_e_idempotente(self, mock_enqueue):
        payload = {
            "event_id": "evt-duplicate-1",
            "event": "payment.approved",
            "data": {
                "order_id": self.order.id,
                "transaction_id": "tx-duplicate-1",
                "payment_method": "PIX",
            },
        }
        raw_payload, signature = self._signed_request_payload(payload, WEBHOOK_TEST_SECRET)

        first_response = self.client.post(
            self.webhook_url,
            data=raw_payload,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )
        second_response = self.client.post(
            self.webhook_url,
            data=raw_payload,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertFalse(second_response.data["processed"])
        self.assertTrue(second_response.data["duplicate"])
        mock_enqueue.assert_called_once()

    def test_webhook_assinatura_invalida_retorna_401(self):
        payload = {
            "event_id": "evt-invalid-signature",
            "event": "payment.approved",
            "data": {"order_id": self.order.id, "transaction_id": "tx-invalid-signature"},
        }
        raw_payload, _signature = self._signed_request_payload(payload, WEBHOOK_TEST_SECRET)

        response = self.client.post(
            self.webhook_url,
            data=raw_payload,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE="assinatura-errada",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_enqueue_order_status_sms_propagates_correlation_id(self):
        with patch("products.tasks.send_order_status_sms_task.delay") as mock_delay:
            with bind_observability_context(correlation_id="corr-task-123", trace_id="trace-task-123"):
                enqueue_order_status_sms(
                    order_id=self.order.id, event_name="payment.approved", status_value=Order.Status.PAID
                )

        mock_delay.assert_called_once()
        self.assertEqual(mock_delay.call_args.kwargs["correlation_id"], "corr-task-123")
        self.assertEqual(mock_delay.call_args.kwargs["trace_id"], "trace-task-123")

    def test_pagamento_aprovado_com_receita_pendente_vai_para_analise_medica(self):
        prescription = MedicalPrescription.objects.create(
            order=self.order,
            prescription_type=MedicalPrescription.Type.DIGITAL_PHOTO,
            status=MedicalPrescription.Status.SUBMITTED,
        )
        prescription.file.name = "prescription_pending.pdf"
        prescription.save()

        payload = {
            "event_id": "evt-approved-with-rx",
            "event": "payment.approved",
            "data": {
                "order_id": self.order.id,
                "transaction_id": "tx-approved-with-rx",
                "payment_method": "PIX",
            },
        }
        raw_payload, signature = self._signed_request_payload(payload, WEBHOOK_TEST_SECRET)

        response = self.client.post(
            self.webhook_url,
            data=raw_payload,
            content_type="application/json",
            HTTP_X_WEBHOOK_SIGNATURE=signature,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.UNDER_MEDICAL_REVIEW)


class PartnerPanelAPITests(APITestCase):
    """Testes da Sprint 9: painel do fornecedor e relatórios financeiros."""

    def setUp(self):
        user_model = get_user_model()
        self.provider = user_model.objects.create_user(
            username="provider_panel",
            email="provider_panel@example.com",
            profile=user_model.Profile.PROVIDER,
        )
        self.other_provider = user_model.objects.create_user(
            username="other_provider_panel",
            email="other_provider_panel@example.com",
            profile=user_model.Profile.PROVIDER,
        )
        self.patient = user_model.objects.create_user(
            username="patient_partner",
            email="patient_partner@example.com",
            profile=user_model.Profile.PATIENT,
        )

        self.category = Category.objects.create(name="Saúde Mental", description="Produtos para bem-estar")

        self.owned_product = Product.objects.create(
            category=self.category,
            provider=self.provider,
            name="Produto do Fornecedor A",
            description="Produto gerenciado pelo fornecedor A",
            price=Decimal("49.90"),
            requires_prescription=False,
            stock=20,
            sku="PAINEL-A-001",
            is_active=True,
        )
        self.other_product = Product.objects.create(
            category=self.category,
            provider=self.other_provider,
            name="Produto do Fornecedor B",
            description="Produto gerenciado pelo fornecedor B",
            price=Decimal("99.90"),
            requires_prescription=False,
            stock=15,
            sku="PAINEL-B-001",
            is_active=True,
        )

        self.order_approved_1 = Order.objects.create(
            user=self.patient,
            provider=self.provider,
            status=Order.Status.PAID,
            total_price=Decimal("100.00"),
            commission_rate=Decimal("10.00"),
        )
        self.order_approved_2 = Order.objects.create(
            user=self.patient,
            provider=self.provider,
            status=Order.Status.PAID,
            total_price=Decimal("50.00"),
            commission_rate=Decimal("10.00"),
        )
        self.order_other_provider = Order.objects.create(
            user=self.patient,
            provider=self.other_provider,
            status=Order.Status.PAID,
            total_price=Decimal("300.00"),
            commission_rate=Decimal("10.00"),
        )

        PaymentTransaction.objects.create(
            order=self.order_approved_1,
            gateway="mock",
            gateway_transaction_id="tx-panel-a-1",
            gateway_status=PaymentTransaction.Status.APPROVED,
            payment_method=PaymentTransaction.Method.PIX,
            gross_amount=Decimal("100.00"),
            provider_amount=Decimal("90.00"),
            ihealth_commission_amount=Decimal("10.00"),
            commission_rate_applied=Decimal("10.00"),
            is_split_calculated=True,
            paid_at=datetime(2026, 4, 5, 10, 0, tzinfo=timezone.utc),
        )
        PaymentTransaction.objects.create(
            order=self.order_approved_2,
            gateway="mock",
            gateway_transaction_id="tx-panel-a-2",
            gateway_status=PaymentTransaction.Status.APPROVED,
            payment_method=PaymentTransaction.Method.BOLETO,
            gross_amount=Decimal("50.00"),
            provider_amount=Decimal("45.00"),
            ihealth_commission_amount=Decimal("5.00"),
            commission_rate_applied=Decimal("10.00"),
            is_split_calculated=True,
            paid_at=datetime(2026, 4, 4, 12, 0, tzinfo=timezone.utc),
        )
        PaymentTransaction.objects.create(
            order=self.order_other_provider,
            gateway="mock",
            gateway_transaction_id="tx-panel-b-1",
            gateway_status=PaymentTransaction.Status.APPROVED,
            payment_method=PaymentTransaction.Method.CREDIT_CARD,
            gross_amount=Decimal("300.00"),
            provider_amount=Decimal("270.00"),
            ihealth_commission_amount=Decimal("30.00"),
            commission_rate_applied=Decimal("10.00"),
            is_split_calculated=True,
            paid_at=datetime(2026, 4, 5, 11, 0, tzinfo=timezone.utc),
        )

    def test_provider_products_list_returns_only_owned_items(self):
        self.client.force_authenticate(user=self.provider)

        response = self.client.get("/api/provider/products/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.owned_product.slug)

    def test_provider_create_product_sets_logged_user_as_owner(self):
        self.client.force_authenticate(user=self.provider)

        payload = {
            "name": "Novo Produto Parceiro",
            "description": "Criado via painel parceiro",
            "price": "129.90",
            "requires_prescription": False,
            "active_ingredient": "",
            "controlled_substance_class": "",
            "min_age_required": 0,
            "max_age_allowed": 0,
            "stock": 11,
            "sku": "PAINEL-A-NEW",
            "category": self.category.id,
            "is_active": True,
        }
        response = self.client.post("/api/provider/products/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_product = Product.objects.get(id=response.data["id"])
        self.assertEqual(created_product.provider, self.provider)

    def test_provider_cannot_access_other_provider_product(self):
        self.client.force_authenticate(user=self.provider)

        response = self.client.get(f"/api/provider/products/{self.other_product.slug}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partner_financial_summary_aggregates_only_provider_transactions(self):
        self.client.force_authenticate(user=self.provider)

        response = self.client.get("/api/provider/finance/statement/summary/?start_date=2026-04-04&end_date=2026-04-05")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_orders"], 2)
        self.assertEqual(response.data["total_gross"], "150.00")
        self.assertEqual(response.data["total_provider_amount"], "135.00")
        self.assertEqual(response.data["total_ihealth_commission"], "15.00")
        self.assertEqual(response.data["average_ticket"], "75.00")

    def test_partner_statement_lists_only_provider_transactions(self):
        self.client.force_authenticate(user=self.provider)

        response = self.client.get("/api/provider/finance/statement/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        order_ids = [item["order_id"] for item in response.data["results"]]
        self.assertIn(self.order_approved_1.id, order_ids)
        self.assertIn(self.order_approved_2.id, order_ids)
        self.assertNotIn(self.order_other_provider.id, order_ids)
