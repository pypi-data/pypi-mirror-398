"""Pydantic models for OKAP protocol."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Provider(str, Enum):
    """Supported AI providers."""
    
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"


class Capabilities(str, Enum):
    """API capabilities that can be requested."""
    
    CHAT = "chat"
    COMPLETIONS = "completions"
    EMBEDDINGS = "embeddings"
    IMAGES = "images"
    AUDIO = "audio"
    MODERATION = "moderation"


class Limits(BaseModel):
    """Rate and spend limits for token."""
    
    monthly_spend: Optional[float] = Field(None, description="Max monthly spend in USD")
    daily_spend: Optional[float] = Field(None, description="Max daily spend in USD")
    requests_per_minute: Optional[int] = Field(None, description="Rate limit per minute")
    requests_per_day: Optional[int] = Field(None, description="Daily request limit")
    tokens_per_request: Optional[int] = Field(None, description="Max tokens per request")


class AccessRequest(BaseModel):
    """Request for API key access."""
    
    okap: str = Field("1.0", description="OKAP protocol version")
    provider: Provider = Field(..., description="AI provider to access")
    models: list[str] = Field(default_factory=list, description="Specific models requested")
    capabilities: list[Capabilities] = Field(
        default_factory=lambda: [Capabilities.CHAT],
        description="API capabilities needed"
    )
    limits: Optional[Limits] = Field(None, description="Usage limits")
    expires: Optional[str] = Field(None, description="Expiration date (ISO 8601)")
    reason: Optional[str] = Field(None, description="Why access is needed")
    app_name: Optional[str] = Field(None, description="Name of requesting app")
    app_url: Optional[str] = Field(None, description="URL of requesting app")
    redirect_uri: Optional[str] = Field(None, description="OAuth-style redirect URI")


class OkapToken(BaseModel):
    """Token returned after successful authorization."""
    
    token: str = Field(..., description="The OKAP token (okap_...)")
    base_url: str = Field(..., description="Base URL to use instead of provider's API")
    provider: Provider = Field(..., description="The provider this token is for")
    models: list[str] = Field(default_factory=list, description="Allowed models")
    capabilities: list[Capabilities] = Field(default_factory=list, description="Allowed capabilities")
    limits: Optional[Limits] = Field(None, description="Applied limits")
    expires_at: Optional[datetime] = Field(None, description="When token expires")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AccessResponse(BaseModel):
    """Response to an access request."""
    
    okap: str = Field("1.0", description="OKAP protocol version")
    approved: bool = Field(..., description="Whether access was granted")
    token: Optional[OkapToken] = Field(None, description="Token if approved")
    error: Optional[str] = Field(None, description="Error message if denied")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")


class TokenInfo(BaseModel):
    """Information about an active token."""
    
    token_id: str
    app_name: Optional[str]
    provider: Provider
    models: list[str]
    capabilities: list[Capabilities]
    limits: Optional[Limits]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage: dict = Field(default_factory=dict)
