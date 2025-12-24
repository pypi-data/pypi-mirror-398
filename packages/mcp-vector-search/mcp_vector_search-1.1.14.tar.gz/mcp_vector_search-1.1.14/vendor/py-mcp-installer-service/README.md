# py-mcp-installer-service

**Universal MCP Server Installer for AI Coding Tools**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

## Overview

`py-mcp-installer-service` is a comprehensive Python library for installing and managing [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers across multiple AI coding platforms. It provides automatic platform detection, smart installation method selection, and atomic configuration updates with validation and auto-fix capabilities.

### Key Features

- **Platform Auto-Detection**: Automatically detects Claude Desktop, Cline, Roo-Code, Continue, Zed, and other MCP-compatible platforms
- **Multi-Format Support**: Handles both modern JSON and legacy cline_mcp_settings.json formats
- **Smart Installation**: Chooses optimal installation method (uv run, pipx, direct, python -m)
- **Atomic Operations**: All configuration changes are atomic with validation and rollback
- **Legacy Migration**: Automatically migrates legacy format configurations to modern JSON
- **Comprehensive Validation**: Validates configurations, detects conflicts, and suggests fixes
- **Auto-Fix Capabilities**: Can automatically repair common configuration issues
- **Dry-Run Mode**: Preview all changes before applying them

### Supported Platforms

| Platform | Scope | Format | Strategy | Config Location |
|----------|-------|--------|----------|----------------|
| **Claude Desktop** | Global | JSON | claude_desktop | `~/Library/Application Support/Claude/` |
| **Cline** | Project/Global | JSON/Legacy | cline | `./.continue/config.json` or `~/.continue/` |
| **Roo-Code** | Project | JSON | roo_code | `./.roo-code/config.json` |
| **Continue** | Project/Global | JSON | continue_dev | `./.continue/config.json` or `~/.continue/` |
| **Zed** | Global | JSON | zed | `~/.config/zed/` |
| **Windsurf** | Global | JSON | windsurf | `~/.codeium/windsurf/` |
| **Cursor** | Global | JSON | cursor | `~/.cursor/` |
| **Void** | Project/Global | JSON | void | `./.void/` or `~/.void/` |

## Installation

### As Standalone Library

```bash
# From PyPI (when published)
pip install py-mcp-installer

# From source
pip install git+https://github.com/bobmatnyc/py-mcp-installer-service.git
```

### Development Install

```bash
git clone https://github.com/bobmatnyc/py-mcp-installer-service.git
cd py-mcp-installer-service
pip install -e .
```

### As Submodule in Another Project

```bash
# Add as git submodule
git submodule add https://github.com/bobmatnyc/py-mcp-installer-service.git src/services/py_mcp_installer

# Initialize and update
git submodule update --init --recursive

# Use in your code
from py_mcp_installer import MCPInstaller
```

## Quick Start

```python
from py_mcp_installer import MCPInstaller

# Auto-detect platform and install server
installer = MCPInstaller.auto_detect()
result = installer.install_server(
    name="mcp-ticketer",
    command="mcp-ticketer",
    args=["mcp"],
    description="Ticket management interface"
)

if result.success:
    print(f"✅ Installed on {result.platform.value} using {result.method.value}")
    print(f"Config: {result.config_path}")
else:
    print(f"❌ Failed: {result.message}")
```

## Features

### Platform Auto-Detection

Automatically detects which MCP-compatible platforms are installed:

```python
from py_mcp_installer import MCPInstaller

installer = MCPInstaller.auto_detect(verbose=True)
print(f"Detected platform: {installer.platform.value}")
```

### Smart Installation Method Selection

Chooses the best installation method based on your environment:

```python
from py_mcp_installer import MCPInstaller, InstallMethod

# Let installer choose best method
installer = MCPInstaller.auto_detect()
result = installer.install_server(name="my-server", command="my-command")

# Or specify method explicitly
result = installer.install_server(
    name="my-server",
    command="uv",
    args=["run", "my-package"],
    method=InstallMethod.UV_RUN
)
```

### Atomic Configuration Updates

All configuration changes are atomic with automatic validation:

```python
# Changes are validated before being written
result = installer.install_server(
    name="my-server",
    command="invalid-command"  # Will be validated
)

# On failure, original config is preserved
if not result.success:
    print(f"Config unchanged: {result.message}")
```

### Legacy Format Migration

Automatically migrates old cline_mcp_settings.json to modern format:

```python
from py_mcp_installer.migration import migrate_legacy_config

success = migrate_legacy_config(
    legacy_path=".continue/cline_mcp_settings.json",
    target_path=".continue/config.json",
    backup=True  # Creates .bak file
)
```

### Comprehensive Validation

Validate and inspect existing configurations:

```python
from py_mcp_installer.inspector import MCPInspector

inspector = MCPInspector(config_path=".continue/config.json")
issues = inspector.inspect()

for issue in issues:
    print(f"{issue.severity}: {issue.message}")
    if issue.auto_fix_available:
        print(f"  Fix: {issue.suggested_fix}")
```

### Auto-Fix Capabilities

Automatically repair common configuration issues:

```python
from py_mcp_installer.inspector import MCPInspector

inspector = MCPInspector(config_path=".continue/config.json")
fixed = inspector.auto_fix()

print(f"Fixed {len(fixed)} issues")
```

### Dry-Run Mode

Preview changes before applying:

```python
installer = MCPInstaller.auto_detect(dry_run=True, verbose=True)
result = installer.install_server(name="test-server", command="test")

# No actual changes made, but full validation performed
print(f"Would install: {result.success}")
print(f"Would write to: {result.config_path}")
```

## Usage Examples

### Basic Installation

```python
from py_mcp_installer import MCPInstaller

installer = MCPInstaller.auto_detect()
result = installer.install_server(
    name="mcp-github",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-github"],
    description="GitHub MCP server"
)

print(f"Installed: {result.success}")
```

### Installation with Environment Variables

```python
result = installer.install_server(
    name="mcp-ticketer",
    command="mcp-ticketer",
    args=["mcp"],
    env={
        "LINEAR_API_KEY": "your-api-key",
        "GITHUB_TOKEN": "your-token"
    }
)
```

### List Installed Servers

```python
servers = installer.list_servers()
for server in servers:
    print(f"{server.name}: {server.command} {' '.join(server.args or [])}")
```

### Inspect and Fix Configuration

```python
from py_mcp_installer.inspector import MCPInspector

# Inspect for issues
inspector = MCPInspector(config_path=".continue/config.json")
issues = inspector.inspect()

# Auto-fix what we can
fixed = inspector.auto_fix()
print(f"Fixed {len(fixed)} issues automatically")

# Report remaining issues
remaining = inspector.inspect()
for issue in remaining:
    if not issue.auto_fix_available:
        print(f"Manual fix needed: {issue.message}")
```

### Migrate Legacy Configuration

```python
from py_mcp_installer.migration import migrate_legacy_config

success = migrate_legacy_config(
    legacy_path=".continue/cline_mcp_settings.json",
    target_path=".continue/config.json",
    backup=True,
    preserve_legacy=False  # Remove old file after migration
)

if success:
    print("✅ Migration complete")
```

### Uninstall Server

```python
success = installer.uninstall_server(name="mcp-ticketer")
print(f"Uninstalled: {success}")
```

### Specific Platform and Scope

```python
from py_mcp_installer import MCPInstaller, Platform, Scope

# Install to specific platform
installer = MCPInstaller(platform=Platform.CLAUDE_DESKTOP)

# Install globally vs. project-scoped
result = installer.install_server(
    name="global-server",
    command="server-cmd",
    scope=Scope.GLOBAL
)
```

## API Reference

For detailed API documentation, see [docs/QUICK-REFERENCE.md](docs/QUICK-REFERENCE.md).

### Core Classes

- **MCPInstaller**: Main installer orchestrator
- **MCPInspector**: Configuration validation and repair
- **ConfigManager**: Low-level config file operations
- **InstallationStrategy**: Platform-specific installation logic

### Key Methods

```python
# MCPInstaller
installer = MCPInstaller.auto_detect(dry_run=False, verbose=False)
result = installer.install_server(name, command, args, env, description, scope, method)
servers = installer.list_servers()
success = installer.uninstall_server(name)

# MCPInspector
inspector = MCPInspector(config_path)
issues = inspector.inspect()
fixed = inspector.auto_fix()
is_valid = inspector.validate()
```

## Architecture

The library is organized into modular components:

```
py_mcp_installer/
├── types/           # Core types and enums
├── exceptions/      # Custom exceptions
├── utils/           # Platform detection and utilities
├── config/          # Configuration management
├── strategies/      # Platform-specific strategies
├── commands/        # Command builders
├── inspector/       # Validation and auto-fix
├── migration/       # Legacy format migration
└── installer.py     # Main orchestrator
```

For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Development

### Prerequisites

- Python 3.11 or higher
- pip or uv for package management

### Setup

```bash
# Clone repository
git clone https://github.com/bobmatnyc/py-mcp-installer-service.git
cd py-mcp-installer-service

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=py_mcp_installer --cov-report=html

# Run specific test file
pytest tests/test_installer.py

# Run with verbose output
pytest -v
```

### Code Formatting

```bash
# Format code with black
black src/

# Sort imports with isort
isort src/

# Check with flake8
flake8 src/
```

### Type Checking

```bash
# Run mypy type checker
mypy src/py_mcp_installer
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Follow code standards**:
   - Use black for formatting
   - Use type hints for all functions
   - Write docstrings for public APIs
   - Follow SOLID principles
3. **Write tests** for all new functionality
4. **Update documentation** for API changes
5. **Submit a pull request** with clear description

### Code Standards

- **Type Hints**: All public functions must have type hints
- **Docstrings**: Google-style docstrings for all classes and public methods
- **Error Handling**: Use custom exceptions, never swallow errors
- **Testing**: Minimum 80% code coverage for new code
- **Logging**: Use structured logging, never print statements

### Testing Requirements

- Unit tests for all core functionality
- Integration tests for platform-specific strategies
- Mock external dependencies (file system, subprocess calls)
- Test error conditions and edge cases

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built as part of the [mcp-ticketer](https://github.com/bobmatnyc/mcp-ticketer) project
- Designed for the [Claude MPM](https://github.com/bobmatnyc/claude-mpm) framework
- Inspired by the [Model Context Protocol](https://modelcontextprotocol.io/) specification

## Links

- **Documentation**: [docs/](docs/)
- **Issue Tracker**: [GitHub Issues](https://github.com/bobmatnyc/py-mcp-installer-service/issues)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **MCP Specification**: https://modelcontextprotocol.io/

---

**Need Help?** Open an issue or check the [documentation](docs/README.md).
