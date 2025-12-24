# py-mcp-installer-service Architecture

**Version:** 1.0.0
**Status:** Design Document
**Target:** Production-ready, reusable library
**Date:** 2025-12-05

## Executive Summary

The py-mcp-installer-service library provides a universal, standalone solution for installing, configuring, and managing MCP (Model Context Protocol) servers across 8 major AI coding tools. It operates completely independently of mcp-ticketer, serving as a reusable library for any Python project that needs MCP installation capabilities.

### Design Principles

1. **Zero Dependencies**: Fully standalone, no mcp-ticketer coupling
2. **Type-Safe**: Complete type hints and runtime validation
3. **Platform-Agnostic**: Cross-platform (macOS, Linux, Windows)
4. **Idempotent**: Safe to re-run operations
5. **Plugin Architecture**: Easy to add new platforms
6. **Fail-Safe**: Atomic operations with backup/restore

---

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   MCPInstaller                          │
│              (Orchestration Layer)                      │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Platform    │ │ Installation │ │     MCP      │
│  Detector    │ │  Strategy    │ │  Inspector   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Config     │ │   Command    │ │   Validator  │
│   Manager    │ │   Builder    │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Data Flow Diagram

```
User Request
    │
    ▼
MCPInstaller.auto_detect()
    │
    ├──► PlatformDetector.detect_all()
    │       ├──► Check config files
    │       ├──► Validate CLI availability
    │       └──► Return DetectedPlatform[]
    │
    ▼
MCPInstaller.install_server()
    │
    ├──► Determine InstallationStrategy
    │       ├──► NativeCLIStrategy (Claude Code/Desktop)
    │       ├──► JSONConfigStrategy (Cursor/Windsurf/Auggie/Gemini)
    │       └──► TOMLConfigStrategy (Codex)
    │
    ├──► CommandBuilder.build_install_command()
    │       ├──► Detect installation method (uv/pipx/binary)
    │       ├──► Resolve absolute paths
    │       └──► Build command strings
    │
    ├──► ConfigManager.update_config()
    │       ├──► Backup existing config
    │       ├──► Update configuration
    │       └──► Validate changes
    │
    └──► Return InstallationResult
```

---

## Core Modules

### 1. Platform Detection (`platform_detector.py`)

**Purpose**: Detect which AI coding tools are installed and available.

**Design Pattern**: Strategy + Factory

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Protocol


class Platform(Enum):
    """Supported AI coding tool platforms."""
    CLAUDE_CODE = "claude-code"
    CLAUDE_DESKTOP = "claude-desktop"
    CURSOR = "cursor"
    AUGGIE = "auggie"
    CODEX = "codex"
    GEMINI = "gemini"
    WINDSURF = "windsurf"
    ANTIGRAVITY = "antigravity"


class ConfigScope(Enum):
    """Configuration scope support."""
    PROJECT = "project"
    GLOBAL = "global"
    BOTH = "both"


@dataclass
class DetectedPlatform:
    """Result of platform detection."""
    platform: Platform
    display_name: str
    config_path: Path
    is_installed: bool
    scope: ConfigScope
    confidence: float  # 0.0-1.0
    executable_path: Optional[str] = None
    issues: list[str] = None  # Validation issues found

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


class PlatformDetector(Protocol):
    """Protocol for platform detection implementations."""

    def detect(self, project_path: Optional[Path] = None) -> Optional[DetectedPlatform]:
        """Detect if this platform is installed.

        Args:
            project_path: Optional project directory for project-level configs

        Returns:
            DetectedPlatform if found, None otherwise
        """
        ...


class PlatformDetectorRegistry:
    """Registry of platform detectors with multi-layered detection."""

    def __init__(self):
        self._detectors: dict[Platform, PlatformDetector] = {}
        self._register_builtin_detectors()

    def register(self, platform: Platform, detector: PlatformDetector) -> None:
        """Register a custom platform detector."""
        self._detectors[platform] = detector

    def detect_all(self, project_path: Optional[Path] = None) -> list[DetectedPlatform]:
        """Detect all installed platforms.

        Returns:
            List of detected platforms, sorted by confidence score (descending)
        """
        results = []
        for platform, detector in self._detectors.items():
            result = detector.detect(project_path)
            if result:
                results.append(result)

        return sorted(results, key=lambda x: x.confidence, reverse=True)

    def detect_one(self, platform: Platform, project_path: Optional[Path] = None) -> Optional[DetectedPlatform]:
        """Detect a specific platform."""
        detector = self._detectors.get(platform)
        if not detector:
            raise ValueError(f"No detector registered for platform: {platform}")
        return detector.detect(project_path)
