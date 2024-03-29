"""
Django settings for ubccoursemonitor project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import datetime
import os

import django_heroku

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("UCM_DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("UCM_DJANGO_DEBUG_VALUE") != "False"

DEBUG_PROPAGATE_EXCEPTIONS = True

ADMINS = [
    (os.environ.get("UCM_DJANGO_ADMIN_NAME"), os.environ.get("UCM_DJANGO_ADMIN_EMAIL"))
]

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "ubccoursemonitor.herokuapp.com",
    "ubccoursemonitor.email",
]

if os.environ.get("UCM_DJANGO_USE_SSL", "False") == "True":
    SECURE_SSL_REDIRECT = True

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat",
    "crispy_forms",
    "courses",
    "users",
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

ROOT_URLCONF = "ubccoursemonitor.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "ubccoursemonitor.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/Vancouver"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

if (os.environ.get("UCM_DJANGO_DEBUG_VALUE") != "True") and (
    os.environ.get("UCM_DJANGO_DEBUG_VALUE") is not None
):
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"


LOGIN_REDIRECT_URL = "courses-home"
LOGIN_URL = "login"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = os.environ.get("UCM_SENDGRID_API_KEY")
DEFAULT_FROM_EMAIL = "accounts@ubccoursemonitor.email"
SERVER_EMAIL = "server@ubccoursemonitor.email"
EMAIL_NOTIFIER_ADDRESS = "notifier@ubccoursemonitor.email"

# Celery
CELERY_BROKER_URL = os.environ.get("REDIS_URL")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CRISPY_TEMPLATE_PACK = "bootstrap4"

if (os.environ.get("UCM_DJANGO_DEBUG_VALUE") != "True") and (
    os.environ.get("UCM_DJANGO_DEBUG_VALUE") is not None
):
    django_heroku.settings(locals())

OPEN_COURSE_DELAY = datetime.timedelta(hours=24)
POLL_FREQUENCY = int(os.environ.get("UCM_POLL_FREQUENCY", "1"))
MAX_NON_PREMIUM_SECTIONS = 2

NON_PREMIUM_NOTIFICATIONS = (
    True if os.environ.get("UCM_DJANGO_NOTIFY_ALL") == "True" else False
)
