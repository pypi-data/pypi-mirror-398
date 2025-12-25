"""OKAP Vault - Manages keys and issues tokens."""

import secrets
from datetime import datetime
from typing import Optional

from okap.models import (
    AccessRequest,
    AccessResponse,
    Capabilities,
    Limits,
    OkapToken,
    Provider,
)
from okap.vault.storage import Storage, MemoryStorage


def generate_token_id() -> str:
    """Generate a unique token ID."""
    return f"okap_{secrets.token_urlsafe(32)}"


class OkapVault:
    """Server-side vault for managing API keys and issuing OKAP tokens.
    
    Example:
        ```python
        from okap.vault import OkapVault, MemoryStorage
        
        vault = OkapVault(storage=MemoryStorage())
        vault.add_key("openai", "sk-...")
        
        # In your FastAPI app
        @app.post("/okap/request")
        def handle_request(request: AccessRequest):
            # Show user approval UI, then:
            return vault.approve_request(request)
        ```
    """
    
    def __init__(
        self,
        storage: Optional[Storage] = None,
        *,
        base_url: Optional[str] = None,
        default_expires_days: int = 30,
    ):
        """Initialize the vault.
        
        Args:
            storage: Storage backend (defaults to MemoryStorage)
            base_url: Base URL where the vault is hosted
            default_expires_days: Default token expiration in days
        """
        self.storage = storage or MemoryStorage()
        self.base_url = base_url or "http://localhost:8000"
        self.default_expires_days = default_expires_days
    
    def add_key(self, provider: str | Provider, key: str) -> None:
        """Add a master API key to the vault.
        
        Args:
            provider: AI provider (e.g., "openai")
            key: The API key
        """
        if isinstance(provider, str):
            provider = Provider(provider.lower())
        self.storage.set_master_key(provider, key)
    
    def validate_request(self, request: AccessRequest) -> tuple[bool, Optional[str]]:
        """Validate an access request.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if we have a key for this provider
        master_key = self.storage.get_master_key(request.provider)
        if not master_key:
            return False, f"No key configured for provider: {request.provider.value}"
        
        # Add more validation as needed
        return True, None
    
    def approve_request(
        self,
        request: AccessRequest,
        *,
        approved_models: Optional[list[str]] = None,
        approved_capabilities: Optional[list[Capabilities]] = None,
        approved_limits: Optional[Limits] = None,
        expires_days: Optional[int] = None,
    ) -> AccessResponse:
        """Approve an access request and issue a token.
        
        Args:
            request: The access request to approve
            approved_models: Override requested models (None = use requested)
            approved_capabilities: Override capabilities (None = use requested)
            approved_limits: Override limits (None = use requested)
            expires_days: Override expiration (None = use default)
        
        Returns:
            AccessResponse with token
        """
        # Validate first
        is_valid, error = self.validate_request(request)
        if not is_valid:
            return AccessResponse(
                approved=False,
                error=error,
                error_code="invalid_request",
            )
        
        # Get master key
        master_key = self.storage.get_master_key(request.provider)
        if not master_key:
            return AccessResponse(
                approved=False,
                error="No key available",
                error_code="no_key",
            )
        
        # Generate token
        token_id = generate_token_id()
        
        # Calculate expiration
        expires_at = None
        if request.expires:
            expires_at = datetime.fromisoformat(request.expires.replace("Z", "+00:00"))
        elif expires_days or self.default_expires_days:
            from datetime import timedelta
            expires_at = datetime.utcnow() + timedelta(days=expires_days or self.default_expires_days)
        
        # Create token
        token = OkapToken(
            token=token_id,
            base_url=f"{self.base_url}/v1/{request.provider.value}",
            provider=request.provider,
            models=approved_models or request.models,
            capabilities=approved_capabilities or request.capabilities,
            limits=approved_limits or request.limits,
            expires_at=expires_at,
        )
        
        # Store token
        self.storage.store_token(token_id, token, master_key)
        
        return AccessResponse(
            approved=True,
            token=token,
        )
    
    def deny_request(
        self,
        request: AccessRequest,
        reason: str = "Access denied by user",
    ) -> AccessResponse:
        """Deny an access request.
        
        Args:
            request: The request being denied
            reason: Reason for denial
        
        Returns:
            AccessResponse with error
        """
        return AccessResponse(
            approved=False,
            error=reason,
            error_code="user_denied",
        )
    
    def revoke_token(self, token_id: str) -> bool:
        """Revoke a token.
        
        Args:
            token_id: The token to revoke
            
        Returns:
            True if token was revoked, False if not found
        """
        return self.storage.revoke_token(token_id)
    
    def get_token_info(self, token_id: str) -> Optional[OkapToken]:
        """Get information about a token.
        
        Args:
            token_id: The token ID
            
        Returns:
            Token info or None if not found
        """
        result = self.storage.get_token(token_id)
        if result:
            return result[0]
        return None
    
    def list_tokens(self) -> list[OkapToken]:
        """List all active tokens.
        
        Returns:
            List of active tokens
        """
        return self.storage.list_tokens()
    
    def get_master_key_for_token(self, token_id: str) -> Optional[str]:
        """Get the master key associated with a token (for proxying).
        
        Args:
            token_id: The OKAP token
            
        Returns:
            The master API key or None if token invalid
        """
        result = self.storage.get_token(token_id)
        if result:
            return result[1]
        return None