```

**Detection Confidence Scoring**:

- **1.0**: Config file exists, valid format, CLI available (if applicable)
- **0.8**: Config file exists, valid format, no CLI required
- **0.6**: Config file exists but empty/invalid, CLI available
- **0.4**: Config file exists but empty/invalid, no CLI
- **0.0**: Platform not detected

**Multi-Layered Detection**:

1. **Layer 1**: Check config file existence
2. **Layer 2**: Validate config format (JSON/TOML parsing)
3. **Layer 3**: Check CLI availability (if platform has CLI)
4. **Layer 4**: Validate config structure (required fields present)

---

### 2. Installation Strategy (`installation_strategy.py`)

**Purpose**: Provide platform-specific installation logic.

**Design Pattern**: Strategy + Template Method

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class InstallMethod(Enum):
    """Installation methods for MCP servers."""
    UV_RUN = "uv-run"  # uv run mcp-ticketer mcp
    PIPX = "pipx"  # mcp-ticketer (installed via pipx)
    DIRECT_BINARY = "direct"  # mcp-ticketer (in PATH)
    PYTHON_MODULE = "python-module"  # python -m mcp_ticketer.mcp.server


@dataclass
class MCPServerConfig:
    """MCP server configuration."""
    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    description: Optional[str] = None
    cwd: Optional[str] = None
    timeout: Optional[int] = None
    trust: bool = False  # Gemini-specific


@dataclass
class InstallationResult:
    """Result of installation operation."""
    success: bool
    platform: Platform
    server_name: str
    config_path: Path
    method: InstallMethod
    message: str
    warnings: list[str] = None
    next_steps: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.next_steps is None:
            self.next_steps = []


class InstallationStrategy(ABC):
    """Abstract base class for installation strategies."""

    @abstractmethod
    def supports_platform(self, platform: Platform) -> bool:
        """Check if this strategy supports the given platform."""
        pass

    @abstractmethod
    def install(
        self,
        platform: DetectedPlatform,
        server_config: MCPServerConfig,
        scope: ConfigScope,
        force: bool = False,
        dry_run: bool = False
    ) -> InstallationResult:
        """Install MCP server on the platform.

        Args:
            platform: Detected platform information
            server_config: Server configuration to install
            scope: Installation scope (project/global)
            force: Force overwrite existing configuration
            dry_run: Simulate installation without changes

        Returns:
            InstallationResult with status and details
        """
        pass

    @abstractmethod
    def uninstall(
        self,
        platform: DetectedPlatform,
        server_name: str,
        dry_run: bool = False
    ) -> InstallationResult:
        """Remove MCP server from platform."""
        pass

    @abstractmethod
    def update(
        self,
        platform: DetectedPlatform,
        server_config: MCPServerConfig,
        dry_run: bool = False
    ) -> InstallationResult:
        """Update existing MCP server configuration."""
        pass


class NativeCLIStrategy(InstallationStrategy):
    """Installation via native CLI commands.

    Used by:
    - Claude Code (claude mcp add)
    - Claude Desktop (claude mcp add --scope user)
    """

    def supports_platform(self, platform: Platform) -> bool:
        return platform in [Platform.CLAUDE_CODE, Platform.CLAUDE_DESKTOP]

    def install(self, platform, server_config, scope, force=False, dry_run=False):
        # Build CLI command
        cmd = self._build_cli_command(platform, server_config, scope)

        if dry_run:
            return InstallationResult(
                success=True,
                platform=platform.platform,
                server_name=server_config.name,
                config_path=platform.config_path,
                method=InstallMethod.DIRECT_BINARY,
                message=f"[DRY RUN] Would execute: {' '.join(cmd)}",
                next_steps=["Restart Claude Code/Desktop"]
            )

        # Execute CLI command
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            # Fallback to JSON strategy
            return JSONConfigStrategy().install(platform, server_config, scope, force, dry_run)

        return InstallationResult(
            success=True,
            platform=platform.platform,
            server_name=server_config.name,
            config_path=platform.config_path,
            method=InstallMethod.DIRECT_BINARY,
            message="Successfully installed via native CLI",
            next_steps=["Restart Claude Code/Desktop"]
        )

    def _build_cli_command(self, platform, server_config, scope):
        """Build native CLI command."""
        # Implementation details...
        pass


class JSONConfigStrategy(InstallationStrategy):
    """Installation via JSON config file manipulation.

    Used by:
    - Claude Code (fallback when CLI fails)
    - Claude Desktop (fallback when CLI fails)
    - Cursor
    - Auggie
    - Windsurf
    - Gemini
    """

    def supports_platform(self, platform: Platform) -> bool:
        return platform in [
            Platform.CLAUDE_CODE, Platform.CLAUDE_DESKTOP,
            Platform.CURSOR, Platform.AUGGIE,
            Platform.WINDSURF, Platform.GEMINI
        ]

    def install(self, platform, server_config, scope, force=False, dry_run=False):
        config_manager = ConfigManager(platform.config_path, format="json")

        # Load existing config
        config = config_manager.load()

        # Check if server already exists
        if server_config.name in config.get("mcpServers", {}) and not force:
            return InstallationResult(
                success=False,
                platform=platform.platform,
                server_name=server_config.name,
                config_path=platform.config_path,
                method=InstallMethod.DIRECT_BINARY,
                message=f"Server '{server_config.name}' already exists. Use force=True to overwrite.",
                warnings=["Existing configuration not modified"]
            )

        # Build server config
        server_dict = self._build_server_config(platform, server_config)

        # Update config
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        config["mcpServers"][server_config.name] = server_dict

        if dry_run:
            return InstallationResult(
                success=True,
                platform=platform.platform,
                server_name=server_config.name,
                config_path=platform.config_path,
                method=InstallMethod.DIRECT_BINARY,
                message=f"[DRY RUN] Would update config: {config}",
                next_steps=["Restart platform"]
            )

        # Save config (atomic operation)
        config_manager.save(config)

        return InstallationResult(
            success=True,
            platform=platform.platform,
            server_name=server_config.name,
            config_path=platform.config_path,
            method=InstallMethod.DIRECT_BINARY,
            message="Successfully installed via JSON config",
            next_steps=[f"Restart {platform.display_name}"]
        )

    def _build_server_config(self, platform, server_config):
        """Build platform-specific server config dict."""
        base_config = {
            "command": server_config.command,
            "args": server_config.args,
            "env": server_config.env
        }

        # Platform-specific fields
        if platform.platform == Platform.CURSOR:
            base_config["type"] = "stdio"
            if server_config.cwd:
                base_config["cwd"] = server_config.cwd

        elif platform.platform in [Platform.CLAUDE_CODE, Platform.CLAUDE_DESKTOP]:
            base_config["type"] = "stdio"

        elif platform.platform == Platform.GEMINI:
            base_config["timeout"] = server_config.timeout or 15000
            base_config["trust"] = server_config.trust

        return base_config


class TOMLConfigStrategy(InstallationStrategy):
    """Installation via TOML config file manipulation.

    Used by:
    - Codex
    """

    def supports_platform(self, platform: Platform) -> bool:
        return platform == Platform.CODEX

    def install(self, platform, server_config, scope, force=False, dry_run=False):
        config_manager = ConfigManager(platform.config_path, format="toml")

        # Load existing config
        config = config_manager.load()

        # Build server config (snake_case for TOML)
        if "mcp_servers" not in config:
            config["mcp_servers"] = {}

        config["mcp_servers"][server_config.name] = {
            "command": server_config.command,
            "args": server_config.args
        }

        if dry_run:
            return InstallationResult(
                success=True,
                platform=platform.platform,
                server_name=server_config.name,
                config_path=platform.config_path,
                method=InstallMethod.DIRECT_BINARY,
                message=f"[DRY RUN] Would update TOML config",
                next_steps=["Restart Codex"]
            )

        # Save config
        config_manager.save(config)

        return InstallationResult(
            success=True,
            platform=platform.platform,
            server_name=server_config.name,
            config_path=platform.config_path,
            method=InstallMethod.DIRECT_BINARY,
            message="Successfully installed via TOML config",
            next_steps=["Restart Codex"]
        )
```

---

### 3. Configuration Management (`config_manager.py`)

**Purpose**: Handle config file operations with atomic updates and backup/restore.

**Design Pattern**: Adapter + Template Method

