"""Custom exceptions for device_fingerprinting package."""

from typing import Optional, Any


class DeviceFingerprintingError(Exception):
    """Base exception for all device fingerprinting errors."""

    pass


class FingerprintGenerationError(DeviceFingerprintingError):
    """Raised when fingerprint generation fails."""

    pass


class DeviceBindingError(DeviceFingerprintingError):
    """Raised when device binding operations fail."""

    pass


class VerificationError(DeviceFingerprintingError):
    """Raised when signature or binding verification fails."""

    pass


class CryptographicError(DeviceFingerprintingError):
    """Raised when cryptographic operations fail."""

    pass


class InvalidBackendError(CryptographicError):
    """Raised when an invalid or unavailable backend is requested."""

    pass


class InvalidNonceError(DeviceFingerprintingError):
    """Raised when nonce validation fails."""

    pass


class ReplayAttackDetected(InvalidNonceError):
    """Raised when a replay attack is detected."""

    pass


class AdminAuthenticationError(DeviceFingerprintingError):
    """Raised when admin authentication fails."""

    pass


class ConfigurationError(DeviceFingerprintingError):
    """Raised when configuration is invalid or missing."""

    pass


class HardwareError(DeviceFingerprintingError):
    """Raised when hardware information cannot be retrieved."""

    pass


class StorageError(DeviceFingerprintingError):
    """Raised when storage operations fail."""

    pass


class ValidationError(DeviceFingerprintingError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Name of the field that failed validation
            value: The invalid value (sanitized)
        """
        self.field = field
        self.value = value
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.field:
            return f"Validation error for '{self.field}': {super().__str__()}"
        return super().__str__()


class TimingAttackDetected(DeviceFingerprintingError):
    """Raised when a timing attack is detected."""

    pass


class CachePoisoningDetected(DeviceFingerprintingError):
    """Raised when cache poisoning is detected."""

    pass


class RateLimitExceeded(DeviceFingerprintingError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        self.retry_after = retry_after
        super().__init__(message)
