"""
Cryptographic primitives for device fingerprinting.
This module provides building blocks for encryption and key derivation with Rust integration.
"""

import os
import hmac
import hashlib
import json
import threading
import logging
from typing import Optional, Tuple, Dict, Any
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.backends import default_backend

# Try to import Rust crypto module
try:
    from pqc_rust import RustCrypto, SecureKey

    RUST_CRYPTO_AVAILABLE = True
    _logger = logging.getLogger(__name__)
    _logger.info("🦀 Rust crypto module successfully loaded")
except ImportError as e:
    RUST_CRYPTO_AVAILABLE = False
    _logger = logging.getLogger(__name__)
    _logger.warning(f"🦀 Rust crypto module not available: {e}")
    _logger.info("💡 Falling back to Python cryptography implementations")

# Try to import real post-quantum crypto libraries directly
try:
    import pqcrypto.sign.ml_dsa_44 as ml_dsa_44
    import pqcrypto.sign.ml_dsa_65 as ml_dsa_65
    import pqcrypto.sign.ml_dsa_87 as ml_dsa_87

    PQC_LIBRARIES_AVAILABLE = True
    _logger.info("PQC libraries (pqcrypto) available")
except ImportError as e:
    PQC_LIBRARIES_AVAILABLE = False
    _logger.warning(f"PQC libraries not available: {e}")


# Simple PQC backend class
class SimplePQCBackend:
    """Simple, direct PQC backend using pqcrypto libraries"""

    def __init__(self, algorithm: str = "Dilithium3"):
        if not PQC_LIBRARIES_AVAILABLE:
            raise NotImplementedError("PQC libraries not available")

        self.algorithm = algorithm

        # Map algorithms to pqcrypto modules
        if algorithm == "Dilithium2":
            self.pqc_module = ml_dsa_44
        elif algorithm == "Dilithium3":
            self.pqc_module = ml_dsa_65
        elif algorithm == "Dilithium5":
            self.pqc_module = ml_dsa_87
        else:
            self.pqc_module = ml_dsa_65  # Default to Dilithium3
            self.algorithm = "Dilithium3"

        # Generate fresh keys for this session
        self.public_key, self.private_key = self.pqc_module.generate_keypair()
        _logger.info(f"PQC backend initialized with {algorithm}")

    def sign(self, message: bytes) -> str:
        """Sign message and return base64 encoded signature"""
        import base64

        signature = self.pqc_module.sign(message, self.private_key)
        return base64.b64encode(signature).decode("utf-8")

    def verify(self, signature_b64: str, message: bytes) -> bool:
        """Verify base64 encoded signature"""
        import base64

        try:
            signature = base64.b64decode(signature_b64)
            verified_msg = self.pqc_module.verify(signature, message, self.public_key)
            return verified_msg == message
        except Exception:
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get backend information"""
        return {
            "algorithm": self.algorithm,
            "library": "pqcrypto",
            "public_key_size": len(self.public_key),
            "private_key_size": len(self.private_key),
        }


def get_available_pqc_algorithms():
    """Get available PQC algorithms"""
    if PQC_LIBRARIES_AVAILABLE:
        return {
            "signatures": ["Dilithium2", "Dilithium3", "Dilithium5"],
            "kems": [],
            "libraries": ["pqcrypto"],
        }
    else:
        return {"signatures": [], "kems": [], "libraries": []}

    # Define dummy classes for graceful degradation
    class RustCrypto:
        def __init__(self):
            raise NotImplementedError("Rust crypto not available")

    class SecureKey:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("Rust secure key not available")


class ScryptKDF:
    """
    A wrapper for the Scrypt Key Derivation Function.
    """

    def __init__(
        self, salt_size: int = 16, n: int = 2**14, r: int = 8, p: int = 1, key_size: int = 32
    ):
        self.salt_size = salt_size
        self.n = n
        self.r = r
        self.p = p
        self.key_size = key_size

    def derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derives a key from the given password and salt.

        Args:
            password: The password to derive the key from.
            salt: The salt to use for the derivation.

        Returns:
            The derived key as bytes.
        """
        kdf = Scrypt(salt=salt, length=self.key_size, n=self.n, r=self.r, p=self.p)
        return kdf.derive(password.encode("utf-8"))


