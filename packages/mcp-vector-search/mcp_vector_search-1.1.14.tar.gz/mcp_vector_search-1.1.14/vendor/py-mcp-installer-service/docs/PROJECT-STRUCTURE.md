# py-mcp-installer-service Project Structure

**Version:** 1.0.0
**Date:** 2025-12-05

---

## Directory Structure

```
py-mcp-installer-service/
├── src/
│   └── py_mcp_installer/
│       ├── __init__.py                 # Public API exports
│       ├── installer.py                # MCPInstaller orchestrator
│       ├── platform_detector.py        # PlatformDetectorRegistry
│       ├── installation_strategy.py    # Installation strategies
│       ├── config_manager.py           # ConfigManager
│       ├── mcp_inspector.py            # MCPInspector
│       ├── command_builder.py          # CommandBuilder
│       ├── types.py                    # Type definitions
│       ├── utils.py                    # Utilities
│       ├── exceptions.py               # Custom exceptions
│       ├── cli.py                      # CLI tool (optional)
│       ├── py.typed                    # PEP 561 marker
│       └── platforms/
│           ├── __init__.py
│           ├── base.py                 # Base detector
│           ├── claude_code.py
│           ├── claude_desktop.py
│           ├── cursor.py
│           ├── auggie.py
│           ├── codex.py
│           ├── gemini.py
│           ├── windsurf.py
│           └── antigravity.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # Shared pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_types.py
│   │   ├── test_utils.py
│   │   ├── test_exceptions.py
│   │   ├── test_config_manager.py
│   │   ├── test_command_builder.py
│   │   ├── test_platform_detector.py
│   │   ├── test_installation_strategy.py
│   │   ├── test_mcp_inspector.py
│   │   └── test_installer.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_full_installation.py
│   │   ├── test_platform_detection.py
│   │   ├── test_migration.py
│   │   └── test_cli.py
│   └── fixtures/
│       ├── configs/
│       │   ├── claude_code_valid.json
│       │   ├── claude_code_legacy.json
│       │   ├── cursor_valid.json
│       │   ├── codex_valid.toml
│       │   └── invalid.json
│       └── mock_binaries/
│
├── docs/
│   ├── ARCHITECTURE.md                 # Architecture design
│   ├── IMPLEMENTATION-PLAN.md          # Implementation plan
│   ├── API-REFERENCE.md                # API documentation
│   ├── PLATFORM-GUIDE.md               # Platform-specific notes
│   ├── TROUBLESHOOTING.md              # Common issues
│   ├── CONTRIBUTING.md                 # Contribution guidelines
│   └── research/
│       └── mcp-server-installation-patterns-2025-12-05.md
│
├── examples/
│   ├── basic_installation.py           # Simple usage
│   ├── advanced_usage.py               # Advanced features
│   ├── custom_platform.py              # Adding custom platforms
│   └── cli_example.sh                  # CLI usage examples
│
├── .github/
│   └── workflows/
│       ├── ci.yml                      # CI pipeline
│       ├── publish.yml                 # PyPI publishing
│       └── release.yml                 # Release automation
│
├── pyproject.toml                      # Project configuration
├── README.md                           # Main documentation
├── LICENSE                             # License (MIT recommended)
├── CHANGELOG.md                        # Version history
├── .gitignore                          # Git ignore rules
├── .python-version                     # Python version (3.10+)
├── .editorconfig                       # Editor configuration
└── Makefile                            # Development tasks
```

---

## File Templates

### pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "py-mcp-installer-service"
version = "1.0.0"
description = "Universal MCP server installer for AI coding tools"
readme = "README.md"
license = { text = "MIT" }
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]
maintainers = [
    { name = "Your Name", email = "your.email@example.com" }
]
keywords = [
    "mcp",
    "model-context-protocol",
    "ai-coding-tools",
    "claude-code",
    "cursor",
    "installer",
    "configuration"
]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: System :: Installation/Setup",
    "Typing :: Typed",
]
requires-python = ">=3.10"
dependencies = [
    "tomli>=2.0.0; python_version < '3.11'",
    "tomli-w>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
    "types-toml>=0.10.0",
]
cli = [
    "click>=8.0.0",
    "rich>=13.0.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/py-mcp-installer-service"
Documentation = "https://github.com/yourusername/py-mcp-installer-service/blob/main/README.md"
Repository = "https://github.com/yourusername/py-mcp-installer-service"
Issues = "https://github.com/yourusername/py-mcp-installer-service/issues"
Changelog = "https://github.com/yourusername/py-mcp-installer-service/blob/main/CHANGELOG.md"

[project.scripts]
mcp-installer = "py_mcp_installer.cli:main"

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/tests",
    "/README.md",
    "/LICENSE",
    "/CHANGELOG.md",
]

[tool.hatch.build.targets.wheel]
packages = ["src/py_mcp_installer"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=py_mcp_installer",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--strict-markers",
    "-v",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
]

[tool.coverage.run]
source = ["src/py_mcp_installer"]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/cli.py",  # CLI tested separately
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
    "@overload",
]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
show_error_codes = true
show_error_context = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Allow unused imports in __init__.py
"tests/*" = ["ARG", "S101"]  # Allow unused arguments and asserts in tests

[tool.ruff.lint.isort]
known-first-party = ["py_mcp_installer"]
```

---

### src/py_mcp_installer/__init__.py

```python
"""Universal MCP server installer for AI coding tools.

This library provides a standalone solution for installing, configuring,
and managing MCP (Model Context Protocol) servers across 8 major AI coding
tools: Claude Code, Claude Desktop, Cursor, Auggie, Codex, Gemini CLI,
Windsurf, and Antigravity.

Example:
    Basic usage:

    >>> from py_mcp_installer import MCPInstaller
    >>> installer = MCPInstaller.auto_detect()
    >>> result = installer.install_server(
    ...     name="mcp-ticketer",
    ...     env={"LINEAR_API_KEY": "..."}
    ... )
    >>> print(result.message)

    Advanced usage:

    >>> from py_mcp_installer import MCPInstaller, Platform, ConfigScope
    >>> installer = MCPInstaller(platform=Platform.CLAUDE_CODE)
    >>> result = installer.install_server(
    ...     name="mcp-ticketer",
    ...     command="uv run mcp-ticketer mcp",
    ...     scope=ConfigScope.PROJECT,
    ...     dry_run=True
    ... )
"""

from .exceptions import (
    BackupError,
    CommandNotFoundError,
    ConfigurationError,
    InstallationFailedError,
    MCPInstallerError,
    PlatformNotFoundError,
    ValidationError,
)
from .installer import MCPInstaller
from .mcp_inspector import MCPInspector
from .types import (
    ConfigIssue,
    ConfigScope,
    DetectedPlatform,
    InstallationResult,
    InstallMethod,
    InstalledServer,
    IssueType,
    IssueSeverity,
    MCPServerConfig,
    Platform,
)

__version__ = "1.0.0"

__all__ = [
    # Main classes
    "MCPInstaller",
    "MCPInspector",
    # Types
    "Platform",
    "ConfigScope",
    "InstallMethod",
    "IssueType",
    "IssueSeverity",
    "DetectedPlatform",
    "MCPServerConfig",
    "InstallationResult",
    "ConfigIssue",
    "InstalledServer",
    # Exceptions
    "MCPInstallerError",
    "PlatformNotFoundError",
    "ConfigurationError",
    "CommandNotFoundError",
    "InstallationFailedError",
    "ValidationError",
    "BackupError",
]
```

---

### README.md Template

```markdown
# py-mcp-installer-service

Universal MCP server installer for AI coding tools.

