"""
This module provides a high-level interface for generating production-ready device fingerprints.
"""

import os
import platform
import psutil
import uuid
import hashlib
import json
import time
import logging
import threading
import secrets
import subprocess
import hmac
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

__version__ = "2.1.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

try:
    from .rust_bridge import RustBridge

    RUST_BRIDGE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    RUST_BRIDGE_AVAILABLE = False


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PARANOID = "paranoid"


class FingerprintMethod(Enum):
    BASIC = "basic"
    SYSTEM = "system"
    COMPOSITE = "composite"
    CRYPTOGRAPHIC = "cryptographic"
    TAMPER_RESISTANT = "tamper_resistant"


@dataclass
class FingerprintResult:
    fingerprint: str
    method: FingerprintMethod
    components: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    confidence: float = 0.0
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    execution_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        return bool(self.fingerprint) and self.confidence > 0.5 and not self.errors

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass to a dictionary, handling enum serialization."""
        return {
            "fingerprint": self.fingerprint,
            "method": self.method.value,
            "components": self.components,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "security_level": self.security_level.value,
            "execution_time": self.execution_time,
            "errors": self.errors,
            "metadata": self.metadata,
        }


class ProductionFingerprintGenerator:
    """
    Generates a detailed and robust device fingerprint suitable for production use.
    It combines hardware, software, and system configuration identifiers.
    """

    def __init__(
        self, security_level=SecurityLevel.HIGH, cache_ttl: int = 300, use_rust_bridge: bool = False
    ):
        """
        Initializes the generator.

        Args:
            security_level: The security level for fingerprinting.
            cache_ttl: Time-to-live for cache in seconds.
            use_rust_bridge: If True, attempts to use the Rust bridge for faster hashing.
        """
        self.security_level = security_level
        self._cache = {}
        self._cache_lock = threading.Lock()
        self.cache_ttl = cache_ttl
        self.salt = secrets.token_bytes(16)
        self.rust_bridge = None
        self.rust_bridge_loaded = False
        if use_rust_bridge and RUST_BRIDGE_AVAILABLE:
            self.rust_bridge = RustBridge()
            self.rust_bridge_loaded = True

    def get_rust_bridge_version(self) -> str:
        """Returns the version of the Rust bridge, if loaded."""
        if self.rust_bridge:
            return self.rust_bridge.get_library_version()
        return "not_loaded"

    def _hash_sha3_512(self, data: bytes) -> str:
        """Hashes data using SHA3-512, via Rust bridge if available."""
        if self.rust_bridge:
            return self.rust_bridge.sha3_512_hex(data)
        return hashlib.sha3_512(data).hexdigest()

    def _get_cpu_features(self) -> str:
        """Gets CPU features, using Rust bridge if available."""
        if self.rust_bridge:
            return self.rust_bridge.get_cpu_features()
        # Fallback for non-x86 or if Rust bridge fails
        return platform.processor()

    def _get_system_info(self) -> Dict[str, Any]:
        """Gathers detailed system information."""
        info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "processor": self._get_cpu_features(),  # Use the method that might call Rust
        }
        if info["platform"] == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "csproduct", "get", "UUID"], capture_output=True, text=True, check=True
                )
                info["uuid"] = result.stdout.strip().split("\n")[-1]
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logging.warning(f"Could not get UUID on Windows: {e}")
        elif info["platform"] == "Linux":
            try:
                with open("/etc/machine-id", "r") as f:
                    info["machine_id"] = f.read().strip()
            except FileNotFoundError:
                try:
                    info["machine_id"] = (
                        subprocess.check_output(["cat", "/var/lib/dbus/machine-id"])
                        .strip()
                        .decode()
                    )
                except (FileNotFoundError, subprocess.CalledProcessError) as e:
                    logging.warning(f"Could not get machine-id on Linux: {e}")

        # Add more hardware details
        try:
            info["cpu_cores"] = psutil.cpu_count(logical=False)
            info["ram_total_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
            info["boot_time"] = psutil.boot_time()
            info["mac_address"] = uuid.getnode()
        except (ImportError, AttributeError, FileNotFoundError):
            pass  # psutil might not be installed or some features not available

        return info

    def generate_fingerprint(self, method=FingerprintMethod.COMPOSITE, **kwargs) -> Dict[str, Any]:
        """
        Generates a dictionary of fingerprint components and a final hash.

        Returns:
            A dictionary containing detailed system information and a final hash.
        """
        components = self._get_system_info()

        # Add security-related info
        security_info = {
            "is_admin": os.geteuid() == 0 if hasattr(os, "geteuid") else False,
        }

        # Combine all info into a single dictionary
        full_fingerprint_data = {
            "system_info": components,
            "software_info": {
                "python_version": platform.python_version(),
            },
            "hardware_info": {
                "cpu_cores": components.get("cpu_cores"),
                "ram_total_gb": components.get("ram_total_gb"),
            },
            "security_info": security_info,
        }

        # Create a stable JSON string for hashing
        json_data = json.dumps(full_fingerprint_data, sort_keys=True, default=str)

        # Generate the final hash
        final_hash = self._hash_sha3_512(json_data.encode("utf-8"))
        full_fingerprint_data["fingerprint_hash"] = final_hash

        return full_fingerprint_data

    def get_security_metrics(self) -> Dict[str, Any]:
        with self._cache_lock:
            cache_size = len(self._cache)
        return {
            "fingerprint_count": cache_size,
            "cache_hit_ratio": 0.0,  # Placeholder for actual hit tracking
            "avg_execution_time": 0.01,  # Placeholder
        }


# Aliases for compatibility
DeviceFingerprintGenerator = ProductionFingerprintGenerator


class AdvancedDeviceFingerprinter(DeviceFingerprintGenerator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


def generate_device_fingerprint(method="composite", security_level="high") -> str:
    sec_level = SecurityLevel(security_level)
    generator = ProductionFingerprintGenerator(security_level=sec_level)

    fp_method = FingerprintMethod.COMPOSITE
    try:
        fp_method = FingerprintMethod(method)
    except ValueError:
        logging.warning(f"Invalid fingerprint method '{method}'. Defaulting to composite.")

    result = generator.generate_fingerprint(fp_method)
    return result.fingerprint


def create_device_binding(data: Dict[str, Any], security_level="high") -> Dict[str, Any]:
    bound_data = data.copy()
    fingerprint = generate_device_fingerprint(security_level=security_level)

    if not fingerprint:
        raise RuntimeError("Failed to generate device fingerprint for binding.")

    bound_data["device_fingerprint"] = fingerprint
    bound_data["binding_timestamp"] = time.time()
    bound_data["binding_security_level"] = security_level

    # Sign the binding
    payload = json.dumps(bound_data, sort_keys=True).encode("utf-8")
    key = generate_device_fingerprint(security_level=security_level).encode(
        "utf-8"
    )  # Use fingerprint as key for simplicity
    signature = hmac.new(key, payload, hashlib.sha256).hexdigest()
    bound_data["signature"] = signature

    return bound_data


def verify_device_binding(bound_data: Dict[str, Any], strict_mode=True) -> bool:
    if "device_fingerprint" not in bound_data or "signature" not in bound_data:
        return False

    # Verify signature first
    signature = bound_data.pop("signature")
    payload = json.dumps(bound_data, sort_keys=True).encode("utf-8")
    key = bound_data["device_fingerprint"].encode("utf-8")
    expected_signature = hmac.new(key, payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        return False

    # Restore signature for fingerprint check
    bound_data["signature"] = signature

    current_fingerprint = generate_device_fingerprint(
        security_level=bound_data.get("binding_security_level", "high")
    )

    if strict_mode:
        return hmac.compare_digest(bound_data["device_fingerprint"], current_fingerprint)
    else:
        # In non-strict mode, we might allow for partial matches or older versions.
        # For now, it's the same as strict.
        return hmac.compare_digest(bound_data["device_fingerprint"], current_fingerprint)
