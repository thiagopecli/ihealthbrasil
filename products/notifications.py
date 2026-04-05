from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from uuid import uuid4

import requests
from django.conf import settings


class SmsProviderError(Exception):
    """Erro funcional ao enviar SMS em provider externo."""


@dataclass
class SmsSendResult:
    message_id: str
    provider_name: str
    raw_response: dict | None = None


class BaseSmsProvider:
    name = "base"

    def send_sms(self, *, to_number: str, message: str) -> SmsSendResult:
        raise NotImplementedError


class MockSmsProvider(BaseSmsProvider):
    name = "mock"

    def send_sms(self, *, to_number: str, message: str) -> SmsSendResult:
        reference = uuid4().hex[:16]
        return SmsSendResult(
            message_id=f"sms_mock_{reference}",
            provider_name=self.name,
            raw_response={"to": to_number, "message": message},
        )


class TwilioSmsProvider(BaseSmsProvider):
    name = "twilio"

    def __init__(self) -> None:
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_FROM_NUMBER
        if not self.account_sid or not self.auth_token or not self.from_number:
            raise SmsProviderError("Credenciais Twilio incompletas (SID, token e from number).")

    def send_sms(self, *, to_number: str, message: str) -> SmsSendResult:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        form_data = {"To": to_number, "From": self.from_number, "Body": message}

        token_raw = f"{self.account_sid}:{self.auth_token}".encode("utf-8")
        auth_header = base64.b64encode(token_raw).decode("utf-8")

        try:
            response = requests.post(
                url,
                data=form_data,
                headers={
                    "Authorization": f"Basic {auth_header}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=15,
            )
        except requests.RequestException as exc:
            raise SmsProviderError(f"Falha de rede ao enviar SMS: {exc}") from exc

        if response.status_code >= 400:
            raise SmsProviderError(f"Falha Twilio HTTP {response.status_code}: {response.text[:200]}")

        payload = json.loads(response.text) if response.text else {}

        sid = str(payload.get("sid") or "")
        if not sid:
            raise SmsProviderError("Twilio nao retornou identificador da mensagem (sid).")

        return SmsSendResult(message_id=sid, provider_name=self.name, raw_response=payload)


def get_sms_provider() -> BaseSmsProvider:
    provider = settings.SMS_PROVIDER.lower()
    if provider == "twilio":
        return TwilioSmsProvider()
    return MockSmsProvider()


def mask_phone_number(value: str) -> str:
    digits = "".join(ch for ch in (value or "") if ch.isdigit())
    if len(digits) <= 4:
        return f"***{digits}"
    return f"***{digits[-4:]}"


def build_order_status_sms_message(order_id: int, status_value: str) -> str:
    return f"iHealth: pedido #{order_id} atualizado para status {status_value}."
