import hashlib
import hmac
import os
from typing import Any, cast
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.db import transaction
from django.db.models import Count, Prefetch, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.permissions import HasAnyProfile
from config.observability import get_current_correlation_id, get_current_trace_id
from products.audit import log_prescription_access
from products.models import (
    Cart,
    CartItem,
    Category,
    MedicalPrescription,
    Order,
    OrderItem,
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
from products.payments import PaymentGatewayError, get_payment_gateway
from products.permissions import IsAdminOrReadOnly, IsProviderOrAdminProfile
from products.serializers import (
    CartCheckoutSerializer,
    CartItemUpsertSerializer,
    CartSerializer,
    CategorySerializer,
    MedicalPrescriptionAdminSerializer,
    MedicalPrescriptionDetailSerializer,
    MedicalPrescriptionUploadSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    PartnerDashboardSummarySerializer,
    PartnerProductSerializer,
    PartnerSplitStatementSerializer,
    PaymentIntentCreateSerializer,
    PaymentIntentSerializer,
    PrescriptionAccessAuditSerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductDosageSerializer,
    ProductListSerializer,
    ProductPackageInsertSerializer,
    ProductPriceSerializer,
    ProductVariationSerializer,
    SalesRestrictionSerializer,
)
from products.tasks import enqueue_order_status_sms
from products.utils import (
    build_prescription_download_token,
    get_localized_message,
    package_insert_language_candidates,
    parse_prescription_download_token,
)


class StandardResultsSetPagination(PageNumberPagination):
    """Paginação padrão para endpoints de listagem."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD de categorias de produtos."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["name"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD completo de produtos com filtros avançados."""

    queryset = (
        Product.objects.filter(is_active=True)
        .prefetch_related("variations", "dosages", "package_inserts", "prices")
        .select_related("category")
    )
    lookup_field = "slug"
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "category",
        "requires_prescription",
        "is_active",
        "min_age_required",
        "max_age_allowed",
    ]
    search_fields = [
        "name",
        "description",
        "sku",
        "active_ingredient",
    ]
    ordering_fields = ["name", "price", "created_at", "stock"]
    ordering = ["-created_at"]

    def get_serializer_class(self):  # type: ignore[override]
        """Retorna o serializer apropriado baseado na ação."""
        if self.action == "retrieve":
            return ProductDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProductCreateUpdateSerializer
        return ProductListSerializer

    def get_queryset(self):  # type: ignore[override]
        """Filtra produtos por categoria se parametro fornecido."""
        queryset = super().get_queryset()
        request = cast(Request, self.request)
        category_slug = request.query_params.get("category_slug")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    @action(detail=False, methods=["get"])
    def requires_prescription(self, request):
        """Retorna apenas produtos que requerem prescrição."""
        products = self.get_queryset().filter(requires_prescription=True)
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def variations(self, request, slug=None):
        """Retorna variações de um produto específico."""
        product = self.get_object()
        variations = product.variations.all()
        serializer = ProductVariationSerializer(variations, many=True)
        return Response({"product_slug": slug, "variations": serializer.data})

    @action(detail=True, methods=["get"])
    def dosages(self, request, slug=None):
        """Retorna dosagens de um produto específico."""
        product = self.get_object()
        dosages = product.dosages.all()
        serializer = ProductDosageSerializer(dosages, many=True)
        return Response({"product_slug": slug, "dosages": serializer.data})

    @action(detail=True, methods=["get"])
    def package_inserts(self, request, slug=None):
        """Retorna bulas de um produto específico."""
        product = self.get_object()
        package_inserts = product.package_inserts.all()

        all_languages = request.query_params.get("all_languages", "false").lower() in ["1", "true", "yes"]
        explicit_language = request.query_params.get("language")
        if explicit_language:
            package_inserts = package_inserts.filter(language=explicit_language)
        elif not all_languages:
            preferred_codes = package_insert_language_candidates(request)
            for code in preferred_codes:
                selected = package_inserts.filter(language=code).first()
                if selected:
                    package_inserts = product.package_inserts.filter(id=selected.id)
                    break

        serializer = ProductPackageInsertSerializer(package_inserts, many=True)
        return Response({"product_slug": slug, "package_inserts": serializer.data})

    @action(detail=True, methods=["get"])
    def restrictions(self, request, slug=None):
        """Retorna restrições de venda de um produto específico."""
        product = self.get_object()
        restrictions = product.sales_restrictions.filter(is_active=True)
        serializer = SalesRestrictionSerializer(restrictions, many=True)
        return Response({"product_slug": slug, "restrictions": serializer.data})


