from __future__ import annotations

from typing import Any, cast

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from products.models import ExternalNotification, Order
from products.notifications import SmsProviderError, build_order_status_sms_message, get_sms_provider, mask_phone_number


@shared_task(
    bind=True,
    ignore_result=True,
    autoretry_for=(SmsProviderError,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def send_order_status_sms_task(self, *, order_id: int, event_name: str, status_value: str) -> None:
    order = Order.objects.select_related("user").filter(id=order_id).first()
    if order is None:
        return

    destination_number = (getattr(order.user, "phone_number", "") or "").strip()
    provider = settings.SMS_PROVIDER.lower()
    message = build_order_status_sms_message(order_id=order.pk, status_value=status_value)

    notification = ExternalNotification.objects.create(
        order=order,
        channel=ExternalNotification.Channel.SMS,
        provider=provider,
        event_name=event_name,
        destination_masked=mask_phone_number(destination_number),
        message=message,
        status=ExternalNotification.Status.PENDING,
        request_metadata={"status": status_value},
    )

    if not settings.SMS_ENABLED:
        notification.status = ExternalNotification.Status.SKIPPED
        notification.error_message = "SMS desabilitado por configuracao."
        notification.save(update_fields=["status", "error_message", "updated_at"])
        return

    if not destination_number:
        notification.status = ExternalNotification.Status.SKIPPED
        notification.error_message = "Usuario sem telefone cadastrado."
        notification.save(update_fields=["status", "error_message", "updated_at"])
        return

    sms_provider = get_sms_provider()
    result = sms_provider.send_sms(to_number=destination_number, message=message)

    notification.status = ExternalNotification.Status.SENT
    notification.external_message_id = result.message_id
    notification.response_metadata = result.raw_response or {}
    notification.sent_at = timezone.now()
    notification.save(
        update_fields=[
            "status",
            "external_message_id",
            "response_metadata",
            "sent_at",
            "updated_at",
        ]
    )


def enqueue_order_status_sms(*, order_id: int, event_name: str, status_value: str) -> None:
    """Enfileira task no Celery e cai para execucao local quando broker nao esta disponivel."""
    try:
        celery_task = cast(Any, send_order_status_sms_task)
        celery_task.delay(order_id=order_id, event_name=event_name, status_value=status_value)
    except Exception:  # pragma: no cover - protecao para ambientes sem broker
        send_order_status_sms_task(order_id=order_id, event_name=event_name, status_value=status_value)


# ============= MEMED INTEGRATION (Sprint 8) =============


@shared_task(
    bind=True,
    ignore_result=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def send_prescription_to_memed_task(self, *, prescription_id: int) -> None:
    """Envia receita para validacao em Memed."""
    from products.models import MedicalPrescription
    from products.notifications import MemedProviderError, get_memed_provider

    prescription = MedicalPrescription.objects.filter(id=prescription_id).first()
    if prescription is None:
        return

    if not settings.MEMED_ENABLED:
        return

    if not prescription.file:
        return

    try:
        memed_provider = get_memed_provider()
        result = memed_provider.send_prescription(
            prescription_id=prescription.pk,
            file_path=prescription.file.path,
            prescriber_name=prescription.prescriber_name or "Indefinido",
        )

        # Registra no metadata da prescricao que foi enviada para Memed
        prescription.verification_notes = (
            f"[Memed] Enviada com ID: {result.prescription_id}. "
            f"Provider: {result.provider_name}\n"
            f"{prescription.verification_notes or ''}"
        )
        prescription.save(update_fields=["verification_notes", "updated_at"])

    except MemedProviderError as exc:
        # Log de erro ligado à auditoria
        from products.models import PrescriptionAccessAudit

        PrescriptionAccessAudit.objects.create(
            prescription=prescription,
            action=PrescriptionAccessAudit.Action.VERIFIED,
            details={
                "error": str(exc),
                "memed_integration": True,
                "status": "failed",
            },
        )


def enqueue_prescription_to_memed(*, prescription_id: int) -> None:
    """Enfileira envio de receita para Memed."""
    try:
        celery_task = cast(Any, send_prescription_to_memed_task)
        celery_task.delay(prescription_id=prescription_id)
    except Exception:  # pragma: no cover
        send_prescription_to_memed_task(prescription_id=prescription_id)


# ============= EMAIL NOTIFICATIONS (Sprint 8) =============


@shared_task(
    bind=True,
    ignore_result=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 2},
)
def send_prescription_notification_email_task(
    self, *, prescription_id: int, notification_type: str
) -> None:
    """Envia email de notificacao apos verificacao/rejeicao de receita."""
    from django.core.mail import send_mail

    from products.models import MedicalPrescription

    prescription = MedicalPrescription.objects.select_related(
        "order__user"
    ).filter(id=prescription_id).first()

    if prescription is None or not settings.EMAIL_ENABLED:
        return

    user = prescription.order.user
    if not user.email:
        return

    # Mensagens por tipo de notificacao
    status_text = prescription.get_status_display()
    subject_map = {
        "verified": f"Receita Aprovada - Pedido #{prescription.order.id}",
        "rejected": f"Receita Rejeitada - Pedido #{prescription.order.id}",
    }
    subject = subject_map.get(notification_type, "Notificacao de Receita")

    body_template = {
        "verified": (
            f"Ola {user.first_name or user.username},\n\n"
            f"Sua receita foi verificada e aprovada!\n"
            f"Seu pedido #{prescription.order.id} pode ser processado normalmente.\n\n"
            f"Obrigado!\n"
            f"iHealth Brasil"
        ),
        "rejected": (
            f"Ola {user.first_name or user.username},\n\n"
            f"Sua receita foi verificada e rejeitada.\n"
            f"Motivo: {prescription.verification_notes or 'Nao informado'}\n\n"
            f"Por favor, envie uma nova receita valida.\n\n"
            f"iHealth Brasil"
        ),
    }
    body = body_template.get(notification_type, "Sua receita foi atualizada.")

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.EMAIL_FROM_ADDRESS,
            recipient_list=[user.email],
            fail_silently=False,
        )
        # Log de sucesso na auditoria
        from products.models import PrescriptionAccessAudit

        PrescriptionAccessAudit.objects.create(
            prescription=prescription,
            user=user,
            action=PrescriptionAccessAudit.Action.VERIFIED,
            details={
                "notification_type": notification_type,
                "email_sent": True,
                "recipient": user.email,
            },
        )
    except Exception as exc:
        # Log de erro
        from products.models import PrescriptionAccessAudit

        PrescriptionAccessAudit.objects.create(
            prescription=prescription,
            user=user,
            action=PrescriptionAccessAudit.Action.VERIFIED,
            details={
                "notification_type": notification_type,
                "email_sent": False,
                "error": str(exc),
            },
        )


def enqueue_prescription_notification_email(
    *, prescription_id: int, notification_type: str
) -> None:
    """Enfileira envio de email de notificacao."""
    try:
        celery_task = cast(Any, send_prescription_notification_email_task)
        celery_task.delay(prescription_id=prescription_id, notification_type=notification_type)
    except Exception:  # pragma: no cover
        send_prescription_notification_email_task(prescription_id=prescription_id, notification_type=notification_type)


# ============= SCHEDULED TASKS / CELERY BEAT (Sprint 8) =============


@shared_task(ignore_result=True)
def mark_expired_prescriptions() -> None:
    """
    Marca receitas como EXPIRED automaticamente baseado em expires_at.
    Executada diariamente via Celery Beat (meia-noite UTC).
    """
    from products.models import MedicalPrescription

    now = timezone.now()
    expired_prescriptions = MedicalPrescription.objects.filter(
        status=MedicalPrescription.Status.SUBMITTED,
        expires_at__lt=now,
    )

    count = expired_prescriptions.update(
        status=MedicalPrescription.Status.EXPIRED,
        updated_at=now,
    )

    if count > 0:
        from products.models import PrescriptionAccessAudit

        # Log para auditoria formal
        for prescription in expired_prescriptions:
            PrescriptionAccessAudit.objects.create(
                prescription=prescription,
                action=PrescriptionAccessAudit.Action.VERIFIED,
                details={
                    "automatic_expiration": True,
                    "reason": "Validade expirada",
                },
            )
