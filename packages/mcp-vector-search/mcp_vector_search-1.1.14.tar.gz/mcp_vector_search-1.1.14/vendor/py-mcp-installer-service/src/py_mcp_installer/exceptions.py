"""Custom exceptions for py-mcp-installer-service.

This module defines a comprehensive exception hierarchy with clear error
messages and recovery suggestions for users.

Design Philosophy:
- Base exception for all library errors
- Specific exceptions for different failure modes
- Clear error messages with actionable recovery suggestions
- Preserve exception chaining for debugging
"""


class PyMCPInstallerError(Exception):
    """Base exception for all py-mcp-installer errors.

    All custom exceptions in this library inherit from this base class,
    making it easy to catch all library-specific errors.

    Attributes:
        message: Error description
        recovery_suggestion: Suggested action to resolve the error
    """

    def __init__(self, message: str, recovery_suggestion: str = "") -> None:
        """Initialize exception with message and optional recovery suggestion.

        Args:
            message: Error description
            recovery_suggestion: How user can resolve this error
        """
        self.message = message
        self.recovery_suggestion = recovery_suggestion
        super().__init__(message)

    def __str__(self) -> str:
        """Format error message with recovery suggestion if available."""
        if self.recovery_suggestion:
            return f"{self.message}\n\nSuggestion: {self.recovery_suggestion}"
        return self.message


class PlatformDetectionError(PyMCPInstallerError):
    """Failed to detect any supported AI coding platform.

    Raised when platform auto-detection cannot find any supported tools
    installed on the system.

    Example:
        >>> raise PlatformDetectionError(
        ...     "No supported platforms detected",
        ...     "Install Claude Code, Cursor, or Windsurf"
        ... )
    """

    def __init__(self, message: str = "No supported AI coding tools detected") -> None:
        """Initialize with default recovery suggestion."""
        super().__init__(
            message,
            recovery_suggestion=(
                "Install one of the supported tools:\n"
                "  - Claude Code: https://claude.ai/download\n"
                "  - Cursor: https://cursor.sh\n"
                "  - Windsurf: https://codeium.com/windsurf\n"
                "  - Auggie: https://auggie.app\n"
                "  - Codex: https://codex.ai"
            ),
        )


class ConfigurationError(PyMCPInstallerError):
    """Configuration file is invalid, corrupted, or inaccessible.

    Raised when:
    - Config file exists but contains invalid JSON/TOML
    - Config file has incorrect permissions
    - Config file is corrupted
    - Config file structure is invalid

    Example:
        >>> raise ConfigurationError(
        ...     "Invalid JSON in config file",
        ...     config_path="/home/user/.config/claude/mcp.json"
        ... )
    """

    def __init__(self, message: str, config_path: str = "") -> None:
        """Initialize with config file path for recovery suggestion.

        Args:
            message: Error description
            config_path: Path to problematic config file
        """
        recovery = ""
        if config_path:
            recovery = (
                f"Fix or delete the config file: {config_path}\n"
                f"Backup will be created before any modifications."
            )
        super().__init__(message, recovery_suggestion=recovery)


class InstallationError(PyMCPInstallerError):
    """MCP server installation operation failed.

    Raised when:
    - Server installation fails
    - Config file cannot be written
    - Native CLI command fails
    - Server already exists (without force=True)

    Example:
        >>> raise InstallationError(
        ...     "Failed to install mcp-ticketer: permission denied",
        ...     "Check file permissions on config directory"
        ... )
    """

    pass


class ValidationError(PyMCPInstallerError):
    """Server configuration validation failed.

    Raised when:
    - Required fields missing from server config
    - Invalid command or args
    - Environment variables invalid
    - Server name conflicts

    Example:
        >>> raise ValidationError(
        ...     "Server configuration missing 'command' field",
        ...     "Provide command parameter or use auto-detection"
        ... )
    """

    pass


class CommandNotFoundError(PyMCPInstallerError):
    """Required command not found in PATH.

    Raised when:
    - MCP server binary not found
    - Platform CLI (claude, cursor) not found
    - uv or pipx not found when required

    Example:
        >>> raise CommandNotFoundError(
        ...     "mcp-ticketer",
        ...     "pipx install mcp-ticketer"
        ... )
    """

    def __init__(self, command: str, install_hint: str = "") -> None:
        """Initialize with command name and installation hint.

        Args:
            command: Command that was not found
            install_hint: How to install the command (optional)
        """
        message = f"Command not found in PATH: {command}"
        recovery = install_hint or f"Install '{command}' and ensure it's in your PATH"
        super().__init__(message, recovery_suggestion=recovery)


class BackupError(PyMCPInstallerError):
    """Failed to create or restore configuration backup.

    Raised when:
    - Backup directory cannot be created
    - Backup file cannot be written
    - Disk space insufficient
    - Restore operation fails

    Example:
        >>> raise BackupError(
        ...     "Failed to create backup: disk full",
        ...     "Free up disk space and try again"
        ... )
    """

    def __init__(self, message: str) -> None:
        """Initialize with default recovery suggestion."""
        super().__init__(
            message, recovery_suggestion="Check file permissions and disk space"
        )


class AtomicWriteError(PyMCPInstallerError):
    """Atomic file write operation failed.

    Raised when:
    - Temporary file cannot be created
    - Write operation fails midway
    - Atomic rename fails
    - File permissions prevent write

    This is a critical error as it may leave config in inconsistent state.

    Example:
        >>> raise AtomicWriteError(
        ...     "Failed to write config file atomically",
        ...     "/home/user/.config/claude/mcp.json"
        ... )
    """

    def __init__(self, message: str, target_path: str = "") -> None:
        """Initialize with target file path."""
        recovery = "Check file permissions and disk space"
        if target_path:
            recovery += f"\nTarget file: {target_path}"
        super().__init__(message, recovery_suggestion=recovery)


class PlatformNotSupportedError(PyMCPInstallerError):
    """Requested platform is not supported by this library.

    Raised when:
    - User specifies unknown platform
    - Platform detection returns unsupported platform
    - Platform implementation missing

    Example:
        >>> raise PlatformNotSupportedError(
        ...     "my_custom_platform",
        ...     ["claude_code", "cursor", "windsurf"]
        ... )
    """

    def __init__(self, platform: str, supported_platforms: list[str]) -> None:
        """Initialize with platform name and list of supported platforms.

        Args:
            platform: Unsupported platform name
            supported_platforms: List of supported platform names
        """
        message = f"Platform not supported: {platform}"
        recovery = "Supported platforms:\n" + "\n".join(
            f"  - {p}" for p in supported_platforms
        )
        super().__init__(message, recovery_suggestion=recovery)
