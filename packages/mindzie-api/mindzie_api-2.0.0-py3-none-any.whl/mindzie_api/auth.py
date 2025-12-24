"""Authentication handling for the Mindzie API client."""

import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import logging

from mindzie_api.constants import AuthType
from mindzie_api.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class AuthProvider(ABC):
    """Abstract base class for authentication providers."""
    
    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        pass
    
    @abstractmethod
    def refresh(self) -> None:
        """Refresh authentication if needed."""
        pass
    
    @abstractmethod
    def is_valid(self) -> bool:
        """Check if authentication is valid."""
        pass


class APIKeyAuth(AuthProvider):
    """API Key authentication provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize API key authentication.
        
        Args:
            api_key: API key for authentication. If not provided, will try to
                    read from MINDZIE_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("MINDZIE_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key is required. Provide it directly or set MINDZIE_API_KEY environment variable."
            )
    
    def get_headers(self) -> Dict[str, str]:
        """Get API key authentication headers."""
        return {
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def refresh(self) -> None:
        """API keys don't need refreshing."""
        pass
    
    def is_valid(self) -> bool:
        """Check if API key is set."""
        return bool(self.api_key)


class BearerAuth(AuthProvider):
    """Bearer token authentication provider."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize bearer token authentication.
        
        Args:
            token: Bearer token for authentication. If not provided, will try to
                  read from MINDZIE_BEARER_TOKEN environment variable.
        """
        self.token = token or os.getenv("MINDZIE_BEARER_TOKEN")
        if not self.token:
            raise AuthenticationError(
                "Bearer token is required. Provide it directly or set MINDZIE_BEARER_TOKEN environment variable."
            )
    
    def get_headers(self) -> Dict[str, str]:
        """Get bearer token authentication headers."""
        return {
            "Authorization": f"Bearer {self.token}"
        }
    
    def refresh(self) -> None:
        """Bearer tokens need external refresh mechanism."""
        logger.warning("Bearer token refresh not implemented. Token may expire.")
    
    def is_valid(self) -> bool:
        """Check if bearer token is set."""
        return bool(self.token)


class AzureADAuth(AuthProvider):
    """Azure AD authentication provider."""
    
    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scope: Optional[str] = None
    ):
        """Initialize Azure AD authentication.
        
        Args:
            tenant_id: Azure AD tenant ID
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            scope: OAuth scope for the token
        """
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID")
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AZURE_CLIENT_SECRET")
        self.scope = scope or os.getenv("AZURE_SCOPE", "api://mindzie/.default")
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise AuthenticationError(
                "Azure AD authentication requires tenant_id, client_id, and client_secret"
            )
        
        # Fail fast if Azure AD auth is requested but not implemented
        raise NotImplementedError(
            "Azure AD authentication requires 'msal' library. Install with: pip install msal"
        )
        
        self.token: Optional[str] = None
        self.token_expiry: Optional[float] = None
    
    def _acquire_token(self) -> None:
        """Acquire token from Azure AD."""
        # This would require the msal library
        # For now, we'll use a placeholder implementation
        logger.warning("Azure AD authentication requires 'msal' library. Install with: pip install msal")
        raise NotImplementedError(
            "Azure AD authentication requires 'msal' library. Install with: pip install mindzie-api[azure]"
        )
    
    def get_headers(self) -> Dict[str, str]:
        """Get Azure AD authentication headers."""
        if not self.is_valid():
            self.refresh()
        return {
            "Authorization": f"Bearer {self.token}"
        }
    
    def refresh(self) -> None:
        """Refresh Azure AD token."""
        self._acquire_token()
    
    def is_valid(self) -> bool:
        """Check if Azure AD token is valid."""
        if not self.token:
            return False
        # Check token expiry
        import time
        if self.token_expiry and time.time() >= self.token_expiry:
            return False
        return True


def create_auth_provider(
    auth_type: AuthType = AuthType.API_KEY,
    **kwargs
) -> AuthProvider:
    """Factory function to create authentication provider.
    
    Args:
        auth_type: Type of authentication to use
        **kwargs: Additional arguments for the auth provider
    
    Returns:
        AuthProvider instance
    """
    if auth_type == AuthType.API_KEY:
        return APIKeyAuth(**kwargs)
    elif auth_type == AuthType.BEARER:
        return BearerAuth(**kwargs)
    elif auth_type == AuthType.AZURE_AD:
        return AzureADAuth(**kwargs)
    else:
        raise ValueError(f"Unsupported authentication type: {auth_type}")