"""Django settings for preservation.studio.

Environment-driven so the same repo runs locally (SQLite) and on Railway
(Postgres via DATABASE_URL or PG* variables). All secrets come from env
vars in production; nothing here hard-codes credentials.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-key-do-not-use-in-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,.up.railway.app"
    ).split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "studio",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "preservationstudio.urls"

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

WSGI_APPLICATION = "preservationstudio.wsgi.application"

# ---- Database: Postgres on Railway (DATABASE_URL or PG*), SQLite locally ----

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

_db_url = os.environ.get("DATABASE_URL", "").strip()
if _db_url:
    from urllib.parse import urlparse

    _parsed = urlparse(_db_url)
    _port_raw = _parsed.port if _parsed.port else 5432
    try:
        _port = int(_port_raw)
    except (TypeError, ValueError):
        _port = 5432
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _parsed.path.lstrip("/") or "railway",
        "USER": _parsed.username or "postgres",
        "PASSWORD": _parsed.password or "",
        "HOST": _parsed.hostname or "",
        "PORT": _port,
        "CONN_MAX_AGE": 60,
    }
else:
    _pg_host = os.environ.get("PGHOST", "").strip()
    if _pg_host:
        try:
            _pg_port = int(os.environ.get("PGPORT", "5432"))
        except (TypeError, ValueError):
            _pg_port = 5432
        DATABASES["default"] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("PGDATABASE", "railway"),
            "USER": os.environ.get("PGUSER", "postgres"),
            "PASSWORD": os.environ.get("PGPASSWORD", ""),
            "HOST": _pg_host,
            "PORT": _pg_port,
            "CONN_MAX_AGE": 60,
        }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Los_Angeles"
USE_I18N = True
USE_TZ = True

# ---- Static files (Whitenoise, compressed + cache-busted) ----------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ---- Uploads (Sentimental Value photos) -----------------------------------

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- Security headers -------------------------------------------------------

# Railway terminates TLS at the edge and forwards plain HTTP to the container.
# Trust the X-Forwarded-Proto header so is_secure() (and SECURE_SSL_REDIRECT)
# behave correctly instead of looping.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "0") == "1"
SESSION_COOKIE_SECURE = os.environ.get("DJANGO_SECURE_COOKIES", "0") == "1"
CSRF_COOKIE_SECURE = os.environ.get("DJANGO_SECURE_COOKIES", "0") == "1"

# ---- Admin: hidden behind an env-var path (unset = admin disabled) ---------

ADMIN_URL = os.environ.get("DJANGO_ADMIN_URL", "").strip().strip("/")

# ---- Email notifications (submission alerts) --------------------------------
#
# Every form submission is saved to the database (reviewable in the admin).
# When NOTIFY_EMAIL is set, a summary email is also sent to that address.
# Until an address is configured, sending is skipped entirely — no crash.
# SMTP credentials come from env vars (works with any provider: Gmail,
# SendGrid, Mailgun, Resend, etc.).

NOTIFY_EMAIL = os.environ.get("DJANGO_NOTIFY_EMAIL", "").strip()
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "")
try:
    EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587"))
except (TypeError, ValueError):
    EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("DJANGO_EMAIL_USE_TLS", "1") == "1"
DEFAULT_FROM_EMAIL = os.environ.get(
    "DJANGO_FROM_EMAIL", "preservation.studio <no-reply@preservation.studio>"
)
