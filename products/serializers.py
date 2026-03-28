from rest_framework import serializers

from products.models import Category, Product, ProductDosage, ProductPackageInsert, ProductVariation, SalesRestriction


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


class ProductDosageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductDosage
        fields = [
            "id",
            "strength",
            "unit",
            "frequency_recommendation",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ProductPackageInsertSerializer(serializers.ModelSerializer):
    language_display = serializers.CharField(source="get_language_display", read_only=True)

    class Meta:
        model = ProductPackageInsert
        fields = [
            "id",
            "language",
            "language_display",
            "title",
            "content",
            "file_url",
            "requires_prescription_note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class SalesRestrictionSerializer(serializers.ModelSerializer):
    restriction_type_display = serializers.CharField(source="get_restriction_type_display", read_only=True)

    class Meta:
        model = SalesRestriction
        fields = [
            "id",
            "restriction_type",
            "restriction_type_display",
            "description",
            "detail",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


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
    dosages = ProductDosageSerializer(many=True, read_only=True)
    package_inserts = ProductPackageInsertSerializer(many=True, read_only=True)
    sales_restrictions = SalesRestrictionSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "requires_prescription",
            "active_ingredient",
            "controlled_substance_class",
            "min_age_required",
            "max_age_allowed",
            "stock",
            "sku",
            "is_active",
            "category",
            "variations",
            "dosages",
            "package_inserts",
            "sales_restrictions",
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
            "active_ingredient",
            "controlled_substance_class",
            "min_age_required",
            "max_age_allowed",
            "stock",
            "sku",
            "category",
            "is_active",
        ]
