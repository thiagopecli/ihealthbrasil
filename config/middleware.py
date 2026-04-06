from __future__ import annotations

import logging
import time

from django.http import HttpResponse

from config.observability import (
    CORRELATION_ID_HEADER,
    METRICS_REGISTRY,
    TRACE_ID_HEADER,
    TRACEPARENT_HEADER,
    bind_observability_context,
    build_traceparent,
    generate_correlation_id,
    generate_span_id,
    generate_trace_id,
    parse_traceparent,
    resolve_request_route,
    resolve_request_user,
)


class RequestObservabilityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("ihealthbrasil.request")

    def __call__(self, request):
        start = time.perf_counter()
        route = resolve_request_route(request)
        user = resolve_request_user(request)
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or request.META.get("HTTP_X_REQUEST_ID")
        if not correlation_id:
            correlation_id = generate_correlation_id()

        incoming_traceparent = request.headers.get("traceparent") or request.META.get("HTTP_TRACEPARENT")
        trace_id, _parent_span_id = parse_traceparent(incoming_traceparent)
        if not trace_id:
            trace_id = request.headers.get(TRACE_ID_HEADER) or generate_trace_id()

        span_id = generate_span_id()

        with bind_observability_context(
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            route=route,
            user=user,
        ):
            request.correlation_id = correlation_id
            request.trace_id = trace_id
            request.span_id = span_id

            try:
                response = self.get_response(request)
            except Exception:
                duration_seconds = time.perf_counter() - start
                duration_ms = duration_seconds * 1000
                METRICS_REGISTRY.record_request(
                    route=route,
                    method=request.method,
                    status_code=500,
                    duration_seconds=duration_seconds,
                )
                self.logger.exception(
                    "request_failed",
                    extra={
                        "route": route,
                        "user": user,
                        "status_code": 500,
                        "duration_ms": round(duration_ms, 2),
                        "correlation_id": correlation_id,
                        "trace_id": trace_id,
                    },
                )
                raise

            duration_seconds = time.perf_counter() - start
            duration_ms = duration_seconds * 1000
            status_code = getattr(response, "status_code", 200)
            METRICS_REGISTRY.record_request(
                route=route,
                method=request.method,
                status_code=status_code,
                duration_seconds=duration_seconds,
            )

            if isinstance(response, HttpResponse):
                response[CORRELATION_ID_HEADER] = correlation_id
                response[TRACE_ID_HEADER] = trace_id
                traceparent = build_traceparent(trace_id, span_id)
                if traceparent:
                    response[TRACEPARENT_HEADER] = traceparent
                response["Server-Timing"] = f"app;dur={duration_ms:.2f}"

            self.logger.info(
                "request_completed",
                extra={
                    "route": route,
                    "user": user,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                    "correlation_id": correlation_id,
                    "trace_id": trace_id,
                },
            )
            return response
