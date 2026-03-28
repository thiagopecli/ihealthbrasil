from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.views import (
    CategoryViewSet,
    ProductDosageViewSet,
    ProductPackageInsertViewSet,
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
router.register(r"sales-restrictions", SalesRestrictionViewSet)

app_name = "products"

urlpatterns = [
    path("", include(router.urls)),
]
