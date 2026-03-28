from django.contrib import admin

from products.models import Category, Product, ProductVariation


class ProductVariationInline(admin.TabularInline):
    """Inline para variações de produtos no admin."""

    model = ProductVariation
    fields = ["name", "value", "sku_suffix", "price_modifier", "stock"]
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "sku",
        "category",
        "price",
        "requires_prescription",
        "stock",
        "is_active",
        "created_at",
    ]
    list_filter = ["category", "is_active", "requires_prescription", "created_at"]
    search_fields = ["name", "sku", "description"]
    readonly_fields = ["created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariationInline]
    fieldsets = (
        (
            "Informações Básicas",
            {"fields": ("name", "slug", "category", "description")},
        ),
        ("Preço e Estoque", {"fields": ("price", "stock", "sku")}),
        (
            "Regulações",
            {"fields": ("requires_prescription", "is_active")},
        ),
        ("Datas", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    ordering = ["-created_at"]


@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "name",
        "value",
        "sku_suffix",
        "price_modifier",
        "stock",
        "created_at",
    ]
    list_filter = ["product__category", "name", "created_at"]
    search_fields = ["product__name", "name", "value", "sku_suffix"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["product", "name", "value"]
