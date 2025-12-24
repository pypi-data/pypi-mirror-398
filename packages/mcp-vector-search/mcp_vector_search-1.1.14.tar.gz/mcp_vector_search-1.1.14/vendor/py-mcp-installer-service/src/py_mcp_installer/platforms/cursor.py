"""Cursor platform implementation.

This module provides platform-specific logic for Cursor, including
configuration paths, installation strategies, and validation.

Cursor supports:
- Project-level config: .cursor/mcp.json
- Global config: ~/.cursor/mcp.json
- JSON manipulation only (no native CLI for MCP)
"""

from __future__ import annotations

from pathlib import Path

from ..command_builder import CommandBuilder
from ..installation_strategy import (
    InstallationStrategy,
    JSONManipulationStrategy,
)
from ..types import InstallMethod, MCPServerConfig, Platform, Scope
from ..utils import resolve_command_path


class CursorStrategy:
    """Cursor platform implementation.

    Provides configuration paths and installation strategies for Cursor.

    Note: Cursor does not have a native CLI for MCP configuration,
    so only JSON manipulation strategy is available.

    Example:
        >>> strategy = CursorStrategy()
        >>> config_path = strategy.get_config_path(Scope.PROJECT)
        >>> installer = strategy.get_strategy(Scope.PROJECT)
        >>> result = installer.install(server, Scope.PROJECT)
    """

    def __init__(self) -> None:
        """Initialize Cursor strategy."""
        self.platform = Platform.CURSOR
        self.config_format = "json"

    def get_config_path(self, scope: Scope) -> Path:
        """Get configuration path for scope.

        Cursor config locations:
        - Project: .cursor/mcp.json (if exists)
        - Global: ~/.cursor/mcp.json

        Args:
            scope: Installation scope (PROJECT or GLOBAL)

        Returns:
            Path to configuration file

        Example:
            >>> strategy = CursorStrategy()
            >>> path = strategy.get_config_path(Scope.GLOBAL)
            >>> print(path)
            /home/user/.cursor/mcp.json
        """
        if scope == Scope.PROJECT:
            # Check for project-level config
            project_config = Path(".cursor") / "mcp.json"
            if project_config.exists():
                return project_config

            # Default to global if project config doesn't exist
            return Path.home() / ".cursor" / "mcp.json"

        else:  # Scope.GLOBAL
            return Path.home() / ".cursor" / "mcp.json"

    def get_strategy(self, scope: Scope) -> InstallationStrategy:
        """Get appropriate installation strategy for scope.

        Cursor only supports JSON manipulation (no native CLI).

        Args:
            scope: Installation scope

        Returns:
            JSON manipulation strategy

        Example:
            >>> strategy = CursorStrategy()
            >>> installer = strategy.get_strategy(Scope.GLOBAL)
            >>> result = installer.install(server, Scope.GLOBAL)
        """
        config_path = self.get_config_path(scope)
        return JSONManipulationStrategy(self.platform, config_path)

    def validate_installation(self) -> bool:
        """Validate Cursor is available.

        Checks for config directory or cursor CLI.

        Returns:
            True if Cursor appears to be installed

        Example:
            >>> strategy = CursorStrategy()
            >>> if strategy.validate_installation():
            ...     print("Cursor is available")
        """
        # Check for config directory
        cursor_dir = Path.home() / ".cursor"
        has_config_dir = cursor_dir.exists() and cursor_dir.is_dir()

        # Check for cursor CLI
        has_cli = resolve_command_path("cursor") is not None

        return has_config_dir or has_cli

    def build_server_config(
        self,
        package: str,
        install_method: InstallMethod | None = None,
        env: dict[str, str] | None = None,
        description: str = "",
    ) -> MCPServerConfig:
        """Build server configuration for Cursor.

        Uses CommandBuilder to auto-detect best installation method.

        Note: Cursor may require absolute paths for better reliability.

        Args:
            package: Package name (e.g., "mcp-ticketer")
            install_method: Installation method (auto-detected if None)
            env: Environment variables
            description: Server description

        Returns:
            Complete server configuration

        Example:
            >>> strategy = CursorStrategy()
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
            >>> strategy = CursorStrategy()
            >>> info = strategy.get_platform_info()
            >>> print(info["name"])
            Cursor
        """
        return {
            "name": "Cursor",
            "platform": self.platform.value,
            "config_format": "json",
            "scope_support": "both",
            "cli_available": "false",  # No MCP CLI support
            "config_key": "mcp_servers",  # Cursor uses snake_case
        }

    def get_recommended_config(self) -> dict[str, str]:
        """Get Cursor-specific configuration recommendations.

        Returns:
            Dict with recommended settings

        Example:
            >>> strategy = CursorStrategy()
            >>> recs = strategy.get_recommended_config()
            >>> print(recs["path_style"])
            absolute
        """
        return {
            "path_style": "absolute",  # Cursor prefers absolute paths
            "restart_required": "yes",  # Must restart Cursor after config changes
            "config_location": str(Path.home() / ".cursor" / "mcp.json"),
        }
