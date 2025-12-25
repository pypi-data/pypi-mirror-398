import base64
import json
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from subprocess import check_output

from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.resource.subscriptions.models import Subscription

logger = logging.getLogger("pulumi_django_azure.azure_helper")


# Azure credentials
AZURE_CREDENTIAL = DefaultAzureCredential()

# Buffer for token expiration (5 minutes)
TOKEN_EXPIRATION_BUFFER = 300

# Get the local IP addresses of the machine (only when runnig on Azure)
if os.environ.get("IS_AZURE_ENVIRONMENT"):
    LOCAL_IP_ADDRESSES = check_output(["hostname", "--all-ip-addresses"]).decode("utf-8").strip().split(" ")
else:
    LOCAL_IP_ADDRESSES = []


class TokenType(Enum):
    DATABASE = "https://ossrdbms-aad.database.windows.net/.default"
    REDIS = "https://redis.azure.com/.default"


def _get_azure_token(type: TokenType) -> str:
    """
    Get a valid token for the given scope.
    """
    global AZURE_CREDENTIAL

    token = AZURE_CREDENTIAL.get_token(type.value)

    if token.expires_on < time.time() + TOKEN_EXPIRATION_BUFFER:
        # We received an expired or nearly expired token from the API. Force a new token by creating a new instance of the credential.
        logger.debug(
            "Received an expired or nearly expired %s token (current time: %s, token expiration: %s)."
            "Creating a new instance of the credential.",
            type.name,
            time.time(),
            token.expires_on,
        )

        AZURE_CREDENTIAL = DefaultAzureCredential()
        token = AZURE_CREDENTIAL.get_token(type.value)

        logger.debug("New %s token (try 2): %s", type.name, token)

    return token.token


def get_db_password() -> str:
    """
    Get a valid password for the database.
    """
    return _get_azure_token(TokenType.DATABASE)


@dataclass
class RedisCredentials:
    username: str
    password: str


def get_redis_credentials() -> RedisCredentials:
    """
    Get valid credentials for the Redis cache.
    """
    token = _get_azure_token(TokenType.REDIS)

    return RedisCredentials(_extract_username_from_token(token), token)


def get_subscription() -> Subscription:
    """
    Get the subscription for the current user.
    """
    subscription_client = SubscriptionClient(AZURE_CREDENTIAL)
    subscriptions = list(subscription_client.subscriptions.list())
    return subscriptions[0]


def _extract_username_from_token(token: str) -> str:
    """
    Extract the username from the JSON Web Token (JWT) token.
    """
    parts = token.split(".")
    base64_str = parts[1]

    if len(base64_str) % 4 == 2:
        base64_str += "=="
    elif len(base64_str) % 4 == 3:
        base64_str += "="

    json_bytes = base64.b64decode(base64_str)
    json_str = json_bytes.decode("utf-8")
    jwt = json.loads(json_str)

    return jwt["oid"]
