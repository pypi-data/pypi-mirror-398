"""
Hardware Security Module (HSM) integration for enterprise-grade key protection.

This module provides a robust and production-ready implementation for integrating
with Hardware Security Modules (HSMs) using the PKCS#11 standard, and simulates
secure enclave storage for protecting sensitive data.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

import PyKCS11
from PyKCS11 import PyKCS11Error, Mechanism, Attribute

from .backends import CryptoBackend, StorageBackend
from .crypto import AESGCMEncryptor, ScryptKDF

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class HSMCryptoBackend(CryptoBackend):
    """
    HSM-backed cryptographic operations using PKCS#11 for maximum security.

    This backend interfaces with HSMs that support the PKCS#11 standard.
    """

    def __init__(self, pkcs11_lib_path: str, user_pin: str, key_label: str) -> None:
        """
        Initialize the HSM crypto backend.

        Args:
            pkcs11_lib_path: Path to the PKCS#11 library file (e.g., softhsm2.dll).
            user_pin: The PIN for the HSM token/slot.
            key_label: The label of the key to be used or created in the HSM.
        """
        self.pkcs11_lib_path = pkcs11_lib_path
        self.user_pin = user_pin
        self.key_label = key_label
        self.session: Optional[PyKCS11.Session] = None
        self.key_handle: Optional[PyKCS11.Object] = None
        self.hsm_available: bool = False
        self._init_hsm()

    def _init_hsm(self) -> None:
        """Initialize the HSM connection and session."""
        try:
            pkcs11 = PyKCS11.PyKCS11Lib()
            pkcs11.load(self.pkcs11_lib_path)

            # Get the first available slot
            slot = pkcs11.getSlotList(tokenPresent=True)[0]

            # Open a session
            self.session = pkcs11.openSession(
                slot, PyKCS11.CKF_SERIAL_SESSION | PyKCS11.CKF_RW_SESSION
            )
            self.session.login(self.user_pin)

            # Find or create the key
            self.key_handle = self._get_or_create_hsm_key()

            if self.key_handle:
                self.hsm_available = True
                logging.info("HSM initialized successfully and key is available.")
            else:
                logging.error("Failed to get or create HSM key.")
                self.session.logout()
        except (PyKCS11Error, IndexError, FileNotFoundError) as e:
            logging.error(f"HSM initialization failed: {e}")
            self.hsm_available = False

    def _get_or_create_hsm_key(self) -> Optional[PyKCS11.Object]:
        """Get or create a symmetric key in the HSM."""
        if not self.session:
            return None

        try:
            # Look for an existing key with the given label
            key = self.session.findObjects(
                [
                    (Attribute.CKA_LABEL, self.key_label),
                    (Attribute.CKA_CLASS, PyKCS11.CKO_SECRET_KEY),
                ]
            )
            if key:
                return key[0]

            # If not found, create a new key
            logging.info(f"Key '{self.key_label}' not found. Creating a new one.")
            key_template = [
                (Attribute.CKA_CLASS, PyKCS11.CKO_SECRET_KEY),
                (Attribute.CKA_KEY_TYPE, PyKCS11.CKK_AES),
                (Attribute.CKA_VALUE_LEN, 32),  # 256-bit AES key
                (Attribute.CKA_LABEL, self.key_label),
                (Attribute.CKA_TOKEN, True),
                (Attribute.CKA_ENCRYPT, True),
                (Attribute.CKA_DECRYPT, True),
                (Attribute.CKA_SENSITIVE, True),
                (Attribute.CKA_EXTRACTABLE, False),
            ]
            return self.session.generateKey(key_template)
        except PyKCS11Error as e:
            logging.error(f"Error accessing HSM key: {e}")
            return None

    def sign(self, data: bytes) -> bytes:
        """Sign data using the HSM (e.g., with HMAC)."""
        if not self.hsm_available or not self.session or not self.key_handle:
            raise RuntimeError("HSM is not available for signing.")

        try:
            hmac_mechanism = Mechanism(PyKCS11.CKM_SHA256_HMAC, None)
            return bytes(self.session.sign(self.key_handle, data, hmac_mechanism))
        except PyKCS11Error as e:
            logging.error(f"HSM signing failed: {e}")
            raise

    def verify(self, signature: bytes, data: bytes) -> bool:
        """Verify a signature using the HSM."""
        if not self.hsm_available or not self.session or not self.key_handle:
            raise RuntimeError("HSM is not available for verification.")

        try:
            hmac_mechanism = Mechanism(PyKCS11.CKM_SHA256_HMAC, None)
            return self.session.verify(self.key_handle, data, signature)
        except PyKCS11Error as e:
            # A verification failure can raise an error
            logging.warning(f"HSM verification failed: {e}")
            return False

    def __del__(self):
        """Clean up the HSM session on object destruction."""
        if self.session:
            self.session.logout()
            self.session.closeSession()
            logging.info("HSM session closed.")


class SecureEnclaveStorage(StorageBackend):
    """
    Simulated secure enclave storage using file-based encryption.

    This class provides a secure storage mechanism by encrypting data before
    writing it to disk, simulating the behavior of a hardware-backed secure enclave.
    """

    def __init__(self, storage_path: str, encryption_key: bytes) -> None:
        """
        Initialize the secure enclave storage.

        Args:
            storage_path: The directory path to store encrypted files.
            encryption_key: The master key for encrypting the stored data.
        """
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path, exist_ok=True)

        # Use Scrypt for key derivation
        salt = os.urandom(16)  # A unique salt should be used per key
        self.kdf = ScryptKDF(salt=salt)
        self.derived_key = self.kdf.derive_key(encryption_key)
        self.encryptor = AESGCMEncryptor(self.derived_key)
        self.enclave_available = True
        logging.info("Secure enclave storage initialized.")

    def _get_file_path(self, key: str) -> str:
        """Generate a secure file path for a given key."""
        safe_key = "".join(c for c in key if c.isalnum() or c in ("-", "_")).rstrip()
        return os.path.join(self.storage_path, f"{safe_key}.enc")

    def store(self, key: str, data: Dict[str, Any]) -> bool:
        """Encrypt and store data in a file."""
        if not self.enclave_available:
            return False

        file_path = self._get_file_path(key)
        try:
            json_data = json.dumps(data, sort_keys=True).encode("utf-8")
            encrypted_data = self.encryptor.encrypt(json_data)

            with open(file_path, "wb") as f:
                f.write(encrypted_data)
            logging.info(f"Successfully stored data for key: {key}")
            return True
        except IOError as e:
            logging.error(f"Failed to write to secure storage for key {key}: {e}")
            return False

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load and decrypt data from a file."""
        if not self.enclave_available:
            return None

        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self.encryptor.decrypt(encrypted_data)
            logging.info(f"Successfully loaded data for key: {key}")
            return json.loads(decrypted_data)
        except (IOError, ValueError) as e:
            logging.error(f"Failed to load or decrypt data for key {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete data from the secure storage."""
        if not self.enclave_available:
            return False

        file_path = self._get_file_path(key)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Successfully deleted data for key: {key}")
                return True
            except OSError as e:
                logging.error(f"Failed to delete data for key {key}: {e}")
                return False
        return True  # Key doesn't exist, so it's "deleted"
