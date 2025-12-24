"""
Python Bridge to Rust PQC Module

This provides a clean Python interface to the real PQC implementations in Rust.
"""

import os
import sys
import subprocess
from typing import Optional, Tuple, Dict, Any
import logging

# --- Build and Import ---
try:
    # Try to import the Rust module
    from pqc_rust import (
        generate_keypair as rust_generate_keypair,
        sign as rust_sign,
        verify as rust_verify,
    )

    PQC_RUST_AVAILABLE = True
    logging.info("✅ Successfully imported Rust PQC module")

except ImportError:
    logging.warning("❌ Rust PQC module not found: No module named 'pqc_rust'")
    logging.info("💡 Run: pip install maturin && maturin develop")

    # Define dummy functions to avoid crashing the application
    def rust_generate_keypair() -> tuple[bytes, bytes]:
        raise NotImplementedError("Rust PQC library not available.")

    def rust_sign(message: bytes, private_key: bytes) -> bytes:
        raise NotImplementedError("Rust PQC library not available.")

    def rust_verify(message: bytes, signature: bytes, public_key: bytes) -> bool:
        raise NotImplementedError("Rust PQC library not available.")

    def rust_get_pqc_info() -> dict:
        raise NotImplementedError("Rust PQC library not available.")

    def rust_test_dilithium() -> bool:
        raise NotImplementedError("Rust PQC library not available.")

    def rust_real_dilithium3():
        raise NotImplementedError("Rust PQC library not available.")

    def rust_real_kyber768():
        raise NotImplementedError("Rust PQC library not available.")

    PQC_RUST_AVAILABLE = False


# --- Python Bridge Class ---
class RustCryptoBridge:
    """Bridge to communicate with Rust PQC module"""

    def __init__(self):
        # This check is no longer needed here as we handle it gracefully
        # if not PQC_RUST_AVAILABLE:
        #     raise ImportError("Rust PQC library not available or failed to build.")
        pass

    def generate_keypair(self) -> tuple[bytes, bytes]:
        """Generate a new keypair"""
        if not PQC_RUST_AVAILABLE:
            raise NotImplementedError("Rust PQC library not available.")
        return rust_generate_keypair()

    def sign(self, message: bytes, private_key: bytes) -> bytes:
        """Sign a message"""
        if not PQC_RUST_AVAILABLE:
            raise NotImplementedError("Rust PQC library not available.")
        return rust_sign(message, private_key)

    def verify(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """Verify a signature"""
        if not PQC_RUST_AVAILABLE:
            raise NotImplementedError("Rust PQC library not available.")
        return rust_verify(message, signature, public_key)

    @staticmethod
    def is_available() -> bool:
        """Check if Rust PQC is available"""
        return PQC_RUST_AVAILABLE

    @staticmethod
    def get_info() -> Dict[str, Any]:
        """Get PQC information"""
        if not PQC_RUST_AVAILABLE:
            return {"error": "Rust PQC not available"}

        try:
            return rust_get_pqc_info()
        except Exception as e:
            return {"error": f"Failed to get info: {e}"}

    @staticmethod
    def test_dilithium() -> bool:
        """Test Dilithium implementation"""
        if not PQC_RUST_AVAILABLE:
            return False

        try:
            return rust_test_dilithium()
        except Exception as e:
            print(f"Dilithium test failed: {e}")
            return False

    @staticmethod
    def create_dilithium3():
        """Create a new Dilithium3 instance"""
        if not PQC_RUST_AVAILABLE:
            raise RuntimeError("Rust PQC module not available")

        return rust_real_dilithium3()

    @staticmethod
    def create_kyber768():
        """Create a new Kyber768 instance"""
        if not PQC_RUST_AVAILABLE:
            raise RuntimeError("Rust PQC module not available")

        return rust_real_kyber768()


# Global instance
rust_pqc = RustCryptoBridge()


def install_rust_pqc():
    """Install and build the Rust PQC module"""
    print("🔧 Installing Rust PQC module...")

    # Check if Rust is installed
    try:
        result = subprocess.run(["rustc", "--version"], capture_output=True, text=True, check=True)
        print(f"✅ Rust found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Rust not found. Please install Rust from https://rustup.rs/")
        return False

    # Install maturin if not available
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "maturin"], check=True)
        print("✅ Maturin installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install maturin: {e}")
        return False

    # Build and install the Rust module
    try:
        pqc_rust_dir = os.path.join(os.path.dirname(__file__), "..", "pqc_rust")
        if os.path.exists(pqc_rust_dir):
            print(f"📁 Building Rust module in: {pqc_rust_dir}")
            subprocess.run(["maturin", "develop"], cwd=pqc_rust_dir, check=True)
            print("✅ Rust PQC module built and installed!")

            # Reload the module
            global rust_pqc
            rust_pqc = RustCryptoBridge()
            return True
        else:
            print(f"❌ pqc_rust directory not found: {pqc_rust_dir}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Rust module: {e}")
        return False


if __name__ == "__main__":
    # Test the bridge
    print("🧪 Testing Rust PQC Bridge...")

    if rust_pqc.is_available():
        print("✅ Rust PQC is available!")
        info = rust_pqc.get_info()
        for k, v in info.items():
            print(f"   {k}: {v}")

        print("\n🧪 Testing Dilithium3...")
        if rust_pqc.test_dilithium():
            print("✅ Dilithium3 test passed!")
        else:
            print("❌ Dilithium3 test failed!")
    else:
        print("❌ Rust PQC not available")
        print("💡 Run install_rust_pqc() to set it up")
