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
