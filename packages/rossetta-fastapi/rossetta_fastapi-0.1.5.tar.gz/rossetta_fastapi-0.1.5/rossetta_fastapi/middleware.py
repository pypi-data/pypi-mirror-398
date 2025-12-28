"""
RossettaMiddleware for FastAPI
Provides end-to-end encryption for all API requests
"""

import json
import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send

from .crypto import (
    generate_keypair,
    export_public_key,
    import_public_key,
    derive_shared_key,
    encrypt,
    decrypt,
)
from .session import SessionManager


class RossettaMiddleware:
    """
    FastAPI middleware for end-to-end encryption
    
    Add this middleware to your FastAPI app with a single line:
    app.add_middleware(RossettaMiddleware)
    """
    
    def __init__(
        self,
        app: ASGIApp,
        session_duration: int = 3600,
        max_timestamp_drift: int = 300,
    ):
        """
        Initialize middleware
        
        Args:
            app: FastAPI application
            session_duration: Session duration in seconds (default: 1 hour)
            max_timestamp_drift: Max allowed timestamp drift in seconds (default: 5 minutes)
        """
        self.app = app
        self.server_private_key, self.server_public_key = generate_keypair()
        self.session_manager = SessionManager(session_duration)
        self.max_timestamp_drift = max_timestamp_drift
        
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ASGI application interface"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        # Handle handshake and encrypted requests
        await self.handle_http(scope, receive, send)
        
    async def handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle HTTP requests"""
        from starlette.requests import Request
        from starlette.datastructures import Headers
        
        # Create request object
        request = Request(scope, receive)
        path = scope.get("path", "")
        
        # Handle key exchange handshake
        if path == "/__rossetta_handshake__":
            await self._handle_handshake_asgi(scope, receive, send)
            return
            
        # Check if request is encrypted
        headers = Headers(scope=scope)
        if headers.get("X-Rossetta-Encrypted") != "true":
            # Pass through non-encrypted requests
            await self.app(scope, receive, send)
            return
            
        try:
            # Read the encrypted body
            body = bytearray()
            while True:
                message = await receive()
                if message['type'] == 'http.request':
                    body.extend(message.get('body', b''))
                    if not message.get('more_body', False):
                        break
            
            encrypted_data = json.loads(body.decode('utf-8'))
            ciphertext = encrypted_data['ciphertext']
            iv = encrypted_data['iv']
            
            # Get session - use client IP as session ID
            # In production, consider using a more robust session token system
            client_info = scope.get('client', None)
            if client_info and len(client_info) > 0:
                session_id = client_info[0]  # Client IP
            else:
                # Fallback - generate from connection details or fail
                await self._send_json_response(
                    send,
                    {"error": "Unable to identify client session"},
                    401
                )
                return
                
            session = self.session_manager.get_session(session_id)
            
            if not session:
                await self._send_json_response(
                    send,
                    {"error": "No valid session. Please establish handshake first."},
                    401
                )
                return
                
            # Decrypt request payload
            decrypted = decrypt(session.shared_key, ciphertext, iv)
            payload = json.loads(decrypted)
            
            # Validate timestamp
            timestamp = payload.get('timestamp', 0)
            current_time = time.time() * 1000
            if abs(current_time - timestamp) > (self.max_timestamp_drift * 1000):
                await self._send_json_response(
                    send,
                    {"error": "Request timestamp out of allowed range"},
                    400
                )
                return
                
            # Validate nonce
            nonce = payload.get('nonce')
            if not nonce or not self.session_manager.validate_nonce(nonce):
                await self._send_json_response(
                    send,
                    {"error": "Invalid or duplicate nonce"},
                    400
                )
                return
            
            # Reconstruct the original request
            original_method = payload.get('method', 'GET')
            original_headers = payload.get('headers', {})
            original_body = payload.get('body')
            
            # Modify scope
            scope['method'] = original_method
            
            # Rebuild headers
            new_headers = []
            for key, value in scope.get('headers', []):
                header_name = key.decode('utf-8').lower()
                if header_name not in ['x-rossetta-encrypted', 'content-length']:
                    new_headers.append((key, value))
            
            # Add original headers
            if original_headers:
                for key, value in original_headers.items():
                    if key.lower() not in ['x-rossetta-encrypted']:
                        new_headers.append((key.lower().encode(), str(value).encode()))
            
            # Add content-length
            body_bytes = b''
            if original_body:
                # Ensure body is properly encoded
                if isinstance(original_body, str):
                    body_bytes = original_body.encode('utf-8')
                elif isinstance(original_body, bytes):
                    body_bytes = original_body
                else:
                    # For other types (dict, list, etc.), serialize to JSON
                    body_bytes = json.dumps(original_body).encode('utf-8')
                new_headers.append((b'content-length', str(len(body_bytes)).encode()))
            else:
                new_headers.append((b'content-length', b'0'))
            
            scope['headers'] = new_headers
            
            # Create receive function for the decrypted body
            body_sent = False
            
            async def receive_modified():
                nonlocal body_sent
                if not body_sent:
                    body_sent = True
                    return {
                        'type': 'http.request',
                        'body': body_bytes,
                        'more_body': False,
                    }
                return {
                    'type': 'http.request',
                    'body': b'',
                    'more_body': False,
                }
            
            # Create send function to capture response
            response_started = False
            response_status = 200
            response_headers = []
            response_body = bytearray()
            
            async def send_capture(message):
                nonlocal response_started, response_status, response_headers, response_body
                
                if message['type'] == 'http.response.start':
                    response_started = True
                    response_status = message['status']
                    response_headers = message.get('headers', [])
                elif message['type'] == 'http.response.body':
                    response_body.extend(message.get('body', b''))
            
            # Call the app with modified scope and receive
            await self.app(scope, receive_modified, send_capture)
            
            # Encrypt and send response
            try:
                response_data = json.loads(response_body.decode('utf-8'))
            except:
                response_data = response_body.decode('utf-8')
            
            response_payload = {
                'status': response_status,
                'statusText': 'OK' if response_status == 200 else 'Error',
                'headers': {k.decode('utf-8'): v.decode('utf-8') for k, v in response_headers},
                'body': response_data,
            }
            
            encrypted_response = encrypt(session.shared_key, json.dumps(response_payload))
            
            await self._send_json_response(
                send,
                {
                    'ciphertext': encrypted_response[0],
                    'iv': encrypted_response[1],
                },
                200
            )
            
        except Exception as e:
            # Use proper logging instead of print in production
            import logging
            logger = logging.getLogger("rossetta_fastapi")
            logger.error(f"Encryption/decryption error: {str(e)}", exc_info=True)
            
            await self._send_json_response(
                send,
                {"error": "Request processing error"},  # Don't expose internal details
                400
            )
            
    async def _handle_handshake_asgi(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle ECDH key exchange handshake"""
        try:
            # Read request body
            body = bytearray()
            while True:
                message = await receive()
                if message['type'] == 'http.request':
                    body.extend(message.get('body', b''))
                    if not message.get('more_body', False):
                        break
            
            data = json.loads(body.decode('utf-8'))
            client_public_key_b64 = data.get('client_public_key')
            
            if not client_public_key_b64:
                await self._send_json_response(
                    send,
                    {"error": "Missing client_public_key"},
                    400
                )
                return
                
            # Import client's public key
            client_public_key = import_public_key(client_public_key_b64)
            
            # Derive shared secret
            shared_key = derive_shared_key(self.server_private_key, client_public_key)
            
            # Create session (use client IP as session ID)
            client_info = scope.get('client', None)
            if client_info and len(client_info) > 0:
                session_id = client_info[0]  # Client IP
            else:
                await self._send_json_response(
                    send,
                    {"error": "Unable to identify client for session"},
                    400
                )
                return
                
            self.session_manager.create_session(session_id, shared_key)
            
            # Return server's public key
            server_public_key_b64 = export_public_key(self.server_public_key)
            
            await self._send_json_response(
                send,
                {'server_public_key': server_public_key_b64},
                200
            )
            
        except Exception as e:
            await self._send_json_response(
                send,
                {"error": f"Handshake error: {str(e)}"},
                400
            )
    
    async def _send_json_response(self, send: Send, content: dict, status: int = 200) -> None:
        """Send JSON response"""
        body = json.dumps(content).encode('utf-8')
        
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [
                (b'content-type', b'application/json'),
                (b'content-length', str(len(body)).encode()),
            ],
        })
        
        await send({
            'type': 'http.response.body',
            'body': body,
        })