```python
import json
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal


ConfigFormat = Literal["json", "toml"]


class ConfigManager:
    """Atomic configuration file manager with backup/restore."""

    def __init__(self, config_path: Path, format: ConfigFormat = "json"):
        self.config_path = config_path
        self.format = format
        self.backup_dir = config_path.parent / ".mcp-installer-backups"
        self.backup_dir.mkdir(exist_ok=True)

    def load(self) -> dict[str, Any]:
        """Load configuration file.

        Returns:
            Configuration dictionary (empty dict if file doesn't exist)

        Raises:
            ConfigurationError: If file exists but is invalid
        """
        if not self.config_path.exists():
            return {}

        try:
            with self.config_path.open('r') as f:
                content = f.read().strip()

                if not content:
                    return {}

                if self.format == "json":
                    return json.loads(content)
                elif self.format == "toml":
                    import tomllib
                    return tomllib.loads(content)
                else:
                    raise ValueError(f"Unsupported format: {self.format}")

        except (json.JSONDecodeError, Exception) as e:
            raise ConfigurationError(
                f"Invalid {self.format.upper()} in {self.config_path}: {e}"
            ) from e

    def save(self, config: dict[str, Any]) -> None:
        """Save configuration with atomic write.

        Uses temporary file + rename for atomicity.
        Creates backup before overwriting.
        """
        # Create backup if file exists
        if self.config_path.exists():
            self._create_backup()

        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.config_path.parent,
            prefix=f".{self.config_path.name}.",
            suffix=".tmp"
        )

        try:
            with os.fdopen(temp_fd, 'w') as f:
                if self.format == "json":
                    json.dump(config, f, indent=2)
                    f.write("\n")  # Trailing newline
                elif self.format == "toml":
                    import tomli_w
                    tomli_w.dump(config, f)

            # Atomic rename
            os.replace(temp_path, self.config_path)

        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise ConfigurationError(f"Failed to save config: {e}") from e

    def validate(self, config: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate configuration structure.

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        # Check required top-level keys
        if self.format == "json":
            if "mcpServers" not in config:
                issues.append("Missing 'mcpServers' key")
            elif not isinstance(config["mcpServers"], dict):
                issues.append("'mcpServers' must be a dictionary")

        elif self.format == "toml":
            if "mcp_servers" not in config:
                issues.append("Missing 'mcp_servers' key")
            elif not isinstance(config["mcp_servers"], dict):
                issues.append("'mcp_servers' must be a table")

        # Validate server configurations
        servers_key = "mcpServers" if self.format == "json" else "mcp_servers"
        for server_name, server_config in config.get(servers_key, {}).items():
            if not isinstance(server_config, dict):
                issues.append(f"Server '{server_name}' config must be a dict/table")
                continue

            if "command" not in server_config:
                issues.append(f"Server '{server_name}' missing 'command' field")

            if "args" in server_config and not isinstance(server_config["args"], list):
                issues.append(f"Server '{server_name}' 'args' must be a list")

        return (len(issues) == 0, issues)

    def _create_backup(self) -> Path:
        """Create timestamped backup of config file."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.config_path.name}.{timestamp}.backup"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(self.config_path, backup_path)

        # Clean old backups (keep last 10)
        self._cleanup_old_backups(keep=10)

        return backup_path

    def _cleanup_old_backups(self, keep: int = 10) -> None:
        """Remove old backups, keeping only the most recent."""
        backups = sorted(
            self.backup_dir.glob(f"{self.config_path.name}.*.backup"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for old_backup in backups[keep:]:
            old_backup.unlink()

    def restore_backup(self, backup_path: Path) -> None:
        """Restore configuration from backup."""
        if not backup_path.exists():
            raise ConfigurationError(f"Backup not found: {backup_path}")

        shutil.copy2(backup_path, self.config_path)

    @contextmanager
    def transaction(self):
        """Context manager for transactional config updates.

        Usage:
            with config_manager.transaction() as config:
                config["mcpServers"]["new-server"] = {...}
            # Auto-saved and backed up on successful exit
        """
        config = self.load()
        backup_path = None

        try:
            if self.config_path.exists():
                backup_path = self._create_backup()

            yield config

            # Save on successful completion
            self.save(config)

        except Exception as e:
            # Restore backup on error
            if backup_path and backup_path.exists():
                self.restore_backup(backup_path)
            raise ConfigurationError(f"Transaction failed: {e}") from e
```

---

### 4. MCP Inspector (`mcp_inspector.py`)

**Purpose**: Inspect, validate, and diagnose MCP server installations.

**Design Pattern**: Visitor + Strategy

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class IssueType(Enum):
    """Types of configuration issues."""
    LEGACY_SERVER = "legacy-server"  # Line-delimited JSON format
    MISSING_PATH = "missing-path"  # Command path doesn't exist
    INVALID_JSON = "invalid-json"  # Malformed JSON
    MISSING_REQUIRED_FIELD = "missing-field"  # Required field absent
    INVALID_ENV_VAR = "invalid-env"  # Environment variable issue
    WRONG_TRANSPORT = "wrong-transport"  # Not using stdio
    PERMISSION_ERROR = "permission-error"  # File permissions issue


class IssueSeverity(Enum):
    """Severity levels for issues."""
    CRITICAL = "critical"  # Server won't work
    ERROR = "error"  # Likely to fail
    WARNING = "warning"  # May cause issues
    INFO = "info"  # Informational only


@dataclass
class ConfigIssue:
    """Detected configuration issue."""
    type: IssueType
    severity: IssueSeverity
    server_name: str
    message: str
    fix_suggestion: str
    auto_fixable: bool = False


@dataclass
class InstalledServer:
    """Information about an installed MCP server."""
    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    config_path: Path
    platform: Platform
    is_valid: bool
    issues: list[ConfigIssue]


