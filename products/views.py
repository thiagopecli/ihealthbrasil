from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from products.models import Category, Product, ProductVariation
from products.serializers import (
    CategorySerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductVariationSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD de categorias de produtos."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD de produtos."""

    queryset = Product.objects.filter(is_active=True).prefetch_related("variations")
    lookup_field = "slug"

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
        category_slug = self.request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    @action(detail=False, methods=["get"])
    def requires_prescription(self, request):
        """Retorna apenas produtos que requerem prescrição."""
        products = self.get_queryset().filter(requires_prescription=True)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def variations(self, request, slug=None):
        """Retorna variações de um produto específico."""
        product = self.get_object()
        variations = product.variations.all()
        serializer = ProductVariationSerializer(variations, many=True)
        return Response(serializer.data)


class ProductVariationViewSet(viewsets.ModelViewSet):
    """CRUD de variações de produtos."""

    queryset = ProductVariation.objects.all()
    serializer_class = ProductVariationSerializer

    def get_queryset(self):
        """Filtra variações por produto se parametro fornecido."""
        queryset = super().get_queryset()
        product_id = self.request.query_params.get("product")
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset
