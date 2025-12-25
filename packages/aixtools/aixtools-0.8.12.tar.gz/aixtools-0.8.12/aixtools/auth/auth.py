"""
Module that manages OAuth2 functions for authentication
"""

import enum

import jwt
from fastmcp.server.auth.auth import AuthProvider
from jwt import ExpiredSignatureError, InvalidAudienceError, InvalidIssuerError, InvalidSignatureError, PyJWKClient
from mcp.server.auth.middleware.auth_context import AuthContextMiddleware
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser, BearerAuthBackend
from mcp.server.auth.provider import (
    AccessToken,
)
from starlette.authentication import AuthenticationError
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from aixtools.auth.user_store import UserStore
from aixtools.context import HTTP_AUTH_CONTEXT_USER, HTTP_USER_ID_HEADER, user_id_var
from aixtools.logging.logging_config import get_logger
from aixtools.utils import config

logger = get_logger(__name__)
TEST_CLIENT = "test-client"

REALM = "Navari"


class AuthTokenErrorCode(str, enum.Enum):
    """Enum for error codes returned by the AuthTokenError exception."""

    TOKEN_EXPIRED = "Token expired"
    INVALID_AUDIENCE = "Token not for expected audience"
    INVALID_ISSUER = "Token not for expected issuer"
    INVALID_SIGNATURE = "Token signature error"
    INVALID_TOKEN = "Invalid token"
    JWT_ERROR = "Generic JWT error"
    MISSING_GROUPS_ERROR = "Missing authorized groups"
    INVALID_TOKEN_SCOPE = "Token scope does not match configured scope"


class AuthTokenError(AuthenticationError):
    """Exception raised for authentication token errors."""

    def __init__(self, error_code: AuthTokenErrorCode, msg: str = None):
        self.error_code = error_code
        error_msg = error_code.value if msg is None else msg
        super().__init__(error_msg)

    def to_http_response(self, required_scope: str | None = None) -> JSONResponse:
        """
        Returns a JSONResponse with status 401 for all AuthTokenErrorCodes,
        including JSON body and WWW-Authenticate header.
        """
        status_code = 401
        www_error = (
            "insufficient_scope" if self.error_code == AuthTokenErrorCode.INVALID_TOKEN_SCOPE else "invalid_token"
        )

        header_value = f'Bearer realm="{REALM}", error="{www_error}", error_description="{self.error_code.value}"'
        if self.error_code == AuthTokenErrorCode.INVALID_TOKEN_SCOPE and required_scope:
            header_value += f', scope="{required_scope}"'

        body = {
            "error": {
                "code": self.error_code.name,
                "message": self.error_code.value,
            }
        }
        if self.error_code == AuthTokenErrorCode.INVALID_TOKEN_SCOPE and required_scope:
            body["error"]["required_scope"] = required_scope

        return JSONResponse(
            content=body,
            status_code=status_code,
            headers={"WWW-Authenticate": header_value},
        )


class AccessTokenVerifier:  # pylint: disable=too-few-public-methods
    """
    Verifies Microsoft SSO JWT token against the configured Tenant ID, Audience, API ID and Issuer URL.
    """

    def __init__(self):
        tenant_id = config.APP_TENANT_ID
        self.api_id = config.APP_API_ID
        self.app_scope = config.APP_DEFAULT_SCOPE
        self.issuer_url = f"https://sts.windows.net/{tenant_id}/"
        self.authorized_groups = set(config.APP_AUTHORIZED_GROUPS.split(",")) if config.APP_AUTHORIZED_GROUPS else set()
        if not self.authorized_groups:
            logger.warning("No authorized groups configured")

        # Azure AD endpoints
        jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        self.jwks_client = PyJWKClient(
            uri=jwks_url,
            # cache keys url response to reduce SSO server network calls,
            # as public keys are not expected to change frequently
            cache_jwk_set=True,
            # cache resolved public keys
            cache_keys=True,
            # cache url response for 10 hours
            lifespan=36000,
        )

        logger.info("Using JWKS: %s", jwks_url)

        # configure user store access, used for passing group membership check
        users_file_path = config.DATA_DIR / "users.json"
        self.user_store = UserStore(file_path=users_file_path)

    def verify(self, token: str) -> dict:
        """
        Verifies The JWT access token and returns decoded claims as a dictionary if the token is
        valid, otherwise raises an AuthTokenError
        """
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            logger.info("Verifying JWT token")
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.api_id,
                issuer=self.issuer_url,
                # ensure audience verification is carried out
                options={"verify_aud": True},
            )
            # set user_id for logging context.
            user_id = claims.get("email")
            if user_id:
                user_id_var.set(user_id)

            self.authorize_claims(claims, self.app_scope)
            logger.info("Verified JWT token")
            return claims

        except ExpiredSignatureError as e:
            raise AuthTokenError(AuthTokenErrorCode.TOKEN_EXPIRED) from e
        except InvalidAudienceError as e:
            raise AuthTokenError(AuthTokenErrorCode.INVALID_AUDIENCE) from e
        except InvalidIssuerError as e:
            raise AuthTokenError(AuthTokenErrorCode.INVALID_ISSUER) from e
        except InvalidSignatureError as e:
            raise AuthTokenError(AuthTokenErrorCode.INVALID_SIGNATURE) from e
        except jwt.exceptions.DecodeError as e:
            raise AuthTokenError(AuthTokenErrorCode.INVALID_TOKEN) from e
        except jwt.exceptions.PyJWKClientError as e:
            raise AuthTokenError(AuthTokenErrorCode.INVALID_TOKEN) from e
        except jwt.exceptions.PyJWTError as e:
            logger.exception("Unable to check JWT token: %s", token)
            raise AuthTokenError(AuthTokenErrorCode.JWT_ERROR) from e

    def authorize_claims(self, claims: dict, expected_scope: str):
        """
        Authorize claims based on token scope, expected scope and authorized groups
        claims: decoded JWT claims
        expected_scope: expected scope for the token
        Raises AuthTokenError if authorization fails.
        """
        logger.info("Checking JWT token claims")
        if expected_scope:
            token_scopes = claims.get("scp", "").split()
            if expected_scope not in token_scopes:
                logger.error("Expected token scope: %s, got: %s", expected_scope, token_scopes)
                raise AuthTokenError(
                    AuthTokenErrorCode.INVALID_TOKEN_SCOPE,
                    f"Expected token scope: {expected_scope}, got: {token_scopes}",
                )

        if not self.authorized_groups:
            logger.info("Authorized JWT token, no authorized groups configured")
            return

        groups = claims.get("groups", [])
        if self.authorized_groups & set(groups):
            logger.info("Authorized JWT token, against %s", groups)
            return

        # check if the user is in the allowed group by-pass list
        email = claims.get("email").lower() if claims.get("email") else None
        user = self.user_store.users.get(email)
        if user:
            logger.info("User %s authorized from %s file", email, self.user_store.file_path)
            return

        logger.warning("User %s group %s does not match configured groups %s", email, groups, self.authorized_groups)
        raise AuthTokenError(
            AuthTokenErrorCode.MISSING_GROUPS_ERROR,
            f"User {email} group {groups} does not match configured groups {self.authorized_groups}",
        )


