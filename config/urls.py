from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def healthcheck(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", healthcheck, name="healthcheck"),
    path("api/schema/", SpectacularAPIView.as_view(), name="api_schema"),
    path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="api_schema"), name="swagger_ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="api_schema"), name="redoc_ui"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("products.urls")),
]
