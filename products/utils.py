"""Utilitários para upload de receitas e integração S3."""

import hashlib
from datetime import timedelta

from django.utils import timezone


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
