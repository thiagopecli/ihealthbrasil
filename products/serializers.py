from rest_framework import serializers

from products.models import (
    Cart,
    CartItem,
    Category,
    MedicalPrescription,
    Order,
    OrderItem,
    PaymentIntent,
    PaymentTransaction,
    PrescriptionAccessAudit,
    Product,
    ProductDosage,
    ProductPackageInsert,
    ProductPrice,
    ProductVariation,
    SalesRestriction,
)
from products.utils import (
    get_localized_message,
    normalize_country_code,
    normalize_currency_code,
    package_insert_language_candidates,
    resolve_product_display_price,
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
    price = serializers.SerializerMethodField()
    price_currency = serializers.SerializerMethodField()
    price_country = serializers.SerializerMethodField()
    price_is_fallback = serializers.SerializerMethodField()

    def _resolved_price(self, obj: Product) -> dict:
        request = self.context.get("request")
        return resolve_product_display_price(obj, request)

    def get_price(self, obj: Product):
        return self._resolved_price(obj)["amount"]

    def get_price_currency(self, obj: Product) -> str:
        return self._resolved_price(obj)["currency"]

    def get_price_country(self, obj: Product) -> str:
        return self._resolved_price(obj)["country"]

    def get_price_is_fallback(self, obj: Product) -> bool:
        return self._resolved_price(obj)["is_fallback"]

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "price",
            "price_currency",
            "price_country",
            "price_is_fallback",
            "requires_prescription",
            "stock",
            "is_active",
            "category",
            "category_name",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer com detalhes completos do produto."""

    category = CategorySerializer(read_only=True)
    price = serializers.SerializerMethodField()
    price_currency = serializers.SerializerMethodField()
    price_country = serializers.SerializerMethodField()
    price_is_fallback = serializers.SerializerMethodField()
    variations = ProductVariationSerializer(many=True, read_only=True)
    dosages = ProductDosageSerializer(many=True, read_only=True)
    package_inserts = serializers.SerializerMethodField()
    sales_restrictions = SalesRestrictionSerializer(many=True, read_only=True)

    def _resolved_price(self, obj: Product) -> dict:
        request = self.context.get("request")
        return resolve_product_display_price(obj, request)

    def get_price(self, obj: Product):
        return self._resolved_price(obj)["amount"]

    def get_price_currency(self, obj: Product) -> str:
        return self._resolved_price(obj)["currency"]

    def get_price_country(self, obj: Product) -> str:
        return self._resolved_price(obj)["country"]

    def get_price_is_fallback(self, obj: Product) -> bool:
        return self._resolved_price(obj)["is_fallback"]

    def get_package_inserts(self, obj: Product) -> list[dict]:
        request = self.context.get("request")
        inserts = list(obj.package_inserts.all())
        if not inserts:
            return []

        preferred_codes = package_insert_language_candidates(request)
        selected = None
        for code in preferred_codes:
            selected = next((item for item in inserts if item.language == code), None)
            if selected:
                break

        if not selected:
            selected = inserts[0]
        serialized = ProductPackageInsertSerializer(selected, context=self.context)
        return [serialized.data]

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "price_currency",
            "price_country",
            "price_is_fallback",
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


class PartnerProductSerializer(serializers.ModelSerializer):
    """Serializer de gestão de produtos no painel do fornecedor."""

    provider_username = serializers.CharField(source="provider.username", read_only=True)

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
            "provider",
            "provider_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "provider", "provider_username", "created_at", "updated_at"]


class ProductPriceSerializer(serializers.ModelSerializer):
    """Serializer de precificacao por pais/moeda."""

    class Meta:
        model = ProductPrice
        fields = [
            "id",
            "product",
            "country_code",
            "currency",
            "amount",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_country_code(self, value: str) -> str:
        normalized = normalize_country_code(value)
        if len(normalized) != 2 or not normalized.isalpha():
            raise serializers.ValidationError(get_localized_message(self.context.get("request"), "invalid_country"))
        return normalized

    def validate_currency(self, value: str) -> str:
        normalized = normalize_currency_code(value)
        if len(normalized) != 3 or not normalized.isalpha():
            raise serializers.ValidationError(get_localized_message(self.context.get("request"), "invalid_currency"))
        return normalized


class PartnerSplitStatementSerializer(serializers.ModelSerializer):
    """Serializer do extrato de split para o parceiro."""

    order_id = serializers.IntegerField(source="order.id", read_only=True)
    order_status = serializers.CharField(source="order.status", read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "order_id",
            "order_status",
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
            "created_at",
        ]
        read_only_fields = fields


class PartnerDashboardSummarySerializer(serializers.Serializer):
    """Resumo financeiro agregado para dashboard do parceiro."""

    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    total_orders = serializers.IntegerField()
    total_gross = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_provider_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_ihealth_commission = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_ticket = serializers.DecimalField(max_digits=12, decimal_places=2)


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer para itens do carrinho."""

    product = ProductListSerializer(read_only=True)
    product_variation = ProductVariationSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_variation",
            "quantity",
            "unit_price",
            "total_price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["unit_price", "total_price", "created_at", "updated_at"]


class CartSerializer(serializers.ModelSerializer):
    """Serializer de detalhe do carrinho persistente."""

    items = CartItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_price", "created_at", "updated_at"]
        read_only_fields = fields


class CartItemUpsertSerializer(serializers.Serializer):
    """Payload para inserir/atualizar item no carrinho."""

    product_id = serializers.IntegerField(min_value=1)
    product_variation_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        product_id = attrs["product_id"]
        variation_id = attrs.get("product_variation_id")

        product = Product.objects.filter(id=product_id, is_active=True).first()
        if not product:
            raise serializers.ValidationError({"product_id": "Produto inválido ou inativo."})

        variation = None
        if variation_id is not None:
            variation = ProductVariation.objects.filter(id=variation_id).first()
            if not variation or variation.product_id != product.id:
                raise serializers.ValidationError({"product_variation_id": "Variação inválida para este produto."})

        if attrs["quantity"] > product.stock:
            raise serializers.ValidationError({"quantity": "Quantidade maior que o estoque disponível."})

        attrs["product"] = product
        attrs["product_variation"] = variation
        return attrs


class CartCheckoutSerializer(serializers.Serializer):
    """Payload para checkout do carrinho em pedido."""

    shipping_address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)


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


class PaymentIntentCreateSerializer(serializers.Serializer):
    """Payload para iniciar pagamento no checkout."""

    provider_user_id = serializers.IntegerField(required=False, min_value=1)
    currency = serializers.CharField(required=False, min_length=3, max_length=3)

    def validate_currency(self, value: str) -> str:
        if not value.isalpha():
            raise serializers.ValidationError(get_localized_message(self.context.get("request"), "invalid_currency"))
        return normalize_currency_code(value).lower()


class PaymentIntentSerializer(serializers.ModelSerializer):
    """Resposta da intenção de pagamento criada no gateway."""

    class Meta:
        model = PaymentIntent
        fields = [
            "id",
            "order",
            "gateway",
            "gateway_payment_intent_id",
            "gateway_checkout_session_id",
            "client_secret",
            "checkout_url",
            "amount",
            "currency",
            "status",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


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
