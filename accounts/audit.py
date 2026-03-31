from __future__ import annotations

from typing import Any

from .models import AuthAuditEvent, User

SENSITIVE_KEYS = {
    "password",
    "senha",
    "token",
    "refresh",
    "access",
    "authorization",
    "secret",
    "api_key",
    "apikey",
}


def _sanitize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = _sanitize_payload(item)
        return sanitized

    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value]

    return value


def _get_client_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_user_agent(request) -> str:
    return (request.META.get("HTTP_USER_AGENT", "") or "")[:255]


def log_auth_event(
    *,
    request,
    event_type: str,
    status: str = AuthAuditEvent.Status.SUCCESS,
    user: User | None = None,
    username: str = "",
    details: dict[str, Any] | None = None,
) -> AuthAuditEvent:
    sanitized_details = _sanitize_payload(details or {})
    resolved_username = username or (user.username if user else "")
    resolved_profile = user.profile if user else ""

    return AuthAuditEvent.objects.create(
        user=user,
        username_snapshot=resolved_username,
        profile_snapshot=resolved_profile,
        event_type=event_type,
        status=status,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        details=sanitized_details,
    )
