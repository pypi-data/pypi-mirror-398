# py-mcp-installer-service: Quick Reference

**Version:** 1.0.0
**Date:** 2025-12-05

---

## Installation

```bash
# Via pip
pip install py-mcp-installer-service

# Via pipx (recommended for CLI)
pipx install py-mcp-installer-service

# With CLI support
pip install py-mcp-installer-service[cli]
```

---

## Python API

### Auto-Detect and Install

```python
from py_mcp_installer import MCPInstaller

# Auto-detect platform
installer = MCPInstaller.auto_detect()

# Install server
result = installer.install_server(
    name="mcp-ticketer",
    env={
        "LINEAR_API_KEY": "your-api-key",
        "LINEAR_TEAM_ID": "your-team-id"
    }
)

print(result.message)
```

### Manual Platform Selection

```python
from py_mcp_installer import MCPInstaller, Platform, ConfigScope

# Target specific platform
installer = MCPInstaller(platform=Platform.CLAUDE_CODE)

# Install with custom command
result = installer.install_server(
    name="mcp-ticketer",
    command="uv run mcp-ticketer mcp",
    args=["--path", "/project/path"],
    env={"LINEAR_API_KEY": "..."},
    scope=ConfigScope.PROJECT,
    force=True,  # Overwrite existing
    dry_run=False
)
```

### List Installed Servers

```python
servers = installer.list_servers()

for server in servers:
    print(f"{server.name}: {'✓' if server.is_valid else '✗'}")
    if server.issues:
        for issue in server.issues:
            print(f"  - {issue.message}")
```

### Validate and Fix

```python
# Validate installation
issues = installer.validate_installation("mcp-ticketer")

if issues:
    print(f"Found {len(issues)} issues:")
    for issue in issues:
        print(f"  - [{issue.severity.value}] {issue.message}")
        print(f"    Fix: {issue.fix_suggestion}")

    # Auto-fix if possible
    result = installer.fix_server("mcp-ticketer")
    print(result.message)
```

### Uninstall

```python
result = installer.uninstall_server("mcp-ticketer")
print(result.message)
```

---

## CLI Tool

### Detect Platforms

```bash
# List all detected platforms
mcp-installer detect

# Output:
# ✓ Claude Code (confidence: 1.0)
#   Config: ~/.config/claude/mcp.json
# ✓ Cursor (confidence: 0.8)
#   Config: ~/.cursor/mcp.json
```

### Install Server

```bash
# Basic installation
mcp-installer install mcp-ticketer \
  --env LINEAR_API_KEY=lin_api_*** \
  --env LINEAR_TEAM_ID=your-team-id

# With custom command
mcp-installer install mcp-ticketer \
  --command "uv run mcp-ticketer mcp" \
  --scope project \
  --platform claude-code

# Dry run
mcp-installer install mcp-ticketer \
  --env LINEAR_API_KEY=*** \
  --dry-run
```

### List Servers

```bash
# List all installed servers
mcp-installer list

# Output:
# mcp-ticketer (Claude Code)
#   ✓ Valid configuration
#   Command: uv run mcp-ticketer mcp
#   Env: LINEAR_API_KEY=***
```

### Validate

```bash
# Validate specific server
mcp-installer validate mcp-ticketer

# Output:
# ✗ Found 2 issues:
#   [ERROR] Environment variable 'LINEAR_API_KEY' is empty
#   [WARNING] Using deprecated line-delimited JSON format
```

### Fix Issues

```bash
# Auto-fix issues
mcp-installer fix mcp-ticketer

# Output:
# ✓ Fixed 1 issue(s)
# - Migrated from legacy format to FastMCP
#
# Next steps:
# 1. Restart Claude Code
```

### Uninstall

```bash
# Remove server
mcp-installer uninstall mcp-ticketer

# Dry run
mcp-installer uninstall mcp-ticketer --dry-run
```

---

## Common Patterns

### Custom Platform Detector

