# Contributing to Device Fingerprinting Library

Thank you for your interest in contributing! This document provides guidelines and best practices for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of cryptography and device fingerprinting

### Areas for Contribution

We welcome contributions in these areas:

1. **🔐 Native PQC Backend Integration**
   - Testing with cpp-pqc, rust-pqc, python-oqs
   - Performance benchmarking
   - Documentation

2. **🔍 Fingerprinting Methods**
   - Cross-platform compatibility improvements
   - Mobile device support
   - Cloud/container fingerprinting

3. **⚡ Performance Optimization**
   - Reduce signature size
   - Faster verification
   - Memory efficiency

4. **🛡️ Security Enhancements**
   - Code review
   - Vulnerability testing
   - Cryptographic analysis

5. **📚 Documentation**
   - API documentation
   - Tutorials and examples
   - Translations

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR-USERNAME/DeviceFingerprinting.git
cd DeviceFingerprinting/device_fingerprinting
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev,test,docs]"

# Install pre-commit hooks
pre-commit install
```

### 4. Verify Setup

```bash
# Run tests
pytest

# Run linters
black --check .
flake8 .
mypy device_fingerprinting

# Run pre-commit hooks
pre-commit run --all-files
```

## Making Changes

### 1. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/issue-number-description
```

### Branch Naming Convention

- `feature/feature-name` - New features
- `fix/issue-number-description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/updates
- `perf/description` - Performance improvements

### 2. Make Your Changes

- Write clear, concise code
- Follow the code style guidelines
- Add tests for new functionality
- Update documentation as needed
- Keep commits atomic and well-described

### 3. Commit Messages

Follow the Conventional Commits specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions/updates
- `chore`: Build process or auxiliary tool changes

**Examples:**

```bash
git commit -m "feat(crypto): add Kyber KEM support"
git commit -m "fix(fingerprint): resolve MAC address detection on Linux"
git commit -m "docs(readme): update installation instructions"
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=device_fingerprinting --cov-report=html

# Run specific test file
pytest tests/test_crypto.py

# Run tests matching a pattern
pytest -k "test_fingerprint"
```

### Writing Tests

```python
import pytest
from device_fingerprinting import generate_fingerprint

def test_fingerprint_generation():
    """Test basic fingerprint generation."""
    fingerprint = generate_fingerprint(method="stable")
    assert fingerprint is not None
    assert len(fingerprint) > 0

def test_fingerprint_stability():
    """Test fingerprint remains stable across calls."""
    fp1 = generate_fingerprint(method="stable")
    fp2 = generate_fingerprint(method="stable")
    assert fp1 == fp2

@pytest.mark.parametrize("method", ["stable", "basic", "comprehensive"])
def test_all_methods(method):
    """Test all fingerprinting methods."""
    fingerprint = generate_fingerprint(method=method)
    assert fingerprint is not None
```

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: 100 characters
- **Indentation**: 4 spaces
- **Quotes**: Prefer double quotes for strings
- **Imports**: Organized by isort

### Code Formatting

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Check with flake8
flake8 .

# Type check with mypy
mypy device_fingerprinting
```

### Type Hints

All functions should have type hints:

```python
from typing import Dict, Optional, Tuple

def create_binding(
    data: Dict[str, Any],
    security_level: str = "high",
    custom_fields: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a device binding.
    
    Args:
        data: Data to bind
        security_level: Security level (basic, medium, high)
        custom_fields: Optional custom fields
        
    Returns:
        Binding dictionary with signature
        
    Raises:
        DeviceBindingError: If binding creation fails
    """
    pass
```

### Documentation

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.
    
    Longer description if needed, explaining what the function does,
    any important details, or usage notes.
    
    Args:
        param1: Description of param1.
        param2: Description of param2.
        
    Returns:
        Description of return value.
        
    Raises:
        ValueError: If param2 is negative.
        TypeError: If param1 is not a string.
        
    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

## Pull Request Process

### 1. Before Submitting

- ✅ All tests pass
- ✅ Code is formatted (Black, isort)
- ✅ Linters pass (flake8, mypy)
- ✅ Documentation is updated
- ✅ Commits are well-formed
- ✅ Branch is up-to-date with main

### 2. Submit Pull Request

1. Push your branch to GitHub
2. Create a Pull Request
3. Fill out the PR template completely
4. Link related issues
5. Request review from maintainers

### 3. PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### 4. Review Process

- Maintainers will review within 7 days
- Address review comments
- Update PR as needed
- Once approved, maintainers will merge

## Reporting Bugs

### Before Reporting

1. Check existing issues
2. Verify it's reproducible
3. Test with latest version

### Bug Report Template

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. ...
2. ...

**Expected behavior**
What you expected to happen

**Actual behavior**
What actually happened

**Environment**
- OS: [e.g., Windows 11]
- Python version: [e.g., 3.11.0]
- Library version: [e.g., 2.0.0]

**Additional context**
Any other relevant information
```

## Suggesting Enhancements

### Enhancement Template

```markdown
**Is your feature request related to a problem?**
Description of the problem

**Describe the solution**
Clear description of proposed solution

**Alternatives considered**
Other solutions you've considered

**Additional context**
Any other relevant information
```

## Development Guidelines

### Performance

- Profile code before optimizing
- Use appropriate data structures
- Avoid premature optimization
- Document performance considerations

### Security

- Never commit secrets or keys
- Use constant-time comparisons for crypto
- Validate all inputs
- Follow secure coding practices
- Report security issues privately

### Compatibility

- Maintain Python 3.8+ compatibility
- Test on multiple platforms
- Document platform-specific behavior
- Avoid breaking changes when possible

## Questions?

- **Discussions**: Use GitHub Discussions for questions
- **Chat**: Join our Discord (link in README)
- **Email**: ajibijohnson@jtnetsolutions.com

---

**Thank you for contributing to Device Fingerprinting Library!** 🎉
