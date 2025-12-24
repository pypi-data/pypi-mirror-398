# Contributing to py-mcp-installer-service

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Documentation Guidelines](#documentation-guidelines)
- [Testing](#testing)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

Be respectful, inclusive, and collaborative. We're all here to build better tools.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/py-mcp-installer-service.git
   cd py-mcp-installer-service
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/bobmatnyc/py-mcp-installer-service.git
   ```

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks (if available)
pre-commit install
```

## Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our [code style](#code-style)

3. Add tests for new functionality

4. Run the test suite:
   ```bash
   make test
   ```

5. Run type checking:
   ```bash
   make type-check
   ```

6. Format your code:
   ```bash
   make format
   ```

## Documentation Guidelines

### Where Documentation Should Live

**DO** add documentation to:
- `/docs/` directory for comprehensive guides
- `/README.md` for overview and quick start
- Docstrings in code (Google style)
- `/examples/` for usage examples

**DON'T** add to repository root:
- ❌ `PHASE*_COMPLETE.md` - Temporary development docs
- ❌ `*_INTEGRATION.md` - Project-specific integration notes
- ❌ `VERIFICATION_CHECKLIST.md` - Internal checklists
- ❌ Personal notes or scratch files

### Documentation Standards

**Code Documentation:**
- Every public function/class must have comprehensive docstrings
- Use Google-style docstrings
- Include examples in docstrings when helpful
- Document all parameters, return types, and exceptions

**Example:**
```python
def install_server(
    self,
    name: str,
    command: str,
    args: list[str] | None = None
) -> InstallationResult:
    """Install MCP server with auto-detection.

    Args:
        name: Unique server identifier
        command: Command to execute (e.g., "mcp-ticketer")
        args: Optional command arguments

    Returns:
        InstallationResult with success status and details

    Raises:
        InstallationError: If installation fails
        ValidationError: If inputs are invalid

    Example:
        >>> installer = MCPInstaller.auto_detect()
        >>> result = installer.install_server(
        ...     name="my-server",
        ...     command="my-command"
        ... )
        >>> print(result.success)
        True
    """
```

**Comprehensive Guides:**
- Add to `/docs/` directory
- Use clear section headers
- Include code examples
- Link to related documentation

**Architecture Documentation:**
- Goes in `/docs/ARCHITECTURE.md`
- Describe design decisions
- Include diagrams when helpful

## Testing

### Writing Tests

- Add tests in `/tests/` directory
- Mirror the structure of `/src/`
- Test both success and failure cases
- Use descriptive test names

**Example:**
```python
def test_install_server_with_valid_config():
    """Test successful server installation with valid configuration."""
    # Arrange
    installer = MCPInstaller(platform=Platform.CLAUDE_CODE)

    # Act
    result = installer.install_server(name="test", command="test-cmd")

    # Assert
    assert result.success
    assert result.server_name == "test"
```

### Running Tests

```bash
# All tests
make test

# Specific test file
pytest tests/test_installer.py

# With coverage
make test-coverage
```

## Code Style

### Python Style

- **PEP 8** compliant
- **Type hints** on all functions (Python 3.10+ syntax)
- **Black** for formatting
- **Ruff** for linting
- **mypy --strict** for type checking

### Type Hints

```python
# Use modern syntax (Python 3.10+)
def process(items: list[str]) -> dict[str, int]:  # ✅
def process(items: List[str]) -> Dict[str, int]:  # ❌ (old style)

# Use None union syntax
def find(name: str) -> Server | None:  # ✅
def find(name: str) -> Optional[Server]:  # ❌ (old style)
```

### Imports

```python
# Standard library
import os
import sys
from pathlib import Path

# Third party
import click
import toml

# Local
from py_mcp_installer.types import Platform
from py_mcp_installer.exceptions import InstallationError
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(installer): add dry-run mode for preview

Implement dry-run mode that shows what would happen without
applying changes. Useful for testing and validation.

Closes #42
```

```
fix(config): prevent corruption on write failure

Use atomic write with temp file to prevent partial writes
that corrupt configuration files.
```

## Pull Request Process

1. **Update documentation** for any changed functionality

2. **Add tests** for new features or bug fixes

3. **Update CHANGELOG.md** in the `[Unreleased]` section

4. **Ensure CI passes:**
   - All tests pass
   - Type checking passes (mypy --strict)
   - Linting passes (ruff)
   - Code formatted (black)

5. **Create pull request** with:
   - Clear description of changes
   - Link to related issues
   - Screenshots (if UI changes)
   - Testing instructions

6. **Address review feedback** promptly

7. **Squash commits** before merging (if requested)

## Platform-Specific Contributions

When adding support for a new platform:

1. Add platform to `Platform` enum in `types.py`
2. Create platform implementation in `platforms/your_platform.py`
3. Add detection logic to `platform_detector.py`
4. Update `README.md` supported platforms table
5. Add tests in `tests/platforms/test_your_platform.py`
6. Update documentation in `/docs/`

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Ask questions in issue comments or discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to py-mcp-installer-service! 🎉
