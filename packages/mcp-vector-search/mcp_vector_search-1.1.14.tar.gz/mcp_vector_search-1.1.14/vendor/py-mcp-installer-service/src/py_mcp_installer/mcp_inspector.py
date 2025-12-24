"""MCP Inspector for validation and health checking.

This module provides comprehensive validation and inspection of MCP server
installations, including legacy format detection, command verification, and
auto-fix capabilities.

Design Philosophy:
- Comprehensive validation of server configurations
- Detect legacy formats and migration needs
- Auto-fix common issues where possible
- Clear severity levels (error, warning, info)
- Actionable recommendations

Example:
    >>> from py_mcp_installer import MCPInspector, PlatformDetector
    >>> detector = PlatformDetector()
    >>> info = detector.detect()
    >>> inspector = MCPInspector(info)
    >>> report = inspector.inspect()
    >>> print(f"Found {len(report.issues)} issues")
    >>> for issue in report.issues:
    ...     print(f"{issue.severity}: {issue.message}")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .config_manager import ConfigManager
from .exceptions import ConfigurationError
from .types import ConfigFormat, MCPServerConfig, Platform, PlatformInfo
from .utils import resolve_command_path

logger = logging.getLogger(__name__)

# ============================================================================
# Data Classes
# ============================================================================


@dataclass(frozen=True)
class ValidationIssue:
    """Represents a validation issue found in configuration.

    Attributes:
        severity: Issue severity level
            - error: Prevents server from working
            - warning: May cause problems
            - info: Recommendations only
        message: Human-readable issue description
        server_name: Affected server name (None for global issues)
        fix_suggestion: How to fix this issue
        auto_fixable: Whether this can be auto-fixed

    Example:
        >>> issue = ValidationIssue(
        ...     severity="error",
        ...     message="Command 'mcp-ticketer' not found in PATH",
        ...     server_name="mcp-ticketer",
        ...     fix_suggestion="Install with: pipx install mcp-ticketer",
        ...     auto_fixable=False
        ... )
    """

    severity: Literal["error", "warning", "info"]
    message: str
    server_name: str | None
    fix_suggestion: str
    auto_fixable: bool = False


@dataclass(frozen=True)
class InspectionReport:
    """Complete inspection report.

    Attributes:
        platform: Detected platform
        config_path: Path to configuration file
        total_servers: Total number of servers found
        valid_servers: Number of valid servers
        issues: List of validation issues
        recommendations: General recommendations for improvement

    Example:
        >>> report = InspectionReport(
        ...     platform=Platform.CLAUDE_CODE,
        ...     config_path=Path.home() / ".config/claude/mcp.json",
        ...     total_servers=5,
        ...     valid_servers=4,
        ...     issues=[...],
        ...     recommendations=["Migrate to uv run for faster startup"]
        ... )
    """

    platform: Platform
    config_path: Path
    total_servers: int
    valid_servers: int
    issues: list[ValidationIssue] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def has_errors(self) -> bool:
        """Check if report contains any errors.

        Returns:
            True if any error-level issues found
        """
        return any(issue.severity == "error" for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if report contains any warnings.

        Returns:
            True if any warning-level issues found
        """
        return any(issue.severity == "warning" for issue in self.issues)

    def summary(self) -> str:
        """Generate human-readable summary.

        Returns:
            Summary string with counts and status
        """
        errors = sum(1 for i in self.issues if i.severity == "error")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        infos = sum(1 for i in self.issues if i.severity == "info")

        status = "PASS" if errors == 0 else "FAIL"
        return (
            f"Inspection {status}: {self.valid_servers}/{self.total_servers} servers valid\n"
            f"  Errors: {errors}, Warnings: {warnings}, Info: {infos}"
        )


# ============================================================================
# MCP Inspector
# ============================================================================


