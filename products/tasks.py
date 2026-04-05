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
