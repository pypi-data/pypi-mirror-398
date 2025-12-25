<p align="center">
  <img src="https://raw.githubusercontent.com/openkeyprotocol/okap/main/logo.png" alt="OKAP Logo" width="120">
</p>

# OKAP Python SDK

Python SDK for [OKAP](https://github.com/openkeyprotocol/okap) (Open Key Access Protocol) - Secure API key delegation.

## Installation

```bash
pip install okap
```

For vault server functionality:
```bash
pip install okap[vault]
```

## Quick Start

### For Apps (Requesting Access)

```python
from okap import OkapClient

# Connect to user's vault
client = OkapClient(
    vault_url="https://vault.example.com",
    app_name="My AI App"
)

# Request access to OpenAI
token = client.request_access(
    provider="openai",
    models=["gpt-4", "gpt-4o-mini"],
    capabilities=["chat"],
    monthly_limit=10.00,  # $10/month max
    reason="For AI-powered features"
)

# Use with OpenAI SDK - just change base_url
from openai import OpenAI

ai = OpenAI(
    api_key=token.token,
    base_url=token.base_url  # Points to vault proxy
)

response = ai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### For Vaults (Hosting Keys)

```python
from okap.vault import OkapVault, MemoryStorage
from fastapi import FastAPI

app = FastAPI()
vault = OkapVault(
    storage=MemoryStorage(),
    base_url="https://vault.example.com"
)

# Add your API keys
vault.add_key("openai", "sk-...")
vault.add_key("anthropic", "sk-ant-...")

@app.post("/okap/request")
def handle_request(request: dict):
    from okap.models import AccessRequest
    req = AccessRequest.model_validate(request)
    
    # In production, show approval UI to user first!
    # For demo, auto-approve:
    return vault.approve_request(req)
```

## Features

- **Secure delegation**: Master keys never leave the vault
- **Usage limits**: Set spend caps and rate limits per app
- **Expiration**: Tokens auto-expire
- **Revocable**: Revoke access instantly
- **Provider agnostic**: Works with OpenAI, Anthropic, Google, etc.

## Models

### AccessRequest
```python
from okap import AccessRequest

request = AccessRequest(
    provider="openai",
    models=["gpt-4"],
    capabilities=["chat", "embeddings"],
    limits=Limits(monthly_spend=10.00),
    expires="2025-03-01",
    reason="For my cool app"
)
```

### OkapToken
```python
from okap import OkapToken

# Returned after approval
token = OkapToken(
    token="okap_abc123...",
    base_url="https://vault.example.com/v1/openai",
    provider="openai",
    models=["gpt-4"],
    expires_at=datetime(2025, 3, 1)
)
```

## Error Handling

```python
from okap import OkapClient
from okap.errors import AccessDeniedError, VaultError

try:
    token = client.request_access(provider="openai")
except AccessDeniedError as e:
    print(f"User denied access: {e}")
except VaultError as e:
    print(f"Vault error: {e}")
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

## License

MIT
