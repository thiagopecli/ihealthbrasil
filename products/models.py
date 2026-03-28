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
    """Produto do marketplace."""

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    requires_prescription = models.BooleanField(default=False)
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
