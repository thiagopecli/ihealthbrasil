from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import HasAnyProfile
from products.audit import log_prescription_access
from products.models import (
    Category,
    MedicalPrescription,
    Order,
    PrescriptionAccessAudit,
    Product,
    ProductDosage,
    ProductPackageInsert,
    ProductVariation,
    SalesRestriction,
)
from products.permissions import IsAdminOrReadOnly
from products.serializers import (
    CategorySerializer,
    MedicalPrescriptionAdminSerializer,
    MedicalPrescriptionDetailSerializer,
    MedicalPrescriptionUploadSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    PrescriptionAccessAuditSerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductDosageSerializer,
    ProductListSerializer,
    ProductPackageInsertSerializer,
    ProductVariationSerializer,
    SalesRestrictionSerializer,
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
        .prefetch_related("variations", "dosages", "package_inserts")
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

    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na ação."""
        if self.action == "retrieve":
            return ProductDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return ProductCreateUpdateSerializer
        return ProductListSerializer

    def get_queryset(self):
        """Filtra produtos por categoria se parametro fornecido."""
        queryset = super().get_queryset()
        category_slug = self.request.query_params.get("category_slug")
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
        serializer = ProductPackageInsertSerializer(package_inserts, many=True)
        return Response({"product_slug": slug, "package_inserts": serializer.data})

    @action(detail=True, methods=["get"])
    def restrictions(self, request, slug=None):
        """Retorna restrições de venda de um produto específico."""
        product = self.get_object()
        restrictions = product.sales_restrictions.filter(is_active=True)
        serializer = SalesRestrictionSerializer(restrictions, many=True)
        return Response({"product_slug": slug, "restrictions": serializer.data})


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
        if product_id:
            queryset = queryset.filter(product_id=product_id)
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

    def get_queryset(self):
        """Pacientes veem apenas seus pedidos. Admins veem todos."""
        user = self.request.user
        queryset = Order.objects.all()
        if not user.is_staff:
            queryset = queryset.filter(user=user)
        return queryset.select_related("user")

    def get_serializer_class(self):
        """Usa serializer apropriado por ação."""
        if self.action == "retrieve":
            return OrderDetailSerializer
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
                {"detail": "Apenas admin pode aprovar receitas."},
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
                {"detail": "Apenas admin pode rejeitar receitas."},
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

    def get_queryset(self):
        """Pacientes veem suas receitas. Admins veem todas."""
        user = self.request.user
        queryset = MedicalPrescription.objects.all()
        if not user.is_staff:
            queryset = queryset.filter(order__user=user)
        return queryset.select_related("order", "order__user").prefetch_related("access_logs")

    def get_serializer_class(self):
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

        # Log de auditoria de download
        log_prescription_access(
            request=request,
            prescription=prescription,
            action=PrescriptionAccessAudit.Action.DOWNLOADED,
            details={"file_format": "original"},
        )

        # Retorna URL/stream do arquivo (simplificado para arquivo local)
        return Response(
            {
                "download_url": request.build_absolute_uri(prescription.file.url),
                "file_name": prescription.file.name,
                "file_size": prescription.file_size,
                "file_hash": prescription.file_hash,
            },
            status=status.HTTP_200_OK,
        )

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

        logs = prescription.access_logs.all().order_by("-created_at")
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = PrescriptionAccessAuditSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PrescriptionAccessAuditSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
