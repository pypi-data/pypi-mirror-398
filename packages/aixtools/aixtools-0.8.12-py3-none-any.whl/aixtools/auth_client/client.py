"""The module that provides an Azure AD token provider taking care of authentication, token caching and refreshing."""

import enum
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import msal

from aixtools.auth_client.msal_client import PublicClientApplicationWithCustomRedirectUri
from aixtools.utils import config


class AuthClientErrorCode(str, enum.Enum):
    """Enum for error codes returned by the AuthTokenError exception."""

    INTERACTIVE_LOGIN_ERROR = "Interactive login error"


class AuthClientError(Exception):
    """Exception raised for authentication token errors."""

    def __init__(self, error_code: AuthClientErrorCode, msg: str = None):
        self.error_code = error_code
        error_msg = error_code.value if msg is None else msg
        super().__init__(error_msg)


@dataclass
class AuthToken:
    """Class representing an Azure AD token."""

    expires_on: datetime
    access_token: str
    refresh_token: str = None


class AuthClient:
    """
    Wrapper around MSAL PublicClientApplication that supports persistent local caching
    of Azure AD tokens using SerializableTokenCache.

    It requires SSO app definition on Azure AD with a Mobile / Desktop platform
    and the following configuration parameters in the environment config:
      APP_TENANT_ID=<tenant id>
      APP_DEFAULT_SCOPE=<target API scope>
      APP_CLIENT_ID=<client id>
      AUTH_REDIRECT_URI="http://localhost:4444/mcp-direct"
    """

    EXPIRY_OFFSET_MINS = 60
    AUTHORITY = f"https://login.microsoftonline.com/{config.APP_TENANT_ID}"
    AUTH_CLIENT_ID = config.APP_CLIENT_ID
    APP_DEFAULT_SCOPE = config.APP_DEFAULT_SCOPE
    CACHE_PATH = os.path.expanduser("~/.azure_token_cache.json")

    _public_msal_client = None
    _cache = None

    @classmethod
    def create(cls):
        """Create an instance of the AuthClient class."""
        if cls._cache is None:
            cls._cache = msal.SerializableTokenCache()
            if os.path.exists(cls.CACHE_PATH):
                with open(cls.CACHE_PATH, "r", encoding="utf-8") as f:
                    cls._cache.deserialize(f.read())

        if cls._public_msal_client is None:
            cls._public_msal_client = PublicClientApplicationWithCustomRedirectUri(
                client_id=cls.AUTH_CLIENT_ID,
                authority=cls.AUTHORITY,
                token_cache=cls._cache,
            )

        return cls()

    @classmethod
    def _save_cache(cls):
        if cls._cache and cls._cache.has_state_changed:
            with open(cls.CACHE_PATH, "w", encoding="utf-8") as f:
                f.write(cls._cache.serialize())

    def acquire_token_silent(self, force_refresh: bool = False) -> AuthToken | None:
        """
        Attempt to get a token silently from cache or via refresh token.
        If force_refresh=True, forces MSAL to refresh even if a valid token exists.
        """
        accounts = self._public_msal_client.get_accounts()
        if not accounts:
            return None

        scopes = [self.APP_DEFAULT_SCOPE]
        result = self._public_msal_client.acquire_token_silent(
            scopes=scopes,
            account=accounts[0],
            force_refresh=force_refresh,
        )
        self._save_cache()

        if result and "access_token" in result:
            return self.get_auth_token(result)
        return None

    def login_with_interactive_flow(self) -> AuthToken:
        """Perform interactive login and cache the tokens."""
        scopes = [self.APP_DEFAULT_SCOPE]
        result = self._public_msal_client.acquire_token_interactive(scopes=scopes)
        self._save_cache()

        if "access_token" in result:
            return self.get_auth_token(result)

        raise AuthClientError(AuthClientErrorCode.INTERACTIVE_LOGIN_ERROR, self.get_error_msg(result))

    def get_auth_token(self, result: dict) -> AuthToken:
        """Return an AuthToken object from an MSAL authentication result."""
        exp = datetime.now(timezone.utc) + timedelta(seconds=result["expires_in"])
        return AuthToken(exp, result["access_token"], result.get("refresh_token"))

    def get_error_msg(self, result: dict) -> str:
        """Extract an error message from an MSAL result dict."""
        return (
            f"Error: {result.get('error', '')}, Description: {result.get('error_description', '')}, "
            f"Codes: {result.get('error_codes', '')}"
        )


class ClientAccessTokenProvider:  # pylint: disable=too-few-public-methods
    """
    Client access token manager — caches Azure AD tokens persistently and refreshes silently.
    """

    def __init__(self):
        self._auth_client = AuthClient.create()

    def get_access_token(self) -> str:
        """Get an access token from the cache or refresh it if needed."""
        now = datetime.now(timezone.utc)
        token = self._auth_client.acquire_token_silent()

        if token:
            # outside expiry window
            if token.expires_on - now > timedelta(minutes=AuthClient.EXPIRY_OFFSET_MINS):
                return token.access_token

            # within the expiry window, force a refresh
            refreshed = self._auth_client.acquire_token_silent(force_refresh=True)
            if refreshed:
                return refreshed.access_token

        # default if silent token refresh fails or no token captured previously.
        return self._auth_client.login_with_interactive_flow().access_token
