from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.views import CategoryViewSet, ProductVariationViewSet, ProductViewSet

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"products", ProductViewSet)
router.register(r"variations", ProductVariationViewSet)

app_name = "products"

urlpatterns = [
    path("", include(router.urls)),
]
