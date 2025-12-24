"""
Default implementations of pluggable backends.

Provides basic implementations that work out of the box
without external dependencies.
"""

import os
import hmac
import hashlib
import json
import secrets
import time
from typing import Dict, Any, Optional, Tuple

from .backends import CryptoBackend, StorageBackend, SecurityCheck


class HmacSha256Backend(CryptoBackend):
    """HMAC-SHA256 crypto backend with enhanced key generation."""

    _default_key: Optional[bytes] = None

    def __init__(self, key: Optional[bytes] = None):
        # Reuse the previously generated default key so that independent backend
        # instances can verify signatures that other instances created.
        if key is not None:
            self.key = key
        elif HmacSha256Backend._default_key is not None:
            self.key = HmacSha256Backend._default_key
        else:
            self.key = self._generate_secure_key()
            HmacSha256Backend._default_key = self.key

    def _generate_secure_key(self) -> bytes:
        """Generate cryptographically secure key with multiple entropy sources"""
        # Gather multiple entropy sources for enhanced security
        system_entropy = os.urandom(32)
        time_entropy = int(time.time() * 1000000).to_bytes(8, "big")
        process_entropy = os.getpid().to_bytes(4, "big")
        random_entropy = secrets.token_bytes(16)

        # Combine all entropy sources
        combined_entropy = system_entropy + time_entropy + process_entropy + random_entropy

        # Use SHA-256 to derive final key from combined entropy
        return hashlib.sha256(combined_entropy).digest()

    def sign(self, data: bytes) -> str:
        return hmac.new(self.key, data, hashlib.sha256).hexdigest()

    def verify(self, signature: str, data: bytes) -> bool:
        expected = self.sign(data)
        return hmac.compare_digest(signature, expected)

    def export_key_info(self) -> str:
        """
        Export key metadata as JSON (not the key itself, for security).

        Returns JSON string with key derivation info.
        """
        key_info = {
            "algorithm": "HMAC-SHA256",
            "key_length": len(self.key) * 8,
            "derived_from": "multi-source-entropy",
            "timestamp": time.time(),
        }
        return json.dumps(key_info)


class InMemoryStorage(StorageBackend):
    """Simple in-memory storage backend"""

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}

    def store(self, key: str, data: Dict[str, Any]) -> bool:
        try:
            self._data[key] = data.copy()
            return True
        except Exception:
            return False

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False


class NoOpSecurityCheck(SecurityCheck):
    """No-op security check for default behavior"""

    def check(self) -> Tuple[bool, str]:
        return False, "no_checks_enabled"
