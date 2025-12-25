"""OKAP Client for applications requesting API access."""

from typing import Optional
from urllib.parse import urljoin

import httpx

from okap.models import (
    AccessRequest,
    AccessResponse,
    Capabilities,
    Limits,
    OkapToken,
    Provider,
)
from okap.errors import OkapError, AccessDeniedError, VaultError


class OkapClient:
    """Client for requesting API key access from an OKAP vault.
    
    Example:
        ```python
        from okap import OkapClient
        
        client = OkapClient("https://vault.example.com")
        token = client.request_access(
            provider="openai",
            models=["gpt-4"],
            monthly_limit=10.00
        )
        
        # Use with OpenAI SDK
        from openai import OpenAI
        ai = OpenAI(api_key=token.token, base_url=token.base_url)
        ```
    """
    
    def __init__(
        self,
        vault_url: str,
        *,
        app_name: Optional[str] = None,
        app_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize the OKAP client.
        
        Args:
            vault_url: Base URL of the OKAP vault
            app_name: Name of your application (shown to user)
            app_url: URL of your application
            timeout: Request timeout in seconds
        """
        self.vault_url = vault_url.rstrip("/")
        self.app_name = app_name
        self.app_url = app_url
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
    
    def request_access(
        self,
        provider: str | Provider,
        *,
        models: Optional[list[str]] = None,
        capabilities: Optional[list[str | Capabilities]] = None,
        monthly_limit: Optional[float] = None,
        daily_limit: Optional[float] = None,
        requests_per_minute: Optional[int] = None,
        expires: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> OkapToken:
        """Request access to an API key.
        
        Args:
            provider: AI provider (e.g., "openai", "anthropic")
            models: Specific models to request access to
            capabilities: API capabilities needed (chat, embeddings, etc.)
            monthly_limit: Maximum monthly spend in USD
            daily_limit: Maximum daily spend in USD
            requests_per_minute: Rate limit
            expires: Expiration date (ISO 8601 format)
            reason: Why your app needs access (shown to user)
        
        Returns:
            OkapToken with credentials to use
            
        Raises:
            AccessDeniedError: If the user denied access
            VaultError: If the vault returned an error
        """
        # Normalize provider
        if isinstance(provider, str):
            provider = Provider(provider.lower())
        
        # Normalize capabilities
        if capabilities:
            capabilities = [
                Capabilities(c) if isinstance(c, str) else c
                for c in capabilities
            ]
        else:
            capabilities = [Capabilities.CHAT]
        
        # Build limits
        limits = None
        if any([monthly_limit, daily_limit, requests_per_minute]):
            limits = Limits(
                monthly_spend=monthly_limit,
                daily_spend=daily_limit,
                requests_per_minute=requests_per_minute,
            )
        
        # Build request
        request = AccessRequest(
            provider=provider,
            models=models or [],
            capabilities=capabilities,
            limits=limits,
            expires=expires,
            reason=reason,
            app_name=self.app_name,
            app_url=self.app_url,
        )
        
        # Send to vault
        url = urljoin(self.vault_url, "/okap/request")
        try:
            response = self._client.post(
                url,
                json=request.model_dump(exclude_none=True),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise VaultError(f"Vault returned error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise VaultError(f"Failed to connect to vault: {e}") from e
        
        # Parse response
        data = response.json()
        access_response = AccessResponse.model_validate(data)
        
        if not access_response.approved:
            raise AccessDeniedError(
                access_response.error or "Access denied",
                code=access_response.error_code,
            )
        
        if not access_response.token:
            raise VaultError("Vault approved but returned no token")
        
        return access_response.token
    
    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self) -> "OkapClient":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
