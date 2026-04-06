from django.contrib import admin
from django.utils.html import format_html

from products.models import (
    Cart,
    CartItem,
    Category,
    ExternalNotification,
    MedicalPrescription,
    PrescriptionAccessAudit,
    Product,
    ProductDosage,
    ProductPackageInsert,
    ProductPrice,
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


class ProductPriceInline(admin.TabularInline):
    """Inline para precificacao multimoeda por pais."""

    model = ProductPrice
    fields = ["country_code", "currency", "amount", "is_active"]
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
        ProductPriceInline,
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


@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin):
    list_display = ["product", "country_code", "currency", "amount", "is_active", "created_at"]
    list_filter = ["country_code", "currency", "is_active", "created_at"]
    search_fields = ["product__name", "product__sku", "country_code", "currency"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["product", "country_code", "currency"]


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


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "total_price", "updated_at", "created_at"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-updated_at"]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cart",
        "product",
        "product_variation",
        "quantity",
        "unit_price",
        "total_price",
    ]
    list_filter = ["product__category", "created_at"]
    search_fields = ["cart__user__username", "product__name", "product__sku"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["cart", "created_at"]


# ============= PRESCRIPTIONS (Sprint 8) =============


class PrescriptionAccessAuditInline(admin.TabularInline):
    """Inline para auditoria de acesso a receita."""

    model = PrescriptionAccessAudit
    fields = ["user", "action", "ip_address", "created_at"]
    extra = 0
    can_delete = False
    readonly_fields = ["user", "action", "ip_address", "created_at", "details"]


@admin.register(MedicalPrescription)
class MedicalPrescriptionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order",
        "status_display",
        "prescription_type",
        "prescriber_name",
        "expires_at",
        "created_at",
        "action_buttons",
    ]
    list_filter = ["status", "prescription_type", "created_at", "expires_at"]
    search_fields = ["order__id", "prescriber_name", "file_hash"]
    readonly_fields = [
        "order",
        "file_hash",
        "file_size",
        "created_at",
        "updated_at",
        "expires_at_display",
    ]
    inlines = [PrescriptionAccessAuditInline]
    actions = ["action_verify_prescription", "action_reject_prescription", "action_send_to_memed"]
    fieldsets = (
        (
            "Pedido e Receita",
            {"fields": ("order", "prescription_type", "prescriber_name", "prescription_date")},
        ),
        (
            "Arquivo",
            {"fields": ("file", "file_size", "file_hash")},
        ),
        (
            "Validação",
            {"fields": ("status", "verification_notes", "validity_days", "expires_at", "expires_at_display")},
        ),
        (
            "Auditoria",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
    ordering = ["-created_at"]

    def status_display(self, obj):
        """Exibe status com cor."""
        color_map = {
            "PENDING": "orange",
            "SUBMITTED": "blue",
            "VERIFIED": "green",
            "REJECTED": "red",
            "EXPIRED": "gray",
        }
        color = color_map.get(obj.status, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_display.short_description = "Status"

    def expires_at_display(self, obj):
        """Exibe data de expiracao com indicador."""
        from django.utils import timezone

        if not obj.expires_at:
            return "Nao configurado"
        now = timezone.now()
        if obj.expires_at < now:
            return format_html('<span style="color: red;">Expirada em {}</span>', obj.expires_at)
        days_left = (obj.expires_at - now).days
        if days_left <= 7:
            return format_html('<span style="color: orange;">{} dias restantes</span>', days_left)
        return format_html('<span style="color: green;">{} dias restantes</span>', days_left)

    expires_at_display.short_description = "Expiracao"

    def action_buttons(self, obj):
        """Botoes de acao rapida."""
        if obj.status == MedicalPrescription.Status.SUBMITTED:
            return format_html(
                '<a class="button" href="javascript:void(0)">✓ Verificar</a> '
                '<a class="button" style="background-color: #ba2121;" href="javascript:void(0)">✗ Rejeitar</a>'
            )
        return "-"

    action_buttons.short_description = "Acoes"

    def action_verify_prescription(self, request, queryset):
        """Action para verificar (aprovar) receita."""
        from products.tasks import enqueue_prescription_notification_email

        count = 0
        for prescription in queryset.filter(status=MedicalPrescription.Status.SUBMITTED):
            prescription.status = MedicalPrescription.Status.VERIFIED
            prescription.save(update_fields=["status", "updated_at"])
            enqueue_prescription_notification_email(prescription_id=prescription.pk, notification_type="verified")
            count += 1

        self.message_user(request, f"{count} receitas verificadas e emails enfileirados.")

    action_verify_prescription.short_description = "Verificar receitas selecionadas (aprovar)"

    def action_reject_prescription(self, request, queryset):
        """Action para rejeitar receita."""
        from products.tasks import enqueue_prescription_notification_email

        count = 0
        for prescription in queryset.filter(status=MedicalPrescription.Status.SUBMITTED):
            prescription.status = MedicalPrescription.Status.REJECTED
            prescription.save(update_fields=["status", "updated_at"])
            enqueue_prescription_notification_email(prescription_id=prescription.pk, notification_type="rejected")
            count += 1

        self.message_user(request, f"{count} receitas rejeitadas e emails enfileirados.")

    action_reject_prescription.short_description = "Rejeitar receitas selecionadas"

    def action_send_to_memed(self, request, queryset):
        """Action para enviar receita para Memed."""
        from django.conf import settings

        from products.tasks import enqueue_prescription_to_memed

        if not settings.MEMED_ENABLED:
            self.message_user(request, "Memed nao esta habilitado nas configuracoes.", level="error")
            return

        count = 0
        for prescription in queryset.filter(file__isnull=False):
            enqueue_prescription_to_memed(prescription_id=prescription.pk)
            count += 1

        self.message_user(request, f"{count} receitas enfileiradas para envio a Memed.")

    action_send_to_memed.short_description = "Enviar para validacao Memed"


@admin.register(PrescriptionAccessAudit)
class PrescriptionAccessAuditAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "prescription",
        "user_display",
        "action",
        "ip_address",
        "created_at",
    ]
    list_filter = ["action", "created_at", "prescription__status"]
    search_fields = ["prescription__id", "user__username", "username_snapshot", "ip_address"]
    readonly_fields = ["prescription", "user", "action", "ip_address", "user_agent", "details", "created_at"]
    ordering = ["-created_at"]

    def user_display(self, obj):
        """Exibe usuario com fallback para snapshot."""
        if obj.user:
            return obj.user.username
        return f"[deleted] {obj.username_snapshot}"

    user_display.short_description = "Usuario"

    def has_add_permission(self, request):
        """Auditoria nao deve ser editada manualmente."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Auditoria nao deve ser deletada."""
        return False
