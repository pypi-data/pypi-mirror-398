"""Django settings for tests."""

SECRET_KEY = "test-secret-key-not-for-production"

DEBUG = True

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_docxtpl",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

USE_TZ = True

# django-docxtpl settings
DOCXTPL_TEMPLATE_DIR = None
DOCXTPL_LIBREOFFICE_PATH = None
