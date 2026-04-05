"""Utilitarios de receitas, i18n e precificacao de catalogo."""

import hashlib
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core import signing
from django.utils import timezone

DEFAULT_COUNTRY = "BR"
DEFAULT_CURRENCY = "BRL"

LANGUAGE_TO_PACKAGE_INSERT = {
    "pt": "pt_BR",
    "pt-br": "pt_BR",
    "en": "en_US",
    "en-us": "en_US",
    "es": "es_ES",
    "es-es": "es_ES",
}

API_MESSAGES = {
    "invalid_currency": {
        "pt": "Moeda deve conter apenas letras (ex.: brl, usd).",
        "en": "Currency must contain letters only (e.g.: brl, usd).",
        "es": "La moneda debe contener solo letras (ej.: brl, usd).",
    },
    "invalid_country": {
        "pt": "Pais deve conter exatamente 2 letras (ex.: BR, US).",
        "en": "Country must contain exactly 2 letters (e.g.: BR, US).",
        "es": "El pais debe contener exactamente 2 letras (ej.: BR, US).",
    },
    "admin_only_action": {
        "pt": "Apenas admin pode executar esta acao.",
        "en": "Only admin can perform this action.",
        "es": "Solo admin puede realizar esta accion.",
    },
}


def calculate_file_hash(file_obj) -> str:
    """
    Calcula SHA-256 de um arquivo para garantir integridade.

    Args:
        file_obj: Django File object ou similar

    Returns:
        SHA-256 hexdigest
    """
    sha256_hash = hashlib.sha256()
    file_obj.seek(0)
    for block in iter(lambda: file_obj.read(4096), b""):
        sha256_hash.update(block)
    file_obj.seek(0)
    return sha256_hash.hexdigest()


def calculate_prescription_expiry(validity_days: int = 30) -> object:
    """
    Calcula data de expiração de uma receita.

    Args:
        validity_days: Número de dias que a receita é válida

    Returns:
        datetime object
    """
    return timezone.now() + timedelta(days=validity_days)


def normalize_country_code(value: str | None) -> str:
    """Normaliza pais para ISO alpha-2 em caixa alta."""
    if not value:
        return DEFAULT_COUNTRY
    return value.strip().upper()


def normalize_currency_code(value: str | None) -> str:
    """Normaliza moeda para ISO 4217 em caixa alta."""
    if not value:
        return DEFAULT_CURRENCY
    return value.strip().upper()


def preferred_language_tag(request) -> str:
    """Extrai idioma preferencial de request usando LANGUAGE_CODE/Accept-Language."""
    if request is None:
        return "pt"

    language_code = getattr(request, "LANGUAGE_CODE", "") or ""
    if language_code:
        return language_code.lower()

    accept_language = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    for raw_part in accept_language.split(","):
        value = raw_part.split(";")[0].strip()
        if value:
            return value.lower()
    return "pt"


def package_insert_language_candidates(request) -> list[str]:
    """Retorna ordem de preferencia de linguagem de bula a partir do idioma requisitado."""
    candidates: list[str] = []

    tag = preferred_language_tag(request)
    if tag:
        normalized = tag.replace("_", "-").lower()
        language_only = normalized.split("-")[0]
        for key in (normalized, language_only):
            mapped = LANGUAGE_TO_PACKAGE_INSERT.get(key)
            if mapped and mapped not in candidates:
                candidates.append(mapped)

    if "pt_BR" not in candidates:
        candidates.append("pt_BR")
    return candidates


def resolve_country_currency_from_request(request) -> tuple[str, str]:
    """Resolve pais e moeda por querystring/cabecalho com defaults seguros."""
    if request is None:
        return DEFAULT_COUNTRY, DEFAULT_CURRENCY

    query_params = getattr(request, "query_params", None)
    query_country = query_params.get("country") if query_params else None
    query_currency = query_params.get("currency") if query_params else None

    header_country = request.headers.get("X-Country")
    header_currency = request.headers.get("X-Currency")

    country = normalize_country_code(query_country or header_country)
    currency = normalize_currency_code(query_currency or header_currency)

    if country == DEFAULT_COUNTRY and currency == DEFAULT_CURRENCY:
        language_tag = preferred_language_tag(request)
        if language_tag.startswith("en"):
            country = "US"
            currency = "USD"
        elif language_tag.startswith("es"):
            country = "ES"
            currency = "EUR"

    return country, currency


def resolve_product_display_price(product, request) -> dict:
    """Escolhe preco por pais/moeda com fallback para preco base do produto."""
    country, currency = resolve_country_currency_from_request(request)
    active_prices = [price for price in product.prices.all() if price.is_active]

    exact_match = next(
        (price for price in active_prices if price.country_code == country and price.currency == currency),
        None,
    )
    if exact_match:
        return {
            "amount": exact_match.amount,
            "currency": exact_match.currency,
            "country": exact_match.country_code,
            "is_fallback": False,
        }

    currency_match = next((price for price in active_prices if price.currency == currency), None)
    if currency_match:
        return {
            "amount": currency_match.amount,
            "currency": currency_match.currency,
            "country": currency_match.country_code,
            "is_fallback": False,
        }

    return {
        "amount": (product.price or Decimal("0.00")).quantize(Decimal("0.01")),
        "currency": DEFAULT_CURRENCY,
        "country": DEFAULT_COUNTRY,
        "is_fallback": True,
    }


def get_localized_message(request, key: str) -> str:
    """Retorna mensagem da API no idioma preferido com fallback para portugues."""
    language_tag = preferred_language_tag(request)
    family = "pt"
    if language_tag.startswith("en"):
        family = "en"
    elif language_tag.startswith("es"):
        family = "es"

    messages = API_MESSAGES.get(key, {})
    return messages.get(family) or messages.get("pt") or key


def build_prescription_download_token(*, prescription_id: int, requested_by_user_id: int | None, file_hash: str) -> str:
    """Gera token assinado para download temporário de receita."""
    payload = {
        "pid": prescription_id,
        "uid": requested_by_user_id,
        "fh": file_hash or "",
    }
    return signing.dumps(payload, salt="prescription-download")


def parse_prescription_download_token(token: str) -> dict:
    """Valida e decodifica token assinado de download de receita."""
    max_age = int(getattr(settings, "PRESCRIPTION_SIGNED_URL_TTL_SECONDS", 300))
    return signing.loads(token, salt="prescription-download", max_age=max_age)
