"""
This module provides classes for runtime security checks and tamper detection.
"""

import os
import platform
import getpass
import hashlib
import hmac
import psutil
import ctypes
import json


class SystemIntegrityChecker:
    """
    Provides methods to check the integrity and details of the underlying system.
    """

    def get_os_details(self) -> dict:
        """Returns a dictionary of OS details."""
        return {
            "os_type": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
        }

    def get_hardware_id(self) -> str:
        """
        Generates a stable hardware ID from various system components.
        This is a simplified version for demonstration.
        """
        # In a real scenario, you'd use more robust and stable identifiers.
        cpu_id = str(psutil.cpu_count()) + platform.processor()
        mac_addr = str(psutil.net_if_addrs().get("Ethernet", [None])[0].address)

        hw_string = f"{cpu_id}-{mac_addr}"
        return hashlib.sha256(hw_string.encode()).hexdigest()


class EnvironmentValidator:
    """
    Validates the execution environment for signs of virtualization or debugging.
    """

    def is_admin(self) -> bool:
        """Checks if the current user has administrative privileges."""
        try:
            if platform.system() == "Windows":
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.getuid() == 0
        except (AttributeError, ImportError):
            return False  # Fallback for systems without these checks

    def is_virtualized(self) -> bool:
        """
        Checks for common signs of a virtualized environment.
        This is a heuristic and not foolproof.
        """
        # Check CPU vendor string (common in VMs)
        try:
            with open("/proc/cpuinfo") as f:
                if "hypervisor" in f.read().lower():
                    return True
        except FileNotFoundError:
            pass  # Not a Linux-like system

        # Check for VM-related MAC address prefixes
        vm_mac_prefixes = ("00:05:69", "00:0C:29", "00:50:56", "08:00:27")
        for iface in psutil.net_if_addrs().values():
            for addr in iface:
                if addr.family == psutil.AF_LINK and addr.address.startswith(vm_mac_prefixes):
                    return True
        return False

    def is_recently_booted(self, threshold_seconds: int = 300) -> bool:
        """Checks if the system was booted very recently."""
        boot_time = psutil.boot_time()
        uptime = psutil.time.time() - boot_time
        return uptime < threshold_seconds


class AntiTampering:
    """
    Provides methods to detect tampering of files using HMAC-SHA256.
    """

    def __init__(self, file_path: str, key: bytes = None):
        self.file_path = file_path
        self.mac_file_path = file_path + ".mac"
        if key is None:
            # Generate a secure random key if none provided
            import secrets

            self._key = secrets.token_bytes(32)  # 256-bit key
            # In production, this key should be stored securely or derived from user input
        else:
            self._key = key

    def generate_mac(self):
        """Generates and saves an HMAC for the file."""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")

        with open(self.file_path, "rb") as f:
            file_content = f.read()

        mac = hmac.new(self._key, file_content, hashlib.sha256).hexdigest()

        with open(self.mac_file_path, "w") as f:
            f.write(mac)

    def verify_mac(self) -> bool:
        """Verifies the file's integrity against its saved HMAC."""
        if not os.path.exists(self.mac_file_path):
            return False  # No MAC to verify against

        with open(self.mac_file_path, "r") as f:
            saved_mac = f.read()

        with open(self.file_path, "rb") as f:
            file_content = f.read()

        current_mac = hmac.new(self._key, file_content, hashlib.sha256).hexdigest()

        return hmac.compare_digest(saved_mac, current_mac)


class SecurityAuditor:
    """
    Logs security-relevant events and system state.
    """

    def __init__(self, logger=None):
        if logger:
            self.logger = logger
        else:
            import logging

            self.logger = logging.getLogger(__name__)

    def log_security_event(self, event: str, level: str, details: dict):
        """Logs a structured security event."""
        log_message = json.dumps(
            {"event": event, "level": level, "details": details, "timestamp": psutil.time.time()}
        )
        self.logger.warning(log_message)

    def get_system_state(self) -> dict:
        """Captures a snapshot of the current system state for auditing."""
        return {
            "timestamp": psutil.time.time(),
            "user": getpass.getuser(),
            "os_details": platform.platform(),
            "running_processes": [p.name() for p in psutil.process_iter(["name"])],
        }
