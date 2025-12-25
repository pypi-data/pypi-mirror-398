import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = os.path.abspath(os.path.join(BASE_DIR, "testproject"))

SECRET_KEY = "django-insecure-%am#r-wl5tx8vp6+l7o+6)3+1iipnex@otx_%dtov7gbnud5t0"

DEBUG = True

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # First party
    "itoutils.django",
    # First party's tests
    "testproject.testapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "testproject.testapp.nexus.middleware.AutoLoginMiddleware",
]

ROOT_URLCONF = "testproject.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Database

DATABASES = {
    "default": {
        "ATOMIC_REQUESTS": True,
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("PGDATABASE", "itoutils"),
        "HOST": os.getenv("PGHOST", "127.0.0.1"),
        "PORT": os.getenv("PGPORT", "5432"),
        "USER": os.getenv("PGUSER", "postgres"),
        "PASSWORD": os.getenv("PGPASSWORD", "password"),
    }
}

# Static files (CSS, JavaScript, Images)

STATIC_URL = "static/"

# Default primary key field type

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "itoutils.django.logging.DataDogJSONFormatter"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "json"},
        "null": {"class": "logging.NullHandler"},
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "INFO"},
    },
}


NEXUS_AUTO_LOGIN_KEY = {"k": "aTR4ZnR1WlpYYmphbFdtaXVlVjB3alljNjhrWXpfYSE", "kty": "oct"}
NEXUS_ALLOWED_REDIRECT_HOSTS = ["plateforme.inclusion.beta.gouv.fr", "plateforme.inclusion.gouv.fr"]

ASSERT_SNAPSHOT_QUERIES_EXTRA_PACKAGES_ALLOWLIST = [("django/db/models/query.py", "count")]
