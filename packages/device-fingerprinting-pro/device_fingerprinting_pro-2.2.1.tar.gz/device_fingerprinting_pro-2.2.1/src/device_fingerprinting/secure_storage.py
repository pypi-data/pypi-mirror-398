"""
Secure storage utilities for device binding tokens.

Handles platform-specific secure storage of sensitive data.
Falls back gracefully when secure storage is not available.
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List

from .crypto import AESGCMEncryptor, ScryptKDF, InvalidTag

# Try to import keyring, but don't make it a hard dependency
try:
    import keyring
except ImportError:
    keyring = None


class SecureStorage:
    """
    Manages encrypted storage of key-value data in a file, with optional
    integration with the system's secret management service (keyring).
    """

    def __init__(
        self, file_path: str, password: Optional[str] = None, key_iterations: int = 100_000
    ):
        """
        Initializes the secure storage.

        Args:
            file_path: The path to the file where data will be stored.
            password: The password to use for encryption. If not provided,
                      the system's keyring will be used as a fallback.
            key_iterations: The number of iterations for the key derivation function.
        """
        self.file_path = file_path
        self.key_iterations = key_iterations
        self._password = password
        self._encryptor = None
        self.data: Dict[str, Any] = {}

        if not self._password and keyring:
            self._password = self._get_password_from_keyring()

        if not self._password:
            raise ValueError(
                "A password must be provided if the system keyring is not available or contains no password."
            )

        self._setup_encryptor()

        if os.path.exists(self.file_path):
            self.load()
        else:
            # New storage, set password in keyring if possible
            if keyring and self._password:
                self._set_password_in_keyring(self._password)

    def _get_password_from_keyring(self) -> Optional[str]:
        """Retrieves the password from the system's keyring."""
        if not keyring:
            return None
        try:
            service_name = "device_fingerprinting_library"
            username = os.path.basename(self.file_path)
            return keyring.get_password(service_name, username)
        except Exception:
            return None

    def _set_password_in_keyring(self, password: str):
        """Stores the password in the system's keyring for future use."""
        if not keyring:
            return
        try:
            service_name = "device_fingerprinting_library"
            username = os.path.basename(self.file_path)
            keyring.set_password(service_name, username, password)
        except Exception:
            pass

    def _setup_encryptor(self):
        """Sets up the encryptor instance variable."""
        # Derive a key from the password
        # In a real application, the salt should be stored with the encrypted data
        salt = b"\\x00" * 16
        kdf = ScryptKDF()
        self._key = kdf.derive_key(self._password, salt)
        self._encryptor = AESGCMEncryptor()

    def save(self):
        """
        Saves the data to the file.
        """
        if not self._encryptor:
            self._setup_encryptor()

        json_data = json.dumps(self.data).encode("utf-8")
        encrypted_blob = self._encryptor.encrypt(json_data, self._key)

        with open(self.file_path, "wb") as f:
            f.write(encrypted_blob)

    def load(self):
        """
        Loads and decrypts the data from the file.
        """
        if not self._encryptor:
            self._setup_encryptor()

        with open(self.file_path, "rb") as f:
            encrypted_blob = f.read()

        try:
            decrypted_data = self._encryptor.decrypt(encrypted_blob, self._key)
            self.data = json.loads(decrypted_data)
        except (ValueError, InvalidTag) as e:
            raise IOError(
                f"Failed to decrypt or load data. Incorrect password or corrupted file. Reason: {e}"
            )
        except json.JSONDecodeError:
            raise IOError("File is corrupted and does not contain valid JSON.")

    def __setitem__(self, key: str, value: Any):
        """Sets an item in the store."""
        self.data[key] = value

    def __getitem__(self, key: str) -> Any:
        """Gets an item from the store."""
        return self.data[key]

    def __delitem__(self, key: str):
        """Deletes an item from the store."""
        del self.data[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Gets an item, returning a default value if the key does not exist."""
        return self.data.get(key, default)

    def keys(self) -> List[str]:
        """Returns a list of all keys in the store."""
        return list(self.data.keys())

    # --- Compatibility methods for tests ---
    def set_item(self, key: str, value: Any):
        self[key] = value

    def get_item(self, key: str, default: Any = None) -> Any:
        return self.get(key, default)

    def delete_item(self, key: str) -> bool:
        if key in self.data:
            del self[key]
            return True
        return False

    def list_keys(self) -> List[str]:
        return self.keys()

    def __enter__(self):
        """Allows the class to be used as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Saves the data to the file upon exiting the context."""
        self.save()

    # --- Fallback to local file-based secret storage (less secure) ---

    def _get_local_secret_path(self):
        """Gets the path for the local secret file."""
        return self.file_path + ".secret"

    def _save_secret_local(self, secret: str):
        """Saves the secret to a local file (fallback) with encryption."""
        secret_path = self._get_local_secret_path()
        # Encrypt the secret before storing to prevent clear-text storage
        # Use Fernet symmetric encryption with machine-specific key
        try:
            from cryptography.fernet import Fernet
            import hashlib

            # Generate a deterministic key from machine-specific data
            machine_key = hashlib.sha256(
                f"{os.environ.get('COMPUTERNAME', 'default')}{os.environ.get('USERNAME', 'user')}".encode()
            ).digest()
            # Fernet requires base64-encoded 32-byte key
            import base64

            fernet_key = base64.urlsafe_b64encode(machine_key)
            cipher = Fernet(fernet_key)

            encrypted = cipher.encrypt(secret.encode("utf-8"))
            with open(secret_path, "wb") as f:
                f.write(encrypted)
        except ImportError:
            # Fallback: Do NOT store the secret if cryptography is not available
            raise RuntimeError(
                "cryptography library is required for secure storage, but not available; secret not saved"
            )

    def _load_secret_local(self) -> Optional[str]:
        """Loads the secret from a local file (fallback) and decrypts it."""
        secret_path = self._get_local_secret_path()
        if not os.path.exists(secret_path):
            return None

        try:
            from cryptography.fernet import Fernet
            import hashlib
            import base64

            # Generate the same machine-specific key
            machine_key = hashlib.sha256(
                f"{os.environ.get('COMPUTERNAME', 'default')}{os.environ.get('USERNAME', 'user')}".encode()
            ).digest()
            fernet_key = base64.urlsafe_b64encode(machine_key)
            cipher = Fernet(fernet_key)

            with open(secret_path, "rb") as f:
                encrypted = f.read()

            try:
                return cipher.decrypt(encrypted).decode("utf-8")
            except Exception:
                # Try base64 fallback for legacy secrets
                import base64

                try:
                    return base64.b64decode(encrypted).decode("utf-8")
                except Exception:
                    return encrypted.decode("utf-8")
        except ImportError:
            # Fallback if cryptography not available
            import base64

            with open(secret_path, "rb") as f:
                data = f.read()
            try:
                return base64.b64decode(data).decode("utf-8")
            except Exception:
                return data.decode("utf-8")