```python
from py_mcp_installer import PlatformDetectorRegistry, DetectedPlatform, Platform, ConfigScope
from pathlib import Path

class MyPlatformDetector:
    def detect(self, project_path=None):
        config_path = Path.home() / ".myplatform" / "config.json"

        if not config_path.exists():
            return None

        return DetectedPlatform(
            platform=Platform.MY_PLATFORM,  # Add to Platform enum
            display_name="My Platform",
            config_path=config_path,
            is_installed=True,
            scope=ConfigScope.GLOBAL,
            confidence=1.0
        )

# Register custom detector
registry = PlatformDetectorRegistry()
registry.register(Platform.MY_PLATFORM, MyPlatformDetector())
```

### Transaction-Based Config Updates

```python
from py_mcp_installer import ConfigManager
from pathlib import Path

config_manager = ConfigManager(
    config_path=Path.home() / ".config/claude/mcp.json",
    format="json"
)

# Use transaction for atomic updates
with config_manager.transaction() as config:
    config["mcpServers"]["new-server"] = {
        "command": "/usr/bin/new-server",
        "args": ["serve"],
        "env": {"API_KEY": "..."}
    }
# Auto-saved and backed up on successful exit
```

### Dry-Run Before Applying Changes

```python
# Preview changes
result = installer.install_server(
    name="mcp-ticketer",
    env={"LINEAR_API_KEY": "..."},
    dry_run=True
)

print(f"Would execute: {result.message}")

# If satisfied, apply changes
if input("Proceed? (y/n): ").lower() == 'y':
    result = installer.install_server(
        name="mcp-ticketer",
        env={"LINEAR_API_KEY": "..."},
        dry_run=False
    )
```

---

## Type Reference

### Enums

```python
from py_mcp_installer import Platform, ConfigScope, InstallMethod, IssueType, IssueSeverity

# Platforms
Platform.CLAUDE_CODE
Platform.CLAUDE_DESKTOP
Platform.CURSOR
Platform.AUGGIE
Platform.CODEX
Platform.GEMINI
Platform.WINDSURF
Platform.ANTIGRAVITY

# Scopes
ConfigScope.PROJECT  # Project-level config
ConfigScope.GLOBAL   # User-level config
ConfigScope.BOTH     # Supports both

# Installation Methods
InstallMethod.UV_RUN          # uv run mcp-ticketer mcp
InstallMethod.PIPX            # mcp-ticketer (via pipx)
InstallMethod.DIRECT_BINARY   # mcp-ticketer (in PATH)
InstallMethod.PYTHON_MODULE   # python -m mcp_ticketer.mcp.server

# Issue Types
IssueType.LEGACY_SERVER
IssueType.MISSING_PATH
IssueType.INVALID_JSON
IssueType.MISSING_REQUIRED_FIELD
IssueType.INVALID_ENV_VAR
IssueType.WRONG_TRANSPORT
IssueType.PERMISSION_ERROR

# Severities
IssueSeverity.CRITICAL  # Server won't work
IssueSeverity.ERROR     # Likely to fail
IssueSeverity.WARNING   # May cause issues
IssueSeverity.INFO      # Informational
```

### Dataclasses

