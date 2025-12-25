"""The A2A client module with Bearer authentication support"""

import httpx
from a2a.client import (
    AuthInterceptor,
    Client,
    ClientCallContext,
    ClientConfig,
    ClientFactory,
    CredentialService,
)
from a2a.types import AgentCard

from aixtools.auth_client.client import ClientAccessTokenProvider


class BearerCredentialService(CredentialService):  # pylint: disable=too-few-public-methods
    """
    Bearer credential service providing a bearer type token if the security scheme is Bearer
    """

    def __init__(self):
        self.token_provider = ClientAccessTokenProvider()

    async def get_credentials(self, security_scheme_name: str, context: ClientCallContext):
        return self.token_provider.get_access_token()


class A2AClientWithBearerAuth:  # pylint: disable=too-few-public-methods
    """A2A client with Bearer authentication support"""

    @staticmethod
    async def create(agent_card: AgentCard, httpx_client: httpx.AsyncClient) -> Client:
        """Create A2A client with Bearer authentication support"""
        client_config = ClientConfig(
            httpx_client=httpx_client,
        )
        auth_interceptor = AuthInterceptor(credential_service=BearerCredentialService())
        client = ClientFactory(client_config).create(agent_card, interceptors=[auth_interceptor])
        return client
