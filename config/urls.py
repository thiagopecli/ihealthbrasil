from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from config.views import HealthCheckView, MetricsView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", HealthCheckView.as_view(), name="healthcheck"),
    path("metrics/", MetricsView.as_view(), name="metrics"),
    path("api/schema/", SpectacularAPIView.as_view(), name="api_schema"),
    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="api_schema"),
        name="swagger_ui",
    ),
    path(
        "api/docs/redoc/",
        SpectacularRedocView.as_view(url_name="api_schema"),
        name="redoc_ui",
    ),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("products.urls")),
]

# Servir media files em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
