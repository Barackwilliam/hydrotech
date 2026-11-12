"""
Milan Hydrotech website settings.

Every secret comes from the environment (the host's Environment page, or a local .env file that is
never committed). See env.example for the full list.
"""
import os
import sys
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path):
    """Local development: KEY=value lines from .env. Real environment variables win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.split(" #", 1)[0].strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


_load_dotenv(BASE_DIR / ".env")


def env(name, default=""):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    return env(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [x.strip() for x in env(name, default).split(",") if x.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("DJANGO_SECRET_KEY is not set (see env.example).")
    SECRET_KEY = "dev-only-not-secret"

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
if env("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(env("RENDER_EXTERNAL_HOSTNAME"))
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h not in ("localhost", "127.0.0.1")]

ADMIN_URL = env("ADMIN_URL", "admin/")
SITE_URL = env("SITE_URL", "").rstrip("/")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "website",
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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "website.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database: DATABASE_URL from Supabase (Connect -> Session pooler). Without it, SQLite for local work.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=int(env("DB_CONN_MAX_AGE", "600")),
        conn_health_checks=True,
    )
}
if DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
    DATABASES["default"].setdefault("OPTIONS", {})["sslmode"] = env("DB_SSLMODE", "require")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "sw"
TIME_ZONE = "Africa/Dar_es_Salaam"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Uploaded pictures: Supabase Storage (public bucket) through its S3-compatible API when the keys are
# set (Supabase -> Storage -> Settings -> S3 access keys). Otherwise the local media/ folder.
SUPABASE_PROJECT_REF = env("SUPABASE_PROJECT_REF")
SUPABASE_BUCKET = env("SUPABASE_BUCKET", "milan-hydrotech")
USE_SUPABASE_STORAGE = bool(
    SUPABASE_PROJECT_REF and env("SUPABASE_S3_ACCESS_KEY_ID") and env("SUPABASE_S3_SECRET_ACCESS_KEY")
)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage" if DEBUG
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
if USE_SUPABASE_STORAGE:
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "endpoint_url": f"https://{SUPABASE_PROJECT_REF}.supabase.co/storage/v1/s3",
            "region_name": env("SUPABASE_S3_REGION", "eu-central-1"),
            "access_key": env("SUPABASE_S3_ACCESS_KEY_ID"),
            "secret_key": env("SUPABASE_S3_SECRET_ACCESS_KEY"),
            "bucket_name": SUPABASE_BUCKET,
            # Public bucket: plain links that never expire.
            "custom_domain": f"{SUPABASE_PROJECT_REF}.supabase.co/storage/v1/object/public/{SUPABASE_BUCKET}",
            "querystring_auth": False,
            "file_overwrite": False,
            "default_acl": None,
            "object_parameters": {"CacheControl": "public, max-age=31536000"},
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Phone photos can be large; they are shrunk on save (website/images.py).
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

VIDEO_MAX_MB = int(env("VIDEO_MAX_MB", "50"))
# Keep YouTube's cover picture as our own (watermarked) poster. Off in tests: no network there.
FETCH_YOUTUBE_POSTERS = env_bool("FETCH_YOUTUBE_POSTERS", "test" not in sys.argv)
# Stamp missing watermarks in the background whenever the web server starts.
WATERMARK_ON_START = env_bool("WATERMARK_ON_START", True)

# Optional: an email to the office for every new request from the contact form.
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Milan Hydrotech <noreply@localhost>")
INQUIRY_NOTIFY_EMAIL = env("INQUIRY_NOTIFY_EMAIL")

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "0"))
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