class PartnerProductViewSet(viewsets.ModelViewSet):
    """CRUD de produtos do próprio fornecedor (ownership)."""

    serializer_class = PartnerProductSerializer
    permission_classes = [IsAuthenticated, IsProviderOrAdminProfile]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "requires_prescription", "is_active"]
    search_fields = ["name", "description", "sku", "active_ingredient"]
    ordering_fields = ["name", "price", "created_at", "stock", "updated_at"]
    ordering = ["-updated_at"]
    lookup_field = "slug"

    def get_queryset(self):  # type: ignore[override]
        if getattr(self, "swagger_fake_view", False):
            return Product.objects.none()

        request = cast(Request, self.request)
        user = request.user
        queryset = Product.objects.select_related("category", "provider").all()

        if not user.is_staff and getattr(user, "profile", None) != "ADMIN":
            queryset = queryset.filter(provider=user)

        category_slug = request.query_params.get("category_slug")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user)


class PartnerSplitStatementViewSet(viewsets.ReadOnlyModelViewSet):
    """Extrato financeiro de split e resumo agregado para o parceiro."""

    serializer_class = PartnerSplitStatementSerializer
    permission_classes = [IsAuthenticated, IsProviderOrAdminProfile]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["paid_at", "created_at", "gross_amount", "provider_amount"]
    ordering = ["-paid_at", "-created_at"]

    def get_queryset(self):  # type: ignore[override]
        if getattr(self, "swagger_fake_view", False):
            return PaymentTransaction.objects.none()

        request = cast(Request, self.request)
        user = request.user
        queryset = PaymentTransaction.objects.select_related("order", "order__provider").filter(
            is_split_calculated=True
        )

        if not user.is_staff and getattr(user, "profile", None) != "ADMIN":
            queryset = queryset.filter(order__provider=user)

        gateway_status = request.query_params.get("gateway_status")
        if gateway_status:
            queryset = queryset.filter(gateway_status=gateway_status.upper())

        start_date = request.query_params.get("start_date")
        if start_date:
            parsed_start = parse_date(start_date)
            if parsed_start:
                queryset = queryset.filter(paid_at__date__gte=parsed_start)

        end_date = request.query_params.get("end_date")
        if end_date:
            parsed_end = parse_date(end_date)
            if parsed_end:
                queryset = queryset.filter(paid_at__date__lte=parsed_end)

        return queryset

    @action(detail=False, methods=["get"])
    def summary(self, request):
        approved_queryset = self.get_queryset().filter(gateway_status=PaymentTransaction.Status.APPROVED)
        totals = approved_queryset.aggregate(
            total_orders=Count("id"),
            total_gross=Sum("gross_amount"),
            total_provider_amount=Sum("provider_amount"),
            total_ihealth_commission=Sum("ihealth_commission_amount"),
        )

        total_orders = totals["total_orders"] or 0
        total_gross = totals["total_gross"] or Decimal("0.00")
        total_provider_amount = totals["total_provider_amount"] or Decimal("0.00")
        total_ihealth_commission = totals["total_ihealth_commission"] or Decimal("0.00")
        average_ticket = (
            Decimal("0.00") if total_orders == 0 else (total_gross / Decimal(total_orders)).quantize(Decimal("0.01"))
        )

        output = PartnerDashboardSummarySerializer(
            {
                "start_date": parse_date(request.query_params.get("start_date", "")),
                "end_date": parse_date(request.query_params.get("end_date", "")),
                "total_orders": total_orders,
                "total_gross": total_gross,
                "total_provider_amount": total_provider_amount,
                "total_ihealth_commission": total_ihealth_commission,
                "average_ticket": average_ticket,
            }
        )
        return Response(output.data, status=status.HTTP_200_OK)


class ProductVariationViewSet(viewsets.ModelViewSet):
    """CRUD completo de variações de produtos."""

    queryset = ProductVariation.objects.select_related("product")
    serializer_class = ProductVariationSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["product", "name"]
    search_fields = ["product__name", "name", "value", "sku_suffix"]
    ordering_fields = ["name", "value", "created_at"]
    ordering = ["product", "name"]

    def get_queryset(self):
        """Filtra variações por produto se parametro fornecido."""
        queryset = super().get_queryset()
        product_id = self.request.query_params.get("product")
        product_slug = self.request.query_params.get("product_slug")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if product_slug:
            queryset = queryset.filter(product__slug=product_slug)
        return queryset


