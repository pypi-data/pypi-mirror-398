"""
TPM (Trusted Platform Module) and secure hardware fingerprinting support.

This module provides optional hardware-backed device identification using:
- Windows: TPM 2.0 (Trusted Platform Module)
- macOS: Secure Enclave (via system_profiler)
- Linux: TPM 2.0 (via tpm2-tools)
- Fallback: Graceful degradation when TPM unavailable

Features:
- Hardware-rooted unique identifiers
- Platform attestation capabilities
- Cross-platform abstraction layer
- No dependencies if feature not used
- Automatic fallback on errors

Security considerations:
- TPM access may require elevated privileges
- Hardware IDs are privacy-sensitive
- Results are obfuscated/hashed for privacy
- Optional feature - disabled by default
"""

import platform
import subprocess
import logging
import hashlib
import json
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

_logger = logging.getLogger(__name__)


@dataclass
class TPMInfo:
    """TPM information container"""
    available: bool
    version: Optional[str] = None
    manufacturer: Optional[str] = None
    hardware_id: Optional[str] = None  # Obfuscated/hashed
    attestation_capable: bool = False
    platform: str = ""
    error: Optional[str] = None


class TPMFingerprinter:
    """
    Cross-platform TPM and secure hardware fingerprinting.
    
    Usage:
        fingerprinter = TPMFingerprinter()
        tpm_info = fingerprinter.get_tpm_info()
        if tpm_info.available:
            # Use TPM-based fingerprint
            fp_data = fingerprinter.get_fingerprint_data()
    """
    
    def __init__(self, obfuscate: bool = True):
        """
        Initialize TPM fingerprinter.
        
        Args:
            obfuscate: If True, hash all hardware IDs for privacy
        """
        self.obfuscate = obfuscate
        self.platform = platform.system()
        self._tpm_cache: Optional[TPMInfo] = None
        
    def is_available(self) -> bool:
        """Quick check if TPM/secure hardware is available"""
        return self.get_tpm_info().available
    
    def get_tpm_info(self) -> TPMInfo:
        """
        Get TPM/secure hardware information for current platform.
        
        Returns:
            TPMInfo object with availability and details
        """
        if self._tpm_cache is not None:
            return self._tpm_cache
            
        if self.platform == "Windows":
            info = self._get_windows_tpm()
        elif self.platform == "Darwin":
            info = self._get_macos_secure_enclave()
        elif self.platform == "Linux":
            info = self._get_linux_tpm()
        else:
            info = TPMInfo(
                available=False,
                platform=self.platform,
                error=f"Platform {self.platform} not supported"
            )
        
        self._tpm_cache = info
        return info
    
    def get_fingerprint_data(self) -> Dict[str, Any]:
        """
        Get TPM-based fingerprint data for device identification.
        
        Returns:
            Dictionary with TPM fingerprint components
        """
        tpm_info = self.get_tpm_info()
        
        data = {
            "tpm_available": tpm_info.available,
            "platform": self.platform,
        }
        
        if tpm_info.available:
            data.update({
                "tpm_version": tpm_info.version,
                "tpm_manufacturer": tpm_info.manufacturer,
                "tpm_hardware_id": tpm_info.hardware_id,
                "attestation_capable": tpm_info.attestation_capable,
            })
        else:
            data["tpm_error"] = tpm_info.error
            
        return data
    
    def _get_windows_tpm(self) -> TPMInfo:
        """Get Windows TPM information using WMI"""
        try:
            # Try using Get-Tpm PowerShell cmdlet first (Windows 8+)
            result = subprocess.run(
                ["powershell", "-Command", "Get-Tpm | ConvertTo-Json"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            if result.returncode == 0 and result.stdout.strip():
                tpm_data = json.loads(result.stdout)
                
                # Extract TPM information
                tpm_present = tpm_data.get("TpmPresent", False)
                tpm_ready = tpm_data.get("TpmReady", False)
                tpm_enabled = tpm_data.get("TpmEnabled", False)
                
                if tpm_present and tpm_enabled:
                    # Get manufacturer ID
                    manufacturer_id = tpm_data.get("ManufacturerId", "Unknown")
                    manufacturer_version = tpm_data.get("ManufacturerVersion", "")
                    
                    # Generate hardware ID from TPM characteristics
                    # Note: We don't extract the actual EK (Endorsement Key) as that requires admin
                    hw_components = [
                        str(manufacturer_id),
                        str(manufacturer_version),
                        str(tpm_data.get("SpecVersion", "")),
                    ]
                    
                    hardware_id = self._obfuscate_id(":".join(hw_components))
                    
                    return TPMInfo(
                        available=True,
                        version="2.0",  # Windows 8+ uses TPM 2.0
                        manufacturer=str(manufacturer_id),
                        hardware_id=hardware_id,
                        attestation_capable=tpm_ready,
                        platform="Windows"
                    )
            
            # Fallback: Try WMI directly
            result = subprocess.run(
                [
                    "wmic",
                    "path",
                    "Win32_Tpm",
                    "get",
                    "IsActivated_InitialValue,IsEnabled_InitialValue,ManufacturerId,SpecVersion",
                    "/format:list"
                ],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                tpm_data = {}
                for line in lines:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        tpm_data[key.strip()] = value.strip()
                
                if tpm_data.get("IsEnabled_InitialValue") == "True":
                    hw_id = self._obfuscate_id(
                        f"{tpm_data.get('ManufacturerId', '')}:{tpm_data.get('SpecVersion', '')}"
                    )
                    
                    return TPMInfo(
                        available=True,
                        version=tpm_data.get("SpecVersion", "2.0"),
                        manufacturer=tpm_data.get("ManufacturerId"),
                        hardware_id=hw_id,
                        attestation_capable=tpm_data.get("IsActivated_InitialValue") == "True",
                        platform="Windows"
                    )
            
            return TPMInfo(
                available=False,
                platform="Windows",
                error="TPM not present or not enabled"
            )
            
        except subprocess.TimeoutExpired:
            _logger.warning("TPM query timeout on Windows")
            return TPMInfo(available=False, platform="Windows", error="Query timeout")
        except json.JSONDecodeError as e:
            _logger.warning(f"Failed to parse TPM JSON: {e}")
            return TPMInfo(available=False, platform="Windows", error="Parse error")
        except Exception as e:
            _logger.debug(f"Windows TPM detection failed: {type(e).__name__}: {e}")
            return TPMInfo(available=False, platform="Windows", error=str(e))
    
    def _get_macos_secure_enclave(self) -> TPMInfo:
        """
        Get macOS Secure Enclave information.
        
        Note: macOS uses Secure Enclave instead of TPM.
        T2 chip (Intel Macs 2018+) or Apple Silicon have Secure Enclave.
        """
        try:
            # Check for T2 chip or Apple Silicon
            result = subprocess.run(
                ["system_profiler", "SPiBridgeDataType", "-json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            has_t2 = False
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    # T2 chip presence indicates Secure Enclave
                    has_t2 = len(data.get("SPiBridgeDataType", [])) > 0
                except json.JSONDecodeError:
                    pass
            
            # Check for Apple Silicon
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            is_apple_silicon = "Apple" in result.stdout if result.returncode == 0 else False
            
            if has_t2 or is_apple_silicon:
                # Get hardware UUID for fingerprinting
                result = subprocess.run(
                    ["system_profiler", "SPHardwareDataType"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                hardware_uuid = None
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if "Hardware UUID" in line or "UUID" in line:
                            parts = line.split(":")
                            if len(parts) > 1:
                                hardware_uuid = parts[1].strip()
                                break
                
                hw_id = self._obfuscate_id(hardware_uuid) if hardware_uuid else None
                
                chip_type = "Apple Silicon" if is_apple_silicon else "T2"
                
                return TPMInfo(
                    available=True,
                    version=chip_type,
                    manufacturer="Apple",
                    hardware_id=hw_id,
                    attestation_capable=True,
                    platform="Darwin"
                )
            
            return TPMInfo(
                available=False,
                platform="Darwin",
                error="No Secure Enclave (requires T2 or Apple Silicon)"
            )
            
        except subprocess.TimeoutExpired:
            _logger.warning("Secure Enclave query timeout on macOS")
            return TPMInfo(available=False, platform="Darwin", error="Query timeout")
        except Exception as e:
            _logger.debug(f"macOS Secure Enclave detection failed: {type(e).__name__}: {e}")
            return TPMInfo(available=False, platform="Darwin", error=str(e))
    
    def _get_linux_tpm(self) -> TPMInfo:
        """
        Get Linux TPM information using /sys or tpm2-tools.
        
        Note: May require root access for full TPM access.
        """
        try:
            # Check /sys/class/tpm for TPM devices
            import os
            
            tpm_devices = []
            tpm_sys_path = "/sys/class/tpm"
            
            if os.path.exists(tpm_sys_path):
                tpm_devices = [d for d in os.listdir(tpm_sys_path) if d.startswith("tpm")]
            
            if not tpm_devices:
                return TPMInfo(
                    available=False,
                    platform="Linux",
                    error="No TPM device found in /sys/class/tpm"
                )
            
            # Try to read TPM version
            tpm_device = tpm_devices[0]
            version_file = os.path.join(tpm_sys_path, tpm_device, "tpm_version_major")
            
            tpm_version = None
            if os.path.exists(version_file):
                try:
                    with open(version_file, 'r') as f:
                        version_major = f.read().strip()
                        tpm_version = f"{version_major}.0"
                except (IOError, PermissionError):
                    tpm_version = "Unknown"
            
            # Try to get manufacturer from device_attributes
            manufacturer = "Unknown"
            did_vid_file = os.path.join(tpm_sys_path, tpm_device, "did_vid")
            if os.path.exists(did_vid_file):
                try:
                    with open(did_vid_file, 'r') as f:
                        did_vid = f.read().strip()
                        manufacturer = did_vid
                except (IOError, PermissionError):
                    pass
            
            # Generate hardware ID from device path and attributes
            hw_components = [tpm_device, manufacturer, tpm_version or ""]
            hw_id = self._obfuscate_id(":".join(hw_components))
            
            # Try tpm2_getcap if available (provides more info)
            try:
                result = subprocess.run(
                    ["tpm2_getcap", "properties-fixed"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                
                if result.returncode == 0:
                    # Enhanced hardware ID with TPM capabilities
                    hw_id = self._obfuscate_id(f"{hw_id}:{result.stdout[:100]}")
                    
            except (FileNotFoundError, subprocess.TimeoutExpired):
                # tpm2-tools not installed or timeout, use basic info
                pass
            
            return TPMInfo(
                available=True,
                version=tpm_version,
                manufacturer=manufacturer,
                hardware_id=hw_id,
                attestation_capable=True,  # Assume capable if TPM present
                platform="Linux"
            )
            
        except Exception as e:
            _logger.debug(f"Linux TPM detection failed: {type(e).__name__}: {e}")
            return TPMInfo(available=False, platform="Linux", error=str(e))
    
    def _obfuscate_id(self, hardware_id: Optional[str]) -> Optional[str]:
        """
        Obfuscate hardware ID for privacy.
        
        Args:
            hardware_id: Raw hardware identifier
            
        Returns:
            SHA-256 hash of hardware ID (or None if input is None)
        """
        if not hardware_id or not self.obfuscate:
            return hardware_id
        
        # Use SHA-256 for privacy - irreversible but deterministic
        return hashlib.sha256(hardware_id.encode('utf-8')).hexdigest()[:32]


# Module-level convenience functions

_global_fingerprinter: Optional[TPMFingerprinter] = None


def get_tpm_info() -> TPMInfo:
    """
    Get TPM information using global fingerprinter instance.
    
    Returns:
        TPMInfo object with TPM/secure hardware details
    """
    global _global_fingerprinter
    
    if _global_fingerprinter is None:
        _global_fingerprinter = TPMFingerprinter()
    
    return _global_fingerprinter.get_tpm_info()


def is_tpm_available() -> bool:
    """
    Quick check if TPM/secure hardware is available.
    
    Returns:
        True if TPM or secure hardware is available
    """
    return get_tpm_info().available


def get_tpm_fingerprint() -> Dict[str, Any]:
    """
    Get TPM-based fingerprint data.
    
    Returns:
        Dictionary with TPM fingerprint components
    """
    global _global_fingerprinter
    
    if _global_fingerprinter is None:
        _global_fingerprinter = TPMFingerprinter()
    
    return _global_fingerprinter.get_fingerprint_data()


# Attestation support (future expansion)

def supports_attestation() -> Tuple[bool, Optional[str]]:
    """
    Check if platform supports hardware attestation.
    
    Returns:
        (supported, platform_type) tuple
    """
    tpm_info = get_tpm_info()
    
    if tpm_info.available and tpm_info.attestation_capable:
        return True, tpm_info.platform
    
    return False, None
