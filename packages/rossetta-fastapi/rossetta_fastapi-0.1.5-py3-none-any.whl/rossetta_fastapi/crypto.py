"""
Cryptographic utilities for rossetta-fastapi
Uses cryptography library for encryption/decryption
"""

import base64
import os
from typing import Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend


def generate_keypair() -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    """Generate ECDH key pair for key exchange"""
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    public_key = private_key.public_key()
    return private_key, public_key


def export_public_key(public_key: ec.EllipticCurvePublicKey) -> str:
    """Export public key to base64 string"""
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return base64.b64encode(pem).decode('utf-8')


def import_public_key(base64_key: str) -> ec.EllipticCurvePublicKey:
    """Import public key from base64 string"""
    pem = base64.b64decode(base64_key)
    return serialization.load_der_public_key(pem, default_backend())


def derive_shared_key(
    private_key: ec.EllipticCurvePrivateKey,
    peer_public_key: ec.EllipticCurvePublicKey
) -> bytes:
    """Derive shared secret from ECDH key exchange"""
    shared_key = private_key.exchange(ec.ECDH(), peer_public_key)
    
    # Use HKDF to derive a proper AES key
    derived_key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'rossetta-api',
        backend=default_backend()
    ).derive(shared_key)
    
    return derived_key


def encrypt(key: bytes, data: str) -> Tuple[str, str]:
    """Encrypt data using AES-GCM"""
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    ciphertext = aesgcm.encrypt(iv, data.encode('utf-8'), None)
    
    return (
        base64.b64encode(ciphertext).decode('utf-8'),
        base64.b64encode(iv).decode('utf-8')
    )


def decrypt(key: bytes, ciphertext: str, iv: str) -> str:
    """Decrypt data using AES-GCM"""
    aesgcm = AESGCM(key)
    ciphertext_bytes = base64.b64decode(ciphertext)
    iv_bytes = base64.b64decode(iv)
    
    plaintext = aesgcm.decrypt(iv_bytes, ciphertext_bytes, None)
    return plaintext.decode('utf-8')
