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


def mask_email_address(value: str) -> str:
    email = (value or "").strip()
    if not email or "@" not in email:
        return "***"

    local, domain = email.split("@", 1)
    if not local:
        return f"***@{domain}"
    if len(local) == 1:
        masked_local = "*"
    elif len(local) == 2:
        masked_local = f"{local[0]}*"
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    return f"{masked_local}@{domain}"


def build_order_status_sms_message(order_id: int, status_value: str) -> str:
    return f"iHealth: pedido #{order_id} atualizado para status {status_value}."


# ============= PRESCRIPTIONS / MEMED INTEGRATION (Sprint 8) =============


class MemedProviderError(Exception):
    """Erro funcional ao enviar receita para Memed."""


@dataclass
class MemedSendResult:
    prescription_id: str
    provider_name: str
    raw_response: dict | None = None


class BaseMemedProvider:
    name = "base"

    def send_prescription(self, *, prescription_id: int, file_path: str, prescriber_name: str) -> MemedSendResult:
        raise NotImplementedError


class MockMemedProvider(BaseMemedProvider):
    """Mock provider para desenvolvimento e testes."""

    name = "mock"

    def send_prescription(self, *, prescription_id: int, file_path: str, prescriber_name: str) -> MemedSendResult:
        """Simula envio para Memed."""
        reference = uuid4().hex[:16]
        return MemedSendResult(
            prescription_id=f"memed_mock_{prescription_id}_{reference}",
            provider_name=self.name,
            raw_response={"prescription_id": prescription_id, "file": file_path, "status": "mock_sent"},
        )


class RealMemedProvider(BaseMemedProvider):
    """Integração real com API Memed para validação de receitas."""

    name = "memed"

    def __init__(self) -> None:
        self.api_key = settings.MEMED_API_KEY
        self.base_url = settings.MEMED_API_BASE_URL
        if not self.api_key or not self.base_url:
            raise MemedProviderError("Credenciais Memed incompletas (API_KEY ou BASE_URL).")

    def send_prescription(self, *, prescription_id: int, file_path: str, prescriber_name: str) -> MemedSendResult:
        """Envia receita para validação em Memed."""
        url = f"{self.base_url}/prescription/validate"

        # Prepara multipart para envio de arquivo
        try:
            with open(file_path, "rb") as f:
                files = {"file": (f.name, f, "application/pdf")}
                data = {
                    "prescription_id": str(prescription_id),
                    "prescriber_name": prescriber_name,
                }
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                }

                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=30,
                )
        except (FileNotFoundError, IOError) as exc:
            raise MemedProviderError(f"Erro ao ler arquivo de receita: {exc}") from exc
        except requests.RequestException as exc:
            raise MemedProviderError(f"Falha de rede ao enviar para Memed: {exc}") from exc

        if response.status_code >= 400:
            raise MemedProviderError(f"Falha Memed HTTP {response.status_code}: {response.text[:200]}")

        payload = json.loads(response.text) if response.text else {}

        memed_id = str(payload.get("id") or payload.get("prescription_id") or "")
        if not memed_id:
            raise MemedProviderError("Memed nao retornou identificador da receita.")

        return MemedSendResult(
            prescription_id=memed_id,
            provider_name=self.name,
            raw_response=payload,
        )


def get_memed_provider() -> BaseMemedProvider:
    """Factory para obter provider Memed configurado."""
    provider = settings.MEMED_PROVIDER.lower()
    if provider == "memed":
        return RealMemedProvider()
    return MockMemedProvider()