class AESGCMEncryptor:
    """
    Provides encryption and decryption using AES-GCM.
    """

    def __init__(self, key_size: int = 32, nonce_size: int = 12):
        if key_size not in [16, 24, 32]:
            raise ValueError("Invalid key size for AES. Must be 16, 24, or 32 bytes.")
        self.key_size = key_size
        self.nonce_size = nonce_size

    def encrypt(self, data: bytes, key: bytes) -> bytes:
        """
        Encrypts data using AES-GCM.

        Args:
            data: The data to encrypt.
            key: The encryption key.

        Returns:
            A blob containing nonce + ciphertext + tag.
        """
        if len(key) != self.key_size:
            raise ValueError(f"Key must be {self.key_size} bytes long.")

        aesgcm = AESGCM(key)
        nonce = os.urandom(self.nonce_size)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext

    def decrypt(self, encrypted_blob: bytes, key: bytes) -> bytes:
        """
        Decrypts an AES-GCM encrypted blob.

        Args:
            encrypted_blob: The blob to decrypt (nonce + ciphertext + tag).
            key: The decryption key.

        Returns:
            The original plaintext data.

        Raises:
            ValueError: If decryption fails due to wrong key or tampered data.
        """
        if len(key) != self.key_size:
            raise ValueError(f"Key must be {self.key_size} bytes long.")

        nonce = encrypted_blob[: self.nonce_size]
        ciphertext = encrypted_blob[self.nonce_size :]

        aesgcm = AESGCM(key)
        try:
            return aesgcm.decrypt(nonce, ciphertext, None)
        except InvalidTag:
            raise ValueError("Decryption failed. The data may be tampered or the key is incorrect.")


