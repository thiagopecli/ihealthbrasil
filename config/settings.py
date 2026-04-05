import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
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
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
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
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (uploads de usuarios)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Validacao de tamanho de upload
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ihealthbrasil API",
    "DESCRIPTION": "Documentacao OpenAPI da API backend do projeto ihealthbrasil.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
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

# Pagamentos (Sprint 6)
PAYMENT_GATEWAY_PROVIDER = os.getenv("PAYMENT_GATEWAY_PROVIDER", "mock").lower()
PAYMENT_DEFAULT_CURRENCY = os.getenv("PAYMENT_DEFAULT_CURRENCY", "brl").lower()
PAYMENT_SUCCESS_URL = os.getenv("PAYMENT_SUCCESS_URL", "http://127.0.0.1:8000/payment/success")
PAYMENT_CANCEL_URL = os.getenv("PAYMENT_CANCEL_URL", "http://127.0.0.1:8000/payment/cancel")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
