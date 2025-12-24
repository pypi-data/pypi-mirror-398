# Changelog

All notable changes to py-mcp-installer-service will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.4] - 2025-12-09

### Fixed
- Added missing `tomli-w` dependency for TOML config writing (Codex platform)
- Added `tomli` dependency for Python < 3.11 TOML reading
- Added `from __future__ import annotations` to all modules for Python 3.9+ compatibility
- Fixed platform forcing bug in MCPInstaller
- Fixed Claude CLI command argument order

## [0.0.3] - 2025-12-05

### Added
- Initial release with complete implementation
- Platform detection for 8 AI coding tools
- Configuration management with atomic operations
- Installation strategies (CLI, JSON, TOML)
- MCP Inspector with validation and auto-fix
- Installer Orchestrator as main API
- Comprehensive documentation

### Features
- Auto-detection of platform and installation method
- Multi-format support (JSON and TOML)
- Legacy format migration
- Dry-run mode
- Comprehensive error handling

[Unreleased]: https://github.com/bobmatnyc/py-mcp-installer-service/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/bobmatnyc/py-mcp-installer-service/compare/v0.0.3...v0.1.4
[0.0.3]: https://github.com/bobmatnyc/py-mcp-installer-service/releases/tag/v0.0.3
