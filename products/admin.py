from django.contrib import admin

from products.models import (
    Category,
    ExternalNotification,
    Product,
    ProductDosage,
    ProductPackageInsert,
    ProductVariation,
    SalesRestriction,
)


class ProductVariationInline(admin.TabularInline):
    """Inline para variações de produtos no admin."""

    model = ProductVariation
    fields = ["name", "value", "sku_suffix", "price_modifier", "stock"]
    extra = 1


class ProductDosageInline(admin.TabularInline):
    """Inline para dosagens de produtos no admin."""

    model = ProductDosage
    fields = ["strength", "unit", "frequency_recommendation", "is_default"]
    extra = 1


class ProductPackageInsertInline(admin.TabularInline):
    """Inline para bulas de produtos no admin."""

    model = ProductPackageInsert
    fields = ["language", "title", "requires_prescription_note"]
    extra = 1


class SalesRestrictionInline(admin.TabularInline):
    """Inline para restrições de venda no admin."""

    model = SalesRestriction
    fields = ["restriction_type", "description", "is_active"]
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
    list_filter = [
        "category",
        "is_active",
        "requires_prescription",
        "created_at",
    ]
    search_fields = ["name", "sku", "description", "active_ingredient"]
    readonly_fields = ["created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [
        ProductVariationInline,
        ProductDosageInline,
        ProductPackageInsertInline,
        SalesRestrictionInline,
    ]
    fieldsets = (
        ("Informações Básicas", {"fields": ("name", "slug", "category", "description")}),
        (
            "Preço e Estoque",
            {"fields": ("price", "stock", "sku")},
        ),
        (
            "Regulações",
            {
                "fields": (
                    "requires_prescription",
                    "active_ingredient",
                    "controlled_substance_class",
                    "is_active",
                )
            },
        ),
        (
            "Restrições de Idade",
            {
                "fields": ("min_age_required", "max_age_allowed"),
                "classes": ("collapse",),
            },
        ),
        (
            "Datas",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
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


@admin.register(ProductDosage)
class ProductDosageAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "strength",
        "unit",
        "frequency_recommendation",
        "is_default",
        "created_at",
    ]
    list_filter = ["product__category", "unit", "is_default", "created_at"]
    search_fields = ["product__name", "strength"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["product", "strength"]


@admin.register(ProductPackageInsert)
class ProductPackageInsertAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "language",
        "title",
        "requires_prescription_note",
        "created_at",
    ]
    list_filter = ["product__category", "language", "requires_prescription_note", "created_at"]
    search_fields = ["product__name", "title", "content"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["product", "language"]


@admin.register(SalesRestriction)
class SalesRestrictionAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "restriction_type",
        "description",
        "is_active",
        "created_at",
    ]
    list_filter = ["product__category", "restriction_type", "is_active", "created_at"]
    search_fields = ["product__name", "description", "detail"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["product", "restriction_type"]


@admin.register(ExternalNotification)
class ExternalNotificationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order",
        "channel",
        "provider",
        "event_name",
        "destination_masked",
        "status",
        "sent_at",
        "created_at",
    ]
    list_filter = ["channel", "provider", "status", "event_name", "created_at"]
    search_fields = ["order__id", "event_name", "destination_masked", "external_message_id"]
    readonly_fields = ["created_at", "updated_at", "sent_at"]
    ordering = ["-created_at"]
