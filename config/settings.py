import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urljoin

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

ENVIRONMENT = os.getenv("DJANGO_ENV", "development").lower()
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me")
if ENVIRONMENT == "production" and SECRET_KEY == "django-insecure-change-me":
    raise ImproperlyConfigured("SECRET_KEY precisa ser definido em producao.")

JWT_SIGNING_KEY = os.getenv("JWT_SIGNING_KEY", SECRET_KEY)
if ENVIRONMENT == "production" and len(JWT_SIGNING_KEY) < 32:
    raise ImproperlyConfigured("JWT_SIGNING_KEY precisa ter ao menos 32 caracteres em producao.")

ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]

INSTALLED_APPS = [
    "accounts",
    "products",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "rest_framework_simplejwt.token_blacklist",
    "storages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "config.middleware.RequestObservabilityMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

sqlite_name = os.getenv("SQLITE_NAME", "db.sqlite3")
default_db_url = f"sqlite:///{(BASE_DIR / sqlite_name).as_posix()}"
raw_database_url = os.getenv("DATABASE_URL")
database_url = raw_database_url or default_db_url

if ENVIRONMENT == "production" and not raw_database_url:
    raise ImproperlyConfigured("DATABASE_URL precisa ser definido em producao.")

DATABASES = {
    "default": dj_database_url.parse(
        database_url,
        conn_max_age=int(os.getenv("DB_CONN_MAX_AGE", "60")),
        ssl_require=os.getenv("DB_SSL_REQUIRE", "True").lower() == "true" and ENVIRONMENT == "production",
    )
}

MEDIA_STORAGE_PROVIDER = os.getenv("MEDIA_STORAGE_PROVIDER", "local").lower()
USE_CLOUD_MEDIA_STORAGE = MEDIA_STORAGE_PROVIDER == "s3"
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "").strip()
AWS_PRIVATE_STORAGE_BUCKET_NAME = os.getenv("AWS_PRIVATE_STORAGE_BUCKET_NAME", AWS_STORAGE_BUCKET_NAME).strip()
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "sa-east-1").strip()
AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN", "").strip()
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "").strip() or None
AWS_PUBLIC_MEDIA_LOCATION = os.getenv("AWS_PUBLIC_MEDIA_LOCATION", "media").strip().strip("/")
AWS_PRIVATE_MEDIA_LOCATION = os.getenv("AWS_PRIVATE_MEDIA_LOCATION", "private").strip().strip("/")
AWS_S3_FILE_OVERWRITE = False

if USE_CLOUD_MEDIA_STORAGE and not AWS_STORAGE_BUCKET_NAME:
    raise ImproperlyConfigured("AWS_STORAGE_BUCKET_NAME precisa ser definido quando MEDIA_STORAGE_PROVIDER=s3.")

if USE_CLOUD_MEDIA_STORAGE and not AWS_PRIVATE_STORAGE_BUCKET_NAME:
    AWS_PRIVATE_STORAGE_BUCKET_NAME = AWS_STORAGE_BUCKET_NAME

if USE_CLOUD_MEDIA_STORAGE:
    public_media_domain = AWS_S3_CUSTOM_DOMAIN or f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
    MEDIA_URL = urljoin(f"https://{public_media_domain}/", "")
else:
    MEDIA_URL = "/media/"

DEFAULT_FILE_STORAGE = (
    "storages.backends.s3boto3.S3Boto3Storage"
    if USE_CLOUD_MEDIA_STORAGE
    else "django.core.files.storage.FileSystemStorage"
)