class MCPInspector:
    """Inspector for MCP server installations."""

    def __init__(self, platform: DetectedPlatform):
        self.platform = platform
        self.config_manager = ConfigManager(platform.config_path)

    def list_servers(self) -> list[InstalledServer]:
        """List all installed MCP servers on this platform.

        Returns:
            List of InstalledServer objects with validation status
        """
        config = self.config_manager.load()
        servers = []

        servers_key = "mcpServers" if self.config_manager.format == "json" else "mcp_servers"

        for name, server_config in config.get(servers_key, {}).items():
            issues = self._validate_server(name, server_config)

            servers.append(InstalledServer(
                name=name,
                command=server_config.get("command", ""),
                args=server_config.get("args", []),
                env=server_config.get("env", {}),
                config_path=self.platform.config_path,
                platform=self.platform.platform,
                is_valid=len([i for i in issues if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.ERROR]]) == 0,
                issues=issues
            ))

        return servers

    def validate_server(self, server_name: str) -> list[ConfigIssue]:
        """Validate a specific server configuration.

        Returns:
            List of issues found (empty if valid)
        """
        config = self.config_manager.load()
        servers_key = "mcpServers" if self.config_manager.format == "json" else "mcp_servers"

        server_config = config.get(servers_key, {}).get(server_name)
        if not server_config:
            return [ConfigIssue(
                type=IssueType.MISSING_REQUIRED_FIELD,
                severity=IssueSeverity.CRITICAL,
                server_name=server_name,
                message=f"Server '{server_name}' not found in configuration",
                fix_suggestion="Install the server using MCPInstaller.install_server()"
            )]

        return self._validate_server(server_name, server_config)

    def _validate_server(self, name: str, config: dict) -> list[ConfigIssue]:
        """Internal validation logic."""
        issues = []

        # Check for legacy line-delimited JSON format
        args = config.get("args", [])
        if len(args) >= 2 and args[0] == "-m" and "mcp_ticketer.mcp.server" in args[1]:
            issues.append(ConfigIssue(
                type=IssueType.LEGACY_SERVER,
                severity=IssueSeverity.CRITICAL,
                server_name=name,
                message="Using deprecated line-delimited JSON format",
                fix_suggestion="Migrate to FastMCP using MCPInspector.fix_server()",
                auto_fixable=True
            ))

        # Check if command path exists
        command = config.get("command", "")
        if command and not command.startswith("uv"):  # Skip uv run commands
            command_path = Path(command)
            if command_path.is_absolute() and not command_path.exists():
                issues.append(ConfigIssue(
                    type=IssueType.MISSING_PATH,
                    severity=IssueSeverity.ERROR,
                    server_name=name,
                    message=f"Command path does not exist: {command}",
                    fix_suggestion="Update command path or reinstall the server",
                    auto_fixable=True
                ))

        # Check required fields
        if not config.get("command"):
            issues.append(ConfigIssue(
                type=IssueType.MISSING_REQUIRED_FIELD,
                severity=IssueSeverity.CRITICAL,
                server_name=name,
                message="Missing required field: 'command'",
                fix_suggestion="Add command field to server configuration"
            ))

        # Check transport type (JSON configs only)
        if self.config_manager.format == "json":
            transport_type = config.get("type")
            if transport_type and transport_type != "stdio":
                issues.append(ConfigIssue(
                    type=IssueType.WRONG_TRANSPORT,
                    severity=IssueSeverity.WARNING,
                    server_name=name,
                    message=f"Unexpected transport type: {transport_type} (expected 'stdio')",
                    fix_suggestion="Change type to 'stdio' for standard MCP servers"
                ))

        # Check environment variables
        env = config.get("env", {})
        for key, value in env.items():
            if not value or value == "***":
                issues.append(ConfigIssue(
                    type=IssueType.INVALID_ENV_VAR,
                    severity=IssueSeverity.ERROR,
                    server_name=name,
                    message=f"Environment variable '{key}' is empty or placeholder",
                    fix_suggestion=f"Set valid value for {key}"
                ))

        return issues

    def suggest_fixes(self, server_name: str) -> dict[str, Any]:
        """Suggest fixes for issues found in server configuration.

        Returns:
            Dict with:
            - auto_fixable: bool
            - fixes: list of suggested fixes
            - new_config: proposed new configuration (if auto-fixable)
        """
        issues = self.validate_server(server_name)

        auto_fixable_issues = [i for i in issues if i.auto_fixable]
        manual_fixes = [i for i in issues if not i.auto_fixable]

        result = {
            "auto_fixable": len(auto_fixable_issues) > 0 and len(manual_fixes) == 0,
            "fixes": [i.fix_suggestion for i in issues],
            "new_config": None
        }

        # Generate new config for auto-fixable issues
        if result["auto_fixable"]:
            config = self.config_manager.load()
            servers_key = "mcpServers" if self.config_manager.format == "json" else "mcp_servers"
            server_config = config[servers_key][server_name]

            # Apply auto-fixes
            for issue in auto_fixable_issues:
                if issue.type == IssueType.LEGACY_SERVER:
                    # Migrate to FastMCP
                    server_config["command"] = self._detect_best_command()
                    server_config["args"] = ["mcp"]
                    if "--path" not in server_config.get("args", []):
                        # Preserve project path if exists
                        pass

                elif issue.type == IssueType.MISSING_PATH:
                    # Update to detected command
                    server_config["command"] = self._detect_best_command()

            result["new_config"] = server_config

        return result

    def _detect_best_command(self) -> str:
        """Detect best available command for mcp-ticketer."""
        # Priority: uv > direct binary > python module
        if shutil.which("uv"):
            return "uv"

        mcp_binary = shutil.which("mcp-ticketer")
        if mcp_binary:
            return mcp_binary

        # Find Python with mcp_ticketer installed
        python_path = sys.executable
        return python_path

    def fix_server(self, server_name: str, dry_run: bool = False) -> InstallationResult:
        """Auto-fix issues with server configuration.

        Only fixes auto-fixable issues. Manual issues require user intervention.
        """
        fixes = self.suggest_fixes(server_name)

        if not fixes["auto_fixable"]:
            return InstallationResult(
                success=False,
                platform=self.platform.platform,
                server_name=server_name,
                config_path=self.platform.config_path,
                method=InstallMethod.DIRECT_BINARY,
                message="Server has issues that require manual intervention",
                warnings=fixes["fixes"]
            )

        if dry_run:
            return InstallationResult(
                success=True,
                platform=self.platform.platform,
                server_name=server_name,
                config_path=self.platform.config_path,
                method=InstallMethod.DIRECT_BINARY,
                message=f"[DRY RUN] Would apply fixes: {fixes['fixes']}",
                next_steps=["Review proposed changes and run without dry_run=True"]
            )

        # Apply fixes
        with self.config_manager.transaction() as config:
            servers_key = "mcpServers" if self.config_manager.format == "json" else "mcp_servers"
            config[servers_key][server_name] = fixes["new_config"]

        return InstallationResult(
            success=True,
            platform=self.platform.platform,
            server_name=server_name,
            config_path=self.platform.config_path,
            method=InstallMethod.DIRECT_BINARY,
            message=f"Successfully fixed {len(fixes['fixes'])} issues",
            next_steps=[f"Restart {self.platform.display_name}"]
        )
```

---

### 5. Command Builder (`command_builder.py`)

**Purpose**: Generate correct command strings for MCP server execution.

**Design Pattern**: Builder + Strategy

```python
import shutil
import sys
from pathlib import Path
from typing import Optional


