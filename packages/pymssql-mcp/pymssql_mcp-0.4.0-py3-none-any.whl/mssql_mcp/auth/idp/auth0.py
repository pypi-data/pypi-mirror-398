"""Auth0 adapter using OIDC."""

import logging

from .oidc import GenericOIDCAdapter

logger = logging.getLogger(__name__)


class Auth0Adapter(GenericOIDCAdapter):
    """Adapter for Auth0 using OpenID Connect.

    Auth0 is fully OIDC-compliant, so this adapter just inherits from
    GenericOIDCAdapter with Auth0-specific defaults.

    Configuration:
        - Discovery URL: https://YOUR_DOMAIN.auth0.com/.well-known/openid-configuration
        - Client ID and Secret from Auth0 application settings
    """

    def __init__(
        self,
        discovery_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        scopes: list[str] | None = None,
        auth0_domain: str | None = None,
    ):
        """Initialize Auth0 OIDC adapter.

        Args:
            discovery_url: Full OIDC discovery URL (takes precedence)
            client_id: Auth0 application client ID
            client_secret: Auth0 application client secret
            scopes: Scopes to request (default: openid, profile, email)
            auth0_domain: Auth0 domain (e.g., your-tenant.auth0.com)
                         Used to construct discovery_url if not provided
        """
        # Construct discovery URL from Auth0 domain if not provided
        if not discovery_url and auth0_domain:
            discovery_url = f"https://{auth0_domain}/.well-known/openid-configuration"

        super().__init__(
            discovery_url=discovery_url,
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes,
        )

        self.auth0_domain = auth0_domain

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        code_challenge: str | None = None,
        code_challenge_method: str | None = None,
        additional_params: dict[str, str] | None = None,
    ) -> str:
        """Generate Auth0 authorization URL.

        Adds Auth0-specific parameters if needed.
        """
        auth0_params = additional_params or {}

        # Auth0-specific parameters (uncomment as needed):
        # auth0_params["audience"] = "https://your-api-identifier"  # API audience
        # auth0_params["connection"] = "google-oauth2"  # Force specific connection
        # auth0_params["prompt"] = "login"  # Force re-authentication

        return await super().get_authorization_url(
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            additional_params=auth0_params,
        )