class ProductDosageViewSet(viewsets.ModelViewSet):
    """CRUD completo de dosagens de produtos."""

    queryset = ProductDosage.objects.select_related("product")
    serializer_class = ProductDosageSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["product", "unit", "is_default"]
    search_fields = ["product__name", "strength", "unit"]
    ordering_fields = ["strength", "created_at"]
    ordering = ["product", "strength"]

    def get_queryset(self):
        """Filtra dosagens por produto se parametro fornecido."""
        queryset = super().get_queryset()
        product_id = self.request.query_params.get("product")
        product_slug = self.request.query_params.get("product_slug")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if product_slug:
            queryset = queryset.filter(product__slug=product_slug)
        return queryset


class ProductPackageInsertViewSet(viewsets.ModelViewSet):
    """CRUD completo de bulas/inserts de produtos."""

    queryset = ProductPackageInsert.objects.select_related("product")
    serializer_class = ProductPackageInsertSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["product", "language", "requires_prescription_note"]
    search_fields = ["product__name", "title", "content"]
    ordering_fields = ["language", "created_at"]
    ordering = ["product", "language"]

    def get_queryset(self):
        """Filtra bulas por produto se parametro fornecido."""
        queryset = super().get_queryset()
        product_id = self.request.query_params.get("product")
        product_slug = self.request.query_params.get("product_slug")
        explicit_language = self.request.query_params.get("language")
        all_languages = self.request.query_params.get("all_languages", "false").lower() in ["1", "true", "yes"]

        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if product_slug:
            queryset = queryset.filter(product__slug=product_slug)
        if explicit_language:
            queryset = queryset.filter(language=explicit_language)
        elif not all_languages:
            preferred_codes = package_insert_language_candidates(self.request)
            for code in preferred_codes:
                if queryset.filter(language=code).exists():
                    queryset = queryset.filter(language=code)
                    break
        return queryset


class ProductPriceViewSet(viewsets.ModelViewSet):
    """CRUD de precificacao por pais/moeda."""

    queryset = ProductPrice.objects.select_related("product", "product__category")
    serializer_class = ProductPriceSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["product", "country_code", "currency", "is_active"]
    search_fields = ["product__name", "product__sku", "country_code", "currency"]
    ordering_fields = ["product", "country_code", "currency", "amount", "created_at"]
    ordering = ["product", "country_code", "currency"]

    def get_queryset(self):
        queryset = super().get_queryset()
        product_slug = self.request.query_params.get("product_slug")
        if product_slug:
            queryset = queryset.filter(product__slug=product_slug)
        return queryset


class SalesRestrictionViewSet(viewsets.ModelViewSet):
    """CRUD completo de restrições de venda."""

    queryset = SalesRestriction.objects.filter(is_active=True).select_related("product")
    serializer_class = SalesRestrictionSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["product", "restriction_type", "is_active"]
    search_fields = ["product__name", "description", "detail"]
    ordering_fields = ["restriction_type", "created_at"]
    ordering = ["product", "restriction_type"]

    def get_queryset(self):
        """Filtra restrições por produto se parametro fornecido."""
        queryset = super().get_queryset()
        product_id = self.request.query_params.get("product")
        product_slug = self.request.query_params.get("product_slug")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if product_slug:
            queryset = queryset.filter(product__slug=product_slug)
        return queryset


