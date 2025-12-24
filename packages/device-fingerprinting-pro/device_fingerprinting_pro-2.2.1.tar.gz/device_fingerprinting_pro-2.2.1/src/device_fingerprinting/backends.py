"""
Abstract base classes for pluggable backends.

Defines interfaces for crypto, storage, and security checks
that applications can implement with their own backends.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from .hybrid_pqc import HybridPQC


class CryptoBackend(ABC):
    """Interface for cryptographic operations"""

    @abstractmethod
    def sign(self, data: bytes) -> str:
        """Create signature for data"""
        pass

    @abstractmethod
    def verify(self, signature: str, data: bytes) -> bool:
        """Verify signature against data"""
        pass


class StorageBackend(ABC):
    """Interface for secure storage operations"""

    @abstractmethod
    def store(self, key: str, data: Dict[str, Any]) -> bool:
        """Store data under key"""
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data by key"""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete data by key"""
        pass


class SecurityCheck(ABC):
    """Interface for runtime security checks"""

    @abstractmethod
    def check(self) -> Tuple[bool, str]:
        """Run security check, return (is_suspicious, reason)"""
        pass


# --- Backend Factory ---

# Import default implementations
from .default_backends import HmacSha256Backend, InMemoryStorage, NoOpSecurityCheck

# A simple registry for backends
_backend_registry = {
    "crypto": HmacSha256Backend,
    "storage": InMemoryStorage,
    "security": NoOpSecurityCheck,
}


def enable_post_quantum_crypto():
    """Switches the active crypto backend to the Hybrid PQC implementation."""
    _backend_registry["crypto"] = HybridPQC


class _DummyScreenResolutionBackend:
    """A dummy backend to satisfy imports until a real one is found."""

    def get(self) -> Optional[Tuple[int, int]]:
        try:
            # This is a placeholder. A real implementation would use a library
            # like 'screeninfo' or platform-specific APIs.
            return (1920, 1080)
        except Exception:
            return None


_backend_registry["screen_resolution"] = _DummyScreenResolutionBackend


def get_backend(name: str) -> Any:
    """
    Factory function to get a backend instance by name.

    Args:
        name: The name of the backend to retrieve.

    Returns:
        An instance of the requested backend.

    Raises:
        ValueError: If the backend name is not found.
    """
    backend_class = _backend_registry.get(name)
    if backend_class:
        return backend_class()

    raise ValueError(f"Unknown backend: '{name}'")
