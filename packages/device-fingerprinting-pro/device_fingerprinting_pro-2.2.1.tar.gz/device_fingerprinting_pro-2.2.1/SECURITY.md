# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          | End of Life |
| ------- | ------------------ | ----------- |
| 2.0.x   | :white_check_mark: | TBD         |
| 1.0.x   | :x:                | 2025-10-18  |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### Reporting Process

1. **Email**: Send details to `security@devicefingerprinting.dev`
2. **Subject Line**: Use "[SECURITY] Brief description"
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)
   - Your contact information

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Status Updates**: Every 7 days until resolved
- **Fix Timeline**: Critical issues within 14 days, others within 30 days
- **Public Disclosure**: After fix is released and users have time to update

### Responsible Disclosure

We follow responsible disclosure principles:

1. **Report privately** first
2. **Give us time** to fix the issue (typically 90 days)
3. **Coordinate disclosure** with our team
4. **Credit** will be given in the security advisory

### Security Measures

Our library implements multiple security layers:

#### Cryptographic Security
- ✅ Post-quantum cryptography (Dilithium3)
- ✅ Hybrid classical + PQC signatures
- ✅ SHA3-256/SHA3-512 hashing
- ✅ PBKDF2 key derivation
- ✅ Constant-time operations

#### Attack Prevention
- ✅ Timing attack protection
- ✅ Cache poisoning prevention
- ✅ Anti-replay protection with nonces
- ✅ Command injection prevention
- ✅ Input validation and sanitization

#### Access Control
- ✅ Admin authentication with session tokens
- ✅ Rate limiting with exponential backoff
- ✅ Secure key storage
- ✅ Monotonic counter operations

### Security Best Practices for Users

1. **Keep Updated**: Always use the latest version
2. **Secure Storage**: Protect key files with proper permissions
3. **Admin Passwords**: Use strong, unique admin passwords
4. **Rate Limiting**: Enable anti-replay protection in production
5. **Logging**: Monitor logs for suspicious activity
6. **Network**: Use HTTPS for nonce/signature transmission

### Security Audits

- **Last Audit**: October 2025
- **Next Scheduled**: January 2026
- **Audit Report**: Available on request for enterprise customers

### Known Security Considerations

#### Current Limitations

1. **PQC Backend**: Currently uses classical fallback (PqcBackend.NONE)
   - **Impact**: Strong classical crypto, but not quantum-resistant yet
   - **Mitigation**: Install native PQC backend (cpp-pqc, rust-pqc, python-oqs)
   - **Timeline**: Full PQC support with native backends

2. **Server Nonce Verification**: Known issue in v2.0.0
   - **Impact**: Nonce verification returns False in some scenarios
   - **Mitigation**: Disable anti-replay for testing, fix in progress
   - **Timeline**: Fix scheduled for v2.0.1

### Security Champions Program

We welcome security researchers and offer:

- 🏆 **Hall of Fame**: Public recognition
- 💰 **Bounty Program**: Rewards for critical vulnerabilities
- 🎓 **Learning**: Feedback and guidance

### Contact Information

- **Security Email**: security@devicefingerprinting.dev
- **GPG Key**: [Download](https://devicefingerprinting.dev/gpg-key.asc)
- **Response Time**: 24-48 hours
- **Preferred Language**: English

### Security Updates

Subscribe to security advisories:
- **GitHub**: Watch repository for security alerts
- **Email**: Subscribe at https://devicefingerprinting.dev/security
- **RSS**: https://github.com/Johnsonajibi/DeviceFingerprinting/security/advisories.atom

---

**Thank you for helping keep Device Fingerprinting Library and its users safe!**
