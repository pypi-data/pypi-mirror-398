# rossetta-fastapi

End-to-end encryption middleware for FastAPI applications.

## Installation

```bash
pip install rossetta-fastapi
```

## Usage

Add the middleware to your FastAPI application with a single line:

```python
from fastapi import FastAPI
from rossetta_fastapi import RossettaMiddleware

app = FastAPI()

# Add the middleware - that's it!
app.add_middleware(RossettaMiddleware)

# All your existing routes now have e2e encryption
@app.get("/api/data")
async def get_data():
    return {"message": "This response is automatically encrypted!"}

@app.post("/api/submit")
async def submit_data(data: dict):
    # Request is automatically decrypted
    return {"received": data}
```

## Features

- **Zero Code Changes**: Add middleware and all routes are automatically protected
- **Transparent Encryption**: Works with existing FastAPI code
- **Automatic Key Exchange**: ECDH key exchange handled automatically
- **Replay Attack Prevention**: Built-in timestamp and nonce validation
- **Session Management**: Automatic session lifecycle management

## Configuration

```python
app.add_middleware(
    RossettaMiddleware,
    session_duration=3600,        # Session duration in seconds (default: 1 hour)
    max_timestamp_drift=300,      # Max timestamp drift in seconds (default: 5 minutes)
)
```

## How It Works

1. Client initiates ECDH key exchange via `/__rossetta_handshake__` endpoint
2. Middleware derives shared secret from key exchange
3. All subsequent requests are encrypted with the shared session key
4. Middleware decrypts requests, validates nonce/timestamp
5. Processes request through normal FastAPI handlers
6. Encrypts response before sending back to client

## Requirements

- Python 3.8+
- FastAPI 0.100.0+
- cryptography 41.0.0+

## Client Compatibility

Works with `rossetta-client` npm package for JavaScript/TypeScript clients.

## License

MIT
