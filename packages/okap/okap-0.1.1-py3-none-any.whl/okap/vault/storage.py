"""Storage backends for OKAP vault."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from okap.models import OkapToken, Provider


class Storage(ABC):
    """Abstract base class for token storage."""
    
    @abstractmethod
    def store_token(self, token_id: str, token: OkapToken, master_key: str) -> None:
        """Store a token with its associated master key."""
        pass
    
    @abstractmethod
    def get_token(self, token_id: str) -> Optional[tuple[OkapToken, str]]:
        """Get a token and its master key by ID. Returns None if not found."""
        pass
    
    @abstractmethod
    def revoke_token(self, token_id: str) -> bool:
        """Revoke a token. Returns True if token existed."""
        pass
    
    @abstractmethod
    def list_tokens(self) -> list[OkapToken]:
        """List all active tokens."""
        pass
    
    @abstractmethod
    def get_master_key(self, provider: Provider) -> Optional[str]:
        """Get the master API key for a provider."""
        pass
    
    @abstractmethod
    def set_master_key(self, provider: Provider, key: str) -> None:
        """Store a master API key for a provider."""
        pass


class MemoryStorage(Storage):
    """In-memory storage for development/testing."""
    
    def __init__(self):
        self._tokens: dict[str, tuple[OkapToken, str]] = {}
        self._master_keys: dict[Provider, str] = {}
    
    def store_token(self, token_id: str, token: OkapToken, master_key: str) -> None:
        self._tokens[token_id] = (token, master_key)
    
    def get_token(self, token_id: str) -> Optional[tuple[OkapToken, str]]:
        result = self._tokens.get(token_id)
        if result:
            token, master_key = result
            # Check expiration
            if token.expires_at and token.expires_at < datetime.utcnow():
                del self._tokens[token_id]
                return None
        return result
    
    def revoke_token(self, token_id: str) -> bool:
        if token_id in self._tokens:
            del self._tokens[token_id]
            return True
        return False
    
    def list_tokens(self) -> list[OkapToken]:
        now = datetime.utcnow()
        active = []
        expired = []
        
        for token_id, (token, _) in self._tokens.items():
            if token.expires_at and token.expires_at < now:
                expired.append(token_id)
            else:
                active.append(token)
        
        # Clean up expired
        for token_id in expired:
            del self._tokens[token_id]
        
        return active
    
    def get_master_key(self, provider: Provider) -> Optional[str]:
        return self._master_keys.get(provider)
    
    def set_master_key(self, provider: Provider, key: str) -> None:
        self._master_keys[provider] = key
