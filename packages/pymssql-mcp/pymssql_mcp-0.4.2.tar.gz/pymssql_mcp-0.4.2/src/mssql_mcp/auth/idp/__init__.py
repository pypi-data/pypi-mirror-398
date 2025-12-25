"""Identity Provider adapters for external OAuth/OIDC providers.

Supports:
- Generic OIDC (any standard OpenID Connect provider)
- Duo (Cisco Duo SSO)
- Auth0
"""

from typing import TYPE_CHECKING

from .auth0 import Auth0Adapter
from .base import BaseIdPAdapter
from .duo import DuoOIDCAdapter
from .oidc import GenericOIDCAdapter

if TYPE_CHECKING:
    from mssql_mcp.config import MSSQLConfig

__all__ = ["BaseIdPAdapter", "GenericOIDCAdapter", "DuoOIDCAdapter", "Auth0Adapter"]


def create_idp_adapter(config: "MSSQLConfig") -> BaseIdPAdapter:
    """Factory function to create the appropriate IdP adapter based on config.

    Args:
        config: MSSQLConfig instance with IdP settings

    Returns:
        Configured IdP adapter instance

    Raises:
        ValueError: If idp_provider is not recognized
    """
    provider = config.idp_provider.lower()

    if provider == "duo":
        return DuoOIDCAdapter(
            discovery_url=config.idp_discovery_url,
            client_id=config.idp_client_id,
            client_secret=config.idp_client_secret,
            scopes=config.idp_scopes.split() if config.idp_scopes else None,
            duo_api_host=config.duo_api_host,
        )
    elif provider == "auth0":
        return Auth0Adapter(
            discovery_url=config.idp_discovery_url,
            client_id=config.idp_client_id,
            client_secret=config.idp_client_secret,
            scopes=config.idp_scopes.split() if config.idp_scopes else None,
        )
    elif provider == "oidc":
        return GenericOIDCAdapter(
            discovery_url=config.idp_discovery_url,
            client_id=config.idp_client_id,
            client_secret=config.idp_client_secret,
            scopes=config.idp_scopes.split() if config.idp_scopes else None,
        )
    else:
        raise ValueError(f"Unknown IdP provider: {provider}. Use 'duo', 'auth0', or 'oidc'")
