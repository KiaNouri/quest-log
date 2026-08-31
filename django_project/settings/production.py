from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Swap the staticfiles storage backend to WhiteNoise's compressed+hashed variant
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Security headers

# --- Proxy & Origins ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

CSRF_TRUSTED_ORIGINS = env.list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default=["https://yourdomain.com", "http://localhost:8001"],
)

# Detect if we are running in an actual HTTPS environment
IS_HTTPS = env.bool("DJANGO_IS_HTTPS", default=True)

# --- Cookies ---
# Keep False for http://localhost testing, True for real production
SESSION_COOKIE_SECURE = IS_HTTPS
CSRF_COOKIE_SECURE = IS_HTTPS

# --- HSTS ---
if IS_HTTPS:
    SECURE_HSTS_SECONDS = 60 * 60 * 24  # 1 day
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_HSTS_SECONDS = 0  # Disable HSTS locally

# --- Misc hardening ---
SECURE_CONTENT_TYPE_NOSNIFF = True

# --- Allauth ---
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https" if IS_HTTPS else "http"


# Google smtp email setup
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = f"Questlog <{EMAIL_HOST_USER}>"
