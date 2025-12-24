"""
Advanced anti-tampering and forensic analysis for device fingerprinting.

This module provides deep system inspection to detect sophisticated threats,
including advanced debugging techniques, virtualization, and code tampering.
"""

import os
import sys
import time
import hashlib
import platform
import subprocess
from typing import Dict, Any, List, Tuple

# Attempt to import psutil for advanced checks, but fail gracefully
try:
    import psutil
except ImportError:
    psutil = None


class ForensicSecurity:
    """
    Performs advanced security checks with forensic capabilities to detect tampering.
    """

    def __init__(self, paranoia_level: int = 1):
        """
        Initializes the forensic security module.

        Args:
            paranoia_level: An integer from 1 to 3 indicating the depth of checks.
                            1: Basic checks (fast).
                            2: Intermediate checks.
                            3: Full checks (slower, more intensive).
        """
        self.paranoia_level = min(max(paranoia_level, 1), 3)
        self.evidence: List[str] = []

    def run_all_checks(self) -> Dict[str, Any]:
        """
        Runs all forensic checks based on the paranoia level.

        Returns:
            A dictionary containing the overall suspicion score and detailed evidence.
        """
        self.evidence.clear()
        suspicion_score = 0

        # Level 1 Checks
        suspicion_score += self._check_debugger_presence()
        suspicion_score += self._check_virtualization()

        # Level 2 Checks
        if self.paranoia_level >= 2:
            suspicion_score += self._check_timing_anomalies()
            suspicion_score += self._check_code_integrity()

        # Level 3 Checks
        if self.paranoia_level >= 3 and psutil:
            suspicion_score += self._check_suspicious_processes()
            suspicion_score += self._check_system_uptime()

        return {
            "suspicion_score": suspicion_score,
            "is_suspicious": suspicion_score > 3,
            "evidence": self.evidence,
        }

    def _check_debugger_presence(self) -> int:
        """Detects if a debugger is attached."""
        score = 0
        if sys.platform == "win32":
            try:
                import ctypes

                if ctypes.windll.kernel32.IsDebuggerPresent():
                    self.evidence.append("Debugger attached (Windows IsDebuggerPresent).")
                    score += 3
            except Exception as e:
                self.evidence.append(f"Error checking for Windows debugger: {e}")

        # Timing-based check
        start = time.perf_counter()
        time.sleep(0.01)
        elapsed = time.perf_counter() - start
        if elapsed > 0.05:
            self.evidence.append(
                f"Suspiciously long sleep time ({elapsed:.2f}s), may indicate debugging."
            )
            score += 2

        return score

    def _check_virtualization(self) -> int:
        """Detects if running in a VM."""
        score = 0
        vm_signatures = ["vmware", "virtualbox", "qemu", "xen", "hyperv"]
        system_info = platform.uname()

        for sig in vm_signatures:
            if sig in str(system_info).lower():
                self.evidence.append(f"VM signature found in system info: {sig}")
                score += 2
                break

        if psutil:
            try:
                # Check for VM-specific MAC address prefixes
                vm_mac_prefixes = ["00:05:69", "00:0c:29", "00:1c:14", "00:50:56", "08:00:27"]
                for iface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == psutil.AF_LINK and any(
                            addr.address.startswith(prefix) for prefix in vm_mac_prefixes
                        ):
                            self.evidence.append(f"VM-specific MAC address found: {addr.address}")
                            score += 2
                            break
            except Exception as e:
                self.evidence.append(f"Error checking MAC addresses: {e}")

        return score

    def _check_timing_anomalies(self) -> int:
        """Detects timing anomalies that could indicate analysis or emulation."""
        timings = []
        for _ in range(10):
            start = time.perf_counter()
            hashlib.sha256(b"some_data_to_hash" * 100).hexdigest()
            timings.append(time.perf_counter() - start)

        mean = sum(timings) / len(timings)
        std_dev = (sum((x - mean) ** 2 for x in timings) / len(timings)) ** 0.5

        if std_dev / mean > 0.5:  # High variance is suspicious
            self.evidence.append(
                f"High variance in execution time (std_dev/mean = {std_dev/mean:.2f})."
            )
            return 2
        return 0

    def _check_code_integrity(self) -> int:
        """Checks for basic signs of code tampering."""
        # This is a placeholder. A real implementation would involve checking
        # file hashes against a known-good manifest.
        script_path = os.path.abspath(sys.argv[0])
        if "temp" in script_path.lower() or "tmp" in script_path.lower():
            self.evidence.append(f"Code is running from a temporary directory: {script_path}")
            return 2
        return 0

    def _check_suspicious_processes(self) -> int:
        """Looks for common analysis and reverse-engineering tools."""
        if not psutil:
            return 0

        suspicious_procs = [
            "ollydbg",
            "ida",
            "x64dbg",
            "windbg",
            "ghidra",
            "fiddler",
            "charles",
            "wireshark",
            "procmon",
            "processhacker",
        ]
        score = 0
        try:
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] and any(
                    p in proc.info["name"].lower() for p in suspicious_procs
                ):
                    self.evidence.append(f"Suspicious process found: {proc.info['name']}")
                    score += 3
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return score

    def _check_system_uptime(self) -> int:
        """Checks for suspiciously low system uptime, which could indicate a sandboxed environment."""
        if not psutil:
            return 0

        try:
            uptime = time.time() - psutil.boot_time()
            if uptime < 300:  # Less than 5 minutes
                self.evidence.append(f"System uptime is suspiciously low ({uptime:.0f} seconds).")
                return 2
        except Exception as e:
            self.evidence.append(f"Could not check system uptime: {e}")
        return 0


def run_forensic_checks(paranoia_level: int = 1) -> Dict[str, Any]:
    """
    A convenience function to run all forensic checks.

    Args:
        paranoia_level: The depth of the security checks (1-3).

    Returns:
        A dictionary with the results of the forensic analysis.
    """
    forensics = ForensicSecurity(paranoia_level=paranoia_level)
    return forensics.run_all_checks()
