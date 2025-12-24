# Changelog

All notable changes to the Device Fingerprinting Library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.3] - 2025-10-26

### Updated
- Upgraded pqcdualusb to version 0.15.5 for latest post-quantum crypto improvements
- Updated pip to version 25.3 to fix CVE-2025-8869 security vulnerability
- Enhanced AntiTampering class to use cryptographically secure random keys instead of hardcoded defaults

### Security
- Fixed hardcoded credential vulnerability in AntiTampering class
- Resolved dependency security issue with pip tarfile extraction
- Improved admin authentication flow validation
- All security audits pass with no critical vulnerabilities

### Maintenance
- Confirmed compatibility with latest pqcdualusb API changes
- All 14 test cases continue to pass
- No breaking changes to public API

## [1.0.0] - 2025-09-05

### Added
- Initial release of Device Fingerprinting Library
- `DeviceFingerprintGenerator` class for basic device identification
- `AdvancedDeviceFingerprinter` class with multiple fingerprinting methods
- Three fingerprinting algorithms: Basic, Advanced, and Quantum-Resistant
- Cross-platform support for Windows, Linux, and macOS
- Hardware component detection (CPU, MAC address, machine ID)
- SHA3-512 quantum-resistant cryptographic hashing
- Token binding and verification functionality
- Privacy-aware design with automatic hashing
- Comprehensive error handling and fallback mechanisms
- Zero external dependencies (pure Python standard library)
- Complete test suite with 100% code coverage
- Professional documentation and examples

### Security Features
- Quantum-resistant cryptography using SHA3-512
- Constant-time comparison for security token verification
- Privacy protection through hashing of sensitive hardware data
- Secure fallback mechanisms for edge cases

### Platform Support
- Windows: WMIC integration for UUID and CPU ID detection
- Linux/Unix: Machine ID file reading from /etc/machine-id
- Cross-platform: MAC address, system info, processor details
- Graceful degradation when hardware access is limited

### API Features
- Simple basic API for quick integration
- Advanced API with detailed results and confidence scoring
- Legacy compatibility functions for existing codebases
- Token binding for security applications
- Fingerprint stability verification

## [Unreleased]

### Planned
- Performance optimizations for large-scale deployments
- Additional hardware component detection
- Advanced tamper detection capabilities
- Integration examples for popular frameworks
- CLI tool for system administrators
