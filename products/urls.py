from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.views import (
    CategoryViewSet,
    MedicalPrescriptionViewSet,
    OrderViewSet,
    PartnerProductViewSet,
    PartnerSplitStatementViewSet,
    PaymentGatewayWebhookAPIView,
    PrescriptionAccessAuditViewSet,
    ProductDosageViewSet,
    ProductPackageInsertViewSet,
    ProductPriceViewSet,
    ProductVariationViewSet,
    ProductViewSet,
    SalesRestrictionViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"variations", ProductVariationViewSet)
router.register(r"dosages", ProductDosageViewSet)
router.register(r"package-inserts", ProductPackageInsertViewSet)
router.register(r"product-prices", ProductPriceViewSet)
router.register(r"sales-restrictions", SalesRestrictionViewSet)
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"prescriptions", MedicalPrescriptionViewSet, basename="prescription")
router.register(r"prescription-audit", PrescriptionAccessAuditViewSet, basename="prescription-audit")
router.register(r"provider/products", PartnerProductViewSet, basename="provider-products")
router.register(r"provider/finance/statement", PartnerSplitStatementViewSet, basename="provider-finance-statement")

app_name = "products"

urlpatterns = [
    path("payments/webhooks/gateway/", PaymentGatewayWebhookAPIView.as_view(), name="payment-webhook-gateway"),
    path("", include(router.urls)),
]
