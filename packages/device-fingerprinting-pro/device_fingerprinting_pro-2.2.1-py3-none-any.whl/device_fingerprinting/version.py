"""Version information for device_fingerprinting package."""

__version__ = "2.2.1"
__version_info__ = tuple(int(i) for i in __version__.split(".") if i.isdigit())

# Version components
MAJOR = 2
MINOR = 2
PATCH = 1
BUILD = "stable"

# Full version string
VERSION = f"{MAJOR}.{MINOR}.{PATCH}"

# Release information
RELEASE_DATE = "2025-11-07"
RELEASE_NAME = "Documentation & Comprehensive Testing Update"

# Compatibility information
MIN_PYTHON_VERSION = (3, 8)
SUPPORTED_PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]


def get_version() -> str:
    """Get the version string."""
    return __version__


def get_version_info() -> tuple:
    """Get the version as a tuple of integers."""
    return __version_info__


def check_python_version() -> bool:
    """Check if the current Python version is supported."""
    import sys

    return sys.version_info >= MIN_PYTHON_VERSION
