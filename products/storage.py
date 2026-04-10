from django.conf import settings
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    """Storage para mídia pública (catalogo/produtos)."""

    location = settings.AWS_PUBLIC_MEDIA_LOCATION
    default_acl = "public-read"
    file_overwrite = False


class PrivateMediaStorage(S3Boto3Storage):
    """Storage privado para receitas médicas com URL assinada temporária."""

    bucket_name = settings.AWS_PRIVATE_STORAGE_BUCKET_NAME
    location = settings.AWS_PRIVATE_MEDIA_LOCATION
    default_acl = "private"
    file_overwrite = False
    custom_domain = False
    querystring_auth = True
    querystring_expire = settings.PRESCRIPTION_SIGNED_URL_TTL_SECONDS


def get_private_media_storage():
    """Retorna storage de receita conforme o provedor configurado."""

    if settings.USE_CLOUD_MEDIA_STORAGE:
        return PrivateMediaStorage()
    return default_storage


# Alias para manter compatibilidade com imports/migrations existentes.
PrivatePrescriptionStorage = PrivateMediaStorage