[![PyPI version](https://badge.fury.io/py/py-mcp-installer-service.svg)](https://badge.fury.io/py/py-mcp-installer-service)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/py-mcp-installer-service/workflows/CI/badge.svg)](https://github.com/yourusername/py-mcp-installer-service/actions)
[![Coverage](https://codecov.io/gh/yourusername/py-mcp-installer-service/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/py-mcp-installer-service)

## Features

- ✅ **Universal**: Supports 8 major AI coding tools (Claude Code, Cursor, Windsurf, etc.)
- ✅ **Auto-Detection**: Automatically detects installed platforms
- ✅ **Type-Safe**: Full type hints and runtime validation
- ✅ **Cross-Platform**: Works on macOS, Linux, Windows
- ✅ **Safe Operations**: Atomic updates with automatic backup/restore
- ✅ **Zero Dependencies**: Fully standalone library
- ✅ **Auto-Migration**: Automatically fixes legacy configurations

## Supported Platforms

| Platform | Scope | Native CLI | Status |
|----------|-------|------------|--------|
| Claude Code | Project | ✅ | ✅ Supported |
| Claude Desktop | Global | ✅ | ✅ Supported |
| Cursor | Project | ❌ | ✅ Supported |
| Auggie | Global | ❌ | ✅ Supported |
| Codex | Global | ❌ | ✅ Supported |
| Gemini CLI | Both | ❌ | ✅ Supported |
| Windsurf | Project | ❌ | ✅ Supported |
| Antigravity | Both | ❌ | 🚧 Planned |

## Installation

```bash
# Via pip
pip install py-mcp-installer-service

# Via pipx (recommended for CLI usage)
pipx install py-mcp-installer-service

# With CLI support
pip install py-mcp-installer-service[cli]
```

## Quick Start

### Python API

```python
from py_mcp_installer import MCPInstaller

# Auto-detect platform and install
installer = MCPInstaller.auto_detect()
result = installer.install_server(
    name="mcp-ticketer",
    env={
        "LINEAR_API_KEY": "your-api-key",
        "LINEAR_TEAM_ID": "your-team-id"
    }
)

print(result.message)
# Output: Successfully installed via native CLI

# List installed servers
servers = installer.list_servers()
for server in servers:
    print(f"{server.name}: {'✓' if server.is_valid else '✗'}")

# Validate and fix issues
issues = installer.validate_installation("mcp-ticketer")
if issues:
    installer.fix_server("mcp-ticketer")
```

### CLI Tool

```bash
# Detect installed platforms
mcp-installer detect

# Install MCP server
mcp-installer install mcp-ticketer \
  --env LINEAR_API_KEY=*** \
  --env LINEAR_TEAM_ID=***

# List installed servers
mcp-installer list

# Validate installation
mcp-installer validate mcp-ticketer

# Fix issues
mcp-installer fix mcp-ticketer

# Uninstall
mcp-installer uninstall mcp-ticketer
```

## Advanced Usage

### Manual Platform Selection

```python
from py_mcp_installer import MCPInstaller, Platform, ConfigScope

# Target specific platform
installer = MCPInstaller(platform=Platform.CLAUDE_CODE)

# Install with custom command
result = installer.install_server(
    name="mcp-ticketer",
    command="uv run mcp-ticketer mcp",
    scope=ConfigScope.PROJECT,
    force=True  # Overwrite existing
)
```

### Dry Run Mode

```python
# Preview changes without applying
result = installer.install_server(
    name="mcp-ticketer",
    dry_run=True
)
print(result.message)
# Output: [DRY RUN] Would execute: ...
```

### Custom Platform Detection

```python
from py_mcp_installer import PlatformDetectorRegistry, Platform

class MyPlatformDetector:
    def detect(self, project_path=None):
        # Custom detection logic
        ...

# Register custom detector
registry = PlatformDetectorRegistry()
registry.register(Platform.MY_PLATFORM, MyPlatformDetector())
```

## Documentation

- [Architecture Design](docs/ARCHITECTURE.md)
- [API Reference](docs/API-REFERENCE.md)
- [Platform-Specific Notes](docs/PLATFORM-GUIDE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Contributing](docs/CONTRIBUTING.md)

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/py-mcp-installer-service.git
cd py-mcp-installer-service

# Install development dependencies
pip install -e ".[dev,cli]"

# Run tests
pytest

# Run type checking
mypy src/py_mcp_installer

# Run linting
ruff check src/py_mcp_installer

# Run all checks
make check
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Research based on analysis of 8 major AI coding tools
- Inspired by the need for universal MCP server management
- Built with type safety and reliability in mind

## Links

- [PyPI Package](https://pypi.org/project/py-mcp-installer-service/)
- [GitHub Repository](https://github.com/yourusername/py-mcp-installer-service)
- [Issue Tracker](https://github.com/yourusername/py-mcp-installer-service/issues)
- [Changelog](CHANGELOG.md)
```

---

### Makefile

```makefile
.PHONY: help install test lint type-check format check clean build publish

help:
	@echo "py-mcp-installer-service development commands:"
	@echo "  make install       Install development dependencies"
	@echo "  make test          Run test suite"
	@echo "  make lint          Run linter"
	@echo "  make type-check    Run type checker"
	@echo "  make format        Format code"
	@echo "  make check         Run all checks (test + lint + type-check)"
	@echo "  make clean         Clean build artifacts"
	@echo "  make build         Build distribution packages"
	@echo "  make publish       Publish to PyPI"

install:
	pip install -e ".[dev,cli]"

test:
	pytest

test-cov:
	pytest --cov --cov-report=html --cov-report=term

lint:
	ruff check src/py_mcp_installer tests

lint-fix:
	ruff check --fix src/py_mcp_installer tests

type-check:
	mypy src/py_mcp_installer

format:
	ruff format src/py_mcp_installer tests

check: test lint type-check
	@echo "✓ All checks passed!"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

publish-test: build
	python -m twine upload --repository testpypi dist/*

publish: build
	python -m twine upload dist/*
```

---

### .gitignore

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.tox/
.nox/

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json

# Linting
.ruff_cache/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Virtual environments
venv/
env/
ENV/
.venv/

# Backup files
*.backup
.mcp-installer-backups/
```

---

### CHANGELOG.md

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-MM-DD

### Added
- Initial release of py-mcp-installer-service
- Support for 7 AI coding tool platforms:
  - Claude Code (project-level)
  - Claude Desktop (global)
  - Cursor (project-level)
  - Auggie (global)
  - Codex (global, TOML)
  - Gemini CLI (both scopes)
  - Windsurf (project-level)
- Auto-detection of installed platforms
- Multi-layered platform detection with confidence scoring
- Native CLI installation support (Claude Code/Desktop)
- JSON and TOML configuration management
- Atomic config updates with backup/restore
- MCP server inspection and validation
- Auto-migration from legacy line-delimited JSON format
- Auto-fix for common configuration issues
- Dry-run mode for all operations
- Type-safe API with 100% type hints
- Cross-platform support (macOS, Linux, Windows)
- CLI tool for command-line usage
- Comprehensive documentation and examples

### Known Limitations
- Antigravity platform not yet supported (config location unknown)
- Requires Python 3.10+
- Only supports stdio transport (not HTTP/SSE)

[Unreleased]: https://github.com/yourusername/py-mcp-installer-service/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/py-mcp-installer-service/releases/tag/v1.0.0
```

---

## Next Steps

1. **Create Repository**
   ```bash
   mkdir py-mcp-installer-service
   cd py-mcp-installer-service
   git init
   ```

2. **Copy Project Structure**
   - Create all directories as outlined above
   - Copy `pyproject.toml`, `README.md`, `Makefile`, etc.

3. **Initialize Package**
   ```bash
   mkdir -p src/py_mcp_installer
   touch src/py_mcp_installer/__init__.py
   touch src/py_mcp_installer/py.typed
   ```

4. **Set Up Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -e ".[dev,cli]"
   ```

5. **Begin Phase 1 Implementation**
   - Start with `types.py`
   - Then `exceptions.py`
   - Then `utils.py`
   - Finally `config_manager.py`

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-05
**Status:** Ready for Setup
