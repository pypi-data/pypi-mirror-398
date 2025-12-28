"""
Rossetta FastAPI Middleware
End-to-end encryption middleware for FastAPI applications
"""

from .middleware import RossettaMiddleware
from .crypto import generate_keypair, derive_shared_key

__version__ = "0.1.5"
__all__ = ["RossettaMiddleware", "generate_keypair", "derive_shared_key"]
