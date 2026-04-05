from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """Categoria de produtos."""

    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Produto do marketplace com suporte a regulações de saúde."""

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Campos de saúde
    requires_prescription = models.BooleanField(default=False, help_text="Exige prescrição médica")
    active_ingredient = models.CharField(max_length=200, blank=True, null=True, help_text="Princípio ativo")
    controlled_substance_class = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Classificação de substância controlada (ex: C1, C4)",
    )
    min_age_required = models.IntegerField(
        default=0, help_text="Idade mínima permitida para compra (0 = sem restrição)"
    )
    max_age_allowed = models.IntegerField(
        default=0,
        help_text="Idade máxima permitida para compra (0 = sem restrição)",
    )

    # Campos gerais
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["requires_prescription"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ProductVariation(models.Model):
    """Variação de um produto (tamanho, cor, concentração, etc)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variations")
    name = models.CharField(max_length=120, help_text="Ex: Tamanho, Cor, Concentração")
    value = models.CharField(max_length=120, help_text="Ex: P, M, G ou Azul, Vermelho")
    sku_suffix = models.CharField(max_length=50)
    price_modifier = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Adicional ao preço base"
    )
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Variação de Produto"
        verbose_name_plural = "Variações de Produtos"
        ordering = ["product", "name"]
        unique_together = [["product", "name", "value"]]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["product", "name"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.name}: {self.value}"

    @property
    def final_price(self) -> float:
        """Calcula o preço final (preço do produto + modificador de variação)."""
        return float(self.product.price + self.price_modifier)


class ProductDosage(models.Model):
    """Informações de dosagem para um produto (ex: 500mg, 1000mg)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="dosages")
    strength = models.CharField(max_length=100, help_text="Ex: 500mg, 10mg/5mL, 2%")
    unit = models.CharField(max_length=50, help_text="Unidade de medida (mg, mcg, g, %)")
    frequency_recommendation = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Freq. recomendada (ex: 2x ao dia)",
    )
    is_default = models.BooleanField(default=False, help_text="Dosagem padrão para este produto")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dosagem de Produto"
        verbose_name_plural = "Dosagens de Produtos"
        ordering = ["product", "strength"]
        unique_together = [["product", "strength", "unit"]]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["product", "is_default"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.strength}{self.unit}"


class ProductPackageInsert(models.Model):
    """Bula/Insert de embalagem para produto (documento PDF)."""

    LANGUAGE_CHOICES = [
        ("pt_BR", "Português (Brasil)"),
        ("en_US", "Inglês (USA)"),
        ("es_ES", "Espanhol (Espanha)"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="package_inserts")
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default="pt_BR",
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(help_text="Conteúdo da bula em HTML ou texto")
    file_url = models.URLField(blank=True, null=True, help_text="URL de arquivo PDF da bula")
    requires_prescription_note = models.BooleanField(default=False, help_text="Se marca 'Venda sob prescrição'")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bula de Produto"
        verbose_name_plural = "Bulas de Produtos"
        ordering = ["product", "language"]
        unique_together = [["product", "language"]]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["language"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - Bula ({self.get_language_display()})"


class SalesRestriction(models.Model):
    """Restrições de venda para um produto."""

    RESTRICTION_TYPE_CHOICES = [
        ("age_min", "Idade mínima"),
        ("age_max", "Idade máxima"),
        ("region", "Por região/estado"),
        ("professional_required", "Profissional de saúde requerido"),
        ("license_required", "Licença/registro especial requerido"),
        ("custom", "Restrição customizada"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales_restrictions")
    restriction_type = models.CharField(max_length=50, choices=RESTRICTION_TYPE_CHOICES)
    description = models.CharField(max_length=255, help_text="Descrição da restrição")
    detail = models.TextField(blank=True, null=True, help_text="Detalhes técnicos/completos")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Restrição de Venda"
        verbose_name_plural = "Restrições de Venda"
        ordering = ["product", "restriction_type"]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["restriction_type"]),
            models.Index(fields=["product", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.get_restriction_type_display()}"


class Order(models.Model):
    """Pedido de compra no marketplace."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Aguardando pagamento"
        PAID = "PAID", "Pago"
        UNDER_MEDICAL_REVIEW = "UNDER_MEDICAL_REVIEW", "Em análise médica"
        APPROVED = "APPROVED", "Aprovado"
        CANCELLED = "CANCELLED", "Cancelado"
        FAILED = "FAILED", "Falha no pagamento"

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    shipping_address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Pedido #{self.id} - {self.user.username} ({self.get_status_display()})"