class CommandBuilder:
    """Builder for MCP server command strings."""

    @staticmethod
    def detect_installation_method(
        server_binary: str = "mcp-ticketer",
        project_path: Optional[Path] = None
    ) -> tuple[InstallMethod, str, list[str]]:
        """Detect optimal installation method and build command.

        Returns:
            Tuple of (method, command, base_args)
        """
        # Priority 1: uv run (fastest, recommended)
        if shutil.which("uv"):
            return (
                InstallMethod.UV_RUN,
                "uv",
                ["run", server_binary, "mcp"]
            )

        # Priority 2: Direct binary in PATH
        binary_path = shutil.which(server_binary)
        if binary_path:
            return (
                InstallMethod.DIRECT_BINARY,
                binary_path,
                ["mcp"]
            )

        # Priority 3: Python module (fallback)
        python_path = CommandBuilder._get_python_executable(project_path)
        if python_path:
            return (
                InstallMethod.PYTHON_MODULE,
                python_path,
                ["-m", "mcp_ticketer.mcp.server"]
            )

        raise CommandNotFoundError(
            f"'{server_binary}' not found. Install with: pipx install {server_binary}"
        )

    @staticmethod
    def _get_python_executable(project_path: Optional[Path] = None) -> Optional[str]:
        """Get Python executable for MCP server.

        Priority:
        1. Project venv (.venv/bin/python)
        2. Current Python if in pipx venv
        3. Python from server binary shebang
        4. Current Python (fallback)
        """
        # Check project venv
        if project_path:
            venv_python = project_path / ".venv" / "bin" / "python"
            if venv_python.exists():
                return str(venv_python)

        # Check if in pipx venv
        if "/pipx/venvs/" in sys.executable:
            return sys.executable

        # Check binary shebang
        mcp_binary = shutil.which("mcp-ticketer")
        if mcp_binary:
            try:
                with open(mcp_binary) as f:
                    shebang = f.readline().strip()
                    if shebang.startswith("#!") and "python" in shebang:
                        python_path = shebang[2:].strip()
                        if Path(python_path).exists():
                            return python_path
            except Exception:
                pass

        # Fallback to current Python
        return sys.executable

    @staticmethod
    def build_server_command(
        method: InstallMethod,
        server_binary: str = "mcp-ticketer",
        project_path: Optional[Path] = None,
        additional_args: Optional[list[str]] = None
    ) -> tuple[str, list[str]]:
        """Build complete command for MCP server.

        Returns:
            Tuple of (command, args)
        """
        additional_args = additional_args or []

        if method == InstallMethod.UV_RUN:
            return ("uv", ["run", server_binary, "mcp"] + additional_args)

        elif method == InstallMethod.DIRECT_BINARY:
            binary_path = shutil.which(server_binary)
            if not binary_path:
                raise CommandNotFoundError(f"Binary not found: {server_binary}")
            return (binary_path, ["mcp"] + additional_args)

        elif method == InstallMethod.PYTHON_MODULE:
            python_path = CommandBuilder._get_python_executable(project_path)
            return (python_path, ["-m", "mcp_ticketer.mcp.server"] + additional_args)

        else:
            raise ValueError(f"Unsupported installation method: {method}")

    @staticmethod
    def resolve_absolute_path(command: str) -> str:
        """Resolve command to absolute path if it's a binary.

        Args:
            command: Command string (may be relative or just binary name)

        Returns:
            Absolute path to command
        """
        # If already absolute, return as-is
        if Path(command).is_absolute():
            return command

        # If it's a known command (uv, python), search PATH
        resolved = shutil.which(command)
        if resolved:
            return resolved

        # Otherwise, treat as relative path and make absolute
        return str(Path(command).resolve())

    @staticmethod
    def mask_credentials(command: str, args: list[str], env: dict[str, str]) -> tuple[str, list[str], dict[str, str]]:
        """Mask sensitive values in command for logging.

        Returns:
            Tuple of (masked_command, masked_args, masked_env)
        """
        sensitive_keys = [
            "API_KEY", "TOKEN", "SECRET", "PASSWORD",
            "CREDENTIALS", "AUTH", "KEY"
        ]

        def is_sensitive(key: str) -> bool:
            return any(s in key.upper() for s in sensitive_keys)

        # Mask environment variables
        masked_env = {}
        for key, value in env.items():
            if is_sensitive(key):
                masked_env[key] = "***"
            else:
                masked_env[key] = value

        # Command and args don't typically contain secrets
        return (command, args, masked_env)
```

---

### 6. Installer Orchestrator (`installer.py`)

**Purpose**: Main entry point coordinating all components.

**Design Pattern**: Facade + Factory

```python
from typing import Optional


class MCPInstaller:
    """Universal MCP installer for any MCP server.

    Main entry point for library users.
    """

    def __init__(self, platform: Optional[Platform] = None):
        """Initialize installer.

        Args:
            platform: Specific platform to target (auto-detects if None)
        """
        self.platform_detector = PlatformDetectorRegistry()
        self.target_platform: Optional[DetectedPlatform] = None

        if platform:
            self.target_platform = self.platform_detector.detect_one(platform)
            if not self.target_platform:
                raise PlatformNotFoundError(f"Platform not detected: {platform}")

    @classmethod
    def auto_detect(cls, project_path: Optional[Path] = None) -> "MCPInstaller":
        """Auto-detect best platform and create installer.

        Detects all platforms and selects highest-confidence match.

        Args:
            project_path: Optional project directory for detection

        Returns:
            MCPInstaller configured for detected platform

        Raises:
            PlatformNotFoundError: If no platforms detected
        """
        detector = PlatformDetectorRegistry()
        platforms = detector.detect_all(project_path)

        if not platforms:
            raise PlatformNotFoundError(
                "No supported AI coding tools detected. "
                "Install Claude Code, Cursor, or another supported tool."
            )

        # Select highest-confidence platform
        best_platform = platforms[0]

        installer = cls()
        installer.target_platform = best_platform
        return installer

    def list_platforms(self, project_path: Optional[Path] = None) -> list[DetectedPlatform]:
        """List all detected platforms.

        Returns:
            List of detected platforms sorted by confidence
        """
        return self.platform_detector.detect_all(project_path)

    def install_server(
        self,
        name: str,
        command: Optional[str] = None,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
        description: Optional[str] = None,
        scope: ConfigScope = ConfigScope.PROJECT,
        force: bool = False,
        dry_run: bool = False
    ) -> InstallationResult:
        """Install MCP server on target platform.

        Args:
            name: Server name (e.g., "mcp-ticketer")
            command: Command to execute (auto-detected if None)
            args: Command arguments (default: ["mcp"])
            env: Environment variables
            description: Server description
            scope: Installation scope (project/global)
            force: Overwrite existing configuration
            dry_run: Simulate installation without changes

        Returns:
            InstallationResult with status and details
        """
        if not self.target_platform:
            raise PlatformNotFoundError("No platform selected. Use auto_detect() or specify platform.")

        # Auto-detect command if not provided
        if command is None:
            method, command, base_args = CommandBuilder.detect_installation_method(name)
        else:
            base_args = []
            method = InstallMethod.DIRECT_BINARY

        # Build server config
        server_config = MCPServerConfig(
            name=name,
            command=CommandBuilder.resolve_absolute_path(command),
            args=args or base_args,
            env=env or {},
            description=description
        )

        # Select installation strategy
        strategy = self._get_strategy_for_platform(self.target_platform.platform)

        # Install
        return strategy.install(
            platform=self.target_platform,
            server_config=server_config,
            scope=scope,
            force=force,
            dry_run=dry_run
        )

    def list_servers(self) -> list[InstalledServer]:
        """List all installed MCP servers on target platform.

        Returns:
            List of installed servers with validation status
        """
        if not self.target_platform:
            raise PlatformNotFoundError("No platform selected.")

        inspector = MCPInspector(self.target_platform)
        return inspector.list_servers()

    def validate_installation(self, server_name: str) -> list[ConfigIssue]:
        """Validate specific server installation.

        Returns:
            List of issues found (empty if valid)
        """
        if not self.target_platform:
            raise PlatformNotFoundError("No platform selected.")

        inspector = MCPInspector(self.target_platform)
        return inspector.validate_server(server_name)

    def fix_server(self, server_name: str, dry_run: bool = False) -> InstallationResult:
        """Auto-fix issues with server configuration.

        Args:
            server_name: Name of server to fix
            dry_run: Simulate fixes without applying

        Returns:
            InstallationResult with fix status
        """
        if not self.target_platform:
            raise PlatformNotFoundError("No platform selected.")

        inspector = MCPInspector(self.target_platform)
        return inspector.fix_server(server_name, dry_run)

    def uninstall_server(self, server_name: str, dry_run: bool = False) -> InstallationResult:
        """Remove server from platform configuration.

        Args:
            server_name: Name of server to remove
            dry_run: Simulate removal without changes

        Returns:
            InstallationResult with removal status
        """
        if not self.target_platform:
            raise PlatformNotFoundError("No platform selected.")

        strategy = self._get_strategy_for_platform(self.target_platform.platform)
        return strategy.uninstall(self.target_platform, server_name, dry_run)

    def _get_strategy_for_platform(self, platform: Platform) -> InstallationStrategy:
        """Get installation strategy for platform."""
        # Try native CLI first
        if platform in [Platform.CLAUDE_CODE, Platform.CLAUDE_DESKTOP]:
            native_strategy = NativeCLIStrategy()
            if shutil.which("claude"):
                return native_strategy
            # Fallback to JSON if CLI not available
            return JSONConfigStrategy()

        elif platform == Platform.CODEX:
            return TOMLConfigStrategy()

        else:
            return JSONConfigStrategy()
