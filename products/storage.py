from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    """Storage para mídia pública (catalogo/produtos)."""

    location = "media"
    default_acl = "public-read"
    file_overwrite = False


class PrivateMediaStorage(S3Boto3Storage):
    """Storage privado para receitas médicas com URL assinada temporária."""

    bucket_name = settings.AWS_PRIVATE_STORAGE_BUCKET_NAME
    location = "private"
    default_acl = "private"
    file_overwrite = False
    custom_domain = False
    querystring_auth = True
    querystring_expire = settings.PRESCRIPTION_SIGNED_URL_TTL_SECONDS


# Alias para manter compatibilidade com imports/migrations existentes.
PrivatePrescriptionStorage = PrivateMediaStorage