class OrderItem(models.Model):
    """Item individual em um pedido."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_variation = models.ForeignKey(ProductVariation, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self) -> str:
        product_name = self.product.name if self.product else "Produto removido"
        return f"{product_name} x{self.quantity} (Pedido #{self.order.id})"


class MedicalPrescription(models.Model):
    """Receita médica vinculada a um pedido para produtos controlados."""

    class Type(models.TextChoices):
        ELECTRONIC = "ELECTRONIC", "Eletrônica"
        PRINTED = "PRINTED", "Impressa"
        DIGITAL_PHOTO = "DIGITAL_PHOTO", "Foto Digital"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Aguardando upload"
        SUBMITTED = "SUBMITTED", "Enviada"
        VERIFIED = "VERIFIED", "Verificada"
        REJECTED = "REJECTED", "Rejeitada"
        EXPIRED = "EXPIRED", "Expirada"

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="prescription",
        help_text="Receita vinculada a este pedido",
    )
    prescription_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.DIGITAL_PHOTO,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    file = models.FileField(
        upload_to="prescriptions/%Y/%m/%d/",
        help_text="Arquivo da receita médica",
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        editable=False,
        help_text="Tamanho do arquivo em bytes",
    )
    file_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        editable=False,
        db_index=True,
        help_text="SHA-256 do arquivo para integridade",
    )

    prescriber_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nome do médico/profissional que prescreveu",
    )
    prescription_date = models.DateField(
        blank=True,
        null=True,
        help_text="Data de emissão da receita",
    )
    validity_days = models.IntegerField(
        default=30,
        help_text="Quantos dias a receita é válida",
    )
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Data/hora de expiração automática",
        db_index=True,
    )

    verification_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notas do verificador (admin/staff)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Receita Médica"
        verbose_name_plural = "Receitas Médicas"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["file_hash"]),
        ]

    def __str__(self) -> str:
        return f"Receita (Pedido #{self.order.id}) - {self.get_status_display()}"


class PrescriptionAccessAudit(models.Model):
    """Auditoria de acesso a receitas médicas para compliance LGPD."""

    class Action(models.TextChoices):
        UPLOADED = "UPLOADED", "Arquivo enviado"
        DOWNLOADED = "DOWNLOADED", "Arquivo baixado"
        VIEWED = "VIEWED", "Visualizado"
        VERIFIED = "VERIFIED", "Verificado (admin)"
        REJECTED = "REJECTED", "Rejeitado (admin)"

    prescription = models.ForeignKey(
        MedicalPrescription,
        on_delete=models.CASCADE,
        related_name="access_logs",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescription_access_logs",
    )
    username_snapshot = models.CharField(
        max_length=150,
        blank=True,
        help_text="Snapshot do username (caso usuário seja deletado)",
    )
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Detalhes customizados (acesso via API/Admin, localização, etc)",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Auditoria de Acesso a Receita"
        verbose_name_plural = "Auditorias de Acesso a Receitas"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["prescription", "action", "created_at"]),
            models.Index(fields=["user", "action", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self) -> str:
        username = self.username_snapshot or (self.user.username if self.user else "anonimo")
        return f"{self.get_action_display()} - Receita #{self.prescription.id} por {username}"


class PaymentCustomer(models.Model):
    """Representa o customer do usuário no gateway de pagamento."""

    GATEWAY_CHOICES = [
        ("mock", "Mock"),
        ("stripe", "Stripe"),
    ]

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="payment_customers")
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES, db_index=True)
    external_customer_id = models.CharField(max_length=120, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer de Pagamento"
        verbose_name_plural = "Customers de Pagamento"
        unique_together = [["user", "gateway"]]
        indexes = [
            models.Index(fields=["gateway", "external_customer_id"]),
            models.Index(fields=["user", "gateway"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.gateway}:{self.external_customer_id}"


class PaymentConnectedAccount(models.Model):
    """Conta conectada no gateway para repasses/split do fornecedor."""

    GATEWAY_CHOICES = [
        ("mock", "Mock"),
        ("stripe", "Stripe"),
    ]

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="connected_accounts")
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES, db_index=True)
    external_account_id = models.CharField(max_length=120, db_index=True)
    onboarding_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conta Conectada de Pagamento"
        verbose_name_plural = "Contas Conectadas de Pagamento"
        unique_together = [["user", "gateway"]]
        indexes = [
            models.Index(fields=["gateway", "external_account_id"]),
            models.Index(fields=["user", "gateway"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.gateway}:{self.external_account_id}"


class PaymentIntent(models.Model):
    """Intenção de pagamento criada durante o checkout."""

    GATEWAY_CHOICES = [
        ("mock", "Mock"),
        ("stripe", "Stripe"),
    ]

    class Status(models.TextChoices):
        REQUIRES_PAYMENT_METHOD = "requires_payment_method", "Requer método de pagamento"
        REQUIRES_CONFIRMATION = "requires_confirmation", "Requer confirmação"
        PROCESSING = "processing", "Processando"
        SUCCEEDED = "succeeded", "Concluído"
        CANCELED = "canceled", "Cancelado"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payment_intents")
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES, db_index=True)
    customer = models.ForeignKey(
        PaymentCustomer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_intents",
    )
    connected_account = models.ForeignKey(
        PaymentConnectedAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_intents",
    )
    gateway_payment_intent_id = models.CharField(max_length=120, db_index=True)
    gateway_checkout_session_id = models.CharField(max_length=120, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    checkout_url = models.URLField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="brl")
    status = models.CharField(
        max_length=40,
        default=Status.REQUIRES_PAYMENT_METHOD,
        db_index=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Intenção de Pagamento"
        verbose_name_plural = "Intenções de Pagamento"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Pedido #{self.order_id} - {self.gateway_payment_intent_id}"
