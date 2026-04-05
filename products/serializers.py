from rest_framework import serializers

from products.models import (
    Category,
    MedicalPrescription,
    Order,
    OrderItem,
    PaymentTransaction,
    PrescriptionAccessAudit,
    Product,
    ProductDosage,
    ProductPackageInsert,
    ProductVariation,
    SalesRestriction,
)


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


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer para itens do pedido."""

    product = ProductListSerializer(read_only=True)
    product_variation = ProductVariationSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "order",
            "product",
            "product_variation",
            "quantity",
            "unit_price",
            "total_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["order", "unit_price", "total_price", "created_at", "updated_at"]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer de transação de pagamento com split calculado."""

    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "gateway",
            "gateway_transaction_id",
            "gateway_status",
            "payment_method",
            "gross_amount",
            "provider_amount",
            "ihealth_commission_amount",
            "commission_rate_applied",
            "is_split_calculated",
            "paid_at",
            "last_event_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer para listar pedidos (resumo)."""

    user = serializers.StringRelatedField(read_only=True)
    payment = PaymentTransactionSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "provider",
            "status",
            "total_price",
            "commission_rate",
            "gateway_reference",
            "payment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "total_price", "created_at", "updated_at"]


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalhe pedido com itens."""

    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    payment = PaymentTransactionSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "provider",
            "status",
            "items",
            "total_price",
            "commission_rate",
            "gateway_reference",
            "payment",
            "shipping_address",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "total_price", "created_at", "updated_at"]


class PrescriptionAccessAuditSerializer(serializers.ModelSerializer):
    """Serializer para logs de auditoria de acesso a receitas."""

    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = PrescriptionAccessAudit
        fields = [
            "id",
            "prescription",
            "user",
            "username_snapshot",
            "action",
            "ip_address",
            "user_agent",
            "details",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "prescription",
            "user",
            "username_snapshot",
            "ip_address",
            "user_agent",
            "details",
            "created_at",
        ]


class MedicalPrescriptionUploadSerializer(serializers.ModelSerializer):
    """Serializer para upload de receita médica (paciente)."""

    class Meta:
        model = MedicalPrescription
        fields = [
            "id",
            "order",
            "prescription_type",
            "file",
            "prescriber_name",
            "prescription_date",
        ]
        read_only_fields = ["id", "file_size", "file_hash", "status", "expires_at"]

    def create(self, validated_data):
        """Calcula hash e tamanho do arquivo ao criar."""
        from products.utils import calculate_file_hash, calculate_prescription_expiry

        instance = super().create(validated_data)
        instance.status = MedicalPrescription.Status.SUBMITTED  # Mudar status ao enviar
        file_obj = instance.file
        instance.file_hash = calculate_file_hash(file_obj)
        instance.file_size = file_obj.size
        instance.expires_at = calculate_prescription_expiry(instance.validity_days)
        instance.save()
        return instance


class MedicalPrescriptionDetailSerializer(serializers.ModelSerializer):
    """Serializer para visualização de receita (incluindo logs de auditoria)."""

    access_logs = PrescriptionAccessAuditSerializer(many=True, read_only=True)

    class Meta:
        model = MedicalPrescription
        fields = [
            "id",
            "order",
            "prescription_type",
            "status",
            "file",
            "file_size",
            "file_hash",
            "prescriber_name",
            "prescription_date",
            "validity_days",
            "expires_at",
            "verification_notes",
            "access_logs",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "file_size",
            "file_hash",
            "expires_at",
            "access_logs",
            "created_at",
            "updated_at",
        ]


class MedicalPrescriptionAdminSerializer(serializers.ModelSerializer):
    """Serializer para admin verificar/rejeitar receitas."""

    class Meta:
        model = MedicalPrescription
        fields = [
            "id",
            "order",
            "status",
            "file",
            "prescriber_name",
            "prescription_date",
            "file_hash",
            "verification_notes",
            "expires_at",
            "created_at",
        ]
        read_only_fields = ["id", "order", "file", "file_hash", "created_at"]