STORAGES = {
    "default": {
        "BACKEND": DEFAULT_FILE_STORAGE,
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
LANGUAGES = [
    ("pt-br", _("Portuguese (Brazil)")),
    ("en-us", _("English (United States)")),
    ("es-es", _("Spanish (Spain)")),
    ("fr-fr", _("French (France)")),
]
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (uploads de usuarios)
MEDIA_ROOT = BASE_DIR / "media"
PRIVATE_MEDIA_ROOT = BASE_DIR / "private_media"
PRESCRIPTION_SIGNED_URL_TTL_SECONDS = int(os.getenv("PRESCRIPTION_SIGNED_URL_TTL_SECONDS", "300"))

# Validacao de tamanho de upload
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {
        "auth-login": os.getenv("THROTTLE_AUTH_LOGIN", "30/min"),
        "auth-register": os.getenv("THROTTLE_AUTH_REGISTER", "20/hour"),
        "auth-refresh": os.getenv("THROTTLE_AUTH_REFRESH", "120/min"),
        "auth-verify": os.getenv("THROTTLE_AUTH_VERIFY", "120/min"),
        "auth-logout": os.getenv("THROTTLE_AUTH_LOGOUT", "60/min"),
        "payment-webhook": os.getenv("THROTTLE_PAYMENT_WEBHOOK", "600/min"),
        "healthcheck": os.getenv("THROTTLE_HEALTHCHECK", "60/min"),
    },
}

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "config.logging.StructuredJSONFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "ihealthbrasil.request": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "ihealthbrasil.tasks": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ihealthbrasil API",
    "DESCRIPTION": "Documentacao OpenAPI da API backend do projeto ihealthbrasil.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "OrderStatusEnum": "products.models.Order.Status",
        "PaymentTransactionStatusEnum": "products.models.PaymentTransaction.Status",
        "PaymentIntentStatusEnum": "products.models.PaymentIntent.Status",
        "MedicalPrescriptionStatusEnum": "products.models.MedicalPrescription.Status",
        "ExternalNotificationStatusEnum": "products.models.ExternalNotification.Status",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": os.getenv("JWT_ROTATE_REFRESH_TOKENS", "True").lower() == "true",
    "BLACKLIST_AFTER_ROTATION": os.getenv("JWT_BLACKLIST_AFTER_ROTATION", "True").lower() == "true",
    "UPDATE_LAST_LOGIN": False,
    "SIGNING_KEY": JWT_SIGNING_KEY,
}

PAYMENT_WEBHOOK_SECRET = os.getenv("PAYMENT_WEBHOOK_SECRET", "dev-webhook-secret-change-me")
PAYMENT_DEFAULT_COMMISSION_RATE = os.getenv("PAYMENT_DEFAULT_COMMISSION_RATE", "12.00")

if ENVIRONMENT == "production" and PAYMENT_WEBHOOK_SECRET == "dev-webhook-secret-change-me":
    raise ImproperlyConfigured("PAYMENT_WEBHOOK_SECRET precisa ser definido em producao.")

if ENVIRONMENT == "production":
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() == "true"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_REFERRER_POLICY = "same-origin"

# Pagamentos (Sprint 6)
PAYMENT_GATEWAY_PROVIDER = os.getenv("PAYMENT_GATEWAY_PROVIDER", "mock").lower()
PAYMENT_DEFAULT_CURRENCY = os.getenv("PAYMENT_DEFAULT_CURRENCY", "brl").lower()
PAYMENT_SUCCESS_URL = os.getenv("PAYMENT_SUCCESS_URL", "http://127.0.0.1:8000/payment/success")
PAYMENT_CANCEL_URL = os.getenv("PAYMENT_CANCEL_URL", "http://127.0.0.1:8000/payment/cancel")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")

# Integracoes externas (Sprint 8)
SMS_ENABLED = os.getenv("SMS_ENABLED", "True").lower() == "true"
SMS_PROVIDER = os.getenv("SMS_PROVIDER", "mock").lower()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

# Memed Integration (prescricoes externas)
MEMED_ENABLED = os.getenv("MEMED_ENABLED", "False").lower() == "true"
MEMED_PROVIDER = os.getenv("MEMED_PROVIDER", "mock").lower()
MEMED_API_KEY = os.getenv("MEMED_API_KEY", "")
MEMED_API_BASE_URL = os.getenv("MEMED_API_BASE_URL", "https://api.memed.com.br/v1")

# Email for notifications (Sprint 8)
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() == "true"
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "noreply@ihealthbrasil.com.br")

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "False").lower() == "true"
CELERY_TASK_EAGER_PROPAGATES = os.getenv("CELERY_TASK_EAGER_PROPAGATES", "True").lower() == "true"
CELERY_TASK_IGNORE_RESULT = os.getenv("CELERY_TASK_IGNORE_RESULT", "True").lower() == "true"

# Celery Beat - Scheduled Tasks (Sprint 8)
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "mark-expired-prescriptions": {
        "task": "products.tasks.mark_expired_prescriptions",
        "schedule": crontab(hour=0, minute=0),  # Executa diariamente à meia noite UTC
        "options": {"queue": "default", "priority": 10},
    },
}
