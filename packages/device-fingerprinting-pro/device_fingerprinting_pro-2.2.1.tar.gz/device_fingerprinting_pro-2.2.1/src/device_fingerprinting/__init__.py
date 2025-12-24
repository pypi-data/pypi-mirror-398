"""
Production device fingerprinting library.

Hardware-based device identification with pluggable backends.
"""

from .device_fingerprinting import (
    generate_fingerprint,
    generate_fingerprint_async,
    create_device_binding,
    verify_device_binding,
    reset_device_id,
    set_crypto_backend,
    set_crypto_backend_sha256,
    set_crypto_backend_sha3_512,
    set_crypto_backend_hybrid_hash,
    set_storage_backend,
    set_security_check,
    set_logger,
    enable_post_quantum_crypto,
    disable_post_quantum_crypto,
    get_crypto_info,
    get_available_crypto_backends,
    enable_anti_replay_protection,
    create_server_nonce,
    verify_server_nonce,
    is_post_quantum_enabled,
    enable_admin_mode,
    lock_configuration,
    unlock_configuration,
    DeviceFingerprintGenerator,
    AdvancedDeviceFingerprinter,
    FingerprintMethod,
    FingerprintResult,
    bind_token_to_device,
    # TPM/Secure Hardware support
    enable_tpm_fingerprinting,
    is_tpm_enabled,
    get_tpm_status,
)

__all__ = [
    "generate_fingerprint",
    "generate_fingerprint_async",
    "create_device_binding",
    "verify_device_binding",
    "reset_device_id",
    "set_crypto_backend",
    "set_crypto_backend_sha256",
    "set_crypto_backend_sha3_512",
    "set_crypto_backend_hybrid_hash",
    "set_storage_backend",
    "set_security_check",
    "set_logger",
    "enable_post_quantum_crypto",
    "disable_post_quantum_crypto",
    "get_crypto_info",
    "get_available_crypto_backends",
    "enable_anti_replay_protection",
    "create_server_nonce",
    "verify_server_nonce",
    "is_post_quantum_enabled",
    "enable_admin_mode",
    "lock_configuration",
    "unlock_configuration",
    "DeviceFingerprintGenerator",
    "AdvancedDeviceFingerprinter",
    "FingerprintMethod",
    "FingerprintResult",
    "bind_token_to_device",
    # TPM/Secure Hardware support
    "enable_tpm_fingerprinting",
    "is_tpm_enabled",
    "get_tpm_status",
]

__version__ = "2.1.3-PQC-DUALUSB-0.15.5"
