"""Tests for OKAP vault."""

from okap.vault import OkapVault, MemoryStorage
from okap.models import AccessRequest, Provider, Capabilities


def test_vault_add_key():
    vault = OkapVault(storage=MemoryStorage())
    vault.add_key("openai", "sk-test-key")
    
    key = vault.storage.get_master_key(Provider.OPENAI)
    assert key == "sk-test-key"


def test_vault_approve_request():
    vault = OkapVault(
        storage=MemoryStorage(),
        base_url="https://vault.test.com"
    )
    vault.add_key("openai", "sk-test-key")
    
    request = AccessRequest(
        provider=Provider.OPENAI,
        models=["gpt-4"],
        capabilities=[Capabilities.CHAT],
    )
    
    response = vault.approve_request(request)
    
    assert response.approved is True
    assert response.token is not None
    assert response.token.token.startswith("okap_")
    assert response.token.base_url == "https://vault.test.com/v1/openai"
    assert response.token.provider == Provider.OPENAI


def test_vault_deny_request():
    vault = OkapVault(storage=MemoryStorage())
    
    request = AccessRequest(
        provider=Provider.OPENAI,
        models=["gpt-4"],
    )
    
    response = vault.deny_request(request, reason="Not today")
    
    assert response.approved is False
    assert response.error == "Not today"


def test_vault_revoke_token():
    vault = OkapVault(storage=MemoryStorage())
    vault.add_key("openai", "sk-test-key")
    
    request = AccessRequest(provider=Provider.OPENAI)
    response = vault.approve_request(request)
    
    token_id = response.token.token
    
    # Token should exist
    assert vault.get_token_info(token_id) is not None
    
    # Revoke
    assert vault.revoke_token(token_id) is True
    
    # Token should be gone
    assert vault.get_token_info(token_id) is None


def test_vault_no_key_configured():
    vault = OkapVault(storage=MemoryStorage())
    # Don't add any keys
    
    request = AccessRequest(provider=Provider.OPENAI)
    response = vault.approve_request(request)
    
    assert response.approved is False
    assert "No key configured" in response.error
