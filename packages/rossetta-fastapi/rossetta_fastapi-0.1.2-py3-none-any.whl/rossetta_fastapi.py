"""
@rossetta-api/fastapi
Zero-config network request obfuscation middleware for FastAPI

Usage:
    from fastapi import FastAPI, Request
    from starlette.middleware.sessions import SessionMiddleware
    from rossetta_fastapi import setup_rossetta

    app = FastAPI()
    setup_rossetta(app)
    app.add_middleware(SessionMiddleware, secret_key="your-secret")

    # All /api/* endpoints automatically encrypted!
    @app.get("/api/users")
    async def get_users():
        return {"users": []}  # Auto-encrypted

    @app.post("/api/users")
    async def create_user(request: Request):
        data = request.state.decrypted_data  # Auto-decrypted
        return {"id": 1, "name": data["name"]}  # Auto-encrypted
"""

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
import hashlib
import hmac
import json
import secrets
import time
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from typing import Optional, Callable
from functools import wraps
import os
import logging
import asyncio

# Configure logger
logger = logging.getLogger(__name__)

ALGORITHM = "AES-CBC"
DEFAULT_SECRET = os.getenv("ROSSETTA_SECRET_KEY", secrets.token_hex(32))
TIMESTAMP_WINDOW = 5 * 60 * 1000  # 5 minutes in milliseconds