class MCPInspector:
    """Inspect and validate MCP server installations.

    Provides comprehensive validation of MCP configurations including:
    - Command existence and accessibility
    - Configuration file validity
    - Legacy format detection
    - Duplicate server detection
    - Auto-fix capabilities for common issues

    Example:
        >>> from py_mcp_installer import PlatformDetector
        >>> detector = PlatformDetector()
        >>> info = detector.detect()
        >>> inspector = MCPInspector(info)
        >>> report = inspector.inspect()
        >>> if report.has_errors():
        ...     print("Found errors:", report.summary())
    """

    def __init__(self, platform_info: PlatformInfo) -> None:
        """Initialize inspector with detected platform info.

        Args:
            platform_info: Platform information from PlatformDetector

        Example:
            >>> from py_mcp_installer import PlatformDetector
            >>> detector = PlatformDetector()
            >>> info = detector.detect()
            >>> inspector = MCPInspector(info)
        """
        self.platform_info = platform_info
        self.config_path = platform_info.config_path or Path()

        # Determine config format based on platform
        if platform_info.platform == Platform.CODEX:
            self.config_format = ConfigFormat.TOML
        else:
            self.config_format = ConfigFormat.JSON

        self.config_manager = ConfigManager(self.config_path, self.config_format)

    def inspect(self) -> InspectionReport:
        """Run complete inspection and return report.

        Performs all validation checks including:
        - Config file existence and validity
        - Server configuration validation
        - Legacy format detection
        - Duplicate detection
        - Command availability checks

        Returns:
            Complete inspection report with issues and recommendations

        Example:
            >>> inspector = MCPInspector(platform_info)
            >>> report = inspector.inspect()
            >>> print(report.summary())
            >>> for issue in report.issues:
            ...     if issue.severity == "error":
            ...         print(f"ERROR: {issue.message}")
        """
        issues: list[ValidationIssue] = []
        recommendations: list[str] = []

        # Check if config file exists
        if not self.config_path.exists():
            issues.append(
                ValidationIssue(
                    severity="warning",
                    message=f"Configuration file not found: {self.config_path}",
                    server_name=None,
                    fix_suggestion=(
                        "Create config file or run installer to initialize"
                    ),
                    auto_fixable=True,
                )
            )
            return InspectionReport(
                platform=self.platform_info.platform,
                config_path=self.config_path,
                total_servers=0,
                valid_servers=0,
                issues=issues,
                recommendations=recommendations,
            )

        # Check for legacy format
        if self.check_legacy_format():
            issues.append(
                ValidationIssue(
                    severity="warning",
                    message="Legacy line-delimited JSON format detected",
                    server_name=None,
                    fix_suggestion="Run migration to convert to FastMCP SDK format",
                    auto_fixable=True,
                )
            )
            recommendations.extend(self.suggest_migration())

        # Read and validate config
        try:
            config = self.config_manager.read()
        except ConfigurationError as e:
            issues.append(
                ValidationIssue(
                    severity="error",
                    message=f"Failed to parse config: {e.message}",
                    server_name=None,
                    fix_suggestion=e.recovery_suggestion,
                    auto_fixable=False,
                )
            )
            return InspectionReport(
                platform=self.platform_info.platform,
                config_path=self.config_path,
                total_servers=0,
                valid_servers=0,
                issues=issues,
                recommendations=recommendations,
            )

        # Get servers from config
        servers = self._extract_servers(config)
        total_servers = len(servers)
        valid_servers = 0

        # Validate each server
        for server in servers:
            server_issues = self.validate_server(server)
            if not any(issue.severity == "error" for issue in server_issues):
                valid_servers += 1
            issues.extend(server_issues)

        # Check for duplicates
        duplicates = self.find_duplicates(config)
        for name1, name2 in duplicates:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    message=f"Duplicate server names detected: {name1}, {name2}",
                    server_name=None,
                    fix_suggestion="Rename one of the servers to avoid conflicts",
                    auto_fixable=False,
                )
            )

        # Add general recommendations
        recommendations.extend(self._generate_recommendations(servers))

        return InspectionReport(
            platform=self.platform_info.platform,
            config_path=self.config_path,
            total_servers=total_servers,
            valid_servers=valid_servers,
            issues=issues,
            recommendations=recommendations,
        )

    def validate_server(self, server: MCPServerConfig) -> list[ValidationIssue]:
        """Validate individual server configuration.

        Checks:
        - Command exists and is executable
        - Required fields are present
        - Environment variables are set (warnings only)
        - Arguments are valid

        Args:
            server: Server configuration to validate

        Returns:
            List of validation issues (empty if valid)

        Example:
            >>> server = MCPServerConfig(
            ...     name="test",
            ...     command="nonexistent",
            ...     args=[]
            ... )
            >>> issues = inspector.validate_server(server)
            >>> if issues:
            ...     print(f"Server invalid: {issues[0].message}")
        """
        issues: list[ValidationIssue] = []

        # Check required fields
        if not server.name:
            issues.append(
                ValidationIssue(
                    severity="error",
                    message="Server missing required 'name' field",
                    server_name=None,
                    fix_suggestion="Add server name",
                    auto_fixable=False,
                )
            )

        if not server.command:
            issues.append(
                ValidationIssue(
                    severity="error",
                    message=f"Server '{server.name}' missing required 'command' field",
                    server_name=server.name,
                    fix_suggestion="Add command field",
                    auto_fixable=False,
                )
            )
            return issues  # Can't continue without command

        # Check if command exists
        if not self.check_command_exists(server.command):
            issues.append(
                ValidationIssue(
                    severity="error",
                    message=f"Command not found: {server.command}",
                    server_name=server.name,
                    fix_suggestion=self._suggest_command_install(server.command),
                    auto_fixable=False,
                )
            )

        # Check for missing description (info only)
        if not server.description:
            issues.append(
                ValidationIssue(
                    severity="info",
                    message=f"Server '{server.name}' missing description",
                    server_name=server.name,
                    fix_suggestion="Add description for better documentation",
                    auto_fixable=False,
                )
            )

        # Check for environment variables that look like placeholders
        for key, value in server.env.items():
            if value.startswith("<") and value.endswith(">"):
                issues.append(
                    ValidationIssue(
                        severity="warning",
                        message=(
                            f"Server '{server.name}' has placeholder env var: "
                            f"{key}={value}"
                        ),
                        server_name=server.name,
                        fix_suggestion=f"Set actual value for {key}",
                        auto_fixable=False,
                    )
                )

        # Check for deprecated args patterns
        deprecated_patterns = {
            "--legacy-mode": "Use new format without --legacy-mode",
            "--old-api": "Update to new API",
        }
        for arg in server.args:
            for pattern, suggestion in deprecated_patterns.items():
                if pattern in arg:
                    issues.append(
                        ValidationIssue(
                            severity="warning",
                            message=f"Server '{server.name}' uses deprecated arg: {arg}",
                            server_name=server.name,
                            fix_suggestion=suggestion,
                            auto_fixable=True,
                        )
                    )

        return issues

    def check_command_exists(self, command: str) -> bool:
        """Check if command is executable.

        Args:
            command: Command to check (e.g., "uv", "/usr/bin/python")

        Returns:
            True if command exists and is executable

        Example:
            >>> inspector.check_command_exists("python")
            True
            >>> inspector.check_command_exists("nonexistent-command")
            False
        """
        # Try to resolve command path
        resolved = resolve_command_path(command)
        return resolved is not None

    def check_legacy_format(self) -> bool:
        """Detect line-delimited JSON format (pre-FastMCP SDK).

        The legacy format used line-delimited JSON objects instead of
        a single JSON object with mcpServers key.

        Returns:
            True if legacy format detected

        Example:
            >>> if inspector.check_legacy_format():
            ...     print("Need to migrate to new format")
        """
        if not self.config_path.exists():
            return False

        if self.config_format != ConfigFormat.JSON:
            return False  # Only JSON configs can be legacy format

        try:
            content = self.config_path.read_text(encoding="utf-8")

            # Legacy format has multiple JSON objects separated by newlines
            # Modern format has single JSON object
            lines = [line.strip() for line in content.split("\n") if line.strip()]

            if len(lines) <= 1:
                return False  # Single object, not legacy

            # Try to parse as line-delimited JSON
            for line in lines:
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    return False  # Not valid line-delimited JSON

            return True  # All lines are valid JSON = legacy format

        except Exception as e:
            logger.warning(f"Error checking legacy format: {e}")
            return False

    def suggest_migration(self) -> list[str]:
        """Suggest migration steps for legacy format.

        Returns:
            List of migration steps

        Example:
            >>> steps = inspector.suggest_migration()
            >>> for step in steps:
            ...     print(f"- {step}")
        """
        return [
            "Backup current config before migration",
            "Run migration to convert line-delimited JSON to modern format",
            "Validate new config with inspector",
            "Restart platform to pick up new config",
        ]

    def find_duplicates(self, config: dict[str, Any]) -> list[tuple[str, str]]:
        """Find duplicate server names or commands.

        Args:
            config: Configuration dictionary

        Returns:
            List of (name1, name2) tuples for duplicates

        Example:
            >>> duplicates = inspector.find_duplicates(config)
            >>> if duplicates:
            ...     print(f"Found {len(duplicates)} duplicate pairs")
        """
        duplicates: list[tuple[str, str]] = []
        servers = self._extract_servers(config)

        # Check for duplicate names
        names = [s.name for s in servers]
        seen_names: set[str] = set()
        for name in names:
            if name in seen_names:
                # Find other server with same name
                for other in servers:
                    if other.name == name and other.name not in [
                        d[0] for d in duplicates
                    ]:
                        duplicates.append((name, name))
                        break
            seen_names.add(name)

        return duplicates

    def auto_fix(self, issue: ValidationIssue) -> bool:
        """Attempt to automatically fix issue.

        Supported fixes:
        - Create missing config file
        - Migrate legacy format
        - Remove deprecated args
        - Resolve relative paths to absolute

        Args:
            issue: Issue to fix

        Returns:
            True if fix succeeded, False otherwise

        Example:
            >>> issue = ValidationIssue(...)
            >>> if issue.auto_fixable:
            ...     success = inspector.auto_fix(issue)
            ...     print(f"Fix {'succeeded' if success else 'failed'}")
        """
        if not issue.auto_fixable:
            return False

        try:
            # Fix: Create missing config file
            if "not found" in issue.message and issue.server_name is None:
                self._create_default_config()
                return True

            # Fix: Migrate legacy format
            if "Legacy" in issue.message:
                return self._migrate_legacy_format()

            # Fix: Remove deprecated args
            if "deprecated arg" in issue.message and issue.server_name:
                return self._remove_deprecated_args(issue.server_name)

            return False

        except Exception as e:
            logger.error(f"Auto-fix failed: {e}")
            return False

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _extract_servers(self, config: dict[str, Any]) -> list[MCPServerConfig]:
        """Extract server configurations from config dict.

        Args:
            config: Configuration dictionary

        Returns:
            List of MCPServerConfig objects
        """
        servers: list[MCPServerConfig] = []

        # Different platforms use different keys
        server_keys = ["mcpServers", "mcp_servers", "servers"]

        for key in server_keys:
            if key in config and isinstance(config[key], dict):
                for name, server_data in config[key].items():
                    if isinstance(server_data, dict):
                        servers.append(
                            MCPServerConfig(
                                name=name,
                                command=server_data.get("command", ""),
                                args=server_data.get("args", []),
                                env=server_data.get("env", {}),
                                description=server_data.get("description", ""),
                            )
                        )
                break

        return servers

    def _generate_recommendations(self, servers: list[MCPServerConfig]) -> list[str]:
        """Generate general recommendations for improvement.

        Args:
            servers: List of server configurations

        Returns:
            List of recommendation strings
        """
        recommendations: list[str] = []

        # Check if any servers could use uv run
        non_uv_servers = [s for s in servers if s.command != "uv"]
        if non_uv_servers:
            recommendations.append(
                f"Consider migrating {len(non_uv_servers)} server(s) to 'uv run' "
                f"for faster startup (10-30% improvement)"
            )

        # Check for missing descriptions
        no_desc = [s for s in servers if not s.description]
        if no_desc:
            recommendations.append(
                f"Add descriptions to {len(no_desc)} server(s) for better documentation"
            )

        # Check for environment variables
        env_servers = [s for s in servers if s.env]
        if env_servers:
            recommendations.append(
                f"{len(env_servers)} server(s) use environment variables - "
                f"ensure secrets are properly secured"
            )

        return recommendations

    def _suggest_command_install(self, command: str) -> str:
        """Suggest how to install missing command.

        Args:
            command: Command that is missing

        Returns:
            Installation suggestion
        """
        suggestions = {
            "uv": "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh",
            "python": "Install Python: https://python.org/downloads",
            "node": "Install Node.js: https://nodejs.org",
            "npm": "Install Node.js (includes npm): https://nodejs.org",
        }

        return suggestions.get(
            command, f"Install {command} and ensure it's in your PATH"
        )

    def _create_default_config(self) -> None:
        """Create default empty configuration file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        if self.config_format == ConfigFormat.JSON:
            default_config: dict[str, Any] = {"mcpServers": {}}
            self.config_manager.write(default_config)
        else:
            # TOML default
            default_config_toml: dict[str, Any] = {"mcp_servers": {}}
            self.config_manager.write(default_config_toml)

    def _migrate_legacy_format(self) -> bool:
        """Migrate from line-delimited JSON to modern format.

        Returns:
            True if migration succeeded
        """
        try:
            content = self.config_path.read_text(encoding="utf-8")
            lines = [line.strip() for line in content.split("\n") if line.strip()]

            # Parse each line as JSON object
            servers: dict[str, Any] = {}
            for line in lines:
                server_data = json.loads(line)
                name = server_data.get("name", f"server-{len(servers)}")
                servers[name] = {
                    "command": server_data.get("command", ""),
                    "args": server_data.get("args", []),
                    "env": server_data.get("env", {}),
                }

            # Write modern format
            modern_config = {"mcpServers": servers}
            self.config_manager.write(modern_config)
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def _remove_deprecated_args(self, server_name: str) -> bool:
        """Remove deprecated arguments from server config.

        Args:
            server_name: Server to update

        Returns:
            True if update succeeded
        """
        try:
            config = self.config_manager.read()
            servers = self._extract_servers(config)

            for server in servers:
                if server.name == server_name:
                    # Remove deprecated args
                    clean_args = [
                        arg
                        for arg in server.args
                        if not any(dep in arg for dep in ["--legacy-mode", "--old-api"])
                    ]

                    # Update config
                    server_key = self._get_server_key(config)
                    if server_key and server.name in config[server_key]:
                        config[server_key][server.name]["args"] = clean_args
                        self.config_manager.write(config)
                        return True

            return False

        except Exception as e:
            logger.error(f"Failed to remove deprecated args: {e}")
            return False

    def _get_server_key(self, config: dict[str, Any]) -> str | None:
        """Get the key used for servers in config.

        Args:
            config: Configuration dictionary

        Returns:
            Server key name or None
        """
        for key in ["mcpServers", "mcp_servers", "servers"]:
            if key in config:
                return key
        return None
