"""Type definitions for py-mcp-installer-service.

This module provides comprehensive type definitions for the entire library,
including enums, dataclasses, and protocols for platform detection and
installation strategies.

Design Philosophy:
- Use Python 3.10+ syntax (list[str], dict[str, Any], Path | None)
- 100% type coverage for mypy --strict
- Immutable dataclasses where possible (frozen=True)
- Clear separation between public API and internal types
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# ============================================================================
# Core Enums
# ============================================================================


class Platform(str, Enum):
    """Supported AI coding tool platforms.

    Each platform has its own configuration format and installation method.
    """

    CLAUDE_CODE = "claude_code"
    CLAUDE_DESKTOP = "claude_desktop"
    CURSOR = "cursor"
    AUGGIE = "auggie"
    CODEX = "codex"
    GEMINI_CLI = "gemini_cli"
    WINDSURF = "windsurf"
    ANTIGRAVITY = "antigravity"
    UNKNOWN = "unknown"


class InstallMethod(str, Enum):
    """Installation methods for MCP servers.

    Priority order (fastest to slowest):
    1. UV_RUN: uv run mcp-ticketer mcp (recommended, fastest)
    2. PIPX: mcp-ticketer (installed via pipx)
    3. DIRECT: Direct binary in PATH
    4. PYTHON_MODULE: python -m mcp_ticketer.mcp.server (fallback)
    """

    UV_RUN = "uv_run"
    PIPX = "pipx"
    DIRECT = "direct"
    PYTHON_MODULE = "python_module"


class Scope(str, Enum):
    """Configuration scope for MCP server installation.

    - PROJECT: Project-level configuration (.claude.json, .cursor/mcp.json)
    - GLOBAL: User-level configuration (~/.config/claude/mcp.json)
    - BOTH: Platform supports both scopes
    """

    PROJECT = "project"
    GLOBAL = "global"
    BOTH = "both"


class ConfigFormat(str, Enum):
    """Configuration file formats supported by platforms.

    - JSON: Most platforms (Claude, Cursor, Auggie, Windsurf, Gemini)
    - TOML: Codex uses TOML format
    """

    JSON = "json"
    TOML = "toml"


class InstallationStrategy(str, Enum):
    """Installation strategies for different platforms.

    - NATIVE_CLI: Use platform's native CLI (claude mcp add)
    - JSON_MANIPULATION: Direct JSON config file modification
    - TOML_MANIPULATION: Direct TOML config file modification
    """

    NATIVE_CLI = "native_cli"
    JSON_MANIPULATION = "json_manipulation"
    TOML_MANIPULATION = "toml_manipulation"


# ============================================================================
# Dataclasses
# ============================================================================


@dataclass(frozen=True)
class MCPServerConfig:
    """MCP server configuration for installation.

    This represents the complete configuration needed to install an MCP server
    on any supported platform.

    Attributes:
        name: Unique server identifier (e.g., "mcp-ticketer")
        command: Executable command (e.g., "uv", "/usr/bin/mcp-ticketer")
        args: Command arguments (e.g., ["run", "mcp-ticketer", "mcp"])
        env: Environment variables (e.g., {"LINEAR_API_KEY": "..."})
        description: Human-readable server description

    Example:
        >>> config = MCPServerConfig(
        ...     name="mcp-ticketer",
        ...     command="uv",
        ...     args=["run", "mcp-ticketer", "mcp"],
        ...     env={"LINEAR_API_KEY": "lin_api_..."}
        ... )
    """

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    description: str = ""


@dataclass(frozen=True)
class PlatformInfo:
    """Information about a detected platform.

    Contains all information needed to work with a detected AI coding tool
    platform, including confidence scoring for multi-platform environments.

    Attributes:
        platform: Detected platform enum
        confidence: Detection confidence (0.0-1.0)
            - 1.0: Config exists, valid, CLI available
            - 0.8: Config exists, valid, no CLI needed
            - 0.6: Config exists but invalid, CLI available
            - 0.4: Config exists but invalid, no CLI
            - 0.0: Platform not detected
        config_path: Path to platform's config file (None if not found)
        cli_available: Whether platform CLI is available in PATH
        scope_support: Which configuration scopes the platform supports

    Example:
        >>> info = PlatformInfo(
        ...     platform=Platform.CLAUDE_CODE,
        ...     confidence=1.0,
        ...     config_path=Path.home() / ".config/claude/mcp.json",
        ...     cli_available=True,
        ...     scope_support=Scope.BOTH
        ... )
    """

    platform: Platform
    confidence: float  # 0.0-1.0
    config_path: Path | None = None
    cli_available: bool = False
    scope_support: Scope = Scope.BOTH


@dataclass(frozen=True)
class InstallationResult:
    """Result of an MCP server installation operation.

    Provides comprehensive information about installation success/failure,
    including error details and recovery suggestions.

    Attributes:
        success: Whether installation succeeded
        platform: Target platform
        server_name: Name of installed server
        method: Installation method used
        message: Human-readable status message
        config_path: Path to updated config file (None on failure)
        error: Exception that caused failure (None on success)

    Example (success):
        >>> result = InstallationResult(
        ...     success=True,
        ...     platform=Platform.CLAUDE_CODE,
        ...     server_name="mcp-ticketer",
        ...     method=InstallMethod.UV_RUN,
        ...     message="Successfully installed mcp-ticketer",
        ...     config_path=Path.home() / ".config/claude/mcp.json"
        ... )

    Example (failure):
        >>> result = InstallationResult(
        ...     success=False,
        ...     platform=Platform.CLAUDE_CODE,
        ...     server_name="mcp-ticketer",
        ...     method=InstallMethod.UV_RUN,
        ...     message="Installation failed: config file not writable",
        ...     error=PermissionError("Permission denied")
        ... )
    """

    success: bool
    platform: Platform
    server_name: str
    method: InstallMethod
    message: str
    config_path: Path | None = None
    error: Exception | None = None


# ============================================================================
# Type Aliases
# ============================================================================

# JSON-serializable dictionary type
JsonDict = dict[str, Any]

# Environment variables dictionary
EnvDict = dict[str, str]

# Command arguments list
ArgsList = list[str]
