from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from products.models import (
    Category,
    MedicalPrescription,
    Order,
    Product,
    ProductDosage,
    ProductPackageInsert,
    ProductVariation,
    PrescriptionAccessAudit,
    SalesRestriction,
)


class ProductsAPITests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="catalog_user",
            email="catalog_user@example.com",
            password="StrongPass@123",
            profile=user_model.Profile.PATIENT,
            is_staff=False,
        )

        self.admin = user_model.objects.create_user(
            username="catalog_admin",
            email="catalog_admin@example.com",
            password="StrongPass@123",
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

        response = self.client.get(f"/api/products/{self.product.slug}/restrictions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["restrictions"]), 1)

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
            password="StrongPass@123",
            profile=user_model.Profile.PATIENT,
        )

        self.admin = user_model.objects.create_user(
            username="order_admin",
            email="admin@example.com",
            password="StrongPass@123",
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


class MedicalPrescriptionAPITests(APITestCase):
    """Testes de upload e auditoria de receitas (Sprint 5)."""

    def setUp(self):
        from io import BytesIO

        user_model = get_user_model()
        self.patient = user_model.objects.create_user(
            username="rx_patient",
            email="patient_rx@example.com",
            password="StrongPass@123",
            profile=user_model.Profile.PATIENT,
        )

        self.admin = user_model.objects.create_user(
            username="rx_admin",
            email="admin_rx@example.com",
            password="StrongPass@123",
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
        prescription = MedicalPrescription.objects.create(
            order=self.order,
            prescription_type="DIGITAL_PHOTO",
            status=MedicalPrescription.Status.VERIFIED,
        )
        prescription.file.name = "prescription.pdf"
        prescription.save()

        self.client.force_authenticate(user=self.patient)
        response = self.client.get(f"/api/prescriptions/{prescription.id}/download/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
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
        prescription = MedicalPrescription.objects.create(
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
