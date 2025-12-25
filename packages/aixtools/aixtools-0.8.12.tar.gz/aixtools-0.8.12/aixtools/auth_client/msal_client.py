"""Custom MSAL module enabling passing customized redirect_uri"""

from msal.application import PublicClientApplication

from aixtools.utils import config


class PublicClientApplicationWithCustomRedirectUri(PublicClientApplication):
    """PublicClientApplication with custom redirect uri functionality"""

    def __init__(self, *args, **kwargs):
        self._redirect_uri = config.AUTH_REDIRECT_URI
        super().__init__(*args, **kwargs)

    def _build_client(self, *args, **kwargs):
        client, regional_client = super()._build_client(*args, **kwargs)

        # Capture original function
        original_obtain_token_by_browser = client.obtain_token_by_browser

        # add custom redirect_uri, which is not possible with original acquire_token_interactive
        def obtain_token_by_browser_with_custom_redirect(*a, **kw):
            kw["redirect_uri"] = self._redirect_uri
            return original_obtain_token_by_browser(*a, **kw)

        # Override original function
        client.obtain_token_by_browser = obtain_token_by_browser_with_custom_redirect
        return client, regional_client