class RossettaMiddleware(BaseHTTPMiddleware):
    """
    Rossetta API middleware for FastAPI
    Provides automatic request/response obfuscation and encryption
    """

    def __init__(
        self,
        app,
        secret: str = DEFAULT_SECRET,
        timestamp_window: int = TIMESTAMP_WINDOW,
    ):
        super().__init__(app)
        self.secret = secret
        self.timestamp_window = timestamp_window

    def obfuscate_endpoint(self, endpoint: str, salt: str) -> str:
        """Generate obfuscated endpoint path"""
        hash_input = f"{endpoint}{salt}".encode()
        hash_digest = hashlib.sha256(hash_input).hexdigest()
        return f"/api/{hash_digest[:16]}"

    def encrypt(self, data: dict, session_key: str) -> str:
        """Encrypt data for transmission"""
        json_string = json.dumps(data)
        key = hashlib.sha256(session_key.encode()).digest()
        iv = secrets.token_bytes(16)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Pad data to be multiple of 16 bytes
        padding_length = 16 - (len(json_string) % 16)
        padded_data = json_string + (chr(padding_length) * padding_length)

        encrypted = encryptor.update(padded_data.encode()) + encryptor.finalize()

        iv_b64 = b64encode(iv).decode()
        encrypted_b64 = b64encode(encrypted).decode()

        return f"{iv_b64}:{encrypted_b64}"

    def decrypt(self, encrypted_data: str, session_key: str) -> dict:
        """Decrypt received data"""
        # Split on first colon to separate IV from encrypted data
        parts = encrypted_data.split(":", 1)
        if len(parts) != 2:
            raise ValueError("Invalid encrypted data format")

        iv_b64, encrypted_b64 = parts
        iv = b64decode(iv_b64)
        encrypted = b64decode(encrypted_b64)

        key = hashlib.sha256(session_key.encode()).digest()

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        decrypted = decryptor.update(encrypted) + decryptor.finalize()

        # Validate and remove padding
        if len(decrypted) == 0:
            raise ValueError("Decrypted data is empty")

        padding_length = decrypted[-1]

        # Validate padding length (must be 1-16 for AES block size)
        if padding_length < 1 or padding_length > 16:
            raise ValueError("Invalid padding length")

        # Validate padding bytes
        if len(decrypted) < padding_length:
            raise ValueError("Invalid padding")

        # Verify all padding bytes are correct
        expected_padding = bytes([padding_length] * padding_length)
        if decrypted[-padding_length:] != expected_padding:
            raise ValueError("Invalid padding bytes")

        decrypted = decrypted[:-padding_length]

        json_string = decrypted.decode()
        return json.loads(json_string)

    def create_signature(self, data: dict, timestamp: int, session_key: str) -> str:
        # 1. separators=(',', ':') removes the default spaces
        # 2. ensure_ascii=False prevents escaping (e.g., keeps 'ñ' instead of '\u00f1')
        # 3. sort_keys=False is default, but ensure your input dictionary order matches JS
        payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False) + str(
            timestamp
        )

        signature = hmac.new(
            session_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return signature

    def verify_signature(
        self, data: dict, timestamp: int, signature: str, session_key: str
    ) -> bool:
        """Verify HMAC signature"""
        expected = self.create_signature(data, timestamp, session_key)
        return hmac.compare_digest(signature, expected)

    def is_timestamp_valid(self, timestamp: int) -> bool:
        """Validate timestamp to prevent replay attacks"""
        now = int(time.time() * 1000)
        age = now - timestamp
        return 0 <= age <= self.timestamp_window

    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch"""

        # Initialize session if not exists
        if "rossetta_key" not in request.session:
            request.session["rossetta_key"] = secrets.token_hex(32)
            request.session["endpoint_salt"] = secrets.token_hex(16)

        session_key = request.session["rossetta_key"]
        endpoint_salt = request.session["endpoint_salt"]

        # Add helper methods to request
        request.state.rossetta = {
            "session_key": session_key,
            "endpoint_salt": endpoint_salt,
            "obfuscate_endpoint": lambda name: self.obfuscate_endpoint(
                name, endpoint_salt
            ),
            "encrypt": lambda data: self.encrypt(data, session_key),
            "decrypt": lambda data: self.decrypt(data, session_key),
        }

        # Decrypt incoming requests
        if request.method in ["POST", "PUT", "DELETE"]:
            try:
                body = await request.body()
                if body:
                    encrypted_data = body.decode()
                    decrypted_payload = self.decrypt(encrypted_data, session_key)

                    # Verify timestamp
                    if not self.is_timestamp_valid(decrypted_payload["timestamp"]):
                        error_response = self.encrypt(
                            {"error": "Request expired"}, session_key
                        )
                        return Response(
                            content=error_response,
                            status_code=401,
                            media_type="text/plain",
                        )

                    # Verify signature
                    if not self.verify_signature(
                        decrypted_payload["data"],
                        decrypted_payload["timestamp"],
                        decrypted_payload["signature"],
                        session_key,
                    ):
                        error_response = self.encrypt(
                            {"error": "Invalid signature"}, session_key
                        )
                        return Response(
                            content=error_response,
                            status_code=401,
                            media_type="text/plain",
                        )

                    # Store decrypted data in request state
                    request.state.decrypted_data = decrypted_payload["data"]

            except Exception as e:
                logger.error(f"Decryption error: {type(e).__name__}")
                error_response = self.encrypt(
                    {"error": "Invalid request format"}, session_key
                )
                return Response(
                    content=error_response, status_code=400, media_type="text/plain"
                )

        # Process request
        response = await call_next(request)

        # Auto-encrypt responses for API endpoints (except init-session and non-API routes)
        if (
            request.url.path.startswith("/api/")
            and request.url.path != "/api/init-session"
        ):
            # Check if response is already encrypted (has text/plain media type from manual encryption)
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("text/plain"):
                # Need to read the response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                # Only encrypt JSON responses
                if "application/json" in content_type and response_body:
                    try:
                        # Parse JSON response
                        response_data = json.loads(response_body.decode())

                        # Encrypt the response
                        timestamp = int(time.time() * 1000)
                        response_payload = {
                            "data": response_data,
                            "timestamp": timestamp,
                        }
                        encrypted = self.encrypt(response_payload, session_key)

                        # Return encrypted response
                        return Response(
                            content=encrypted,
                            status_code=response.status_code,
                            headers={
                                k: v
                                for k, v in response.headers.items()
                                if k.lower() != "content-length"
                            },
                            media_type="text/plain",
                        )
                    except Exception as e:
                        logger.error(f"Response encryption error: {type(e).__name__}")
                        # Return original response if encryption fails
                        pass

        return response


def encrypt_response(data: dict, session_key: str) -> str:
    """
    Helper function to manually encrypt responses (advanced usage).

    Note: This is rarely needed as automatic encryption is enabled for all /api/* endpoints.
    """
    # Use the encryption logic directly without creating middleware instance
    key = hashlib.sha256(session_key.encode()).digest()
    iv = secrets.token_bytes(16)

    timestamp = int(time.time() * 1000)
    response_payload = {"data": data, "timestamp": timestamp}
    json_string = json.dumps(response_payload)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Pad data to be multiple of 16 bytes
    padding_length = 16 - (len(json_string) % 16)
    padded_data = json_string + (chr(padding_length) * padding_length)

    encrypted = encryptor.update(padded_data.encode()) + encryptor.finalize()

    iv_b64 = b64encode(iv).decode()
    encrypted_b64 = b64encode(encrypted).decode()

    return f"{iv_b64}:{encrypted_b64}"


def protected_route(f: Callable) -> Callable:
    """
    Decorator for routes that require encrypted responses

    Usage:
        @app.get('/api/data')
        @protected_route
        async def get_data(request: Request):
            return {'message': 'Hello, World!'}
    """

    @wraps(f)
    async def decorated_function(*args, **kwargs):
        # Find the Request object in the arguments
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        # Also check kwargs
        if request is None:
            request = kwargs.get("request")

        if request is None:
            raise ValueError(
                "Request object not found. Make sure to include Request in your route parameters."
            )

        # Call the original function
        result = (
            await f(*args, **kwargs)
            if asyncio.iscoroutinefunction(f)
            else f(*args, **kwargs)
        )

        # If result is already a Response, return it as is
        if isinstance(result, Response):
            return result

        # Otherwise, encrypt it
        session_key = request.state.rossetta["session_key"]
        encrypted = encrypt_response(result, session_key)
        return Response(content=encrypted, media_type="text/plain")

    return decorated_function


def setup_rossetta(
    app, secret: str = DEFAULT_SECRET, timestamp_window: int = TIMESTAMP_WINDOW
):
    """
    Setup Rossetta middleware and automatically register the /api/init-session endpoint.

    Usage:
        from fastapi import FastAPI
        from starlette.middleware.sessions import SessionMiddleware
        from rossetta_fastapi import setup_rossetta

        app = FastAPI()

        # Setup Rossetta (adds middleware and creates /api/init-session endpoint)
        setup_rossetta(app)

        # Add session middleware (middleware execution order in Starlette is reverse of registration)
        app.add_middleware(SessionMiddleware, secret_key="your-secret")

    Args:
        app: FastAPI application instance
        secret: Secret key for encryption (defaults to env var or auto-generated)
        timestamp_window: Request validity window in milliseconds (default: 300000)
    """
    if not isinstance(app, FastAPI):
        raise TypeError("app must be a FastAPI instance")

    # Register the /api/init-session endpoint
    @app.post("/api/init-session")
    async def init_session(request: Request):
        """Initialize session and return session keys"""
        if "rossetta_key" not in request.session:
            request.session["rossetta_key"] = secrets.token_hex(32)
            request.session["endpoint_salt"] = secrets.token_hex(16)

        return {
            "sessionKey": request.session["rossetta_key"],
            "endpointSalt": request.session["endpoint_salt"],
        }

    # Add the middleware
    app.add_middleware(
        RossettaMiddleware, secret=secret, timestamp_window=timestamp_window
    )
