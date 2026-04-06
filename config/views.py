from __future__ import annotations

from typing import Any, cast

from celery import current_app as celery_current_app
from django.db import connections
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from config.observability import METRICS_REGISTRY


class HealthCheckResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    components = serializers.DictField(child=serializers.CharField())


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "healthcheck"

    @extend_schema(responses=HealthCheckResponseSerializer)
    def get(self, request):
        detailed = request.query_params.get("detailed", "").lower() == "true"
        status_data = {"status": "ok", "components": {}}

        try:
            connections["default"].ensure_connection()
            status_data["components"]["database"] = "ok"
        except Exception as exc:
            status_data["status"] = "error"
            status_data["components"]["database"] = f"error: {str(exc)[:100]}"

        if detailed:
            try:
                cast(Any, celery_current_app).connection().connect()
                status_data["components"]["redis"] = "ok"
            except Exception as exc:
                status_data["status"] = "degraded"
                status_data["components"]["redis"] = f"warning: {str(exc)[:100]}"

        status_code = 200 if status_data["status"] in {"ok", "degraded"} else 503
        return Response(status_data, status=status_code)


class MetricsView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(responses=OpenApiTypes.STR)
    def get(self, _request):
        response = HttpResponse(METRICS_REGISTRY.render_prometheus(), content_type="text/plain; version=0.0.4")
        response["Cache-Control"] = "no-store"
        return response
