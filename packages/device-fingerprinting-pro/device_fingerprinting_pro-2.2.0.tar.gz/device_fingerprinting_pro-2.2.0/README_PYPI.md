# Device Fingerprinting Pro

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/device-fingerprinting-pro.svg)](https://badge.fury.io/py/device-fingerprinting-pro)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-57_passing-brightgreen.svg)](tests/)
[![Downloads](https://pepy.tech/badge/device-fingerprinting-pro)](https://pepy.tech/project/device-fingerprinting-pro)

A Python library for hardware-based device fingerprinting with anomaly detection. Generates stable device identifiers from hardware characteristics, provides encrypted storage, and detects anomalous system behavior.

> **📚 Full Documentation:** For complete documentation with interactive diagrams and detailed examples, visit the [GitHub Repository](https://github.com/Johnsonajibi/DeviceFingerprinting)

## Overview

**Device Fingerprinting Pro** provides production-ready tools for:

- **Hardware Fingerprinting**: Generate unique, stable device identifiers
- **Cryptographic Security**: AES-GCM encryption with SHA3-512 hashing
- **Anomaly Detection**: ML-based detection of suspicious system behavior
- **Secure Storage**: Encrypted key-value store with OS keyring integration
- **Cross-Platform**: Windows, macOS, and Linux support

## Quick Start

### Installation

```bash
# Basic installation
pip install device-fingerprinting-pro

# With post-quantum cryptography
pip install device-fingerprinting-pro[pqc]

# With cloud storage support
pip install device-fingerprinting-pro[cloud]

# Full installation
pip install device-fingerprinting-pro[pqc,cloud,dev]
```

### Basic Usage

```python
from device_fingerprinting.production_fingerprint import ProductionFingerprintGenerator

# Generate device fingerprint
generator = ProductionFingerprintGenerator()
fingerprint_data = generator.generate_fingerprint()

print(f"Fingerprint: {fingerprint_data['fingerprint_hash']}")
print(f"Platform: {fingerprint_data['system_info']['platform']}")
print(f"CPU: {fingerprint_data['hardware_info']['cpu_model']}")
```

**Output:**
```python
{
    'fingerprint_hash': 'sha3_512_hash_value...',
    'hardware_info': {
        'cpu_model': 'Intel Core i7-9750H',
        'cpu_cores': 6,
        'mac_addresses': ['00:1B:44:11:3A:B7'],
        'disk_serials': ['S3Z3NY0M123456']
    },
    'system_info': {
        'platform': 'Windows-10-...',
        'python_version': '3.11.0'
    }
}
```

## Core Features

### 1. Device Fingerprinting

Generate stable, unique device identifiers from hardware characteristics:

- **Data Sources**: CPU model, MAC addresses, disk serials, OS details
- **Hash Algorithm**: SHA3-512 (quantum-resistant)
- **Properties**: Stable across reboots, deterministic, collision-resistant

**Process Flow:**
```
Hardware Data → Normalization → Sorting → SHA3-512 → Fingerprint Hash
```

### 2. Secure Storage

Encrypted key-value storage with OS keyring integration:

```python
from device_fingerprinting.secure_storage import SecureStorage

# Initialize storage
storage = SecureStorage(
    storage_path="./secure_data",
    service_name="my_app",
    username="device_001"
)

# Store encrypted data
storage.set_item("api_key", "secret_value")
api_key = storage.get_item("api_key")

# List and delete
keys = storage.list_keys()
storage.delete_item("api_key")
```

**Security Features:**
- AES-GCM authenticated encryption
- Scrypt KDF for key derivation
- OS keyring integration (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- No plaintext storage

### 3. Anomaly Detection

ML-based detection of suspicious system behavior:

```python
from device_fingerprinting.ml_features import FeatureExtractor, AnomalyDetector
import numpy as np

# Train on baseline data
normal_data = np.random.rand(100, 3)  # [cpu%, memory%, battery%]
detector = AnomalyDetector()
detector.train(normal_data)

# Monitor system
extractor = FeatureExtractor()
current_features = extractor.collect_features()
prediction, score = detector.predict(current_features)

if prediction == -1:
    print(f"⚠ Anomaly detected (score: {score:.2f})")
else:
    print(f"✓ Normal behavior (score: {score:.2f})")

# Save/load model
detector.save_model("baseline.pkl")
detector.load_model("baseline.pkl")
```

**Detection Capabilities:**
- Debugger and reverse engineering detection
- Virtual machine identification
- System tampering indicators
- Abnormal resource usage patterns

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                   Your Application                       │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │  API Layer      │
        │  - Fingerprint  │
        │  - Security     │
        │  - Storage      │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐   ┌───▼───┐   ┌───▼────┐
│Crypto │   │  ML   │   │Storage │
│Engine │   │Anomaly│   │Manager │
└───────┘   └───────┘   └────────┘
    │            │            │
    └────────────┼────────────┘
                 │
        ┌────────┴────────┐
        │  Data Collection│
        │  - CPU Info     │
        │  - MAC Address  │
        │  - Disk Serial  │
        │  - System Stats │
        └─────────────────┘
```

### Security Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Hashing | SHA3-512 | Fingerprint generation |
| Encryption | AES-GCM-256 | Data at rest encryption |
| KDF | Scrypt | Password-based key derivation |
| Storage | OS Keyring | Secure credential management |
| ML | IsolationForest | Anomaly detection |

## Advanced Usage

### Complete Integration Example

```python
from device_fingerprinting.production_fingerprint import ProductionFingerprintGenerator
from device_fingerprinting.ml_features import FeatureExtractor, AnomalyDetector
from device_fingerprinting.secure_storage import SecureStorage
import numpy as np

class DeviceSecurityManager:
    def __init__(self):
        self.generator = ProductionFingerprintGenerator()
        self.storage = SecureStorage("./data", "my_app", "device_001")
        self.detector = AnomalyDetector()
        
    def initialize(self):
        """Initialize security system"""
        # Generate and store fingerprint
        fp = self.generator.generate_fingerprint()
        self.storage.set_item("fingerprint", fp['fingerprint_hash'])
        
        # Train anomaly detector
        baseline = self._collect_baseline()
        self.detector.train(baseline)
        self.detector.save_model("./detector.pkl")
        
        return fp['fingerprint_hash']
    
    def verify_device(self):
        """Verify device hasn't changed"""
        current = self.generator.generate_fingerprint()
        stored = self.storage.get_item("fingerprint")
        return current['fingerprint_hash'] == stored
    
    def check_security(self):
        """Check for anomalies"""
        extractor = FeatureExtractor()
        features = extractor.collect_features()
        prediction, score = self.detector.predict(features)
        
        return {
            'is_normal': prediction == 1,
            'score': score
        }
    
    def _collect_baseline(self, samples=100):
        extractor = FeatureExtractor()
        data = [extractor.collect_features() for _ in range(samples)]
        return np.array(data)

# Usage
manager = DeviceSecurityManager()
device_id = manager.initialize()

# Periodic verification
if manager.verify_device():
    status = manager.check_security()
    if not status['is_normal']:
        print(f"⚠ Security alert: Anomaly detected")
```

### JWT Authentication Integration

```python
from device_fingerprinting.production_fingerprint import ProductionFingerprintGenerator
import jwt
from datetime import datetime, timedelta

def create_device_bound_token(user_id, secret_key):
    """Create JWT bound to device"""
    generator = ProductionFingerprintGenerator()
    device_fp = generator.generate_fingerprint()
    
    payload = {
        'user_id': user_id,
        'device_id': device_fp['fingerprint_hash'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    
    return jwt.encode(payload, secret_key, algorithm='HS256')

def verify_device_bound_token(token, secret_key):
    """Verify JWT and device match"""
    payload = jwt.decode(token, secret_key, algorithms=['HS256'])
    
    generator = ProductionFingerprintGenerator()
    current = generator.generate_fingerprint()
    
    if payload['device_id'] != current['fingerprint_hash']:
        raise SecurityError("Device mismatch detected")
    
    return payload['user_id']
```

## Use Cases

### Authentication & Security
- Multi-factor authentication (device-based 2FA)
- Session binding to specific devices
- Account takeover detection
- Credential sharing prevention

### Licensing & DRM
- Per-device software licensing
- License key validation
- Installation tracking
- Prevent unauthorized copying

### Fraud Detection
- Detect suspicious device changes
- Monitor for automated bots
- Identify virtual machines
- Track device reputation

### Compliance & Auditing
- Device access logs
- Compliance reporting
- Track data access by device
- Audit trail generation

## Technical Specifications

### Hardware Data Collection

| Component | Information | Platform Support |
|-----------|-------------|------------------|
| CPU | Model, cores, architecture | Windows, macOS, Linux |
| Network | MAC addresses | Windows, macOS, Linux |
| Storage | Disk serial numbers | Windows, macOS, Linux |
| System | OS type, version, hostname | All platforms |

### Cryptographic Primitives

| Algorithm | Key Size | Security Level | Standard |
|-----------|----------|----------------|----------|
| SHA3-512 | N/A | 256-bit | FIPS 202 |
| AES-GCM | 256-bit | 256-bit | FIPS 197 |
| Scrypt | 256-bit | Memory-hard | RFC 7914 |

### ML Anomaly Detection

- **Algorithm**: IsolationForest (scikit-learn)
- **Features**: CPU%, Memory%, Battery%, Network activity
- **Training**: Minimum 50-100 baseline samples
- **Output**: Binary classification (-1=anomaly, 1=normal) + anomaly score

## Dependencies

### Core Requirements
- `numpy >= 1.21.0` - Numerical operations
- `scikit-learn >= 1.0.0` - Machine learning
- `psutil >= 5.8.0` - System metrics
- `cryptography >= 41.0.0` - Encryption
- `keyring >= 23.0.0` - OS keyring integration

### Optional Features
- `pqcdualusb >= 0.1.4` - Post-quantum cryptography
- `boto3` - AWS S3 integration
- `azure-storage-blob` - Azure Blob Storage

## Testing

### Test Suite
- **57 tests** covering all core functionality
- **31% code coverage**
- Automated CI/CD with GitHub Actions
- Multi-platform testing (Windows, macOS, Linux)
- Multi-version testing (Python 3.9-3.12)

### Run Tests

```bash
# Install dev dependencies
pip install device-fingerprinting-pro[dev]

# Run tests
pytest

# With coverage
pytest --cov=device_fingerprinting --cov-report=html
```

## Troubleshooting

### Common Issues

**ImportError: No module named 'sklearn'**
```bash
pip install scikit-learn>=1.0.0
```

**KeyringError: No backend found (Linux)**
```bash
sudo apt-get install gnome-keyring
# or
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

**Fingerprint changes after reboot**
- Check if MAC addresses are randomized (privacy features)
- Ensure network interfaces have stable ordering
- Verify disk serials are accessible with proper permissions

**Anomaly detector reports false positives**
- Collect more baseline samples (100+ recommended)
- Train during normal system operation
- Adjust contamination parameter (default: 0.1)

## Performance Optimization

**Fingerprint Generation:**
- Cache results (fingerprints rarely change)
- Use async for network operations
- Skip slow hardware checks if needed

**Anomaly Detection:**
- Reduce sampling frequency (e.g., every 60s)
- Use pre-trained models
- Batch predictions when possible

**Storage Operations:**
- Batch writes
- Use in-memory cache for frequent reads
- Compress large data before encryption

## Documentation & Support

- **GitHub Repository**: https://github.com/Johnsonajibi/DeviceFingerprinting
- **Full Documentation**: https://github.com/Johnsonajibi/DeviceFingerprinting/blob/main/README.md
- **Issue Tracker**: https://github.com/Johnsonajibi/DeviceFingerprinting/issues
- **Changelog**: https://github.com/Johnsonajibi/DeviceFingerprinting/blob/main/CHANGELOG.md

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](https://github.com/Johnsonajibi/DeviceFingerprinting/blob/main/CONTRIBUTING.md)

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - see [LICENSE](https://github.com/Johnsonajibi/DeviceFingerprinting/blob/main/LICENSE) for details

## Changelog

### Version 2.0.0 (2025-10-18)
- Initial PyPI release
- Production-ready device fingerprinting
- ML-based anomaly detection
- AES-GCM encryption and secure storage
- Cross-platform support (Windows, macOS, Linux)
- Comprehensive test suite (57 tests)
- CI/CD pipeline with GitHub Actions

---

**Made with ❤️ by the Device Fingerprinting Pro Team**

For detailed documentation with interactive diagrams, visit: https://github.com/Johnsonajibi/DeviceFingerprinting
