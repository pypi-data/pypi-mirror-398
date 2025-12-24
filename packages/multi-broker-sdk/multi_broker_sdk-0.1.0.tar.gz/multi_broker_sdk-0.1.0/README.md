# Multi-Broker SDK

Unified Python SDK for authenticating and interacting with multiple Indian stock broker APIs.

## Supported Brokers

- **Fyers** (v3 API) - *Implemented*
- **Angel One** - *Planned*
- **Zerodha** - *Planned*
- **Upstox** - *Planned*

## Features

- **Unified Interface**: consistent API across different brokers.
- **Auto-Authentication**: Handles TOTP generation and token management automatically.
- **Secure Token Storage**: Encrypts and stores access tokens locally to avoid frequent login requests.
- **Token Management**: Automatically refreshes tokens when they expire (handle daily 12 AM reset).

## Installation

```bash
pip install multi-broker-sdk
```

## Usage

### Fyers

```python
from multi_broker_sdk import FyersBroker

# Initialize broker
broker = FyersBroker(
    username="XY12345",
    totp_key="YOUR_TOTP_KEY",
    pin="1234",
    client_id="YOUR_CLIENT_ID",
    secret_key="YOUR_SECRET_KEY",
    redirect_uri="https://trade.fyers.in/api-login/redirect-uri/index.html"
)

# Authenticate (handles TOTP and token generation automatically)
# This will cache the token in ~/.multi_broker_sdk/tokens/
access_token = broker.authenticate()

print(f"Access Token: {access_token}")

# Get Fyers client instance (fyers_apiv3)
client = broker.get_client()

# Use the client
print(client.get_profile())
```

## Security

Tokens are stored in `~/.multi_broker_sdk/tokens/` in an encrypted format using a key derived from your credentials. This ensures that even if someone gets access to the file, they cannot use it without your credentials.

## License

MIT