```python
from py_mcp_installer import (
    DetectedPlatform,
    MCPServerConfig,
    InstallationResult,
    ConfigIssue,
    InstalledServer
)

# DetectedPlatform
platform = DetectedPlatform(
    platform=Platform.CLAUDE_CODE,
    display_name="Claude Code",
    config_path=Path("~/.config/claude/mcp.json"),
    is_installed=True,
    scope=ConfigScope.PROJECT,
    confidence=1.0,
    executable_path="/usr/bin/claude",
    issues=[]
)

# MCPServerConfig
config = MCPServerConfig(
    name="mcp-ticketer",
    command="uv",
    args=["run", "mcp-ticketer", "mcp"],
    env={"LINEAR_API_KEY": "..."},
    description="Universal ticket management",
    cwd="/project/path",  # Optional
    timeout=15000,  # Optional (Gemini)
    trust=False  # Optional (Gemini)
)

# InstallationResult
result = InstallationResult(
    success=True,
    platform=Platform.CLAUDE_CODE,
    server_name="mcp-ticketer",
    config_path=Path("~/.config/claude/mcp.json"),
    method=InstallMethod.UV_RUN,
    message="Successfully installed via native CLI",
    warnings=["Existing config overwritten"],
    next_steps=["Restart Claude Code"]
)

# ConfigIssue
issue = ConfigIssue(
    type=IssueType.LEGACY_SERVER,
    severity=IssueSeverity.CRITICAL,
    server_name="mcp-ticketer",
    message="Using deprecated line-delimited JSON format",
    fix_suggestion="Migrate to FastMCP using fix_server()",
    auto_fixable=True
)

# InstalledServer
server = InstalledServer(
    name="mcp-ticketer",
    command="uv",
    args=["run", "mcp-ticketer", "mcp"],
    env={"LINEAR_API_KEY": "***"},
    config_path=Path("~/.config/claude/mcp.json"),
    platform=Platform.CLAUDE_CODE,
    is_valid=True,
    issues=[]
)
```

---

## Exception Handling

```python
from py_mcp_installer import (
    MCPInstallerError,
    PlatformNotFoundError,
    ConfigurationError,
    CommandNotFoundError,
    InstallationFailedError,
    ValidationError,
    BackupError
)

try:
    installer = MCPInstaller.auto_detect()
    result = installer.install_server("mcp-ticketer")

except PlatformNotFoundError as e:
    print(f"No platform detected: {e}")
    print(f"Suggestion: {e.recovery_suggestion}")

except ConfigurationError as e:
    print(f"Config error: {e}")
    print(f"Suggestion: {e.recovery_suggestion}")

except CommandNotFoundError as e:
    print(f"Command not found: {e}")
    print(f"Suggestion: {e.recovery_suggestion}")

except InstallationFailedError as e:
    print(f"Installation failed: {e}")

except MCPInstallerError as e:
    print(f"Unexpected error: {e}")
```

---

## Advanced Usage

### Inspect Configuration Files

```python
from py_mcp_installer import ConfigManager
from pathlib import Path

# JSON config
config_manager = ConfigManager(
    config_path=Path.home() / ".config/claude/mcp.json",
    format="json"
)

# Load
config = config_manager.load()

# Validate
is_valid, issues = config_manager.validate(config)

if not is_valid:
    print("Config issues:")
    for issue in issues:
        print(f"  - {issue}")

# Update with transaction
with config_manager.transaction() as config:
    config["mcpServers"]["new-server"] = {...}
# Automatically saved and backed up
```

### Command Building

```python
from py_mcp_installer import CommandBuilder, InstallMethod
from pathlib import Path

# Auto-detect best method
method, command, args = CommandBuilder.detect_installation_method(
    server_binary="mcp-ticketer",
    project_path=Path.cwd()
)

print(f"Method: {method}")
print(f"Command: {command}")
print(f"Args: {args}")

# Build full command
command, args = CommandBuilder.build_server_command(
    method=InstallMethod.UV_RUN,
    server_binary="mcp-ticketer",
    project_path=Path.cwd(),
    additional_args=["--path", "/project/path"]
)

print(f"Full command: {command} {' '.join(args)}")
```

### Platform Detection Details

```python
from py_mcp_installer import PlatformDetectorRegistry

registry = PlatformDetectorRegistry()

# Detect all platforms
platforms = registry.detect_all()

for platform in platforms:
    print(f"{platform.display_name}:")
    print(f"  Confidence: {platform.confidence}")
    print(f"  Config: {platform.config_path}")
    print(f"  Scope: {platform.scope.value}")
    print(f"  Installed: {platform.is_installed}")

    if platform.issues:
        print("  Issues:")
        for issue in platform.issues:
            print(f"    - {issue}")
```

---

## Platform-Specific Notes

