"""Utilitários para auditoria de acesso a receitas médicas (LGPD)."""

from typing import Any

from accounts.models import User as DjangoUser
from config.observability import get_current_correlation_id, get_current_trace_id
from products.models import MedicalPrescription, PrescriptionAccessAudit


def _sanitize_payload(value: Any) -> Any:
    """Recursivamente sanitiza payloads, removendo dados sensíveis."""
    SENSITIVE_KEYS = {"password", "token", "refresh", "authorization", "secret", "api_key", "cpf", "medical_record"}

    if isinstance(value, dict):
        return {k: "[REDACTED]" if str(k).lower() in SENSITIVE_KEYS else _sanitize_payload(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_sanitize_payload(item) for item in value]
    elif isinstance(value, str) and len(value) > 1000:
        return value[:500] + "...[truncated]"
    return value


def _get_client_ip(request) -> str | None:
    """Extrai IP do cliente do request, considerando proxies."""
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_user_agent(request) -> str:
    """Extrai user-agent do request."""
    return request.META.get("HTTP_USER_AGENT", "")[:255]


def log_prescription_access(
    *,
    request,
    prescription: MedicalPrescription,
    action: str,
    user: DjangoUser | None = None,
    details: dict[str, Any] | None = None,
) -> PrescriptionAccessAudit:
    """
    Registra acesso a uma receita médica para auditoria LGPD.

    Args:
        request: Django request object
        prescription: MedicalPrescription instance
        action: Tipo de ação (use PrescriptionAccessAudit.Action choices)
        user: User que acessou (se None, será extraído de request.user)
        details: Dados adicionais contextuais (ex: "via_api", "download_format")

    Returns:
        PrescriptionAccessAudit instance criado
    """
    if user is None:
        user = request.user if request.user.is_authenticated else None

    correlation_id = get_current_correlation_id()
    trace_id = get_current_trace_id()
    sanitized_details = _sanitize_payload(details or {})
    if correlation_id:
        sanitized_details["correlation_id"] = correlation_id
    if trace_id:
        sanitized_details["trace_id"] = trace_id

    return PrescriptionAccessAudit.objects.create(
        prescription=prescription,
        user=user,
        username_snapshot=user.username if user else request.META.get("REMOTE_USER", ""),
        action=action,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        details=sanitized_details,
    )


def get_prescription_access_logs(prescription: MedicalPrescription, action: str | None = None):
    """
    Retorna logs de auditoria para uma receita, opcionalmente filtrados por ação.

    Args:
        prescription: MedicalPrescription instance
        action: Filtra por ação específica (ex: 'DOWNLOADED')

    Returns:
        QuerySet de PrescriptionAccessAudit
    """
    prescription_model = prescription
    logs = getattr(prescription_model, "access_logs").all()
    if action:
        logs = logs.filter(action=action)
    return logs.order_by("-created_at")
