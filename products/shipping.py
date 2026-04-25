from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Sequence

import requests
from django.conf import settings

from products.models import Cart


class ShippingProviderError(Exception):
    """Erro funcional ao consultar cotacao de frete."""


@dataclass
class ShippingServiceQuote:
    service_code: str
    service_name: str
    price: Decimal
    delivery_days: int | None = None
    deadline: str | None = None
    provider_name: str = ""
    raw_response: dict | None = None


@dataclass
class ShippingQuote:
    provider_name: str
    origin_cep: str
    destination_cep: str
    package_weight_kg: Decimal
    package_length_cm: Decimal
    package_height_cm: Decimal
    package_width_cm: Decimal
    declared_value: Decimal
    services: list[ShippingServiceQuote]


def _normalize_cep(value: str | None) -> str:
    return "".join(character for character in (value or "") if character.isdigit())


def _parse_decimal(value: str | None, default: str = "0.00") -> Decimal:
    raw_value = (value or default).strip().replace(",", ".")
    try:
        return Decimal(raw_value)
    except Exception as exc:  # pragma: no cover - protecao de parsing
        raise ShippingProviderError(f"Valor decimal invalido: {value!r}") from exc


def _parse_decimal_setting(name: str, default: str) -> Decimal:
    return _parse_decimal(getattr(settings, name, default), default)


def _parse_service_codes(value: str | Sequence[str] | None) -> list[str]:
    if value is None:
        raw_codes = getattr(settings, "CORREIOS_SERVICE_CODES", "04014,04510")
    else:
        raw_codes = value

    if isinstance(raw_codes, str):
        candidates = raw_codes.split(",")
    else:
        candidates = list(raw_codes)

    return [code.strip() for code in candidates if code and code.strip()]