### Claude Code
- **Config**: `~/.config/claude/mcp.json` (new) or `~/.claude.json` (legacy)
- **Scope**: Project-level
- **CLI**: `claude mcp add --scope local`
- **Restart Required**: Yes

### Claude Desktop
- **Config**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
- **Scope**: Global only
- **CLI**: `claude mcp add --scope user`
- **Restart Required**: Yes

### Cursor
- **Config**: `~/.cursor/mcp.json`
- **Scope**: Project-level
- **CLI**: None (JSON only)
- **Special Fields**: `type: "stdio"`, `cwd` supported

### Auggie
- **Config**: `~/.augment/settings.json`
- **Scope**: Global only
- **CLI**: None (JSON only)
- **Special**: No `type` field required

### Codex
- **Config**: `~/.codex/config.toml`
- **Scope**: Global only
- **Format**: TOML (not JSON)
- **Naming**: `mcp_servers` (snake_case, not camelCase)

### Gemini CLI
- **Config**: `.gemini/settings.json` (project) or `~/.gemini/settings.json` (global)
- **Scope**: Both
- **Special Fields**: `timeout`, `trust`
- **Gitignore**: Auto-adds `.gemini/` to `.gitignore`

### Windsurf
- **Config**: `~/.codeium/windsurf/mcp_config.json`
- **Scope**: Project-level
- **GUI**: Supports command palette (`Cmd/Ctrl + Shift + P`)
- **Special**: Part of Codeium ecosystem

### Antigravity
- **Status**: Config location not yet documented
- **Implementation**: Stub only (returns None)

---

## Troubleshooting

### Platform Not Detected

```python
# Check if config file exists
from pathlib import Path

claude_config = Path.home() / ".config/claude/mcp.json"
print(f"Claude Code config exists: {claude_config.exists()}")

# Manual detection
from py_mcp_installer import PlatformDetectorRegistry, Platform

registry = PlatformDetectorRegistry()
result = registry.detect_one(Platform.CLAUDE_CODE)

if result:
    print(f"Detected: {result.display_name}")
    print(f"Confidence: {result.confidence}")
else:
    print("Not detected")
```

### Installation Fails

```python
# Try dry-run first
result = installer.install_server(
    name="mcp-ticketer",
    env={"LINEAR_API_KEY": "..."},
    dry_run=True
)

print(f"Would execute: {result.message}")

# Check for issues
if not result.success:
    print(f"Error: {result.message}")
    for warning in result.warnings:
        print(f"  Warning: {warning}")
```

### Legacy Server Migration

```python
# Check for legacy format
issues = installer.validate_installation("mcp-ticketer")

legacy_issues = [i for i in issues if i.type == IssueType.LEGACY_SERVER]

if legacy_issues:
    print("Legacy format detected!")

    # Preview migration
    result = installer.fix_server("mcp-ticketer", dry_run=True)
    print(f"Would apply: {result.message}")

    # Apply migration
    result = installer.fix_server("mcp-ticketer")
    print(result.message)
```

### Backup Management

```python
from py_mcp_installer import ConfigManager
from pathlib import Path

config_manager = ConfigManager(
    config_path=Path.home() / ".config/claude/mcp.json",
    format="json"
)

# List backups
backup_dir = config_manager.backup_dir
backups = sorted(backup_dir.glob("*.backup"))

print(f"Found {len(backups)} backups:")
for backup in backups:
    print(f"  - {backup.name}")

# Restore specific backup
if backups:
    latest_backup = backups[-1]
    config_manager.restore_backup(latest_backup)
    print(f"Restored from: {latest_backup}")
```

---

## Links

- **Documentation**: `ARCHITECTURE.md`
- **Implementation Plan**: `IMPLEMENTATION-PLAN.md`
- **Project Structure**: `PROJECT-STRUCTURE.md`
- **Diagrams**: `DIAGRAMS.md`
- **Research**: `research/mcp-server-installation-patterns-2025-12-05.md`

---

**Version:** 1.0.0
**Last Updated:** 2025-12-05
