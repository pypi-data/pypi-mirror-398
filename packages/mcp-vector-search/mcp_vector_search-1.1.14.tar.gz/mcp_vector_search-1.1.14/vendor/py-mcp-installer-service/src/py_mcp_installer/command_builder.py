"""Command builder for MCP server installations.

This module provides utilities to build correct command strings for MCP server
installations, including auto-detection of installation methods (uv, pipx, direct).

Design Philosophy:
- Auto-detect best installation method
- Build platform-specific command strings
- Validate commands are executable
- Support for multiple installation methods

Priority:
1. UV_RUN: uv run mcp-ticketer mcp (fastest, recommended)
2. PIPX: mcp-ticketer (installed via pipx)
3. DIRECT: Direct binary in PATH
4. PYTHON_MODULE: python -m mcp_ticketer mcp (fallback)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .exceptions import CommandNotFoundError
from .types import InstallMethod, MCPServerConfig, Platform
from .utils import detect_install_method, resolve_command_path


class CommandBuilder:
    """Build correct command strings for MCP server installations.

    Provides methods to auto-detect installation methods and build
    platform-specific command configurations.

    Example:
        >>> builder = CommandBuilder(Platform.CLAUDE_CODE)
        >>> command, args = builder.build_command(
        ...     MCPServerConfig(name="mcp-ticketer", command="", args=[]),
        ...     InstallMethod.UV_RUN
        ... )
        >>> print(f"{command} {' '.join(args)}")
        uv run mcp-ticketer mcp
    """

    def __init__(self, platform: Platform) -> None:
        """Initialize command builder for target platform.

        Args:
            platform: Target platform for command building

        Example:
            >>> builder = CommandBuilder(Platform.CLAUDE_CODE)
        """
        self.platform = platform

    def build_command(
        self, server: MCPServerConfig, install_method: InstallMethod
    ) -> str:
        """Build command string for server installation.

        Constructs the appropriate command based on installation method:
        - UV_RUN: "uv run mcp-ticketer mcp"
        - PIPX: "mcp-ticketer mcp"
        - DIRECT: "mcp-ticketer mcp"
        - PYTHON_MODULE: "python -m mcp_ticketer.mcp.server"

        Args:
            server: Server configuration
            install_method: Installation method to use

        Returns:
            Command string

        Example:
            >>> builder = CommandBuilder(Platform.CLAUDE_CODE)
            >>> server = MCPServerConfig(name="mcp-ticketer", command="", args=[])
            >>> cmd = builder.build_command(server, InstallMethod.UV_RUN)
            >>> print(cmd)
            uv
        """
        if install_method == InstallMethod.UV_RUN:
            # uv run {package} {subcommand}
            return "uv"

        elif install_method == InstallMethod.PIPX:
            # Binary installed via pipx
            binary_path = resolve_command_path(server.name)
            if binary_path:
                return str(binary_path)
            else:
                raise CommandNotFoundError(
                    server.name,
                    install_hint=f"pipx install {server.name}",
                )

        elif install_method == InstallMethod.DIRECT:
            # Direct binary in PATH
            binary_path = resolve_command_path(server.name)
            if binary_path:
                return str(binary_path)
            else:
                raise CommandNotFoundError(
                    server.name,
                    install_hint=f"Install {server.name} and ensure it's in PATH",
                )

        elif install_method == InstallMethod.PYTHON_MODULE:
            # python -m {module}
            import sys

            return sys.executable

        else:
            raise ValueError(f"Unknown install method: {install_method}")

    def build_args(
        self, server: MCPServerConfig, install_method: InstallMethod
    ) -> list[str]:
        """Build argument list from server config.

        Constructs arguments based on installation method:
        - UV_RUN: ["run", "{package}", "mcp", ...]
        - PIPX/DIRECT: ["mcp", ...]
        - PYTHON_MODULE: ["-m", "{module}", ...]

        Args:
            server: Server configuration
            install_method: Installation method

        Returns:
            List of arguments

        Example:
            >>> builder = CommandBuilder(Platform.CLAUDE_CODE)
            >>> server = MCPServerConfig(
            ...     name="mcp-ticketer",
            ...     command="",
            ...     args=["--verbose"]
            ... )
            >>> args = builder.build_args(server, InstallMethod.UV_RUN)
            >>> print(args)
            ['run', 'mcp-ticketer', 'mcp', '--verbose']
        """
        if install_method == InstallMethod.UV_RUN:
            # uv run {package} {subcommand} [args...]
            base_args = ["run", server.name, "mcp"]
            return base_args + list(server.args)

        elif install_method in (InstallMethod.PIPX, InstallMethod.DIRECT):
            # {binary} mcp [args...]
            return ["mcp"] + list(server.args)

        elif install_method == InstallMethod.PYTHON_MODULE:
            # python -m {module} [args...]
            base_args = ["-m", "mcp_ticketer.mcp.server"]
            return base_args + list(server.args)

        else:
            raise ValueError(f"Unknown install method: {install_method}")

    def build_env(self, server: MCPServerConfig) -> dict[str, str]:
        """Build environment variables dict.

        Simply returns server's env dict, no platform-specific
        transformations needed.

        Args:
            server: Server configuration

        Returns:
            Environment variables dictionary

        Example:
            >>> builder = CommandBuilder(Platform.CLAUDE_CODE)
            >>> server = MCPServerConfig(
            ...     name="mcp-ticketer",
            ...     command="",
            ...     args=[],
            ...     env={"API_KEY": "secret"}
            ... )
            >>> env = builder.build_env(server)
            >>> print(env)
            {'API_KEY': 'secret'}
        """
        return dict(server.env)

    def validate_command(self, command: str) -> bool:
        """Validate command is executable.

        Checks if command exists in PATH or is an absolute path
        to an executable file.

        Args:
            command: Command to validate

        Returns:
            True if command is executable, False otherwise

        Example:
            >>> builder = CommandBuilder(Platform.CLAUDE_CODE)
            >>> if builder.validate_command("python"):
            ...     print("Python is available")
        """
        # Check if it's an absolute path
        path = Path(command)
        if path.is_absolute():
            return path.exists() and path.is_file()

        # Check if in PATH
        return resolve_command_path(command) is not None

    def detect_best_method(self, package: str) -> InstallMethod:
        """Auto-detect best installation method for package.

        Checks in priority order:
        1. UV available → UV_RUN
        2. Binary in PATH → DIRECT
        3. Package installed via pip → PYTHON_MODULE

        Args:
            package: Package name (e.g., "mcp-ticketer")

        Returns:
            Best available installation method

        Raises:
            CommandNotFoundError: If no installation method available

        Example:
            >>> builder = CommandBuilder(Platform.CLAUDE_CODE)
            >>> method = builder.detect_best_method("mcp-ticketer")
            >>> print(method)
            InstallMethod.UV_RUN
        """
        # Priority 1: uv run (fastest)
        if resolve_command_path("uv"):
            return InstallMethod.UV_RUN

        # Priority 2: Direct binary in PATH
        if resolve_command_path(package):
            # Check if installed via pipx
            install_method = detect_install_method(package)
            if install_method == "pipx":
                return InstallMethod.PIPX
            else:
                return InstallMethod.DIRECT

        # Priority 3: Python module (fallback)
        # Try to import the module
        try:
            # Convert package name to module name (mcp-ticketer → mcp_ticketer)
            module_name = package.replace("-", "_")
            __import__(module_name)
            return InstallMethod.PYTHON_MODULE
        except ImportError:
            pass

        # No installation method found
        raise CommandNotFoundError(
            package,
            install_hint=(
                f"Install {package} using one of:\n"
                f"  - uv pip install {package}\n"
                f"  - pipx install {package}\n"
                f"  - pip install {package}"
            ),
        )

    def build_full_config(
        self,
        package: str,
        install_method: InstallMethod | None = None,
        additional_args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> tuple[str, list[str], dict[str, str]]:
        """Build complete command configuration.

        Convenience method that builds command, args, and env in one call.

        Args:
            package: Package name
            install_method: Installation method (auto-detected if None)
            additional_args: Additional arguments to append
            env: Environment variables

        Returns:
            Tuple of (command, args, env)

        Example:
            >>> builder = CommandBuilder(Platform.CLAUDE_CODE)
            >>> command, args, env = builder.build_full_config(
            ...     "mcp-ticketer",
            ...     additional_args=["--verbose"],
            ...     env={"API_KEY": "secret"}
            ... )
            >>> print(f"{command} {' '.join(args)}")
            uv run mcp-ticketer mcp --verbose
        """
        # Auto-detect method if not provided
        if install_method is None:
            install_method = self.detect_best_method(package)

        # Create server config
        server = MCPServerConfig(
            name=package,
            command="",  # Will be built
            args=additional_args or [],
            env=env or {},
        )

        # Build command and args
        command = self.build_command(server, install_method)
        args = self.build_args(server, install_method)
        env_dict = self.build_env(server)

        return (command, args, env_dict)

    def to_server_config(
        self,
        package: str,
        install_method: InstallMethod | None = None,
        additional_args: list[str] | None = None,
        env: dict[str, str] | None = None,
        description: str = "",
    ) -> MCPServerConfig:
        """Build MCPServerConfig from package name.

        Convenience method to create full server configuration
        with auto-detected installation method.

        Args:
            package: Package name
            install_method: Installation method (auto-detected if None)
            additional_args: Additional arguments
            env: Environment variables
            description: Server description

        Returns:
            Complete MCPServerConfig

        Example:
            >>> builder = CommandBuilder(Platform.CLAUDE_CODE)
            >>> config = builder.to_server_config(
            ...     "mcp-ticketer",
            ...     env={"LINEAR_API_KEY": "..."},
            ...     description="Linear ticket management"
            ... )
            >>> print(f"{config.command} {' '.join(config.args)}")
            uv run mcp-ticketer mcp
        """
        # Build full config
        command, args, env_dict = self.build_full_config(
            package,
            install_method,
            additional_args,
            env,
        )

        return MCPServerConfig(
            name=package,
            command=command,
            args=args,
            env=env_dict,
            description=description,
        )

    def get_platform_command_recommendations(self, package: str) -> dict[str, Any]:
        """Get platform-specific command recommendations.

        Provides information about best practices for command
        configuration on this platform.

        Args:
            package: Package name

        Returns:
            Dict with recommendations and platform-specific info

        Example:
            >>> builder = CommandBuilder(Platform.CLAUDE_CODE)
            >>> recs = builder.get_platform_command_recommendations("mcp-ticketer")
            >>> print(recs["recommended_method"])
            UV_RUN
        """
        try:
            best_method = self.detect_best_method(package)
        except CommandNotFoundError:
            best_method = None

        return {
            "platform": self.platform.value,
            "package": package,
            "recommended_method": best_method.value if best_method else None,
            "available_methods": self._get_available_methods(package),
            "platform_notes": self._get_platform_notes(),
        }

    def _get_available_methods(self, package: str) -> list[str]:
        """Get list of available installation methods.

        Args:
            package: Package name

        Returns:
            List of available method names
        """
        available = []

        if resolve_command_path("uv"):
            available.append("UV_RUN")

        if resolve_command_path(package):
            available.append("DIRECT")

        # Check if module is importable
        try:
            module_name = package.replace("-", "_")
            __import__(module_name)
            available.append("PYTHON_MODULE")
        except ImportError:
            pass

        return available

    def _get_platform_notes(self) -> str:
        """Get platform-specific notes about command configuration.

        Returns:
            Platform-specific notes
        """
        if self.platform in (Platform.CLAUDE_CODE, Platform.CLAUDE_DESKTOP):
            return (
                "Claude supports both CLI and JSON configuration. "
                "Prefer uv run for fastest startup times."
            )
        elif self.platform == Platform.CURSOR:
            return (
                "Cursor only supports JSON configuration. "
                "Use absolute paths for better reliability."
            )
        elif self.platform == Platform.CODEX:
            return (
                "Codex uses TOML configuration. "
                "Environment variables may need special handling."
            )
        else:
            return "Standard MCP server configuration applies."
