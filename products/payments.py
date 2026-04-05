from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import uuid4

from django.conf import settings
import stripe


class PaymentGatewayError(Exception):
    """Erro funcional da comunicação com gateway de pagamento."""


@dataclass
class PaymentIntentResult:
    payment_intent_id: str
    status: str
    client_secret: str = ""
    checkout_url: str = ""
    checkout_session_id: str = ""
    raw_response: dict | None = None


class BasePaymentGateway:
    name = "base"

    def get_or_create_customer_external_id(self, user) -> str:
        raise NotImplementedError

    def get_or_create_connected_account_external_id(self, user) -> str:
        raise NotImplementedError

    def create_payment_intent(
        self,
        *,
        order_id: int,
        amount: Decimal,
        currency: str,
        customer_external_id: str,
        connected_account_external_id: Optional[str] = None,
    ) -> PaymentIntentResult:
        raise NotImplementedError


class MockPaymentGateway(BasePaymentGateway):
    """Gateway fake para desenvolvimento e testes locais."""

    name = "mock"

    def get_or_create_customer_external_id(self, user) -> str:
        return f"cus_mock_{user.id}"

    def get_or_create_connected_account_external_id(self, user) -> str:
        return f"acct_mock_{user.id}"

    def create_payment_intent(
        self,
        *,
        order_id: int,
        amount: Decimal,
        currency: str,
        customer_external_id: str,
        connected_account_external_id: Optional[str] = None,
    ) -> PaymentIntentResult:
        reference = uuid4().hex[:16]
        return PaymentIntentResult(
            payment_intent_id=f"pi_mock_{reference}",
            checkout_session_id=f"cs_mock_{reference}",
            client_secret=f"pi_mock_{reference}_secret",
            checkout_url=f"https://mock-payments.local/checkout/{reference}",
            status="requires_payment_method",
            raw_response={
                "order_id": order_id,
                "amount": str(amount),
                "currency": currency,
                "customer": customer_external_id,
                "connected_account": connected_account_external_id,
            },
        )


class StripePaymentGateway(BasePaymentGateway):
    """Integração com Stripe para customer, connected account e payment intent."""

    name = "stripe"

    def __init__(self) -> None:
        secret_key = settings.STRIPE_SECRET_KEY
        if not secret_key:
            raise PaymentGatewayError("STRIPE_SECRET_KEY não configurada.")

        stripe.api_key = secret_key

    def get_or_create_customer_external_id(self, user) -> str:
        payload = {
            "name": (user.get_full_name() or user.username),
            "metadata": {"user_id": str(user.id), "username": user.username},
        }
        if user.email:
            payload["email"] = user.email

        customer = stripe.Customer.create(**payload)
        return customer["id"]

    def get_or_create_connected_account_external_id(self, user) -> str:
        payload = {
            "type": "express",
            "country": "BR",
            "capabilities": {
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
            "metadata": {"user_id": str(user.id), "username": user.username},
        }
        if user.email:
            payload["email"] = user.email

        account = stripe.Account.create(**payload)
        return account["id"]

    def create_payment_intent(
        self,
        *,
        order_id: int,
        amount: Decimal,
        currency: str,
        customer_external_id: str,
        connected_account_external_id: Optional[str] = None,
    ) -> PaymentIntentResult:
        amount_cents = int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        metadata = {"order_id": str(order_id)}

        payment_intent_payload = {
            "amount": amount_cents,
            "currency": currency,
            "customer": customer_external_id,
            "automatic_payment_methods": {"enabled": True},
            "metadata": metadata,
        }
        if connected_account_external_id:
            payment_intent_payload["transfer_data"] = {
                "destination": connected_account_external_id,
            }

        intent = stripe.PaymentIntent.create(**payment_intent_payload)

        session_payload = {
            "mode": "payment",
            "customer": customer_external_id,
            "line_items": [
                {
                    "price_data": {
                        "currency": currency,
                        "unit_amount": amount_cents,
                        "product_data": {"name": f"Pedido #{order_id}"},
                    },
                    "quantity": 1,
                }
            ],
            "success_url": f"{settings.PAYMENT_SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": settings.PAYMENT_CANCEL_URL,
            "metadata": metadata,
        }
        if connected_account_external_id:
            session_payload["payment_intent_data"] = {
                "transfer_data": {"destination": connected_account_external_id},
                "metadata": metadata,
            }

        session = stripe.checkout.Session.create(**session_payload)

        return PaymentIntentResult(
            payment_intent_id=intent.get("id", ""),
            checkout_session_id=session.get("id", ""),
            client_secret=intent.get("client_secret", ""),
            checkout_url=session.get("url", ""),
            status=intent.get("status", "requires_payment_method"),
            raw_response={
                "payment_intent_id": intent.get("id"),
                "checkout_session_id": session.get("id"),
                "checkout_url": session.get("url"),
            },
        )


def get_payment_gateway() -> BasePaymentGateway:
    provider = settings.PAYMENT_GATEWAY_PROVIDER
    if provider == "stripe":
        return StripePaymentGateway()
    return MockPaymentGateway()