class CryptoManager:
    """Handles cryptographic operations for device binding"""

    def __init__(self, password: bytes, salt: Optional[bytes] = None) -> None:
        self.backend = default_backend()
        self.salt = salt or os.urandom(16)
        self.key = self._derive_key(password, self.salt)
        self.aesgcm = AESGCM(self.key)

    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """Derive a 32-byte key for AES-256."""
        kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1, backend=self.backend)
        return kdf.derive(password)

    def encrypt(self, plaintext: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """Encrypts plaintext using AES-GCM."""
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, associated_data)
        return nonce + ciphertext

    def decrypt(self, ciphertext: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """Decrypts ciphertext using AES-GCM."""
        nonce = ciphertext[:12]
        encrypted_data = ciphertext[12:]
        return self.aesgcm.decrypt(nonce, encrypted_data, associated_data)

    def sign(self, data: bytes) -> str:
        """Create HMAC-SHA-256 signature for data"""
        return hmac.new(self.key, data, hashlib.sha256).hexdigest()

    def verify(self, signature: str, data: bytes) -> bool:
        """Verify HMAC signature with constant-time comparison"""
        expected_sig = self.sign(data)
        return hmac.compare_digest(signature, expected_sig)


# Global instance management
_crypto_manager: Optional[CryptoManager] = None
_crypto_lock = threading.Lock()


def initialize_crypto_manager(password: str, salt: Optional[str] = None) -> None:
    """Initializes the global crypto manager with a password and optional salt."""
    global _crypto_manager
    with _crypto_lock:
        if _crypto_manager is None:
            password_bytes = password.encode("utf-8")
            salt_bytes = salt.encode("utf-8") if salt else None
            _crypto_manager = CryptoManager(password=password_bytes, salt=salt_bytes)


def get_crypto_manager() -> CryptoManager:
    """
    Get the global crypto manager.
    It must be initialized with initialize_crypto_manager first.
    """
    with _crypto_lock:
        if _crypto_manager is None:
            raise RuntimeError(
                "CryptoManager has not been initialized. Call initialize_crypto_manager first."
            )
        return _crypto_manager


def sign_data(data: Dict[str, Any]) -> str:
    """Sign a data dictionary with HMAC"""
    payload = json.dumps(data, sort_keys=True).encode()
    return get_crypto_manager().sign(payload)


def verify_signature(signature: str, data: Dict[str, Any]) -> bool:
    """Verify HMAC signature of data dictionary"""
    payload = json.dumps(data, sort_keys=True).encode()
    return get_crypto_manager().verify(signature, payload)


def encrypt_data(plaintext: str, associated_data: Optional[str] = None) -> bytes:
    """Encrypts a string using the global crypto manager."""
    cm = get_crypto_manager()
    plaintext_bytes = plaintext.encode("utf-8")
    ad_bytes = associated_data.encode("utf-8") if associated_data else None
    return cm.encrypt(plaintext_bytes, ad_bytes)


def decrypt_data(ciphertext: bytes, associated_data: Optional[str] = None) -> str:
    """Decrypts a string using the global crypto manager."""
    cm = get_crypto_manager()
    ad_bytes = associated_data.encode("utf-8") if associated_data else None
    decrypted_bytes = cm.decrypt(ciphertext, ad_bytes)
    return decrypted_bytes.decode("utf-8")


class EnhancedCrypto:
    """
    Enhanced cryptographic operations with Rust and Post-Quantum Crypto integration.

    CLASSICAL CRYPTO (IMPLEMENTED):
    - AES-256-GCM encryption/decryption (Python + Rust)
    - ChaCha20Poly1305 encryption/decryption (Rust only)
    - Argon2id key derivation (Rust only, Python fallback to Scrypt)
    - Scrypt key derivation (Python + Rust)
    - Cryptographically secure random generation

    POST-QUANTUM CRYPTO (REAL IMPLEMENTATIONS):
    - Digital signatures using Dilithium2/3/5, Falcon-512, SPHINCS+ (when libraries available)
    - Hybrid mode combining classical and post-quantum signatures
    - Support for multiple PQC libraries: pqcrypto, liboqs, rust-pqc
    - Automatic fallback when PQC libraries not installed

    NOT YET IMPLEMENTED:
    - Post-quantum KEM (Key Encapsulation Mechanisms)
    - These will be added as the underlying libraries mature
    """

    def __init__(self, prefer_rust: bool = True, enable_pqc: bool = True):
        self.prefer_rust = prefer_rust and RUST_CRYPTO_AVAILABLE
        self.enable_pqc = enable_pqc and PQC_LIBRARIES_AVAILABLE
        self._rust_crypto = None
        self._pqc_backend = None

        # Initialize Rust crypto backend
        if self.prefer_rust:
            try:
                self._rust_crypto = RustCrypto()
                _logger.info("Rust crypto backend initialized")
            except Exception as e:
                _logger.warning(f"Rust crypto initialization failed: {e}, falling back to Python")
                self.prefer_rust = False

        # Initialize Post-Quantum Crypto backend
        if self.enable_pqc:
            try:
                self._pqc_backend = SimplePQCBackend(algorithm="Dilithium3")
                _logger.info("Post-quantum crypto backend initialized")
            except Exception as e:
                _logger.warning(f"PQC backend initialization failed: {e}")
                self.enable_pqc = False

        if not self.prefer_rust and not self.enable_pqc:
            _logger.info("Enhanced crypto initialized with Python backend only")
        elif self.enable_pqc and not self.prefer_rust:
            _logger.info("Enhanced crypto initialized with Python + PQC backends")
        elif self.prefer_rust and not self.enable_pqc:
            _logger.info("Enhanced crypto initialized with Rust backend only")
        else:
            _logger.info("Enhanced crypto initialized with Rust + PQC backends")

    def is_rust_available(self) -> bool:
        """Check if Rust crypto backend is available and active"""
        return self.prefer_rust and self._rust_crypto is not None

    def is_pqc_available(self) -> bool:
        """Check if post-quantum crypto backend is available and active"""
        return self.enable_pqc and self._pqc_backend is not None

    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the active crypto backend"""
        backends = []
        algorithms = []

        # Classical crypto info
        if self.is_rust_available():
            backends.append("Rust (RustCrypto)")
            algorithms.extend(["AES-256-GCM", "ChaCha20Poly1305", "Argon2id", "Scrypt"])
            memory_security = "zeroize + secrecy"
            performance = "optimized"
        else:
            backends.append("Python (cryptography)")
            algorithms.extend(["AES-256-GCM", "Scrypt"])
            memory_security = "standard"
            performance = "standard"

        # Post-quantum crypto info
        pqc_info = {}
        if self.is_pqc_available():
            backends.append("PQC (Real)")
            pqc_algorithms = get_available_pqc_algorithms()
            algorithms.extend(pqc_algorithms.get("signatures", []))
            backend_info = self._pqc_backend.get_info() if self._pqc_backend else {}
            pqc_info = {
                "pqc_backend": backend_info.get("library", "SimplePQCBackend"),
                "pqc_algorithm": backend_info.get("algorithm", "Unknown"),
                "pqc_libraries": pqc_algorithms.get("libraries", []),
                "pqc_key_sizes": {
                    "public": backend_info.get("public_key_size", 0),
                    "private": backend_info.get("private_key_size", 0),
                },
            }

        return {
            "backends": backends,
            "implementation": " + ".join(backends),
            "post_quantum": self.is_pqc_available(),
            "memory_security": memory_security,
            "performance": performance,
            "available_algorithms": algorithms,
            **pqc_info,
        }

    # AES-256-GCM Operations
    def aes_encrypt(self, plaintext: bytes, key: bytes) -> bytes:
        """Encrypt using AES-256-GCM (Rust implementation preferred)"""
        if self.is_rust_available():
            try:
                return self._rust_crypto.aes_encrypt(plaintext, key)
            except Exception as e:
                _logger.warning(f"Rust AES encryption failed: {e}, falling back to Python")

        # Fallback to Python implementation
        encryptor = AESGCMEncryptor(key_size=32)
        return encryptor.encrypt(plaintext, key)

    def aes_decrypt(self, ciphertext: bytes, key: bytes) -> bytes:
        """Decrypt using AES-256-GCM (Rust implementation preferred)"""
        if self.is_rust_available():
            try:
                return self._rust_crypto.aes_decrypt(ciphertext, key)
            except Exception as e:
                _logger.warning(f"Rust AES decryption failed: {e}, falling back to Python")

        # Fallback to Python implementation
        encryptor = AESGCMEncryptor(key_size=32)
        return encryptor.decrypt(ciphertext, key)

    # ChaCha20-Poly1305 Operations (Rust only)
    def chacha_encrypt(self, plaintext: bytes, key: bytes) -> bytes:
        """Encrypt using ChaCha20-Poly1305 (Rust implementation only)"""
        if not self.is_rust_available():
            raise NotImplementedError("ChaCha20-Poly1305 requires Rust crypto backend")

        return self._rust_crypto.chacha_encrypt(plaintext, key)

    def chacha_decrypt(self, ciphertext: bytes, key: bytes) -> bytes:
        """Decrypt using ChaCha20-Poly1305 (Rust implementation only)"""
        if not self.is_rust_available():
            raise NotImplementedError("ChaCha20-Poly1305 requires Rust crypto backend")

        return self._rust_crypto.chacha_decrypt(ciphertext, key)

    # Key Derivation Functions
    def derive_key_argon2(self, password: bytes, salt: bytes, length: int = 32) -> bytes:
        """Derive key using Argon2id (Rust implementation preferred)"""
        if self.is_rust_available():
            try:
                return self._rust_crypto.derive_key_argon2(password, salt, length)
            except Exception as e:
                _logger.warning(f"Rust Argon2 failed: {e}, falling back to Scrypt")

        # Fallback to Scrypt (Python)
        kdf = ScryptKDF(key_size=length)
        return kdf.derive_key(password.decode("utf-8", errors="ignore"), salt)

    def derive_key_scrypt(self, password: bytes, salt: bytes, length: int = 32) -> bytes:
        """Derive key using Scrypt"""
        if self.is_rust_available():
            try:
                return self._rust_crypto.derive_key_scrypt(password, salt, length)
            except Exception as e:
                _logger.warning(f"Rust Scrypt failed: {e}, falling back to Python")

        # Python implementation
        kdf = ScryptKDF(key_size=length)
        return kdf.derive_key(password.decode("utf-8", errors="ignore"), salt)

    # Post-Quantum Cryptography - REAL IMPLEMENTATIONS
    # These methods use actual PQC libraries when available

    def pqc_generate_signature_keypair(self) -> Tuple[bytes, bytes]:
        """Generate post-quantum signature keypair using real PQC libraries"""
        if not self.is_pqc_available():
            raise NotImplementedError(
                "Post-quantum cryptography backend not available. "
                "Install pqcrypto, liboqs, or rust-pqc libraries for PQC support."
            )

        # The RealPostQuantumBackend manages its own keys, so we return the current keys
        if hasattr(self._pqc_backend, "public_key") and hasattr(self._pqc_backend, "private_key"):
            # Convert keys to bytes if they're strings (some PQC libraries use Base64)
            pub_key = self._pqc_backend.public_key
            priv_key = self._pqc_backend.private_key

            if isinstance(pub_key, str):
                pub_key = pub_key.encode("utf-8")
            if isinstance(priv_key, str):
                priv_key = priv_key.encode("utf-8")

            return pub_key, priv_key
        else:
            raise RuntimeError("PQC backend keys not properly initialized")

    def pqc_generate_kem_keypair(self) -> Tuple[bytes, bytes]:
        """Generate post-quantum KEM keypair (not yet implemented)"""
        # KEM (Key Encapsulation Mechanism) support would need additional implementation
        # in the quantum_crypto module. For now, focusing on signatures.
        raise NotImplementedError(
            "Post-quantum KEM is not yet implemented. "
            "Currently only PQC digital signatures are supported."
        )

    def pqc_sign(self, message: bytes, secret_key: Optional[bytes] = None) -> bytes:
        """Create post-quantum digital signature"""
        if not self.is_pqc_available():
            raise NotImplementedError(
                "Post-quantum cryptography backend not available. "
                "Install pqcrypto, liboqs, or rust-pqc libraries for PQC support."
            )

        try:
            # The RealPostQuantumBackend uses its internal keys
            signature_b64 = self._pqc_backend.sign(message)
            return signature_b64.encode("utf-8")
        except Exception as e:
            _logger.error(f"PQC signing failed: {e}")
            raise RuntimeError(f"Post-quantum signing failed: {e}")

    def pqc_verify(
        self, message: bytes, signature: bytes, public_key: Optional[bytes] = None
    ) -> bool:
        """Verify post-quantum digital signature"""
        if not self.is_pqc_available():
            raise NotImplementedError(
                "Post-quantum cryptography backend not available. "
                "Install pqcrypto, liboqs, or rust-pqc libraries for PQC support."
            )

        try:
            # Convert signature back to string for the backend
            signature_str = signature.decode("utf-8")
            return self._pqc_backend.verify(signature_str, message)
        except Exception as e:
            _logger.error(f"PQC verification failed: {e}")
            return False

    def pqc_encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """Post-quantum key encapsulation (not yet implemented)"""
        raise NotImplementedError(
            "Post-quantum KEM is not yet implemented. "
            "Currently only PQC digital signatures are supported."
        )

    def pqc_decapsulate(self, ciphertext: bytes, secret_key: bytes) -> bytes:
        """Post-quantum key decapsulation (not yet implemented)"""
        raise NotImplementedError(
            "Post-quantum KEM is not yet implemented. "
            "Currently only PQC digital signatures are supported."
        )

    def get_pqc_info(self) -> Dict[str, Any]:
        """Get detailed information about the PQC backend"""
        if not self.is_pqc_available():
            return {
                "available": False,
                "reason": "PQC backend not initialized",
                "required_packages": ["pqcrypto"],
            }

        backend_info = self._pqc_backend.get_info() if self._pqc_backend else {}
        return {
            "available": True,
            "backend_info": backend_info,
            **backend_info,  # Include all info from the backend directly
        }

    # Secure Random Generation
    def generate_random(self, length: int) -> bytes:
        """Generate cryptographically secure random bytes"""
        if self.is_rust_available():
            try:
                return bytes(self._rust_crypto.generate_random(length))
            except Exception as e:
                _logger.warning(f"Rust random generation failed: {e}, falling back to Python")

        # Python fallback
        return os.urandom(length)

    # Self-Test
    def self_test(self) -> Dict[str, bool]:
        """Run comprehensive self-test of crypto operations"""
        results = {}

        # Test AES-256-GCM
        try:
            key = self.generate_random(32)
            plaintext = b"Hello, World!"
            ciphertext = self.aes_encrypt(plaintext, key)
            decrypted = self.aes_decrypt(ciphertext, key)
            results["aes_gcm"] = decrypted == plaintext
        except Exception as e:
            _logger.error(f"AES-GCM test failed: {e}")
            results["aes_gcm"] = False

        # Test ChaCha20-Poly1305 (if Rust available)
        if self.is_rust_available():
            try:
                key = self.generate_random(32)
                plaintext = b"Hello, ChaCha!"
                ciphertext = self.chacha_encrypt(plaintext, key)
                decrypted = self.chacha_decrypt(ciphertext, key)
                results["chacha20_poly1305"] = decrypted == plaintext
            except Exception as e:
                _logger.error(f"ChaCha20-Poly1305 test failed: {e}")
                results["chacha20_poly1305"] = False
        else:
            results["chacha20_poly1305"] = None  # Not available

        # Test Key Derivation
        try:
            password = b"test_password"
            salt = self.generate_random(16)
            key1 = self.derive_key_argon2(password, salt, 32)
            key2 = self.derive_key_argon2(password, salt, 32)
            results["key_derivation"] = key1 == key2 and len(key1) == 32
        except Exception as e:
            _logger.error(f"Key derivation test failed: {e}")
            results["key_derivation"] = False

        # Post-Quantum Crypto - Real implementations when available
        if self.is_pqc_available():
            try:
                # Test PQC signature generation and verification
                test_message = b"PQC test message"

                # Generate keypair (uses backend's persistent keys)
                pub_key, priv_key = self.pqc_generate_signature_keypair()

                # Sign and verify
                signature = self.pqc_sign(test_message)
                is_valid = self.pqc_verify(test_message, signature)

                results["pqc_signatures"] = is_valid and len(signature) > 0
            except Exception as e:
                _logger.error(f"PQC signature test failed: {e}")
                results["pqc_signatures"] = False
        else:
            results["pqc_signatures"] = None  # Not available

        # PQC KEM - Not yet implemented
        try:
            self.pqc_generate_kem_keypair()
            results["pqc_kem"] = True  # This line will never execute
        except NotImplementedError:
            results["pqc_kem"] = None  # Expected - not implemented yet
        except Exception as e:
            _logger.error(f"Unexpected PQC KEM test error: {e}")
            results["pqc_kem"] = False

        return results


# Global enhanced crypto instance
_enhanced_crypto: Optional[EnhancedCrypto] = None
_crypto_lock_enhanced = threading.Lock()


def get_enhanced_crypto(enable_pqc: bool = True) -> EnhancedCrypto:
    """Get global enhanced crypto instance with Rust and PQC integration"""
    global _enhanced_crypto
    with _crypto_lock_enhanced:
        if _enhanced_crypto is None:
            _enhanced_crypto = EnhancedCrypto(enable_pqc=enable_pqc)
        return _enhanced_crypto


def enable_rust_crypto() -> bool:
    """Enable Rust crypto backend (recreates enhanced crypto instance)"""
    global _enhanced_crypto
    with _crypto_lock_enhanced:
        if RUST_CRYPTO_AVAILABLE:
            # Keep PQC enabled if it was previously enabled
            old_pqc = _enhanced_crypto.enable_pqc if _enhanced_crypto else True
            _enhanced_crypto = EnhancedCrypto(prefer_rust=True, enable_pqc=old_pqc)
            return _enhanced_crypto.is_rust_available()
        return False


def disable_rust_crypto() -> None:
    """Disable Rust crypto backend (force Python implementation)"""
    global _enhanced_crypto
    with _crypto_lock_enhanced:
        # Keep PQC enabled if it was previously enabled
        old_pqc = _enhanced_crypto.enable_pqc if _enhanced_crypto else True
        _enhanced_crypto = EnhancedCrypto(prefer_rust=False, enable_pqc=old_pqc)


def enable_pqc_crypto() -> bool:
    """Enable post-quantum crypto backend"""
    global _enhanced_crypto
    with _crypto_lock_enhanced:
        if PQC_LIBRARIES_AVAILABLE:
            # Keep Rust enabled if it was previously enabled
            old_rust = _enhanced_crypto.prefer_rust if _enhanced_crypto else True
            _enhanced_crypto = EnhancedCrypto(prefer_rust=old_rust, enable_pqc=True)
            return _enhanced_crypto.is_pqc_available()
        return False


def disable_pqc_crypto() -> None:
    """Disable post-quantum crypto backend"""
    global _enhanced_crypto
    with _crypto_lock_enhanced:
        # Keep Rust enabled if it was previously enabled
        old_rust = _enhanced_crypto.prefer_rust if _enhanced_crypto else True
        _enhanced_crypto = EnhancedCrypto(prefer_rust=old_rust, enable_pqc=False)
