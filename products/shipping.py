from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ShippingProviderError(Exception):
    """Erro lançado quando não há provedor de frete configurado ou ocorre falha."""


@dataclass
class ShippingService:
    service_code: str
    service_name: str
    price: float
    delivery_days: int | None
    deadline: str | None
    provider_name: str
    raw_response: Any | None = None


@dataclass
class ShippingQuote:
    provider_name: str
    origin_cep: str
    destination_cep: str
    package_weight_kg: float
    package_length_cm: float
    package_height_cm: float
    package_width_cm: float
    declared_value: float
    services: list[ShippingService]


class _NoopProvider:
    """Provedor de frete mínimo que apenas informa que não há integração configurada.

    Usado para desenvolvimento local quando a implementação real não está disponível.
    """

    provider_name = "noop"

    def quote_cart(self, *args, **kwargs) -> ShippingQuote:  # type: ignore[override]
        raise ShippingProviderError("Nenhum provedor de frete configurado para esta instância.")


def get_shipping_provider() -> _NoopProvider:
    """Retorna um provedor de frete funcional (ou um stub no ambiente local)."""

    # Para ambientes de desenvolvimento locais sem integração de frete,
    # retornamos um provedor 'noop' que sinaliza erro ao ser usado.
    return _NoopProvider()
