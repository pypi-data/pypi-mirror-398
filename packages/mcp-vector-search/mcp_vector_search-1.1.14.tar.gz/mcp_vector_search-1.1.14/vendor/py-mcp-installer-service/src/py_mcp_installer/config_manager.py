"""Configuration file manager with atomic operations and backup/restore.

This module provides a ConfigManager class that handles MCP configuration files
with atomic writes, automatic backups, and format validation for both JSON and TOML.

Design Philosophy:
- Atomic operations prevent partial writes
- Automatic backups before modifications
- Support both JSON (most platforms) and TOML (Codex)
- Graceful handling of missing files
- Legacy format migration support

Example:
    >>> manager = ConfigManager(Path.home() / ".config/claude/mcp.json", ConfigFormat.JSON)
    >>> config = manager.read()
    >>> config["mcpServers"]["new-server"] = {"command": "test", "args": []}
    >>> manager.write(config)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# tomllib is imported conditionally in parse_toml_safe utility

try:
    import tomli_w  # For TOML writing  # type: ignore[import-untyped]
except ImportError:
    tomli_w = None  # type: ignore[assignment,unused-ignore]

from .exceptions import BackupError, ConfigurationError, ValidationError
from .types import ConfigFormat, MCPServerConfig
from .utils import (
    atomic_write,
    backup_file,
    parse_json_safe,
    parse_toml_safe,
    restore_backup,
)


class ConfigManager:
    """Manage MCP configuration files with atomic operations.

    Provides safe read/write operations for MCP configuration files with
    automatic backup creation and validation. Supports both JSON and TOML formats.

    Attributes:
        config_path: Path to configuration file
        format: Configuration file format (JSON or TOML)

    Example:
        >>> manager = ConfigManager(
        ...     Path.home() / ".config/claude/mcp.json",
        ...     ConfigFormat.JSON
        ... )
        >>> config = manager.read()
        >>> manager.add_server(MCPServerConfig(
        ...     name="test",
        ...     command="test",
        ...     args=["run"]
        ... ))
    """

    def __init__(self, config_path: Path, format: ConfigFormat) -> None:
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file
            format: Configuration file format (JSON or TOML)

        Example:
            >>> manager = ConfigManager(
            ...     Path(".claude.json"),
            ...     ConfigFormat.JSON
            ... )
        """
        self.config_path = config_path
        self.format = format

    def read(self) -> dict[str, Any]:
        """Read and parse configuration file.

        Returns empty dict if file doesn't exist. Validates structure
        and raises ConfigurationError if invalid.

        Returns:
            Configuration dictionary (empty dict if file missing)

        Raises:
            ConfigurationError: If file exists but is invalid

        Example:
            >>> manager = ConfigManager(Path(".claude.json"), ConfigFormat.JSON)
            >>> config = manager.read()
            >>> print(config.get("mcpServers", {}))
        """
        if self.format == ConfigFormat.JSON:
            return parse_json_safe(self.config_path)
        elif self.format == ConfigFormat.TOML:
            return parse_toml_safe(self.config_path)
        else:
            raise ConfigurationError(
                f"Unsupported config format: {self.format}",
                config_path=str(self.config_path),
            )

    def write(self, config: dict[str, Any]) -> None:
        """Write configuration with atomic operation.

        Creates backup before writing. Uses atomic write pattern
        (temp file + rename) to prevent partial writes.

        Args:
            config: Configuration dictionary to write

        Raises:
            BackupError: If backup creation fails
            ConfigurationError: If write operation fails

        Example:
            >>> manager = ConfigManager(Path(".claude.json"), ConfigFormat.JSON)
            >>> config = {"mcpServers": {"test": {"command": "test"}}}
            >>> manager.write(config)
        """
        # Create backup if file exists
        if self.config_path.exists():
            try:
                backup_file(self.config_path)
            except Exception as e:
                raise BackupError(f"Failed to backup before write: {e}") from e

        # Serialize configuration
        try:
            if self.format == ConfigFormat.JSON:
                content = json.dumps(config, indent=2) + "\n"
            elif self.format == ConfigFormat.TOML:
                if tomli_w is None:
                    raise ConfigurationError(
                        "TOML write support requires tomli-w package",
                        config_path=str(self.config_path),
                    )
                import io

                # tomli_w.dump requires binary mode IO
                buffer = io.BytesIO()
                tomli_w.dump(config, buffer)
                content = buffer.getvalue().decode("utf-8")
            else:
                raise ConfigurationError(
                    f"Unsupported config format: {self.format}",
                    config_path=str(self.config_path),
                )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to serialize config: {e}", config_path=str(self.config_path)
            ) from e

        # Write atomically
        try:
            atomic_write(self.config_path, content)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to write config: {e}", config_path=str(self.config_path)
            ) from e

    def backup(self) -> Path:
        """Create timestamped backup of current config.

        Backups are stored in .mcp-installer-backups/ directory with
        timestamp in filename.

        Returns:
            Path to created backup file

        Raises:
            BackupError: If backup creation fails

        Example:
            >>> manager = ConfigManager(Path(".claude.json"), ConfigFormat.JSON)
            >>> backup_path = manager.backup()
            >>> print(backup_path)
            .mcp-installer-backups/.claude.json.20250105_143022.backup
        """
        if not self.config_path.exists():
            raise BackupError(f"Cannot backup non-existent file: {self.config_path}")

        return backup_file(self.config_path)

    def restore(self, backup_path: Path) -> None:
        """Restore configuration from backup file.

        Args:
            backup_path: Path to backup file to restore

        Raises:
            BackupError: If restore fails

        Example:
            >>> manager = ConfigManager(Path(".claude.json"), ConfigFormat.JSON)
            >>> backup_path = manager.backup()
            >>> # ... make changes ...
            >>> manager.restore(backup_path)  # Rollback changes
        """
        restore_backup(backup_path, self.config_path)

    def add_server(self, server: MCPServerConfig) -> None:
        """Add MCP server to configuration.

        Reads current config, adds server, and writes atomically.
        Creates backup before modification.

        Args:
            server: Server configuration to add

        Raises:
            ValidationError: If server with same name already exists
            ConfigurationError: If write fails

        Example:
            >>> manager = ConfigManager(Path(".claude.json"), ConfigFormat.JSON)
            >>> server = MCPServerConfig(
            ...     name="mcp-ticketer",
            ...     command="uv",
            ...     args=["run", "mcp-ticketer", "mcp"],
            ...     env={"API_KEY": "..."}
            ... )
            >>> manager.add_server(server)
        """
        config = self.read()

        # Determine servers key based on format
        servers_key = (
            "mcpServers" if self.format == ConfigFormat.JSON else "mcp_servers"
        )

        # Initialize servers section if missing
        if servers_key not in config:
            config[servers_key] = {}

        # Check if server already exists
        if server.name in config[servers_key]:
            raise ValidationError(
                f"Server '{server.name}' already exists in configuration",
                recovery_suggestion=(
                    "Use update_server() to modify existing server, "
                    "or remove it first"
                ),
            )

        # Build server config dict
        server_dict: dict[str, Any] = {
            "command": server.command,
            "args": list(server.args),  # Convert to list to ensure JSON serialization
        }

        # Add optional fields
        if server.env:
            server_dict["env"] = dict(server.env)  # Convert to dict
        if server.description:
            server_dict["description"] = server.description

        # Add server
        config[servers_key][server.name] = server_dict

        # Write config
        self.write(config)

    def remove_server(self, name: str) -> None:
        """Remove MCP server from configuration.

        Args:
            name: Name of server to remove

        Raises:
            ValidationError: If server doesn't exist
            ConfigurationError: If write fails

        Example:
            >>> manager = ConfigManager(Path(".claude.json"), ConfigFormat.JSON)
            >>> manager.remove_server("mcp-ticketer")
        """
        config = self.read()

        # Determine servers key
        servers_key = (
            "mcpServers" if self.format == ConfigFormat.JSON else "mcp_servers"
        )

        # Check if server exists
        if servers_key not in config or name not in config[servers_key]:
            raise ValidationError(
                f"Server '{name}' not found in configuration",
                recovery_suggestion="Use list_servers() to see available servers",
            )

        # Remove server
        del config[servers_key][name]

        # Write config
        self.write(config)

    def update_server(self, name: str, server: MCPServerConfig) -> None:
        """Update existing server configuration.

        Args:
            name: Name of server to update
            server: New server configuration

        Raises:
            ValidationError: If server doesn't exist
            ConfigurationError: If write fails

        Example:
            >>> manager = ConfigManager(Path(".claude.json"), ConfigFormat.JSON)
            >>> updated = MCPServerConfig(
            ...     name="mcp-ticketer",
            ...     command="mcp-ticketer",  # Changed from uv run
            ...     args=["mcp"]
            ... )
            >>> manager.update_server("mcp-ticketer", updated)
        """
        config = self.read()

        # Determine servers key
        servers_key = (
            "mcpServers" if self.format == ConfigFormat.JSON else "mcp_servers"
        )

        # Check if server exists
        if servers_key not in config or name not in config[servers_key]:
            raise ValidationError(
                f"Server '{name}' not found in configuration",
                recovery_suggestion="Use add_server() to create new server",
            )

        # Build updated server config
        server_dict: dict[str, Any] = {
            "command": server.command,
            "args": list(server.args),
        }

        if server.env:
            server_dict["env"] = dict(server.env)
        if server.description:
            server_dict["description"] = server.description

        # Update server
        config[servers_key][name] = server_dict

        # Write config
        self.write(config)

    def list_servers(self) -> list[MCPServerConfig]:
        """List all configured MCP servers.

        Returns:
            List of server configurations

        Example:
            >>> manager = ConfigManager(Path(".claude.json"), ConfigFormat.JSON)
            >>> servers = manager.list_servers()
            >>> for server in servers:
            ...     print(f"{server.name}: {server.command}")
        """
        config = self.read()

        # Determine servers key
        servers_key = (
            "mcpServers" if self.format == ConfigFormat.JSON else "mcp_servers"
        )

        servers: list[MCPServerConfig] = []

        for name, server_dict in config.get(servers_key, {}).items():
            if not isinstance(server_dict, dict):
                continue  # Skip invalid entries

            servers.append(
                MCPServerConfig(
                    name=name,
                    command=server_dict.get("command", ""),
                    args=server_dict.get("args", []),
                    env=server_dict.get("env", {}),
                    description=server_dict.get("description", ""),
                )
            )

        return servers

    def get_server(self, name: str) -> MCPServerConfig | None:
        """Get specific server configuration.

        Args:
            name: Server name to lookup

        Returns:
            Server configuration if found, None otherwise

        Example:
            >>> manager = ConfigManager(Path(".claude.json"), ConfigFormat.JSON)
            >>> server = manager.get_server("mcp-ticketer")
            >>> if server:
            ...     print(f"Command: {server.command}")
        """
        config = self.read()

        # Determine servers key
        servers_key = (
            "mcpServers" if self.format == ConfigFormat.JSON else "mcp_servers"
        )

        server_dict = config.get(servers_key, {}).get(name)
        if not server_dict or not isinstance(server_dict, dict):
            return None

        return MCPServerConfig(
            name=name,
            command=server_dict.get("command", ""),
            args=server_dict.get("args", []),
            env=server_dict.get("env", {}),
            description=server_dict.get("description", ""),
        )

    def validate(self) -> list[str]:
        """Validate configuration structure.

        Returns list of validation issues found. Empty list means valid.

        Returns:
            List of validation error messages (empty if valid)

        Example:
            >>> manager = ConfigManager(Path(".claude.json"), ConfigFormat.JSON)
            >>> issues = manager.validate()
            >>> if issues:
            ...     print("Configuration issues:")
            ...     for issue in issues:
            ...         print(f"  - {issue}")
        """
        issues: list[str] = []

        try:
            config = self.read()
        except ConfigurationError as e:
            return [f"Failed to read config: {e.message}"]

        # Determine servers key
        servers_key = (
            "mcpServers" if self.format == ConfigFormat.JSON else "mcp_servers"
        )

        # Check for servers key
        if servers_key not in config:
            issues.append(f"Missing '{servers_key}' key in configuration")
            return issues

        servers = config[servers_key]
        if not isinstance(servers, dict):
            issues.append(f"'{servers_key}' must be a dictionary/table")
            return issues

        # Validate each server
        for server_name, server_config in servers.items():
            if not isinstance(server_config, dict):
                issues.append(f"Server '{server_name}' config must be a dictionary")
                continue

            # Check required fields
            if "command" not in server_config:
                issues.append(
                    f"Server '{server_name}' missing required 'command' field"
                )

            # Validate field types
            if "args" in server_config and not isinstance(server_config["args"], list):
                issues.append(f"Server '{server_name}' 'args' must be a list")

            if "env" in server_config and not isinstance(server_config["env"], dict):
                issues.append(f"Server '{server_name}' 'env' must be a dictionary")

        return issues

    def migrate_legacy(self) -> bool:
        """Detect and migrate legacy line-delimited JSON format.

        Checks if any servers use deprecated python module format and
        migrates them to modern format.

        Returns:
            True if migration was performed, False if not needed

        Example:
            >>> manager = ConfigManager(Path(".claude.json"), ConfigFormat.JSON)
            >>> if manager.migrate_legacy():
            ...     print("Legacy servers migrated successfully")
        """
        # Only applies to JSON format
        if self.format != ConfigFormat.JSON:
            return False

        config = self.read()
        servers = config.get("mcpServers", {})

        migrated = False

        for server_name, server_config in servers.items():
            if not isinstance(server_config, dict):
                continue

            args = server_config.get("args", [])

            # Check for legacy python module format
            # Old: ["python", "-m", "mcp_ticketer.mcp.server"]
            # New: ["uv", "run", "mcp-ticketer", "mcp"]
            if (
                len(args) >= 2
                and args[0] == "-m"
                and "mcp_ticketer.mcp.server" in args[1]
            ):
                # Migrate to modern format
                # Try to detect best command (uv, pipx, or binary)
                from .utils import resolve_command_path

                if resolve_command_path("uv"):
                    server_config["command"] = "uv"
                    server_config["args"] = ["run", "mcp-ticketer", "mcp"]
                elif resolve_command_path("mcp-ticketer"):
                    server_config["command"] = str(resolve_command_path("mcp-ticketer"))
                    server_config["args"] = ["mcp"]
                else:
                    # Keep python fallback but use modern entry point
                    # Leave command as-is (should be python path)
                    server_config["args"] = ["-m", "mcp_ticketer.mcp.server"]

                migrated = True

        if migrated:
            self.write(config)

        return migrated
