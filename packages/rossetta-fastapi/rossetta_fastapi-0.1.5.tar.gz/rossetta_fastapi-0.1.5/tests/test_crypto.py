"""
Unit tests for rossetta-fastapi
"""

import pytest
from rossetta_fastapi.crypto import (
    generate_keypair,
    export_public_key,
    import_public_key,
    derive_shared_key,
    encrypt,
    decrypt,
)
from rossetta_fastapi.session import SessionManager
import time


def test_generate_keypair():
    """Test ECDH key pair generation"""
    private_key, public_key = generate_keypair()
    assert private_key is not None
    assert public_key is not None


def test_export_import_public_key():
    """Test public key export and import"""
    _, public_key = generate_keypair()
    exported = export_public_key(public_key)
    
    assert isinstance(exported, str)
    assert len(exported) > 0
    
    # Import it back
    imported = import_public_key(exported)
    assert imported is not None


def test_key_derivation():
    """Test ECDH key derivation"""
    # Generate two key pairs (simulating client and server)
    client_private, client_public = generate_keypair()
    server_private, server_public = generate_keypair()
    
    # Both parties derive the same shared secret
    client_shared = derive_shared_key(client_private, server_public)
    server_shared = derive_shared_key(server_private, client_public)
    
    assert client_shared == server_shared


def test_encryption_decryption():
    """Test encryption and decryption"""
    # Generate a shared key
    client_private, client_public = generate_keypair()
    server_private, server_public = generate_keypair()
    shared_key = derive_shared_key(client_private, server_public)
    
    # Encrypt a message
    message = "Hello, encrypted world!"
    ciphertext, iv = encrypt(shared_key, message)
    
    assert isinstance(ciphertext, str)
    assert isinstance(iv, str)
    assert len(ciphertext) > 0
    assert len(iv) > 0
    
    # Decrypt the message
    decrypted = decrypt(shared_key, ciphertext, iv)
    assert decrypted == message


def test_encryption_with_different_keys_fails():
    """Test that decryption fails with wrong key"""
    # Generate two different shared keys
    key1_private, key1_public = generate_keypair()
    key2_private, key2_public = generate_keypair()
    shared_key1 = derive_shared_key(key1_private, key2_public)
    
    key3_private, key3_public = generate_keypair()
    key4_private, key4_public = generate_keypair()
    shared_key2 = derive_shared_key(key3_private, key4_public)
    
    # Encrypt with one key
    message = "Secret message"
    ciphertext, iv = encrypt(shared_key1, message)
    
    # Try to decrypt with different key - should fail
    with pytest.raises(Exception):
        decrypt(shared_key2, ciphertext, iv)


def test_session_manager_create_get():
    """Test session creation and retrieval"""
    manager = SessionManager()
    
    _, public_key = generate_keypair()
    shared_key = b"test_shared_key_32_bytes_long!!"
    
    manager.create_session("session1", shared_key)
    session = manager.get_session("session1")
    
    assert session is not None
    assert session.shared_key == shared_key


def test_session_expiration():
    """Test session expiration"""
    manager = SessionManager(session_duration=1)  # 1 second
    
    shared_key = b"test_shared_key_32_bytes_long!!"
    manager.create_session("session1", shared_key)
    
    # Should exist immediately
    assert manager.get_session("session1") is not None
    
    # Wait for expiration
    time.sleep(2)
    
    # Should be expired now
    assert manager.get_session("session1") is None


def test_nonce_validation():
    """Test nonce validation for replay attack prevention"""
    manager = SessionManager()
    
    # First use of nonce should be valid
    assert manager.validate_nonce("nonce1") is True
    
    # Second use of same nonce should be invalid
    assert manager.validate_nonce("nonce1") is False
    
    # Different nonce should be valid
    assert manager.validate_nonce("nonce2") is True


def test_nonce_expiration():
    """Test nonce expiration"""
    manager = SessionManager()
    
    # Use a nonce
    assert manager.validate_nonce("nonce1") is True
    
    # Manually expire nonces
    manager.nonces["nonce1"] = time.time() - 400  # 400 seconds ago
    
    # Should be cleaned up and allow reuse
    assert manager.validate_nonce("nonce1") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
