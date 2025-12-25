"""Provides FastMCP client configured with a Bearer token provider"""

from pydantic_ai.mcp import MCPServerStreamableHTTP

from aixtools.auth_client.client import ClientAccessTokenProvider


class MCPClientWithAuth(MCPServerStreamableHTTP):
    """StreamableHTTPClient with an access token from a token provider."""

    def __init__(self, mcp_url, **kwargs):
        self.token_provider = ClientAccessTokenProvider()
        access_token = self.token_provider.get_access_token()
        original_headers = kwargs.pop("headers", {}) or {}
        headers = {
            **original_headers,
            "Authorization": f"Bearer {access_token}",
        }
        super().__init__(mcp_url, headers=headers, **kwargs)