class CartViewSet(viewsets.ViewSet):
    """Carrinho persistente por usuário com checkout para pedido."""

    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def _get_or_create_cart(self, user) -> Cart:
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    def _serialize_cart(self, cart: Cart, request: Request) -> dict:
        cart_model = cast(Any, cart)
        cart = (
            Cart.objects.select_related("user")
            .prefetch_related(
                Prefetch(
                    "items",
                    queryset=CartItem.objects.select_related(
                        "product__category",
                        "product_variation",
                        "product_variation__product",
                    ),
                )
            )
            .get(id=cart_model.id)
        )
        cart.recalculate_total(save=True)
        return cast(dict[str, Any], CartSerializer(cart, context={"request": request}).data)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Retorna o carrinho persistente do usuário autenticado."""
        cart = self._get_or_create_cart(request.user)
        return Response(self._serialize_cart(cart, request), status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="items")
    @transaction.atomic
    def add_item(self, request):
        """Adiciona item ao carrinho ou incrementa quantidade se já existir."""
        cart = self._get_or_create_cart(request.user)
        serializer = CartItemUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = cast(dict[str, Any], serializer.validated_data)
        product = validated_data["product"]
        product_variation = validated_data["product_variation"]
        quantity = validated_data["quantity"]

        item_qs = CartItem.objects.select_for_update().filter(cart=cart, product=product)
        if product_variation is None:
            item_qs = item_qs.filter(product_variation__isnull=True)
        else:
            item_qs = item_qs.filter(product_variation=product_variation)

        cart_item = item_qs.first()
        if cart_item:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return Response(
                    {"detail": "Quantidade total excede o estoque disponível."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            cart_item.quantity = new_quantity
        else:
            cart_item = CartItem(
                cart=cart,
                product=product,
                product_variation=product_variation,
                quantity=quantity,
                unit_price=Decimal("0.00"),
                total_price=Decimal("0.00"),
            )

        cart_item.recalculate_prices(save=True)
        cart.recalculate_total(save=True)

        return Response(self._serialize_cart(cart, request), status=status.HTTP_200_OK)

    @action(detail=False, methods=["patch", "delete"], url_path=r"items/(?P<item_id>\d+)")
    @transaction.atomic
    def update_item(self, request, item_id: int | None = None):
        """Atualiza quantidade ou remove item do carrinho."""
        cart = self._get_or_create_cart(request.user)
        item = CartItem.objects.select_for_update().filter(id=item_id, cart=cart).first()
        if not item:
            return Response({"detail": "Item do carrinho não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        if request.method.lower() == "delete":
            item.delete()
            cart.recalculate_total(save=True)
            return Response(self._serialize_cart(cart, request), status=status.HTTP_200_OK)

        quantity = request.data.get("quantity")
        if not isinstance(quantity, int) or quantity < 1:
            return Response(
                {"detail": "Campo quantity deve ser inteiro maior que zero."}, status=status.HTTP_400_BAD_REQUEST
            )
        if quantity > item.product.stock:
            return Response(
                {"detail": "Quantidade maior que o estoque disponível."}, status=status.HTTP_400_BAD_REQUEST
            )

        item.quantity = quantity
        item.recalculate_prices(save=True)
        cart.recalculate_total(save=True)
        return Response(self._serialize_cart(cart, request), status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"], url_path="clear")
    @transaction.atomic
    def clear(self, request):
        """Remove todos os itens do carrinho."""
        cart = self._get_or_create_cart(request.user)
        cart.clear()
        return Response(self._serialize_cart(cart, request), status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="checkout")
    @transaction.atomic
    def checkout(self, request):
        """Converte carrinho em pedido consolidado e limpa carrinho."""
        payload_serializer = CartCheckoutSerializer(data=request.data)
        payload_serializer.is_valid(raise_exception=True)
        payload_data = cast(dict[str, Any], payload_serializer.validated_data)

        cart = (
            Cart.objects.select_for_update()
            .prefetch_related("items", "items__product", "items__product_variation")
            .filter(user=request.user)
            .first()
        )
        cart_model = cast(Any, cart)
        if not cart_model or not cart_model.items.exists():
            return Response({"detail": "Carrinho vazio."}, status=status.HTTP_400_BAD_REQUEST)

        for item in cart_model.items.all():
            if not item.product.is_active:
                return Response(
                    {"detail": f"Produto inativo no carrinho: {item.product.name}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if item.quantity > item.product.stock:
                return Response(
                    {"detail": f"Estoque insuficiente para {item.product.name}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        cart_model.recalculate_total(save=True)

        provider_ids = {item.product.provider_id for item in cart_model.items.all() if item.product.provider_id}
        provider_id = provider_ids.pop() if len(provider_ids) == 1 else None

        order = Order.objects.create(
            user=request.user,
            provider_id=provider_id,
            status=Order.Status.PENDING,
            total_price=cart_model.total_price,
            shipping_address=payload_data.get("shipping_address"),
            notes=payload_data.get("notes"),
        )

        order_items = []
        for item in cart_model.items.all():
            order_items.append(
                OrderItem(
                    order=order,
                    product=item.product,
                    product_variation=item.product_variation,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                )
            )

        OrderItem.objects.bulk_create(order_items)
        cart_model.clear()

        order_output = OrderDetailSerializer(order, context={"request": request})
        return Response(order_output.data, status=status.HTTP_201_CREATED)


class OrderViewSet(viewsets.ModelViewSet):
    """CRUD e gestão de pedidos (compras)."""

    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "user"]
    search_fields = ["id", "user__username", "user__email"]
    ordering_fields = ["total_price", "status", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):  # type: ignore[override]
        """Pacientes veem apenas seus pedidos. Admins veem todos."""
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()

        request = cast(Request, self.request)
        user = request.user
        queryset = Order.objects.select_related("user", "provider", "payment")

        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "items",
                    queryset=OrderItem.objects.select_related(
                        "product__category",
                        "product_variation",
                        "product_variation__product",
                    ),
                )
            )

        if not user.is_staff:
            queryset = queryset.filter(user=user)
        return queryset

    def get_serializer_class(self):  # type: ignore[override]
        """Usa serializer apropriado por ação."""
        if self.action == "retrieve":
            return OrderDetailSerializer
        if self.action == "create_payment_intent":
            return PaymentIntentCreateSerializer
        return OrderListSerializer

    def get_permissions(self):
        """Admin pode ver todos os pedidos, paciente apenas o seu."""
        if self.action == "list" and not self.request.user.is_staff:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def approve_prescription(self, request, pk=None):
        """
        Admin aprova receita médica do pedido.
        POST /orders/{id}/approve_prescription/
        """
        # Verificar se é admin
        if not request.user.is_staff:
            return Response(
                {"detail": get_localized_message(request, "admin_only_action")},
                status=status.HTTP_403_FORBIDDEN,
            )

        order = self.get_object()
        if not hasattr(order, "prescription"):
            return Response(
                {"detail": "Este pedido não possui receita médica."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prescription = order.prescription
        if prescription.status == MedicalPrescription.Status.VERIFIED:
            return Response(
                {"detail": "Receita já foi verificada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prescription.status = MedicalPrescription.Status.VERIFIED
        prescription.verification_notes = request.data.get("notes", "")
        prescription.save()

        # Log de auditoria
        log_prescription_access(
            request=request,
            prescription=prescription,
            action=PrescriptionAccessAudit.Action.VERIFIED,
            details={"verified_by": request.user.username},
        )

        serializer = MedicalPrescriptionDetailSerializer(prescription)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def reject_prescription(self, request, pk=None):
        """
        Admin rejeita receita médica do pedido.
        POST /orders/{id}/reject_prescription/
        """
        # Verificar se é admin
        if not request.user.is_staff:
            return Response(
                {"detail": get_localized_message(request, "admin_only_action")},
                status=status.HTTP_403_FORBIDDEN,
            )

        order = self.get_object()
        if not hasattr(order, "prescription"):
            return Response(
                {"detail": "Este pedido não possui receita médica."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prescription = order.prescription
        prescription.status = MedicalPrescription.Status.REJECTED
        prescription.verification_notes = request.data.get("reason", "Sem motivo especificado")
        prescription.save()

        # Log de auditoria
        log_prescription_access(
            request=request,
            prescription=prescription,
            action=PrescriptionAccessAudit.Action.REJECTED,
            details={"rejected_by": request.user.username, "reason": prescription.verification_notes},
        )

        serializer = MedicalPrescriptionDetailSerializer(prescription)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="payment-intent", permission_classes=[IsAuthenticated])
    @extend_schema(
        summary="Criar intenção de pagamento para o pedido",
        description="Gera o payment intent no gateway e retorna dados necessários para o checkout.",
        request=PaymentIntentCreateSerializer,
        responses={201: PaymentIntentSerializer},
        examples=[
            OpenApiExample(
                "Payload mínimo",
                value={"currency": "brl"},
                request_only=True,
            ),
            OpenApiExample(
                "Payload com fornecedor",
                value={"provider_user_id": 42, "currency": "brl"},
                request_only=True,
            ),
            OpenApiExample(
                "Resposta de sucesso",
                value={
                    "id": 1,
                    "order": 99,
                    "gateway": "mock",
                    "gateway_payment_intent_id": "pi_mock_123",
                    "gateway_checkout_session_id": "cs_mock_123",
                    "client_secret": "secret_mock_123",
                    "checkout_url": "https://checkout.example.com/session/cs_mock_123",
                    "amount": "199.90",
                    "currency": "brl",
                    "status": "requires_payment_method",
                    "metadata": {"provider_user_id": 42},
                    "created_at": "2026-04-05T14:00:00Z",
                },
                response_only=True,
            ),
        ],
    )
    def create_payment_intent(self, request, pk=None):
        """
        Cria intenção de pagamento no gateway para o pedido.
        POST /orders/{id}/payment-intent/
        """
        order = self.get_object()
        if order.total_price <= 0:
            return Response(
                {"detail": "Pedido sem valor total para pagamento."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider_user = None
        provider_user_id = serializer.validated_data.get("provider_user_id")
        if provider_user_id:
            user_model = get_user_model()
            provider_user = user_model.objects.filter(id=provider_user_id, is_active=True).first()
            if not provider_user:
                return Response(
                    {"detail": "Fornecedor informado não foi encontrado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if provider_user.profile not in [user_model.Profile.PROVIDER, user_model.Profile.ADMIN]:
                return Response(
                    {"detail": "Usuário informado não possui perfil de fornecedor/admin."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            gateway = get_payment_gateway()

            customer_external_id = gateway.get_or_create_customer_external_id(order.user)
            customer, _ = PaymentCustomer.objects.update_or_create(
                user=order.user,
                gateway=gateway.name,
                defaults={"external_customer_id": customer_external_id},
            )

            connected_account = None
            connected_account_external_id = None
            if provider_user:
                connected_account_external_id = gateway.get_or_create_connected_account_external_id(provider_user)
                connected_account, _ = PaymentConnectedAccount.objects.update_or_create(
                    user=provider_user,
                    gateway=gateway.name,
                    defaults={
                        "external_account_id": connected_account_external_id,
                        "onboarding_complete": True,
                    },
                )

            payment_result = gateway.create_payment_intent(
                order_id=order.id,
                amount=order.total_price,
                currency=serializer.validated_data.get("currency", "brl"),
                customer_external_id=customer_external_id,
                connected_account_external_id=connected_account_external_id,
            )

            payment_intent = PaymentIntent.objects.create(
                order=order,
                gateway=gateway.name,
                customer=customer,
                connected_account=connected_account,
                gateway_payment_intent_id=payment_result.payment_intent_id,
                gateway_checkout_session_id=payment_result.checkout_session_id,
                client_secret=payment_result.client_secret,
                checkout_url=payment_result.checkout_url,
                amount=order.total_price,
                currency=serializer.validated_data.get("currency", "brl"),
                status=payment_result.status,
                metadata={
                    "provider_user_id": provider_user.id if provider_user else None,
                    "gateway_response": payment_result.raw_response or {},
                },
            )
        except PaymentGatewayError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        output_serializer = PaymentIntentSerializer(payment_intent)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class MedicalPrescriptionViewSet(viewsets.ModelViewSet):
    """Upload, visualização e gestão de receitas médicas."""

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "prescription_type"]
    ordering_fields = ["status", "created_at", "expires_at"]
    ordering = ["-created_at"]

    def get_queryset(self):  # type: ignore[override]
        """Pacientes veem suas receitas. Admins veem todas."""
        if getattr(self, "swagger_fake_view", False):
            return MedicalPrescription.objects.none()

        request = cast(Request, self.request)
        user = request.user
        queryset = MedicalPrescription.objects.select_related("order", "order__user")
        if not user.is_staff:
            queryset = queryset.filter(order__user=user)
        audit_logs_queryset = PrescriptionAccessAudit.objects.select_related("user").order_by("-created_at")
        return queryset.prefetch_related(Prefetch("access_logs", queryset=audit_logs_queryset))

    def get_serializer_class(self):  # type: ignore[override]
        """Serializer apropriado por ação."""
        if self.action == "create":
            return MedicalPrescriptionUploadSerializer
        elif self.action == "retrieve":
            return MedicalPrescriptionDetailSerializer
        elif self.action in ["update", "partial_update"]:
            return MedicalPrescriptionAdminSerializer
        return MedicalPrescriptionDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        Upload de receita médica por paciente.
        POST /prescriptions/ com file + order_id
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prescription = serializer.save()

        # Log de entrada da receita
        log_prescription_access(
            request=request,
            prescription=prescription,
            action=PrescriptionAccessAudit.Action.UPLOADED,
            details={"file_name": prescription.file.name},
        )

        output_serializer = MedicalPrescriptionDetailSerializer(prescription)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """
        Download seguro de arquivo de receita com auditoria.
        GET /prescriptions/{id}/download/
        """
        prescription = self.get_object()

        # Permissão: paciente do pedido ou admin
        if not request.user.is_staff and prescription.order.user != request.user:
            return Response(
                {"detail": "Você não tem permissão para acessar esta receita."},
                status=status.HTTP_403_FORBIDDEN,
            )

        token = build_prescription_download_token(
            prescription_id=prescription.id,
            requested_by_user_id=request.user.id,
            file_hash=prescription.file_hash or "",
        )
        signed_download_url = request.build_absolute_uri(f"/api/prescriptions/secure-download/?token={token}")

        ttl_seconds = int(getattr(settings, "PRESCRIPTION_SIGNED_URL_TTL_SECONDS", 300))
        return Response(
            {
                "download_url": signed_download_url,
                "expires_in_seconds": ttl_seconds,
                "file_name": prescription.file.name,
                "file_size": prescription.file_size,
                "file_hash": prescription.file_hash,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="secure-download", permission_classes=[AllowAny])
    def secure_download(self, request):
        """
        Download real do arquivo de receita via token assinado com expiração.
        GET /prescriptions/secure-download/?token=...
        """
        token = request.query_params.get("token", "")
        if not token:
            return Response({"detail": "Token ausente."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = parse_prescription_download_token(token)
        except signing.SignatureExpired:
            return Response({"detail": "Token expirado."}, status=status.HTTP_403_FORBIDDEN)
        except signing.BadSignature:
            return Response({"detail": "Token inválido ou expirado."}, status=status.HTTP_403_FORBIDDEN)

        prescription = get_object_or_404(
            MedicalPrescription.objects.select_related("order", "order__user"), id=payload["pid"]
        )

        expected_hash = payload.get("fh", "")
        if expected_hash and expected_hash != (prescription.file_hash or ""):
            return Response({"detail": "Token inválido para o arquivo atual."}, status=status.HTTP_403_FORBIDDEN)

        try:
            file_handle = prescription.file.open("rb")
        except FileNotFoundError:
            return Response({"detail": "Arquivo de receita não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        log_prescription_access(
            request=request,
            prescription=prescription,
            action=PrescriptionAccessAudit.Action.DOWNLOADED,
            details={
                "file_format": "original",
                "signed_url": True,
                "requested_by_user_id": payload.get("uid"),
            },
        )

        file_name = os.path.basename(prescription.file.name)
        return FileResponse(file_handle, as_attachment=True, filename=file_name)

    @action(detail=True, methods=["get"])
    def access_logs(self, request, pk=None):
        """
        Retorna histórico de acesso à receita (apenas admin ou paciente dono).
        GET /prescriptions/{id}/access_logs/
        """
        prescription = self.get_object()

        # Permissão: paciente do pedido ou admin
        if not request.user.is_staff and prescription.order.user != request.user:
            return Response(
                {"detail": "Você não tem permissão para acessar estes logs."},
                status=status.HTTP_403_FORBIDDEN,
            )

        logs = prescription.access_logs.all()
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = PrescriptionAccessAuditSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PrescriptionAccessAuditSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentGatewayWebhookAPIView(APIView):
    """Webhook para atualizações de pagamento enviadas pelo gateway."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payment-webhook"

    @staticmethod
    def _normalize_payment_method(value: str | None) -> str:
        normalized = (value or "").strip().upper()
        if normalized in {
            PaymentTransaction.Method.PIX,
            PaymentTransaction.Method.BOLETO,
            PaymentTransaction.Method.CREDIT_CARD,
            PaymentTransaction.Method.DEBIT_CARD,
        }:
            return normalized
        return PaymentTransaction.Method.UNKNOWN

    def _is_valid_signature(self, request) -> bool:
        secret = settings.PAYMENT_WEBHOOK_SECRET
        signature = request.headers.get("X-Webhook-Signature", "")
        digest = hmac.new(secret.encode("utf-8"), request.body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature)

    @extend_schema(
        summary="Receber evento de webhook do gateway de pagamento",
        description="Valida assinatura HMAC, processa evento com idempotência e atualiza status do pedido.",
        request=OpenApiTypes.OBJECT,
        responses={
            200: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Evento recebido/processado."),
            400: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Payload inválido."),
            401: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Assinatura inválida."),
            202: OpenApiResponse(response=OpenApiTypes.OBJECT, description="Pedido não encontrado."),
        },
        examples=[
            OpenApiExample(
                "Evento aprovado",
                value={
                    "event_id": "evt-approved-1",
                    "event": "payment.approved",
                    "data": {
                        "order_id": 100,
                        "transaction_id": "tx-approved-1",
                        "payment_method": "PIX",
                        "gateway": "asaas",
                    },
                },
                request_only=True,
            ),
            OpenApiExample(
                "Resposta processada",
                value={
                    "received": True,
                    "processed": True,
                    "event_id": "evt-approved-1",
                    "order_id": 100,
                    "order_status": "PAID",
                    "payment_status": "APPROVED",
                    "split": {
                        "gross_amount": "100.00",
                        "provider_amount": "88.00",
                        "ihealth_commission_amount": "12.00",
                        "commission_rate_applied": "12.00",
                    },
                },
                response_only=True,
            ),
        ],
    )
    @transaction.atomic
    def post(self, request):
        if not self._is_valid_signature(request):
            return Response({"detail": "Assinatura inválida."}, status=status.HTTP_401_UNAUTHORIZED)

        correlation_id = getattr(request, "correlation_id", None) or get_current_correlation_id()
        trace_id = getattr(request, "trace_id", None) or get_current_trace_id()
        payload = request.data if isinstance(request.data, dict) else {}
        payload_data = cast(dict[str, Any], payload)
        event_name = str(payload_data.get("event") or payload_data.get("type") or "").strip().lower()
        event_id = str(payload_data.get("event_id") or payload_data.get("id") or "").strip()
        data = cast(dict[str, Any], payload_data.get("data") if isinstance(payload_data.get("data"), dict) else {})

        if not event_name or not event_id:
            return Response(
                {"detail": "Payload inválido. Campos event/event_id são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order_id = data.get("order_id")
        gateway_reference = data.get("gateway_reference")

        order = None
        if order_id:
            order = Order.objects.select_for_update().filter(id=order_id).first()
        if order is None and gateway_reference:
            order = Order.objects.select_for_update().filter(gateway_reference=gateway_reference).first()

        if order is None:
            return Response(
                {
                    "received": True,
                    "processed": False,
                    "reason": "order_not_found",
                    "event_id": event_id,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        order_model = cast(Any, order)
        gateway_transaction_id = str(data.get("transaction_id") or data.get("payment_id") or f"order-{order_model.id}")
        payment, _created = PaymentTransaction.objects.select_for_update().get_or_create(
            order=order,
            defaults={
                "gateway": str(data.get("gateway") or "sandbox_gateway"),
                "gateway_transaction_id": gateway_transaction_id,
                "payment_method": self._normalize_payment_method(data.get("payment_method")),
            },
        )

        if payment.gateway_transaction_id != gateway_transaction_id:
            payment.gateway_transaction_id = gateway_transaction_id

        if not payment.is_split_calculated:
            payment.apply_split()

        event, created_event = PaymentWebhookEvent.objects.get_or_create(
            event_id=event_id,
            defaults={
                "payment": payment,
                "event_name": event_name,
                "payload": payload,
            },
        )
        if not created_event:
            return Response(
                {
                    "received": True,
                    "processed": False,
                    "duplicate": True,
                    "event_id": event_id,
                    "order_status": payment.order.status,
                    "payment_status": payment.gateway_status,
                },
                status=status.HTTP_200_OK,
            )

        payment.payment_method = self._normalize_payment_method(data.get("payment_method"))
        payment_model = cast(Any, payment)
        previous_order_status = payment_model.order.status
        payment.apply_gateway_event(event_name=event_name, payload=payload)
        payment.save()
        payment_model.order.save(update_fields=["status", "updated_at"])

        if previous_order_status != payment_model.order.status:
            enqueue_order_status_sms(
                order_id=payment_model.order_id,
                event_name=event_name,
                status_value=payment_model.order.status,
            )

        event.payload = {
            **(event.payload or {}),
            "observability": {
                "correlation_id": correlation_id,
                "trace_id": trace_id,
            },
        }
        event.save(update_fields=["payload"])

        return Response(
            {
                "received": True,
                "processed": True,
                "event_id": event.event_id,
                "order_id": payment_model.order_id,
                "order_status": payment_model.order.status,
                "payment_status": payment.gateway_status,
                "split": {
                    "gross_amount": str(payment.gross_amount),
                    "provider_amount": str(payment.provider_amount),
                    "ihealth_commission_amount": str(payment.ihealth_commission_amount),
                    "commission_rate_applied": str(payment.commission_rate_applied),
                },
            },
            status=status.HTTP_200_OK,
        )


class PrescriptionAccessAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Visualização de logs de auditoria de receitas (admin only).
    READ-ONLY para compliance LGPD.
    """

    serializer_class = PrescriptionAccessAuditSerializer
    permission_classes = [IsAuthenticated, HasAnyProfile]
    allowed_profiles = ["ADMIN"]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["action", "prescription"]
    search_fields = ["username_snapshot", "ip_address", "prescription__order__user__username"]
    ordering_fields = ["action", "created_at"]
    ordering = ["-created_at"]

    queryset = PrescriptionAccessAudit.objects.all().select_related("prescription", "user")

    @action(detail=False, methods=["get"])
    def by_prescription(self, request):
        """
        Lista logs por receita específica.
        GET /prescription-audit/by_prescription/?prescription_id=123
        """
        prescription_id = request.query_params.get("prescription_id")
        if not prescription_id:
            return Response(
                {"detail": "Parâmetro 'prescription_id' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logs = self.get_queryset().filter(prescription_id=prescription_id)
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def by_user(self, request):
        """
        Lista logs de acesso de um usuário específico.
        GET /prescription-audit/by_user/?user_id=123
        """
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"detail": "Parâmetro 'user_id' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logs = self.get_queryset().filter(user_id=user_id)
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
