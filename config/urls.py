from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


def healthcheck(request):
    """
    Health check endpoint com verificacao basica de componentes.
    GET /health/ -> status geral
    GET /health/?detailed=true -> inclui status de Redis/broker
    """
    detailed = request.GET.get("detailed", "").lower() == "true"
    status_data = {"status": "ok", "components": {}}

    # Check database
    try:
        from django.db import connections
        connections["default"].ensure_connection()
        status_data["components"]["database"] = "ok"
    except Exception as e:
        status_data["status"] = "error"
        status_data["components"]["database"] = f"error: {str(e)[:100]}"

    # Check Redis/Broker if detailed requested
    if detailed:
        try:
            from celery import current_app
            current_app.connection().connect()
            status_data["components"]["redis"] = "ok"
        except Exception as e:
            status_data["status"] = "degraded"
            status_data["components"]["redis"] = f"warning: {str(e)[:100]}"

    status_code = 200 if status_data["status"] == "ok" else (503 if status_data["status"] == "error" else 200)
    return JsonResponse(status_data, status=status_code)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", healthcheck, name="healthcheck"),
    path("api/schema/", SpectacularAPIView.as_view(), name="api_schema"),
    path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="api_schema"), name="swagger_ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="api_schema"), name="redoc_ui"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("products.urls")),
]

# Servir media files em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