```

---

## Supporting Modules

### 7. Types (`types.py`)

Complete type definitions for public API surface.

```python
"""Type definitions for py-mcp-installer-service."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Protocol


# Core Enums
class Platform(Enum):
    """Supported AI coding tool platforms."""
    CLAUDE_CODE = "claude-code"
    CLAUDE_DESKTOP = "claude-desktop"
    CURSOR = "cursor"
    AUGGIE = "auggie"
    CODEX = "codex"
    GEMINI = "gemini"
    WINDSURF = "windsurf"
    ANTIGRAVITY = "antigravity"


class ConfigScope(Enum):
    """Configuration scope."""
    PROJECT = "project"  # Project-level config
    GLOBAL = "global"    # User-level config
    BOTH = "both"        # Supports both scopes


class InstallMethod(Enum):
    """Installation methods for MCP servers."""
    UV_RUN = "uv-run"
    PIPX = "pipx"
    DIRECT_BINARY = "direct"
    PYTHON_MODULE = "python-module"


class ConfigFormat(Enum):
    """Configuration file formats."""
    JSON = "json"
    TOML = "toml"


class IssueType(Enum):
    """Types of configuration issues."""
    LEGACY_SERVER = "legacy-server"
    MISSING_PATH = "missing-path"
    INVALID_JSON = "invalid-json"
    MISSING_REQUIRED_FIELD = "missing-field"
    INVALID_ENV_VAR = "invalid-env"
    WRONG_TRANSPORT = "wrong-transport"
    PERMISSION_ERROR = "permission-error"


class IssueSeverity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Dataclasses
@dataclass
class DetectedPlatform:
    """Result of platform detection."""
    platform: Platform
    display_name: str
    config_path: Path
    is_installed: bool
    scope: ConfigScope
    confidence: float  # 0.0-1.0
    executable_path: Optional[str] = None
    issues: list[str] = field(default_factory=list)


@dataclass
class MCPServerConfig:
    """MCP server configuration."""
    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    description: Optional[str] = None
    cwd: Optional[str] = None
    timeout: Optional[int] = None
    trust: bool = False


@dataclass
class InstallationResult:
    """Result of installation operation."""
    success: bool
    platform: Platform
    server_name: str
    config_path: Path
    method: InstallMethod
    message: str
    warnings: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)


@dataclass
class ConfigIssue:
    """Detected configuration issue."""
    type: IssueType
    severity: IssueSeverity
    server_name: str
    message: str
    fix_suggestion: str
    auto_fixable: bool = False


@dataclass
class InstalledServer:
    """Information about installed MCP server."""
    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    config_path: Path
    platform: Platform
    is_valid: bool
    issues: list[ConfigIssue]


# Protocols
class PlatformDetector(Protocol):
    """Protocol for platform detection implementations."""

    def detect(self, project_path: Optional[Path] = None) -> Optional[DetectedPlatform]:
        """Detect if this platform is installed."""
        ...


class InstallationStrategy(Protocol):
    """Protocol for installation strategy implementations."""

    def supports_platform(self, platform: Platform) -> bool:
        """Check if strategy supports platform."""
        ...

    def install(
        self,
        platform: DetectedPlatform,
        server_config: MCPServerConfig,
        scope: ConfigScope,
        force: bool = False,
        dry_run: bool = False
    ) -> InstallationResult:
        """Install MCP server."""
        ...
```

---

### 8. Utilities (`utils.py`)

Common utility functions.

```python
"""Utility functions for py-mcp-installer-service."""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Optional


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for library.

    Args:
        verbose: Enable debug logging

    Returns:
        Configured logger
    """
    logger = logging.getLogger("py_mcp_installer")

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Only add handler if none exist
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(levelname)s] %(name)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def find_command_path(command: str) -> Optional[str]:
    """Find absolute path to command in PATH.

    Args:
        command: Command name to find

    Returns:
        Absolute path to command, or None if not found
    """
    return shutil.which(command)


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, creating if necessary.

    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON file atomically with temp file + rename.

    Args:
        path: Target file path
        data: Data to write as JSON
    """
    import tempfile

    ensure_directory(path.parent)

    # Write to temp file
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp"
    )

    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        # Atomic rename
        os.replace(temp_path, path)

    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def validate_json_file(path: Path) -> tuple[bool, Optional[str]]:
    """Validate JSON file is parseable.

    Args:
        path: Path to JSON file

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path.exists():
        return (False, "File does not exist")

    try:
        with path.open() as f:
            content = f.read().strip()
            if not content:
                return (True, None)  # Empty file is valid
            json.loads(content)
        return (True, None)

    except json.JSONDecodeError as e:
        return (False, f"Invalid JSON: {e}")

    except Exception as e:
        return (False, f"Error reading file: {e}")


