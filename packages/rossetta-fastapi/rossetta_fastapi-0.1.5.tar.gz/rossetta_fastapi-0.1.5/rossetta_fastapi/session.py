"""
Session management for rossetta-fastapi
Handles encryption sessions and key storage
"""

import time
from typing import Dict, Optional
from cryptography.hazmat.primitives.asymmetric import ec


class Session:
    """Represents an encryption session"""
    
    def __init__(self, shared_key: bytes, expires_at: float):
        self.shared_key = shared_key
        self.expires_at = expires_at
        
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return time.time() > self.expires_at


class SessionManager:
    """Manages encryption sessions"""
    
    def __init__(self, session_duration: int = 3600):
        """
        Initialize session manager
        
        Args:
            session_duration: Session duration in seconds (default: 1 hour)
        """
        self.sessions: Dict[str, Session] = {}
        self.session_duration = session_duration
        self.nonces: Dict[str, float] = {}  # For replay attack prevention
        
    def create_session(self, session_id: str, shared_key: bytes) -> None:
        """Create a new session"""
        expires_at = time.time() + self.session_duration
        self.sessions[session_id] = Session(shared_key, expires_at)
        
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session if exists and not expired"""
        session = self.sessions.get(session_id)
        if session and not session.is_expired():
            return session
        elif session:
            # Clean up expired session
            del self.sessions[session_id]
        return None
        
    def validate_nonce(self, nonce: str, max_age: int = 300) -> bool:
        """
        Validate nonce to prevent replay attacks
        
        Args:
            nonce: The nonce to validate
            max_age: Maximum age in seconds for a nonce (default: 5 minutes)
            
        Returns:
            True if nonce is valid (not seen before or expired), False otherwise
        """
        current_time = time.time()
        
        # Clean up old nonces
        self.nonces = {
            n: t for n, t in self.nonces.items()
            if current_time - t < max_age
        }
        
        # Check if nonce was already used
        if nonce in self.nonces:
            return False
            
        # Store nonce with timestamp
        self.nonces[nonce] = current_time
        return True
        
    def cleanup_expired(self) -> None:
        """Remove expired sessions"""
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired()
        ]
        for sid in expired:
            del self.sessions[sid]
