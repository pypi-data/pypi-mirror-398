# ruff: noqa: PLR0913
"""
Provides a Vault client for storing and retrieving user service api keys.
"""

import logging

import hvac
import requests
from hvac.exceptions import InvalidPath
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from aixtools.utils import config

logger = logging.getLogger(__name__)


class VaultAuthError(Exception):
    """Exception raised for vault authentication errors."""


class VaultClient:
    """Vault client for storing and retrieving user service api keys."""

    def __init__(self):
        self.client = hvac.Client(url=config.VAULT_ADDRESS, token=config.VAULT_TOKEN)
        self._configure_retries(self.client)

        if not self.client.is_authenticated():
            raise VaultAuthError("Vault client authentication failed. Check vault_token.")

    def _configure_retries(self, client: hvac.Client) -> None:
        """Configure retries for the client."""
        session: requests.Session = client.session

        # retry for connection errors and transient Vault API errors
        # see https://python-hvac.org/en/stable/advanced_usage.html
        # see https://developer.hashicorp.com/vault/api-docs#http-status-codes
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.3,
            status_forcelist=(412, 500, 502, 503),
            allowed_methods=frozenset(["GET", "HEAD", "OPTIONS", "PUT", "POST", "DELETE", "LIST"]),
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

    def _get_secret_path(self, user_id: str, service_name: str | None = None) -> str:
        """Generate the vault secret path for a user and optionally a service."""
        if service_name:
            return f"{config.VAULT_PATH_PREFIX}/{config.VAULT_ENV}/{user_id}/{service_name}"
        return f"{config.VAULT_PATH_PREFIX}/{config.VAULT_ENV}/{user_id}"

    def store_user_service_api_key(self, *, user_id: str, service_name: str, user_api_key: str):
        """
        Store user's service api key in the Vault at the specified vault mount
        point, where the path is <path_prefix>/<env>/<user_id>/<service_name>.

        This is a convenience method for storing a single API key.
        For storing multiple secrets, use store_user_service_secret().
        """
        secret_dict = {"user-api-key": user_api_key}
        self.store_user_service_secret(user_id=user_id, service_name=service_name, secret_data=secret_dict)

    def read_user_service_api_key(self, *, user_id: str, service_name: str) -> str | None:
        """
        Read user's service api key in from vault at the specified mount point,
        where the path is <path_prefix>/<env>/<user_id>/<service_name>.

        This is a convenience method for reading a single API key.
        For reading multiple secrets, use read_user_service_secret().
        """
        secret_data = self.read_user_service_secret(user_id=user_id, service_name=service_name)
        if secret_data is None:
            return None
        return secret_data.get("user-api-key")

    def store_user_service_secret(self, *, user_id: str, service_name: str, secret_data: dict[str, str]):
        """
        Store complete user service secret with multiple key-value pairs in the Vault
        at the specified vault mount point, where the path is <path_prefix>/<env>/<user_id>/<service_name>.
        """
        secret_path = None
        try:
            secret_path = self._get_secret_path(user_id, service_name)
            logger.info("Writing complete secret to path %s", secret_path)
            self.client.secrets.kv.v2.create_or_update_secret(
                secret_path, secret=secret_data, mount_point=config.VAULT_MOUNT_POINT
            )

            logger.info("Complete secret written to path %s", secret_path)
        except Exception as e:
            logger.error("Failed to write complete secret to path %s: %s", secret_path, str(e))
            raise VaultAuthError(e) from e

    def read_user_service_secret(self, *, user_id: str, service_name: str) -> dict[str, str] | None:
        """
        Read complete user service secret from vault at the specified mount point,
        where the path is <path_prefix>/<env>/<user_id>/<service_name>.
        Returns all key-value pairs in the secret or None if the secret doesn't exist.
        """
        secret_path = None

        try:
            secret_path = self._get_secret_path(user_id, service_name)
            logger.info("Reading complete secret from path %s", secret_path)
            response = self.client.secrets.kv.v2.read_secret_version(
                secret_path, mount_point=config.VAULT_MOUNT_POINT, raise_on_deleted_version=True
            )
            secret_data = response["data"]["data"]
            logger.info("Complete secret read from path %s", secret_path)
            return secret_data
        except InvalidPath:
            # Secret path does not exist
            logger.warning("Secret path does not exist %s", secret_path)
            return None
        except Exception as e:
            logger.error("Failed to read complete secret from path %s: %s", secret_path, str(e))
            raise VaultAuthError(e) from e

    def list_user_secret_keys(self, *, user_id: str) -> list[str]:
        """
        List all secret keys (service names) for a user, optionally filtered by service name.

        Args:
            user_id: The user ID to list secrets for
            service_name: Optional service name to filter results. If provided, returns only this service if it exists.

        Returns:
            List of service names (secret keys) for the user. Empty list if no secrets exist.
        """
        try:
            # List all services for user
            user_path = self._get_secret_path(user_id)
            logger.info("Listing secret keys for user at path %s", user_path)

            response = self.client.secrets.kv.v2.list_secrets(path=user_path, mount_point=config.VAULT_MOUNT_POINT)

            if response and "data" in response and "keys" in response["data"]:
                secret_keys = response["data"]["keys"]
                # Remove trailing slashes from directory names if any
                secret_keys = [key.rstrip("/") for key in secret_keys]
                logger.info("Found %d secret keys for user %s", len(secret_keys), user_id)
                return secret_keys
            logger.info("No secret keys found for user %s", user_id)
            return []

        except InvalidPath:
            # User path does not exist
            logger.warning("User path does not exist for user %s", user_id)
            return []
        except Exception as e:
            logger.error("Failed to list secret keys for user %s: %s", user_id, str(e))
            raise VaultAuthError(e) from e