def _estimate_package_weight_kg(total_quantity: int) -> Decimal:
    default_item_weight = _parse_decimal_setting("SHIPPING_DEFAULT_ITEM_WEIGHT_KG", "0.50")
    weight = (default_item_weight * Decimal(total_quantity)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    return weight if weight > Decimal("0.000") else Decimal("0.001")


def _cart_declared_value(cart: Cart) -> Decimal:
    return (cart.total_price or Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _cart_total_quantity(cart: Cart) -> int:
    return sum(item.quantity for item in cart.items.all())


def _build_quote(
    *,
    provider_name: str,
    origin_cep: str,
    destination_cep: str,
    package_weight_kg: Decimal,
    declared_value: Decimal,
    package_length_cm: Decimal,
    package_height_cm: Decimal,
    package_width_cm: Decimal,
    services: list[ShippingServiceQuote],
) -> ShippingQuote:
    return ShippingQuote(
        provider_name=provider_name,
        origin_cep=origin_cep,
        destination_cep=destination_cep,
        package_weight_kg=package_weight_kg,
        package_length_cm=package_length_cm,
        package_height_cm=package_height_cm,
        package_width_cm=package_width_cm,
        declared_value=declared_value,
        services=services,
    )


class BaseShippingProvider:
    name = "base"

    def quote_cart(
        self,
        *,
        cart: Cart,
        destination_cep: str,
        service_codes: Sequence[str] | None = None,
    ) -> ShippingQuote:
        raise NotImplementedError


class MockCorreiosShippingProvider(BaseShippingProvider):
    """Provider local para desenvolvimento e testes."""

    name = "mock"

    _SERVICE_CATALOG = {
        "04014": ("SEDEX", Decimal("18.90"), 3),
        "04510": ("PAC", Decimal("12.90"), 7),
    }

    def quote_cart(
        self,
        *,
        cart: Cart,
        destination_cep: str,
        service_codes: Sequence[str] | None = None,
    ) -> ShippingQuote:
        normalized_destination = _normalize_cep(destination_cep)
        if len(normalized_destination) != 8:
            raise ShippingProviderError("CEP de destino invalido. Informe 8 digitos.")

        origin_cep = _normalize_cep(getattr(settings, "SHIPPING_ORIGIN_CEP", "")) or "00000000"
        codes = _parse_service_codes(service_codes)
        total_quantity = _cart_total_quantity(cart)
        package_weight_kg = _estimate_package_weight_kg(total_quantity)
        declared_value = _cart_declared_value(cart)

        package_length_cm = _parse_decimal_setting("SHIPPING_DEFAULT_PACKAGE_LENGTH_CM", "20")
        package_height_cm = _parse_decimal_setting("SHIPPING_DEFAULT_PACKAGE_HEIGHT_CM", "10")
        package_width_cm = _parse_decimal_setting("SHIPPING_DEFAULT_PACKAGE_WIDTH_CM", "15")

        services: list[ShippingServiceQuote] = []
        for service_code in codes:
            service_name, base_price, delivery_days = self._SERVICE_CATALOG.get(
                service_code,
                (f"Servico {service_code}", Decimal("15.00"), 5),
            )
            price = (base_price + (package_weight_kg * Decimal("4.20")) + (declared_value * Decimal("0.008"))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            services.append(
                ShippingServiceQuote(
                    service_code=service_code,
                    service_name=service_name,
                    price=price,
                    delivery_days=delivery_days,
                    deadline=None,
                    provider_name=self.name,
                    raw_response={
                        "mode": "mock",
                        "service_code": service_code,
                        "base_price": str(base_price),
                        "delivery_days": delivery_days,
                    },
                )
            )

        return _build_quote(
            provider_name=self.name,
            origin_cep=origin_cep,
            destination_cep=normalized_destination,
            package_weight_kg=package_weight_kg,
            declared_value=declared_value,
            package_length_cm=package_length_cm,
            package_height_cm=package_height_cm,
            package_width_cm=package_width_cm,
            services=services,
        )


class CorreiosShippingProvider(BaseShippingProvider):
    """Integracao com o calculador de frete dos Correios."""

    name = "correios"

    def __init__(self) -> None:
        self.base_url = getattr(settings, "CORREIOS_API_BASE_URL", "https://ws.correios.com.br/calculador/CalcPrecoPrazo.aspx")
        self.origin_cep = _normalize_cep(getattr(settings, "SHIPPING_ORIGIN_CEP", ""))
        self.account_code = getattr(settings, "CORREIOS_ACCOUNT_CODE", "").strip()
        self.account_password = getattr(settings, "CORREIOS_ACCOUNT_PASSWORD", "").strip()
        self.default_service_codes = _parse_service_codes(None)

        if len(self.origin_cep) != 8:
            raise ShippingProviderError("SHIPPING_ORIGIN_CEP precisa conter 8 digitos para usar o provider dos Correios.")

    def quote_cart(
        self,
        *,
        cart: Cart,
        destination_cep: str,
        service_codes: Sequence[str] | None = None,
    ) -> ShippingQuote:
        normalized_destination = _normalize_cep(destination_cep)
        if len(normalized_destination) != 8:
            raise ShippingProviderError("CEP de destino invalido. Informe 8 digitos.")

        codes = _parse_service_codes(service_codes) or self.default_service_codes
        if not codes:
            raise ShippingProviderError("Nenhum servico dos Correios foi configurado.")

        total_quantity = _cart_total_quantity(cart)
        package_weight_kg = _estimate_package_weight_kg(total_quantity)
        declared_value = _cart_declared_value(cart)

        package_length_cm = _parse_decimal_setting("SHIPPING_DEFAULT_PACKAGE_LENGTH_CM", "20")
        package_height_cm = _parse_decimal_setting("SHIPPING_DEFAULT_PACKAGE_HEIGHT_CM", "10")
        package_width_cm = _parse_decimal_setting("SHIPPING_DEFAULT_PACKAGE_WIDTH_CM", "15")
        package_format = getattr(settings, "CORREIOS_PACKAGE_FORMAT", "1")
        calculation_mode = getattr(settings, "CORREIOS_CALCULATION_MODE", "3")

        params = {
            "nCdEmpresa": self.account_code,
            "sDsSenha": self.account_password,
            "sCepOrigem": self.origin_cep,
            "sCepDestino": normalized_destination,
            "nVlPeso": f"{package_weight_kg:.3f}",
            "nCdFormato": package_format,
            "nVlComprimento": f"{package_length_cm:.2f}",
            "nVlAltura": f"{package_height_cm:.2f}",
            "nVlLargura": f"{package_width_cm:.2f}",
            "sCdServico": ",".join(codes),
            "nVlDiametro": "0",
            "sCdMaoPropria": "N",
            "nVlValorDeclarado": f"{declared_value:.2f}",
            "sCdAvisoRecebimento": "N",
            "StrRetorno": "xml",
            "nIndicaCalculo": calculation_mode,
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=20)
        except requests.RequestException as exc:
            raise ShippingProviderError(f"Falha de rede ao consultar Correios: {exc}") from exc

        if response.status_code >= 400:
            raise ShippingProviderError(f"Falha Correios HTTP {response.status_code}: {response.text[:200]}")

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as exc:
            raise ShippingProviderError("Resposta dos Correios nao esta em XML valido.") from exc

        services: list[ShippingServiceQuote] = []
        for service_node in root.findall(".//cServico"):
            service_code = (service_node.findtext("Codigo") or "").strip()
            error_code = (service_node.findtext("Erro") or "0").strip()
            if error_code not in {"", "0"}:
                message = (service_node.findtext("MsgErro") or service_node.findtext("Msg") or "Erro desconhecido nos Correios").strip()
                raise ShippingProviderError(message)

            price = _parse_decimal(service_node.findtext("Valor"), default="0.00").quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            delivery_days_text = (service_node.findtext("PrazoEntrega") or "").strip()
            delivery_days = int(delivery_days_text) if delivery_days_text.isdigit() else None
            deadline = (service_node.findtext("DataMaxEntrega") or service_node.findtext("DataPostagem") or "").strip() or None
            service_name = (
                service_node.findtext("Msg")
                or service_node.findtext("Nome")
                or service_node.findtext("Servico")
                or service_code
            ).strip()

            services.append(
                ShippingServiceQuote(
                    service_code=service_code,
                    service_name=service_name,
                    price=price,
                    delivery_days=delivery_days,
                    deadline=deadline,
                    provider_name=self.name,
                    raw_response={
                        "codigo": service_code,
                        "valor": service_node.findtext("Valor"),
                        "prazo_entrega": delivery_days_text,
                        "data_max_entrega": service_node.findtext("DataMaxEntrega"),
                    },
                )
            )

        if not services:
            raise ShippingProviderError("Correios nao retornou cotacao de frete para os servicos solicitados.")

        return _build_quote(
            provider_name=self.name,
            origin_cep=self.origin_cep,
            destination_cep=normalized_destination,
            package_weight_kg=package_weight_kg,
            declared_value=declared_value,
            package_length_cm=package_length_cm,
            package_height_cm=package_height_cm,
            package_width_cm=package_width_cm,
            services=services,
        )


def get_shipping_provider() -> BaseShippingProvider:
    provider = getattr(settings, "SHIPPING_PROVIDER", "mock").lower()
    if provider == "correios":
        return CorreiosShippingProvider()
    return MockCorreiosShippingProvider()