def mask_sensitive_value(key: str, value: str) -> str:
    """Mask sensitive values for logging.

    Args:
        key: Environment variable or config key
        value: Value to potentially mask

    Returns:
        Masked value if sensitive, original otherwise
    """
    sensitive_keywords = [
        "KEY", "TOKEN", "SECRET", "PASSWORD",
        "CREDENTIALS", "AUTH", "API"
    ]

    if any(kw in key.upper() for kw in sensitive_keywords):
        return "***"

    return value


def format_command_for_display(command: str, args: list[str], env: dict[str, str]) -> str:
    """Format command for human-readable display.

    Args:
        command: Command to execute
        args: Command arguments
        env: Environment variables

    Returns:
        Formatted command string with masked credentials
    """
    cmd_parts = [command] + args

    # Add environment variables (masked)
    env_parts = []
    for key, value in env.items():
        masked_value = mask_sensitive_value(key, value)
        env_parts.append(f"{key}={masked_value}")

    if env_parts:
        return f"{' '.join(env_parts)} {' '.join(cmd_parts)}"

    return ' '.join(cmd_parts)


def get_platform_config_location(platform: Platform) -> Path:
    """Get default config file location for platform.

    Args:
        platform: Platform to get config location for

    Returns:
        Path to config file
    """
    import sys

    if platform == Platform.CLAUDE_CODE:
        # Try new location first
        new_config = Path.home() / ".config" / "claude" / "mcp.json"
        if new_config.exists():
            return new_config
        return Path.home() / ".claude.json"

    elif platform == Platform.CLAUDE_DESKTOP:
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        elif sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            return Path(appdata) / "Claude" / "claude_desktop_config.json"
        else:  # Linux
            return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

    elif platform == Platform.CURSOR:
        return Path.home() / ".cursor" / "mcp.json"

    elif platform == Platform.AUGGIE:
        return Path.home() / ".augment" / "settings.json"

    elif platform == Platform.CODEX:
        return Path.home() / ".codex" / "config.toml"

    elif platform == Platform.GEMINI:
        return Path.home() / ".gemini" / "settings.json"

    elif platform == Platform.WINDSURF:
        return Path.home() / ".codeium" / "windsurf" / "mcp_config.json"

    elif platform == Platform.ANTIGRAVITY:
        # Not yet documented
        raise NotImplementedError("Antigravity config location not yet known")

    else:
        raise ValueError(f"Unknown platform: {platform}")
```

---

### 9. Exceptions (`exceptions.py`)

Custom exception hierarchy with recovery suggestions.

```python
"""Custom exceptions for py-mcp-installer-service."""


class MCPInstallerError(Exception):
    """Base exception for all library errors."""

    def __init__(self, message: str, recovery_suggestion: str = ""):
        self.message = message
        self.recovery_suggestion = recovery_suggestion
        super().__init__(message)

    def __str__(self):
        if self.recovery_suggestion:
            return f"{self.message}\n\nSuggestion: {self.recovery_suggestion}"
        return self.message


class PlatformNotFoundError(MCPInstallerError):
    """No supported platform detected."""

    def __init__(self, message: str = "No supported AI coding tools detected"):
        super().__init__(
            message,
            recovery_suggestion=(
                "Install one of the supported tools:\n"
                "  - Claude Code: https://claude.ai/download\n"
                "  - Cursor: https://cursor.sh\n"
                "  - Windsurf: https://codeium.com/windsurf"
            )
        )


class ConfigurationError(MCPInstallerError):
    """Configuration file error."""

    def __init__(self, message: str, config_path: str = ""):
        recovery = f"Fix or delete the config file: {config_path}" if config_path else ""
        super().__init__(message, recovery_suggestion=recovery)


class CommandNotFoundError(MCPInstallerError):
    """Required command not found in PATH."""

    def __init__(self, command: str):
        super().__init__(
            f"Command not found: {command}",
            recovery_suggestion=f"Install the command or ensure it's in PATH"
        )


class InstallationFailedError(MCPInstallerError):
    """Installation operation failed."""
    pass


class ValidationError(MCPInstallerError):
    """Configuration validation failed."""
    pass


class BackupError(MCPInstallerError):
    """Backup operation failed."""

    def __init__(self, message: str):
        super().__init__(
            message,
            recovery_suggestion="Check file permissions and disk space"
        )
```

---

## Platform-Specific Implementations

### 10. Platform Modules (`platforms/`)

Each platform has a dedicated detector implementation.

```python
# platforms/claude_code.py

from pathlib import Path
from typing import Optional
from ..types import DetectedPlatform, Platform, ConfigScope
from ..utils import validate_json_file


class ClaudeCodeDetector:
    """Detector for Claude Code platform."""

    def detect(self, project_path: Optional[Path] = None) -> Optional[DetectedPlatform]:
        """Detect Claude Code installation.

        Detection strategy:
        1. Check new config location (~/.config/claude/mcp.json)
        2. Fallback to legacy location (~/.claude.json)
        3. Validate JSON format
        4. Check for claude CLI
        """
        # Priority 1: New location
        new_config = Path.home() / ".config" / "claude" / "mcp.json"
        old_config = Path.home() / ".claude.json"

        config_path = new_config if new_config.exists() else old_config

        if not config_path.exists():
            return None

        # Validate JSON
        is_valid, error = validate_json_file(config_path)

        issues = []
        if not is_valid:
            issues.append(f"Invalid config: {error}")

        # Check CLI availability
        cli_available = shutil.which("claude") is not None

        # Calculate confidence
        confidence = 0.0
        if config_path.exists():
            confidence += 0.5
        if is_valid:
            confidence += 0.3
        if cli_available:
            confidence += 0.2

        return DetectedPlatform(
            platform=Platform.CLAUDE_CODE,
            display_name="Claude Code",
            config_path=config_path,
            is_installed=is_valid,
            scope=ConfigScope.PROJECT,
            confidence=confidence,
            executable_path=shutil.which("claude"),
            issues=issues
        )


# Similar implementations for other platforms...
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_platform_detector.py

import pytest
from pathlib import Path
from py_mcp_installer import PlatformDetectorRegistry, Platform


def test_detect_claude_code(tmp_path, monkeypatch):
    """Test Claude Code detection with valid config."""
    # Setup mock config
    config_dir = tmp_path / ".config" / "claude"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "mcp.json"
    config_file.write_text('{"mcpServers": {}}')

    # Mock home directory
    monkeypatch.setenv("HOME", str(tmp_path))

    # Detect
    detector = PlatformDetectorRegistry()
    result = detector.detect_one(Platform.CLAUDE_CODE)

    assert result is not None
    assert result.platform == Platform.CLAUDE_CODE
    assert result.is_installed
    assert result.confidence > 0.5


def test_detect_invalid_json(tmp_path, monkeypatch):
    """Test detection with invalid JSON config."""
    config_dir = tmp_path / ".config" / "claude"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "mcp.json"
    config_file.write_text('{"invalid": json}')

    monkeypatch.setenv("HOME", str(tmp_path))

    detector = PlatformDetectorRegistry()
    result = detector.detect_one(Platform.CLAUDE_CODE)

    assert result is not None
    assert not result.is_installed
    assert len(result.issues) > 0
