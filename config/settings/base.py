"""
Django settings for Metecho project.

Generated by 'django-admin startproject' using Django 1.11.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

from ipaddress import IPv4Network
from os import environ
from pathlib import Path
from typing import List

import dj_database_url
import sentry_sdk
from django.core.exceptions import ImproperlyConfigured
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.rq import RqIntegration

BOOLS = ("True", "true", "T", "t", "1", 1)


def boolish(val: str) -> bool:
    return val in BOOLS


def ipv4_networks(val: str) -> List[IPv4Network]:
    return [IPv4Network(s.strip()) for s in val.split(",")]


class NoDefaultValue:
    pass


def env(name, default=NoDefaultValue, type_=str):
    """
    Get a configuration value from the environment.

    Arguments
    ---------
    name : str
        The name of the environment variable to pull from for this
        setting.
    default : any
        A default value of the return type in case the intended
        environment variable is not set. If this argument is not passed,
        the environment variable is considered to be required, and
        ``ImproperlyConfigured`` may be raised.
    type_ : callable
        A callable that takes a string and returns a value of the return
        type.

    Returns
    -------
    any
        A value of the type returned by ``type_``.

    Raises
    ------
    ImproperlyConfigured
        If there is no ``default``, and the environment variable is not
        set.
    """
    try:
        val = environ[name]
    except KeyError:
        if default == NoDefaultValue:
            raise ImproperlyConfigured(f"Missing environment variable: {name}.")
        val = default
    if val is not None:
        val = type_(val)
    return val


# Build paths inside the project like this: BASE_DIR.joinpath(...)
PROJECT_ROOT = Path(__file__).absolute().parent.parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("DJANGO_SECRET_KEY")
HASHID_FIELD_SALT = env("DJANGO_HASHID_SALT")
HASHID_FIELD_ALLOW_INT_LOOKUP = True
HASHID_FIELD_ENABLE_HASHID_OBJECT = False  # Use plain strings
DB_ENCRYPTION_KEY = env("DB_ENCRYPTION_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DJANGO_DEBUG", default=False, type_=boolish)

MODE = env("DJANGO_MODE", default="dev" if DEBUG else "prod")

if MODE == "dev":
    environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

API_DOCS_ENABLED = env("API_DOCS_ENABLED", default=DEBUG, type_=boolish)

ALLOWED_HOSTS = [
    "127.0.0.1",
    "127.0.0.1:8000",
    "127.0.0.1:8080",
    "0.0.0.0",
    "0.0.0.0:8000",
    "0.0.0.0:8080",
    "localhost",
    "localhost:8000",
    "localhost:8080",
] + [
    el.strip()
    for el in env("DJANGO_ALLOWED_HOSTS", default="", type_=lambda x: x.split(","))
    if el.strip()
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.sites",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "channels",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django_rq",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "anymail",
    "metecho",
    "metecho.oauth2.github",
    "metecho.oauth2.salesforce",
    "metecho.api",
    "metecho.adminapi.apps.AdminapiConfig",
    "django_js_reverse",
    "parler",
    "drf_spectacular",
]

MIDDLEWARE = [
    "metecho.logging_middleware.LoggingMiddleware",
    "sfdo_template_helpers.admin.middleware.AdminRestrictMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "NAME": "django",
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # This gets overridden in settings.production:
        "DIRS": [str(PROJECT_ROOT / "dist"), str(PROJECT_ROOT / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # `allauth` needs this from django:
                "django.template.context_processors.request",
                # custom
                "metecho.context_processors.env",
            ]
        },
    },
    {
        "NAME": "email",
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(PROJECT_ROOT / "email_templates")],
        "APP_DIRS": False,
        "OPTIONS": {"autoescape": False},
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ASGI_APPLICATION = "metecho.routing.application"

SITE_ID = 1

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {"default": dj_database_url.config(default="postgres:///metecho")}

# Custom User model:
AUTH_USER_MODEL = "api.User"


# URL configuration:
ROOT_URLCONF = "metecho.urls"

ADMIN_AREA_PREFIX = env("DJANGO_ADMIN_URL", default="admin")
RESTRICTED_PREFIXES = env(
    "RESTRICTED_PREFIXES", default=(), type_=lambda x: x.split(",") if x else ()
)
UNRESTRICTED_PREFIXES = ["api/hook"]

ADMIN_API_ALLOWED_SUBNETS = env(
    "ADMIN_API_ALLOWED_SUBNETS",
    default="127.0.0.1/32,172.16.0.0/12",
    type_=ipv4_networks,
)

# GitHub settings:
GITHUB_HOOK_SECRET = env(
    "GITHUB_HOOK_SECRET", default="", type_=lambda x: bytes(x, encoding="utf-8")
)
# The username of the user that GitHub webhook actions should authenticate as:
GITHUB_USER_NAME = env("GITHUB_USER_NAME", default="GitHub user")
GITHUB_APP_ID = env("GITHUB_APP_ID", default=0, type_=int)
# Ugly hack to fix https://github.com/moby/moby/issues/12997
DOCKER_GITHUB_APP_KEY = env("DOCKER_GITHUB_APP_KEY", default="").replace("\\n", "\n")
GITHUB_APP_KEY = bytes(env("GITHUB_APP_KEY", default=DOCKER_GITHUB_APP_KEY), "utf-8")


# Salesforce Devhub settings:
DEVHUB_USERNAME = env("DEVHUB_USERNAME", default=None)

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {"NAME": ("django.contrib.auth.password_validation.MinimumLengthValidator")},
    {"NAME": ("django.contrib.auth.password_validation.CommonPasswordValidator")},
    {"NAME": ("django.contrib.auth.password_validation.NumericPasswordValidator")},
]

LOGIN_REDIRECT_URL = "/"

# Use HTTPS:
SECURE_PROXY_SSL_HEADER = env(
    "SECURE_PROXY_SSL_HEADER",
    default="HTTP_X_FORWARDED_PROTO:https",
    type_=(lambda v: tuple(v.split(":", 1)) if (v is not None and ":" in v) else None),
)
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", default=True, type_=boolish)
SESSION_COOKIE_SECURE = env(
    "SESSION_COOKIE_SECURE", default=SECURE_SSL_REDIRECT, type_=boolish
)
# "Lax" is required for GitHub login redirects to work properly
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_SECURE = env(
    "CSRF_COOKIE_SECURE", default=SECURE_SSL_REDIRECT, type_=boolish
)
SECURE_HSTS_SECONDS = env(
    "SECURE_HSTS_SECONDS", default=3600 if SECURE_SSL_REDIRECT else 0, type_=int
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, type_=boolish
)
SECURE_HSTS_PRELOAD = env("SECURE_HSTS_PRELOAD", default=False, type_=boolish)


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Email settings
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@metecho.org")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    ANYMAIL = {
        "MAILGUN_API_KEY": env("MAILGUN_API_KEY", default=""),
        "MAILGUN_SENDER_DOMAIN": env("MAILGUN_DOMAIN", default=None),
    }

DAYS_BEFORE_ORG_EXPIRY_TO_ALERT = env(
    "DAYS_BEFORE_ORG_EXPIRY_TO_ALERT", default=3, type_=int
)
ORG_RECHECK_MINUTES = env("ORG_RECHECK_MINUTES", default=5, type_=int)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

# This gets overridden in settings.production:
STATICFILES_DIRS = [
    str(PROJECT_ROOT / "static"),
    str(PROJECT_ROOT / "dist"),
    str(PROJECT_ROOT / "locales"),
]
STATIC_URL = "/static/"
STATIC_ROOT = str(PROJECT_ROOT / "staticfiles")


# Per the docs:
# > Absolute path to a directory of files which will be served at the root of
# > your application (ignored if not set).
# Set this way, this lets us serve the styleguide relative to itself. If you
# access the styleguide at `/styleguide/`, then the relative path asset
# requests it makes will land in WhiteNoise, and get served appropriately,
# given how the static directory is structured (with an internal `styleguide`
# directory).
# This comes at a cost, though:
# > you won't benefit from cache versioning
# WHITENOISE_ROOT = PROJECT_ROOT.joinpath(static_dir_root)

GITHUB_CLIENT_ID = env("GITHUB_CLIENT_ID", default=None)
GITHUB_CLIENT_SECRET = env("GITHUB_CLIENT_SECRET", default=None)

# If GITHUB_OAUTH_PRIVATE_REPO env var is True, oauth scope should include
# private repositories. Otherwise, the scope will only be for public repos.
GITHUB_OAUTH_PRIVATE_REPO = env(
    "GITHUB_OAUTH_PRIVATE_REPO", default=False, type_=boolish
)
GITHUB_OAUTH_SCOPES = ["read:user", "user:email"]
GITHUB_OAUTH_SCOPES.append("repo" if GITHUB_OAUTH_PRIVATE_REPO else "public_repo")

# SF client settings:
SFDX_CLIENT_CALLBACK_URL = env(
    "SFDX_CLIENT_CALLBACK_URL", default=env("SF_CALLBACK_URL", default=None)
)
SFDX_CLIENT_ID = env("SFDX_CLIENT_ID", default=env("SF_CLIENT_ID", default=None))
SFDX_CLIENT_SECRET = env(
    "SFDX_CLIENT_SECRET", default=env("SF_CLIENT_SECRET", default=None)
)
SFDX_SIGNUP_INSTANCE = env(
    "SFDX_SIGNUP_INSTANCE", default=env("SF_SIGNUP_INSTANCE", default=None)
)
# Ugly hack to fix https://github.com/moby/moby/issues/12997
DOCKER_SFDX_HUB_KEY = env("DOCKER_SFDX_HUB_KEY", default="").replace("\\n", "\n")
SFDX_HUB_KEY = env(
    "SFDX_HUB_KEY", default=env("SF_CLIENT_KEY", default=DOCKER_SFDX_HUB_KEY)
)

if not SFDX_CLIENT_SECRET:
    raise ImproperlyConfigured("Missing environment variable: SFDX_CLIENT_SECRET.")
if not SFDX_CLIENT_CALLBACK_URL:
    raise ImproperlyConfigured(
        "Missing environment variable: SFDX_CLIENT_CALLBACK_URL."
    )
if not SFDX_CLIENT_ID:
    raise ImproperlyConfigured("Missing environment variable: SFDX_CLIENT_ID.")
if not SFDX_HUB_KEY:
    raise ImproperlyConfigured("Missing environment variable: SFDX_HUB_KEY.")

# CCI expects these env vars to be set to refresh org oauth tokens
environ["SFDX_CLIENT_ID"] = SFDX_CLIENT_ID
environ["SFDX_HUB_KEY"] = SFDX_HUB_KEY

SOCIALACCOUNT_PROVIDERS = {
    "github": {
        "SCOPE": GITHUB_OAUTH_SCOPES,
        "APP": {"client_id": GITHUB_CLIENT_ID, "secret": GITHUB_CLIENT_SECRET},
    },
    "salesforce": {
        "SCOPE": ["web", "full", "refresh_token"],
        "APP": {"client_id": SFDX_CLIENT_ID, "secret": SFDX_CLIENT_SECRET},
    },
}
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = False
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_ADAPTER = "metecho.oauth2.adapter.CustomSocialAccountAdapter"
# Tokens are required to call the GitHub API on behalf of users
SOCIALACCOUNT_STORE_TOKENS = True

JS_REVERSE_JS_VAR_NAME = "api_urls"
JS_REVERSE_EXCLUDE_NAMESPACES = ["admin", "admin_rest"]


# Redis configuration:

REDIS_LOCATION = "{}/0".format(
    env("REDIS_TLS_URL", default=env("REDIS_URL", default="redis://localhost:6379"))
)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_LOCATION,
        "OPTIONS": {},
    }
}
RQ_QUEUES = {
    "default": {
        "URL": REDIS_LOCATION,
        "DEFAULT_TIMEOUT": env("REDIS_JOB_TIMEOUT", type_=int, default=3600),
        "DEFAULT_RESULT_TTL": 720,
    }
}
RQ = {"WORKER_CLASS": "metecho.rq_worker.ConnectionClosingWorker"}
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_LOCATION]},
    }
}

# Rest Framework settings:
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# API docs settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Metecho",
    "DESCRIPTION": "2019–2021, Salesforce.org",
    "VERSION": "0.1.0",
    "ENUM_NAME_OVERRIDES": {
        "TaskStatusEnum": "metecho.api.models.TaskStatus.choices",
        "EpicStatusEnum": "metecho.api.models.EpicStatus.choices",
        "ReviewStatusEnum": "metecho.api.models.TaskReviewStatus.choices",
    },
    "SERVE_INCLUDE_SCHEMA": False,  # Don't include schema view in docs
}


# Logging

LOG_REQUESTS = True
LOG_REQUEST_ID_HEADER = "HTTP_X_REQUEST_ID"
GENERATE_REQUEST_ID_IF_NOT_IN_HEADER = True
REQUEST_ID_RESPONSE_HEADER = "X-Request-ID"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "filters": {
        "request_id": {"()": "log_request_id.filters.RequestIDFilter"},
        "job_id": {"()": "metecho.logfmt.JobIDFilter"},
    },
    "formatters": {
        "logfmt": {
            "()": "metecho.logfmt.LogfmtFormatter",
            "format": (
                "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d "
                "%(message)s"
            ),
        },
        "simple": {
            "()": "django.utils.log.ServerFormatter",
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console_error": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "simple",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "logfmt",
        },
        "rq_console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "filters": ["job_id"],
            "formatter": "logfmt",
        },
    },
    "loggers": {
        "django.db.backends": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "django.server": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {
            "handlers": ["console_error"],
            "level": "INFO",
            "propagate": False,
        },
        "rq.worker": {"handlers": ["rq_console"], "level": "DEBUG"},
        "metecho.oauth2": {"handlers": ["console"], "level": "DEBUG"},
        "metecho.logging_middleware": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

API_PAGE_SIZE = env("API_PAGE_SIZE", type_=int, default=50)

GITHUB_ISSUE_LIMIT = env("GITHUB_ISSUE_LIMIT", type_=int, default=1000)

# New feature branch prefix:
BRANCH_PREFIX = env("BRANCH_PREFIX", default=None)

ENABLE_WALKTHROUGHS = env("ENABLE_WALKTHROUGHS", default=True, type_=boolish)

# Sentry
SENTRY_DSN = env("SENTRY_DSN", default="")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), RedisIntegration(), RqIntegration()],
    )
