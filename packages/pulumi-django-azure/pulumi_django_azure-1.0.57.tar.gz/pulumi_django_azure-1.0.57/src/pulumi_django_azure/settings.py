import environ
from azure.keyvault.secrets import SecretClient

from .azure_helper import AZURE_CREDENTIAL, LOCAL_IP_ADDRESSES, get_db_password, get_subscription

env = environ.Env()

SECRET_KEY = env("DJANGO_SECRET_KEY", default=None)

IS_AZURE_ENVIRONMENT = env("IS_AZURE_ENVIRONMENT", default=False)

# Some generic stuff we only need if we're running in Azure.
# Most of the other stuff will check for the explicit variable we need.
if IS_AZURE_ENVIRONMENT:
    # Detect HTTPS behind AppService
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # Azure context
    AZURE_SUBSCRIPTION = get_subscription()
    AZURE_TENANT_ID = AZURE_SUBSCRIPTION.tenant_id
    AZURE_SUBSCRIPTION_ID = AZURE_SUBSCRIPTION.subscription_id

# Health check path
HEALTH_CHECK_PATH = env("HEALTH_CHECK_PATH", default="/health")

ALLOWED_HOSTS: list = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# WEBSITE_HOSTNAME contains the Azure domain name
if website_hostname := env("WEBSITE_HOSTNAME", default=None):
    ALLOWED_HOSTS.append(website_hostname)

# Add the local IP addresses of the machine for health checks
ALLOWED_HOSTS.extend(LOCAL_IP_ADDRESSES)

# Azure Key Vault
if azure_key_vault := env("AZURE_KEY_VAULT", default=None):
    AZURE_KEY_VAULT_URI = f"https://{azure_key_vault}.vault.azure.net"
    AZURE_KEY_VAULT_CLIENT = SecretClient(vault_url=AZURE_KEY_VAULT_URI, credential=AZURE_CREDENTIAL)

# Allow CSRF cookies to be sent from our domains
# CSRF_TRUSTED_ORIGINS = ["https://" + host for host in ALLOWED_HOSTS]
if azure_storage_account_name := env("AZURE_STORAGE_ACCOUNT_NAME", default=None):
    AZURE_ACCOUNT_NAME = azure_storage_account_name
    AZURE_TOKEN_CREDENTIAL = AZURE_CREDENTIAL


# CDN domain - shared for all storages
AZURE_CUSTOM_DOMAIN = env("CDN_HOST", default=None)

# Storage configuration
STORAGES = {}
if container_media := env("AZURE_STORAGE_CONTAINER_MEDIA", default=None):
    STORAGES["default"] = {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "azure_container": container_media,
            "overwrite_files": False,
        },
    }

    if AZURE_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AZURE_CUSTOM_DOMAIN}/{container_media}/"

if container_staticfiles := env("AZURE_STORAGE_CONTAINER_STATICFILES", default=None):
    STORAGES["staticfiles"] = {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "azure_container": container_staticfiles,
        },
    }
    COLLECTFASTA_STRATEGY = "collectfasta.strategies.azure.AzureBlobStrategy"

    if AZURE_CUSTOM_DOMAIN:
        STATIC_URL = f"https://{AZURE_CUSTOM_DOMAIN}/{container_staticfiles}/"


# This setting enables password rotation in the health check middleware
if IS_AZURE_ENVIRONMENT:
    AZURE_DB_PASSWORD = True
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "HOST": env("DB_HOST"),
            "PASSWORD": get_db_password(),
            "PORT": "5432",
            "OPTIONS": {
                "sslmode": "require",
            },
            # Make connections persistent
            "CONN_MAX_AGE": None,
            # To enable health checks, add the following:
            # "CONN_HEALTH_CHECKS": True,
        }
    }

# Email
EMAIL_BACKEND = "django_azure_communication_email.EmailBackend"
AZURE_COMMUNICATION_ENDPOINT = env("AZURE_COMMUNICATION_SERVICE_ENDPOINT", default=None)
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default=None)


# Logging
if IS_AZURE_ENVIRONMENT:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "timestamped": {
                "format": "{asctime} {levelname} [p:{process:d}] [t:{thread:d}] {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "timestamped",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": True,
            },
            "pulumi_django_azure": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": True,
            },
        },
    }

# Redis, if enabled
REDIS_SIDECAR = env("REDIS_SIDECAR", default=False)

if REDIS_SIDECAR:
    # This will prevent the website from failing if Redis is not available.
    DJANGO_REDIS_IGNORE_EXCEPTIONS = True
    DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://localhost:6379/0",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "PARSER_CLASS": "redis.connection._HiredisParser",
            },
        },
    }


# Django tasks
DJANGO_TASKS = env("DJANGO_TASKS", default=False)
if DJANGO_TASKS and REDIS_SIDECAR:
    RQ_QUEUES = {
        "default": {
            "USE_REDIS_CACHE": "default",
            "QUEUES": ["default"],
        }
    }

    TASKS = {
        "default": {
            "BACKEND": "django_tasks.backends.rq.RQBackend",
        }
    }


def patch_django_settings_for_azure(INSTALLED_APPS: list, MIDDLEWARE: list, TEMPLATES: list):
    """
    Patch the Django settings to add the required apps and middleware.

    :param INSTALLED_APPS: Reference to INSTALLED_APPS setting.
    :param MIDDLEWARE: Reference to MIDDLEWARE setting.
    :param TEMPLATES: Reference to TEMPLATES setting.
    """
    # Insert collectfasta at the correct position
    INSTALLED_APPS.insert(INSTALLED_APPS.index("django.contrib.staticfiles"), "collectfasta")

    # Add the required apps
    INSTALLED_APPS.append("pulumi_django_azure")
    INSTALLED_APPS.append("django_rq")
    INSTALLED_APPS.append("django_tasks")

    # Add the middleware
    MIDDLEWARE.append("pulumi_django_azure.middleware.HealthCheckMiddleware")

    # Add the template context processors
    TEMPLATES[0]["OPTIONS"]["context_processors"].append("pulumi_django_azure.context_processors.add_build_info")