class AccessTokenAuthProvider(AuthProvider):
    """Authentication provider for MCP servers for validating, authorizing and extracting access tokens."""

    def __init__(self) -> None:
        super().__init__()
        self.token_verifier = AccessTokenVerifier()
        self.app_scope = config.APP_DEFAULT_SCOPE

    async def verify_token(self, token: str) -> AccessToken:
        """Verify the access token and return an AccessToken object."""
        logger.info("Received verify token request")
        test_token = config.AUTH_TEST_TOKEN

        # check if the token is a test token
        # this is used for integration test run
        if test_token and token == test_token:
            logger.info("Using test token:%s", test_token)
            return AccessToken(token=token, client_id=TEST_CLIENT, scopes=[], expires_at=None)

        claims = self.token_verifier.verify(token)
        scopes = claims.get("scp", "")

        scopes_arr = []
        if scopes:
            scopes_arr = scopes.split(" ")

        logger.info("Authorized the token")
        user_id = self._extract_user_name(claims).lower()
        return AccessToken(token=token, client_id=user_id, scopes=scopes_arr, expires_at=claims.get("exp", None))

    def _extract_user_name(self, claims: dict) -> str:
        """
        Extracts a user id from the claims dictionary.
        """
        return claims.get("email")

    async def verify_auth_header(self, auth_header: str | None) -> AccessToken:
        """
        Splits the authorization header and looks for bearer type token,
        then verifies the extracted bearer token and returns an AccessToken object.
        """

        if auth_header and auth_header.lower().startswith("bearer "):
            auth_token = auth_header.split(" ", 1)[1].strip()
            return await self.verify_token(auth_token)

        raise AuthTokenError(
            AuthTokenErrorCode.INVALID_TOKEN,
            f"Could not find bearer token in authorization header: {auth_header}",
        )

    @staticmethod
    def auth_error_handler(conn, exc: AuthenticationError):  # pylint: disable=unused-argument
        """Customize error handler for authentication errors"""
        if isinstance(exc, AuthTokenError):
            return exc.to_http_response()

        return JSONResponse(
            content={"error": {"code": "UNAUTHORIZED", "message": str(exc)}},
            status_code=401,
            headers={"WWW-Authenticate": f'Bearer realm="{REALM}", error="invalid_token"'},
        )

    def get_middleware(self) -> list:
        # customize exception handling
        mws = [
            Middleware(AuthenticationMiddleware, backend=BearerAuthBackend(self), on_error=self.auth_error_handler),
            Middleware(AuthContextMiddleware),
        ]

        return mws + [Middleware(UserIdCheckMiddleware)]


class UserIdCheckMiddleware:  # pylint: disable=too-few-public-methods
    """Middleware to to check http user-id and JWT user"""

    HEADERS = "headers"

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] not in ["http"]:
            await self.app(scope, receive, send)
            return
        user = scope.get(HTTP_AUTH_CONTEXT_USER)

        # FastMCP AuthenticationMiddleware still calls next middleware, therefore, need to check if the user
        # is an AuthenticatedUser.
        if not isinstance(user, AuthenticatedUser):
            await self.app(scope, receive, send)
            return

        username = user.username
        headers = {k.decode().lower(): v.decode() for k, v in scope.get(self.HEADERS, [])}

        user_id = headers.get(HTTP_USER_ID_HEADER)
        if user_id and username and username.lower() != user_id.lower():
            logger.error("user: %s and user-id: %s header mismatch", username, user_id)
            response = JSONResponse(
                {"detail": f"Unauthorized: JWT token user id and user-id: {user_id} header mismatch"},
                status_code=401,
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