```

### Integration Tests

```python
# tests/integration/test_installation.py

import pytest
from py_mcp_installer import MCPInstaller, ConfigScope


def test_full_installation_flow(tmp_path, monkeypatch):
    """Test complete installation flow."""
    # Setup mock environment
    setup_mock_claude_code(tmp_path, monkeypatch)

    # Create installer
    installer = MCPInstaller.auto_detect()

    # Install server (dry run)
    result = installer.install_server(
        name="test-server",
        command="/usr/bin/test-server",
        args=["serve"],
        env={"API_KEY": "test-key"},
        scope=ConfigScope.PROJECT,
        dry_run=True
    )

    assert result.success
    assert "DRY RUN" in result.message

    # Install server (actual)
    result = installer.install_server(
        name="test-server",
        command="/usr/bin/test-server",
        args=["serve"],
        env={"API_KEY": "test-key"},
        scope=ConfigScope.PROJECT
    )

    assert result.success

    # Verify installation
    servers = installer.list_servers()
    assert len(servers) == 1
    assert servers[0].name == "test-server"
    assert servers[0].is_valid
```

---

## Public API Surface

### High-Level API (Recommended)

```python
from py_mcp_installer import MCPInstaller

# Auto-detect and install
installer = MCPInstaller.auto_detect()
result = installer.install_server(
    name="mcp-ticketer",
    env={"LINEAR_API_KEY": "..."}
)

# List servers
servers = installer.list_servers()

# Validate
issues = installer.validate_installation("mcp-ticketer")

# Fix
installer.fix_server("mcp-ticketer")
```

### Low-Level API (Advanced)

```python
from py_mcp_installer import (
    PlatformDetectorRegistry,
    JSONConfigStrategy,
    MCPServerConfig,
    Platform,
    ConfigScope
)

# Manual detection
detector = PlatformDetectorRegistry()
platforms = detector.detect_all()

# Manual installation
platform = platforms[0]
strategy = JSONConfigStrategy()
config = MCPServerConfig(
    name="mcp-ticketer",
    command="/usr/bin/mcp-ticketer",
    args=["mcp"],
    env={"API_KEY": "..."}
)
result = strategy.install(platform, config, ConfigScope.PROJECT)
```

---

## Extension Points

### Adding New Platforms

```python
# 1. Create detector
class MyPlatformDetector:
    def detect(self, project_path=None):
        # Custom detection logic
        ...

# 2. Register detector
from py_mcp_installer import PlatformDetectorRegistry, Platform

# Extend enum
Platform.MY_PLATFORM = "my-platform"

# Register
registry = PlatformDetectorRegistry()
registry.register(Platform.MY_PLATFORM, MyPlatformDetector())
```

### Custom Installation Strategies

```python
class CustomStrategy(InstallationStrategy):
    def supports_platform(self, platform):
        return platform == Platform.MY_PLATFORM

    def install(self, platform, server_config, scope, force, dry_run):
        # Custom installation logic
        ...

# Use custom strategy
installer = MCPInstaller(platform=Platform.MY_PLATFORM)
installer._strategy = CustomStrategy()
```

---

## Implementation Phases

### Phase 1: Core Abstractions (Week 1)
- [ ] Type definitions (`types.py`)
- [ ] Base exceptions (`exceptions.py`)
- [ ] Utilities (`utils.py`)
- [ ] ConfigManager with atomic operations
- [ ] Unit tests for core modules

### Phase 2: Platform Detection (Week 2)
- [ ] PlatformDetector protocol
- [ ] Claude Code detector
- [ ] Claude Desktop detector
- [ ] Cursor detector
- [ ] Unit tests for detectors

### Phase 3: Installation Strategies (Week 3)
- [ ] InstallationStrategy base class
- [ ] NativeCLIStrategy
- [ ] JSONConfigStrategy
- [ ] TOMLConfigStrategy
- [ ] CommandBuilder
- [ ] Integration tests

### Phase 4: Inspector & Validator (Week 4)
- [ ] MCPInspector implementation
- [ ] Legacy server detection
- [ ] Auto-migration logic
- [ ] Validation rules
- [ ] Fix suggestions

### Phase 5: Orchestrator & Polish (Week 5)
- [ ] MCPInstaller facade
- [ ] Remaining platform detectors
- [ ] Comprehensive integration tests
- [ ] Documentation
- [ ] Examples

### Phase 6: CLI & Packaging (Week 6)
- [ ] CLI tool (`mcp-installer` command)
- [ ] PyPI packaging
- [ ] CI/CD setup
- [ ] README and guides
- [ ] Release v1.0.0

---

## Dependencies

### Required (Runtime)
```toml
[dependencies]
python = "^3.10"
tomli = "^2.0.0"  # TOML reading (stdlib in 3.11+)
tomli-w = "^1.0.0"  # TOML writing
```

### Optional (Development)
```toml
[dev-dependencies]
pytest = "^7.0.0"
pytest-cov = "^4.0.0"
pytest-mock = "^3.10.0"
mypy = "^1.0.0"
ruff = "^0.1.0"
```

**Zero application dependencies** - fully standalone library.

---

## Success Metrics

### Code Quality
- ✅ 100% type coverage (mypy strict mode)
- ✅ >90% test coverage
- ✅ Zero external runtime dependencies (except TOML)
- ✅ All public APIs documented

### Functionality
- ✅ Supports 8/8 platforms (Antigravity TBD)
- ✅ Cross-platform (macOS, Linux, Windows)
- ✅ Atomic config updates with rollback
- ✅ Auto-migration of legacy servers

### Usability
- ✅ Single-line installation: `MCPInstaller.auto_detect().install_server("mcp-ticketer")`
- ✅ Clear error messages with recovery suggestions
- ✅ Dry-run mode for all operations
- ✅ Comprehensive documentation

---

## Non-Goals

- ❌ Managing MCP server lifecycle (start/stop/restart)
- ❌ Downloading/installing MCP server binaries
- ❌ GUI or web interface
- ❌ Server discovery/marketplace
- ❌ Configuration validation beyond MCP format
- ❌ Platform-specific bug workarounds

---

## Conclusion

This architecture provides a production-ready, extensible foundation for universal MCP server installation. The design prioritizes:

1. **Reliability**: Atomic operations, backup/restore, validation
2. **Flexibility**: Plugin architecture, multiple strategies
3. **Usability**: Auto-detection, clear errors, dry-run mode
4. **Maintainability**: Type-safe, well-tested, documented

The library can be used standalone, as a submodule, or integrated into other Python projects requiring MCP installation capabilities.

**Next Action**: Begin Phase 1 implementation with core abstractions and configuration management.
