# Contributing to Orca SDK

Thank you for your interest in contributing to Orca SDK! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- pip

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/orca-sdk
cd orca-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black mypy flake8
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Use prefixes:

- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation
- `refactor/` for code refactoring
- `test/` for test improvements

### 2. Make Changes

- Write clean, readable code
- Follow PEP 8 style guide
- Add docstrings to functions and classes
- Update tests for your changes
- Update documentation if needed

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=orca --cov-report=html

# Run specific test file
pytest tests/test_handler.py

# Run with verbose output
pytest -v
```

### 4. Code Quality Checks

```bash
# Format code with black
black orca/ tests/ examples/

# Type checking with mypy
mypy orca/

# Linting with flake8
flake8 orca/ tests/ examples/
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature"
```

Use conventional commit messages:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `refactor:` for code refactoring
- `test:` for tests
- `chore:` for maintenance

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Guidelines

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use meaningful variable names
- Add docstrings to all public functions/classes

Example:

```python
from typing import Optional, Dict, Any

def process_data(
    data: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> str:
    """
    Process data with optional configuration.

    Args:
        data: Input data dictionary
        options: Optional configuration parameters

    Returns:
        Processed result as string

    Raises:
        ValueError: If data is invalid
    """
    if not data:
        raise ValueError("Data cannot be empty")

    # Processing logic
    return str(data)
```

### Architecture

Orca SDK follows clean architecture principles:

1. **Domain Layer** (`domain/`)

   - Interfaces and models
   - No dependencies on other layers

2. **Services Layer** (`services/`)

   - Business logic
   - Depends only on domain

3. **Infrastructure Layer** (`infrastructure/`)

   - External clients (API, Centrifugo, etc.)
   - Implements domain interfaces

4. **Core Layer** (`core/`)
   - Main handler and session orchestration
   - Uses services and infrastructure

When adding new features:

- Define interfaces in `domain/`
- Implement business logic in `services/`
- Add external integrations in `infrastructure/`
- Wire everything in `core/`

### Testing

- Write unit tests for all new code
- Aim for >80% code coverage
- Use mocking for external dependencies
- Test edge cases and error conditions

Example test:

```python
import pytest
from orca import OrcaHandler

def test_handler_initialization():
    """Test that handler initializes correctly."""
    handler = OrcaHandler(dev_mode=True)
    assert handler.dev_mode is True

def test_handler_begin_session():
    """Test session creation."""
    handler = OrcaHandler(dev_mode=True)
    # Test logic here
    pass

def test_error_handling():
    """Test error handling."""
    handler = OrcaHandler(dev_mode=True)
    with pytest.raises(ValueError):
        # Code that should raise error
        pass
```

### Documentation

- Update README.md for user-facing changes
- Add docstrings to all public APIs
- Update guides in `docs/` for major features
- Add examples to `examples/` directory

## Pull Request Process

1. **Ensure Tests Pass**: All tests must pass
2. **Update Documentation**: Update relevant docs
3. **Add Examples**: Add examples if adding new features
4. **Code Review**: Wait for maintainer review
5. **Address Feedback**: Make requested changes
6. **Squash Commits**: Keep PR history clean

## Pull Request Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests added
```

## Release Process

Releases are handled by maintainers:

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create git tag
4. Build and publish to PyPI
5. Create GitHub release

## Questions?

- Open an issue for bugs or feature requests
- Join our Discord for discussions
- Email support@orca.ai for other questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to Orca SDK! 🚀
