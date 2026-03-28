from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from products.models import Category, Product, ProductDosage, ProductPackageInsert, ProductVariation, SalesRestriction


class ProductsAPITests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
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
