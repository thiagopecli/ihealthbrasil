from __future__ import annotations

import time
import uuid
from collections import Counter, defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from threading import Lock
from typing import Any, Iterator

CORRELATION_ID_HEADER = "X-Correlation-ID"
TRACE_ID_HEADER = "X-Trace-Id"
TRACEPARENT_HEADER = "Traceparent"

correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[str | None] = ContextVar("span_id", default=None)
route_var: ContextVar[str | None] = ContextVar("route", default=None)
user_var: ContextVar[str | None] = ContextVar("user", default=None)
status_code_var: ContextVar[int | None] = ContextVar("status_code", default=None)
duration_ms_var: ContextVar[float | None] = ContextVar("duration_ms", default=None)

REQUEST_LATENCY_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)


def generate_correlation_id() -> str:
    return uuid.uuid4().hex


def generate_trace_id() -> str:
    return uuid.uuid4().hex


def generate_span_id() -> str:
    return uuid.uuid4().hex[:16]


def _normalize_hex(value: str | None, expected_length: int) -> str | None:
    if not value:
        return None
    candidate = value.strip().lower()
    if len(candidate) != expected_length:
        return None
    if any(character not in "0123456789abcdef" for character in candidate):
        return None
    return candidate


def parse_traceparent(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None

    parts = [part.strip() for part in value.split("-")]
    if len(parts) != 4:
        return None, None

    trace_id = _normalize_hex(parts[1], 32)
    parent_span_id = _normalize_hex(parts[2], 16)
    if not trace_id or not parent_span_id:
        return None, None
    return trace_id, parent_span_id


def build_traceparent(trace_id: str | None, span_id: str | None, sampled: str = "01") -> str | None:
    normalized_trace_id = _normalize_hex(trace_id, 32)
    normalized_span_id = _normalize_hex(span_id, 16)
    if not normalized_trace_id or not normalized_span_id:
        return None
    sampled_flag = sampled if sampled in {"00", "01"} else "01"
    return f"00-{normalized_trace_id}-{normalized_span_id}-{sampled_flag}"


def resolve_request_route(request: Any) -> str:
    resolver_match = getattr(request, "resolver_match", None)
    view_name = getattr(resolver_match, "view_name", None)
    if view_name:
        return str(view_name)
    return getattr(request, "path", None) or getattr(request, "path_info", "unknown") or "unknown"


def resolve_request_user(request: Any) -> str:
    user = getattr(request, "user", None)
    if user is None:
        return "anonymous"
    if getattr(user, "is_authenticated", False):
        username = getattr(user, "username", None) or getattr(user, "email", None)
        return str(username or user.pk or "authenticated")
    return "anonymous"


@contextmanager
def bind_observability_context(
    *,
    correlation_id: str | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
    route: str | None = None,
    user: str | None = None,
    status_code: int | None = None,
    duration_ms: float | None = None,
) -> Iterator[None]:
    tokens = []
    if correlation_id is not None:
        tokens.append((correlation_id_var, correlation_id_var.set(correlation_id)))
    if trace_id is not None:
        tokens.append((trace_id_var, trace_id_var.set(trace_id)))
    if span_id is not None:
        tokens.append((span_id_var, span_id_var.set(span_id)))
    if route is not None:
        tokens.append((route_var, route_var.set(route)))
    if user is not None:
        tokens.append((user_var, user_var.set(user)))
    if status_code is not None:
        tokens.append((status_code_var, status_code_var.set(status_code)))
    if duration_ms is not None:
        tokens.append((duration_ms_var, duration_ms_var.set(duration_ms)))

    try:
        yield
    finally:
        for variable, token in reversed(tokens):
            variable.reset(token)


def current_observability_context() -> dict[str, Any]:
    return {
        "correlation_id": correlation_id_var.get(),
        "trace_id": trace_id_var.get(),
        "span_id": span_id_var.get(),
        "route": route_var.get(),
        "user": user_var.get(),
        "status_code": status_code_var.get(),
        "duration_ms": duration_ms_var.get(),
    }


def get_current_correlation_id() -> str | None:
    return correlation_id_var.get()


def get_current_trace_id() -> str | None:
    return trace_id_var.get()


def get_current_span_id() -> str | None:
    return span_id_var.get()


@dataclass
class _LatencySample:
    count: int = 0
    total: float = 0.0
    buckets: Counter[float] | None = None

    def __post_init__(self) -> None:
        if self.buckets is None:
            self.buckets = Counter()


class ObservabilityMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._started_at = time.time()
        self._requests_total: Counter[tuple[str, str, int]] = Counter()
        self._errors_total: Counter[tuple[str, str]] = Counter()
        self._latency_samples: dict[tuple[str, str], _LatencySample] = defaultdict(_LatencySample)

    def record_request(self, *, route: str, method: str, status_code: int, duration_seconds: float) -> None:
        normalized_route = route or "unknown"
        normalized_method = method.upper() if method else "GET"
        with self._lock:
            self._requests_total[(normalized_route, normalized_method, status_code)] += 1
            if status_code >= 500:
                self._errors_total[(normalized_route, normalized_method)] += 1

            sample = self._latency_samples[(normalized_route, normalized_method)]
            buckets = sample.buckets or Counter()
            sample.count += 1
            sample.total += duration_seconds
            for bucket in REQUEST_LATENCY_BUCKETS:
                if duration_seconds <= bucket:
                    buckets[bucket] += 1
            buckets[float("inf")] += 1
            sample.buckets = buckets

    def render_prometheus(self) -> str:
        with self._lock:
            lines = [
                "# HELP ihealthbrasil_http_requests_total Total de requests HTTP observadas.",
                "# TYPE ihealthbrasil_http_requests_total counter",
            ]
            for (route, method, status_code), count in sorted(self._requests_total.items()):
                lines.append(
                    "ihealthbrasil_http_requests_total"
                    f'{{route="{route}",method="{method}",status_code="{status_code}"}} {count}'
                )

            lines.extend(
                [
                    "# HELP ihealthbrasil_http_request_errors_total Total de requests com erro por rota e metodo.",
                    "# TYPE ihealthbrasil_http_request_errors_total counter",
                ]
            )
            for (route, method), count in sorted(self._errors_total.items()):
                lines.append("ihealthbrasil_http_request_errors_total" f'{{route="{route}",method="{method}"}} {count}')

            lines.extend(
                [
                    "# HELP ihealthbrasil_http_request_duration_seconds Latencia por rota e metodo.",
                    "# TYPE ihealthbrasil_http_request_duration_seconds histogram",
                ]
            )
            for (route, method), sample in sorted(self._latency_samples.items()):
                buckets = sample.buckets or Counter()
                cumulative = 0
                for bucket in REQUEST_LATENCY_BUCKETS:
                    cumulative += buckets[bucket]
                    lines.append(
                        "ihealthbrasil_http_request_duration_seconds_bucket"
                        f'{{route="{route}",method="{method}",le="{bucket}"}} {cumulative}'
                    )
                cumulative += buckets[float("inf")]
                lines.append(
                    "ihealthbrasil_http_request_duration_seconds_bucket"
                    f'{{route="{route}",method="{method}",le="+Inf"}} {cumulative}'
                )
                lines.append(
                    "ihealthbrasil_http_request_duration_seconds_sum"
                    f'{{route="{route}",method="{method}"}} {sample.total:.6f}'
                )
                lines.append(
                    "ihealthbrasil_http_request_duration_seconds_count"
                    f'{{route="{route}",method="{method}"}} {sample.count}'
                )

            lines.append("# HELP ihealthbrasil_process_uptime_seconds Tempo de uptime do processo.")
            lines.append("# TYPE ihealthbrasil_process_uptime_seconds gauge")
            lines.append(f"ihealthbrasil_process_uptime_seconds {time.time() - self._started_at:.6f}")
            return "\n".join(lines) + "\n"


METRICS_REGISTRY = ObservabilityMetrics()
