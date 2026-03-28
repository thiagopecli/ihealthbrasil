from rest_framework import serializers

from products.models import Category, Product, ProductVariation


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "slug", "created_at", "updated_at"]
        read_only_fields = ["slug", "created_at", "updated_at"]


class ProductVariationSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariation
        fields = [
            "id",
            "name",
            "value",
            "sku_suffix",
            "price_modifier",
            "stock",
            "final_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_final_price(self, obj: ProductVariation) -> float:
        """Retorna o preço final (base + modificador)."""
        return obj.final_price


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar produtos."""

    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "price",
            "requires_prescription",
            "stock",
            "is_active",
            "category",
            "category_name",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer com detalhes completos do produto."""

    category = CategorySerializer(read_only=True)
    variations = ProductVariationSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "requires_prescription",
            "stock",
            "sku",
            "is_active",
            "category",
            "variations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criar/atualizar produtos."""

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "requires_prescription",
            "stock",
            "sku",
            "category",
            "is_active",
        ]
