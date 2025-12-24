"""Claude Code platform implementation.

This module provides platform-specific logic for Claude Code, including
configuration paths, installation strategies, and validation.

Claude Code supports:
- Project-level config: .claude.json or ~/.config/claude/mcp.json
- Global config: ~/.config/claude/mcp.json
- Native CLI: claude mcp add/remove
- JSON manipulation fallback
"""

from __future__ import annotations

from pathlib import Path

from ..command_builder import CommandBuilder
from ..installation_strategy import (
    InstallationStrategy,
    JSONManipulationStrategy,
    NativeCLIStrategy,
)
from ..types import InstallMethod, MCPServerConfig, Platform, Scope
from ..utils import resolve_command_path


class ClaudeCodeStrategy:
    """Claude Code platform implementation.

    Provides configuration paths and installation strategies for Claude Code.

    Example:
        >>> strategy = ClaudeCodeStrategy()
        >>> config_path = strategy.get_config_path(Scope.PROJECT)
        >>> installer = strategy.get_strategy(Scope.PROJECT)
        >>> result = installer.install(server, Scope.PROJECT)
    """

    def __init__(self) -> None:
        """Initialize Claude Code strategy."""
        self.platform = Platform.CLAUDE_CODE
        self.config_format = "json"

    def get_config_path(self, scope: Scope) -> Path:
        """Get configuration path for scope.

        Priority order:
        1. Project scope: .claude.json (legacy) or ~/.config/claude/mcp.json (new)
        2. Global scope: ~/.config/claude/mcp.json

        Args:
            scope: Installation scope (PROJECT or GLOBAL)

        Returns:
            Path to configuration file

        Example:
            >>> strategy = ClaudeCodeStrategy()
            >>> path = strategy.get_config_path(Scope.PROJECT)
            >>> print(path)
            /home/user/.config/claude/mcp.json
        """
        if scope == Scope.PROJECT:
            # Check for new location first
            new_config = Path.home() / ".config" / "claude" / "mcp.json"
            if new_config.exists():
                return new_config

            # Fallback to legacy project-level config
            legacy_project = Path(".claude.json")
            if legacy_project.exists():
                return legacy_project

            # Default to new location if creating new config
            return new_config

        else:  # Scope.GLOBAL
            # Global config always in new location
            return Path.home() / ".config" / "claude" / "mcp.json"

    def get_strategy(self, scope: Scope) -> InstallationStrategy:
        """Get appropriate installation strategy for scope.

        Prefers native CLI if available, falls back to JSON manipulation.

        Args:
            scope: Installation scope

        Returns:
            Installation strategy instance

        Example:
            >>> strategy = ClaudeCodeStrategy()
            >>> installer = strategy.get_strategy(Scope.PROJECT)
            >>> if installer.validate():
            ...     result = installer.install(server, Scope.PROJECT)
        """
        # Prefer native CLI if available
        if resolve_command_path("claude"):
            return NativeCLIStrategy(self.platform, "claude")

        # Fallback to JSON manipulation
        config_path = self.get_config_path(scope)
        return JSONManipulationStrategy(self.platform, config_path)

    def get_strategy_with_fallback(
        self, scope: Scope
    ) -> tuple[InstallationStrategy, InstallationStrategy | None]:
        """Get primary strategy and fallback strategy.

        Returns both native CLI and JSON strategies for graceful fallback.

        Args:
            scope: Installation scope

        Returns:
            Tuple of (primary_strategy, fallback_strategy)

        Example:
            >>> strategy = ClaudeCodeStrategy()
            >>> primary, fallback = strategy.get_strategy_with_fallback(Scope.PROJECT)
            >>> try:
            ...     result = primary.install(server, Scope.PROJECT)
            ... except InstallationError:
            ...     if fallback:
            ...         result = fallback.install(server, Scope.PROJECT)
        """
        config_path = self.get_config_path(scope)

        # Primary: Native CLI if available
        primary: InstallationStrategy | None = None
        if resolve_command_path("claude"):
            primary = NativeCLIStrategy(self.platform, "claude")

        # Fallback: Always JSON
        fallback = JSONManipulationStrategy(self.platform, config_path)

        # If no CLI, use JSON as primary
        if primary is None:
            return (fallback, None)

        return (primary, fallback)

    def validate_installation(self) -> bool:
        """Validate Claude Code is available.

        Checks for config file existence or CLI availability.

        Returns:
            True if Claude Code appears to be installed

        Example:
            >>> strategy = ClaudeCodeStrategy()
            >>> if strategy.validate_installation():
            ...     print("Claude Code is available")
        """
        # Check for any config file
        global_config = Path.home() / ".config" / "claude" / "mcp.json"
        legacy_config = Path.home() / ".claude.json"
        project_config = Path(".claude.json")

        has_config = (
            global_config.exists() or legacy_config.exists() or project_config.exists()
        )

        # Check for CLI
        has_cli = resolve_command_path("claude") is not None

        return has_config or has_cli

    def build_server_config(
        self,
        package: str,
        install_method: InstallMethod | None = None,
        env: dict[str, str] | None = None,
        description: str = "",
    ) -> MCPServerConfig:
        """Build server configuration for Claude Code.

        Uses CommandBuilder to auto-detect best installation method.

        Args:
            package: Package name (e.g., "mcp-ticketer")
            install_method: Installation method (auto-detected if None)
            env: Environment variables
            description: Server description

        Returns:
            Complete server configuration

        Example:
            >>> strategy = ClaudeCodeStrategy()
            >>> config = strategy.build_server_config(
            ...     "mcp-ticketer",
            ...     env={"LINEAR_API_KEY": "..."}
            ... )
            >>> print(f"{config.command} {' '.join(config.args)}")
            uv run mcp-ticketer mcp
        """
        builder = CommandBuilder(self.platform)
        return builder.to_server_config(
            package=package,
            install_method=install_method,
            env=env,
            description=description,
        )

    def get_platform_info(self) -> dict[str, str]:
        """Get platform information.

        Returns:
            Dict with platform details

        Example:
            >>> strategy = ClaudeCodeStrategy()
            >>> info = strategy.get_platform_info()
            >>> print(info["name"])
            Claude Code
        """
        return {
            "name": "Claude Code",
            "platform": self.platform.value,
            "config_format": "json",
            "scope_support": "both",
            "cli_available": str(resolve_command_path("claude") is not None),
            "config_key": "mcpServers",
        }
