# py-mcp-installer-service: Design Summary

**Version:** 1.0.0
**Date:** 2025-12-05
**Status:** Design Complete - Ready for Implementation

---

## Executive Summary

This document summarizes the comprehensive design for **py-mcp-installer-service**, a production-ready, standalone library for installing and managing MCP (Model Context Protocol) servers across 8 major AI coding tools.

### Key Design Achievements

1. ✅ **Complete Architecture**: 9 core modules with clear responsibilities
2. ✅ **Detailed Implementation Plan**: 6-week phased approach with milestones
3. ✅ **Project Structure**: Full directory layout with templates
4. ✅ **Research Foundation**: Based on real-world analysis of 8 platforms
5. ✅ **Zero Dependencies**: Fully standalone (except TOML support)

---

## Design Documents

### 1. Architecture Design
**Location**: `../ARCHITECTURE.md`

**Key Components**:
- **Platform Detection** (`platform_detector.py`): Multi-layered detection with confidence scoring
- **Installation Strategy** (`installation_strategy.py`): Three strategies (Native CLI, JSON, TOML)
- **Configuration Manager** (`config_manager.py`): Atomic operations with backup/restore
- **MCP Inspector** (`mcp_inspector.py`): Validation, issue detection, auto-fix
- **Command Builder** (`command_builder.py`): Intelligent command generation
- **Installer Orchestrator** (`installer.py`): Main API facade

**Design Patterns Used**:
- Strategy Pattern (installation methods)
- Factory Pattern (platform detectors)
- Facade Pattern (MCPInstaller)
- Template Method (base detector)
- Adapter Pattern (config formats)

**Quality Attributes**:
- Type-safe: 100% type hints, mypy strict mode
- Idempotent: Safe to re-run operations
- Atomic: All config updates use temp file + rename
- Cross-platform: macOS, Linux, Windows support

---

### 2. Implementation Plan
**Location**: `../IMPLEMENTATION-PLAN.md`

**6-Week Timeline**:

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1** | 6 days | Core abstractions (types, exceptions, utils, ConfigManager) |
| **Phase 2** | 7 days | Platform detection (all 8 platforms) |
| **Phase 3** | 7 days | Installation strategies (Native CLI, JSON, TOML) |
| **Phase 4** | 7 days | Inspector & validator (auto-fix, migration) |
| **Phase 5** | 7 days | Orchestrator & polish (API, docs, tests) |
| **Phase 6** | 7 days | CLI tool & packaging (PyPI release) |

**Quality Gates**:
- >90% test coverage required per phase
- mypy strict mode must pass
- All public APIs documented
- Cross-platform tests must pass

---

### 3. Project Structure
**Location**: `../PROJECT-STRUCTURE.md`

**Package Layout**:
```
py-mcp-installer-service/
├── src/py_mcp_installer/      # Main package
│   ├── installer.py            # Public API
│   ├── platforms/              # Platform-specific detectors
│   └── types.py                # Type definitions
├── tests/                      # Comprehensive test suite
├── docs/                       # Documentation
├── examples/                   # Usage examples
└── pyproject.toml              # Package configuration
```

**Key Templates Provided**:
- `pyproject.toml`: Complete packaging configuration
- `README.md`: Comprehensive documentation template
- `Makefile`: Development task automation
- `.gitignore`: Python best practices
- `CHANGELOG.md`: Version tracking

---

### 4. Research Foundation
**Location**: `../research/mcp-server-installation-patterns-2025-12-05.md`

**Platform Coverage**: 8/8 platforms analyzed

| Platform | Config Location | Format | Scope | CLI |
|----------|----------------|--------|-------|-----|
| Claude Code | `~/.config/claude/mcp.json` | JSON | Project | `claude` |
| Claude Desktop | Platform-specific | JSON | Global | `claude` |
| Cursor | `~/.cursor/mcp.json` | JSON | Project | None |
| Auggie | `~/.augment/settings.json` | JSON | Global | `auggie` |
| Codex | `~/.codex/config.toml` | TOML | Global | `codex` |
| Gemini | `.gemini/settings.json` or `~/.gemini/` | JSON | Both | `gemini` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | JSON | Project | GUI |
| Antigravity | Via MCP Store | JSON | Both | GUI |

**Key Insights**:
- All tools use stdio transport with Content-Length framing
- Legacy format (line-delimited JSON) must be auto-migrated
- Installation method priority: `uv run` > pipx > direct binary
- Configuration requires absolute paths (not relative)

---

## API Design

### High-Level API (Recommended for Users)

```python
from py_mcp_installer import MCPInstaller

# Auto-detect and install
installer = MCPInstaller.auto_detect()
result = installer.install_server(
    name="mcp-ticketer",
    env={"LINEAR_API_KEY": "..."}
)

# List and validate
servers = installer.list_servers()
issues = installer.validate_installation("mcp-ticketer")

# Auto-fix issues
installer.fix_server("mcp-ticketer")
```

### Low-Level API (Advanced Users)

```python
from py_mcp_installer import (
    PlatformDetectorRegistry,
    JSONConfigStrategy,
    MCPServerConfig,
    Platform,
)

# Manual detection and installation
detector = PlatformDetectorRegistry()
platforms = detector.detect_all()

strategy = JSONConfigStrategy()
config = MCPServerConfig(...)
result = strategy.install(platforms[0], config, ...)
```

### CLI Tool

```bash
# Detect platforms
mcp-installer detect

# Install server
mcp-installer install mcp-ticketer --env LINEAR_API_KEY=***

# Validate and fix
mcp-installer validate mcp-ticketer
mcp-installer fix mcp-ticketer
```

---

## Technical Highlights

### Type Safety
- **100% type coverage**: All public APIs fully typed
- **mypy strict mode**: No type errors allowed
- **Runtime validation**: Dataclass validation at runtime
- **Protocol definitions**: Clear interfaces for plugins

### Reliability
- **Atomic operations**: Temp file + rename for all writes
- **Automatic backups**: Created before every modification
- **Transaction support**: Context manager with auto-rollback
- **Idempotent**: Safe to re-run any operation

### Platform Support
- **Multi-layered detection**: File existence + format validation + CLI check
- **Confidence scoring**: 0.0-1.0 confidence for each detection
- **Graceful degradation**: Falls back from CLI to JSON manipulation
- **Cross-platform paths**: Uses pathlib for all file operations

### Auto-Migration
- **Legacy detection**: Identifies line-delimited JSON format
- **Safe migration**: Creates backup before migrating
- **Preserves data**: Maintains project paths and env vars
- **User notification**: Clear messages about migration

---

## Dependencies

### Runtime (Minimal)
```toml
[dependencies]
python = ">=3.10"
tomli = ">=2.0.0; python_version < '3.11'"  # TOML reading
tomli-w = ">=1.0.0"  # TOML writing
```

**Zero application dependencies** - fully standalone library.

### Development
```toml
[dev-dependencies]
pytest = ">=7.0.0"
pytest-cov = ">=4.0.0"
mypy = ">=1.0.0"
ruff = ">=0.1.0"
```

### Optional (CLI)
```toml
[cli-dependencies]
click = ">=8.0.0"  # CLI framework
rich = ">=13.0.0"  # Colored output
```

---

## Testing Strategy

### Unit Tests (>90% coverage)
- Mock file systems for config operations
- Mock CLI availability checks
- Test all validation rules
- Test error conditions and edge cases

### Integration Tests
- End-to-end installation workflows
- Platform detection accuracy
- Legacy format migration
- Error recovery and rollback
- Real-world config file samples

### Cross-Platform Tests
- CI/CD runs on macOS, Linux, Windows
- Python 3.10, 3.11, 3.12 tested
- Platform-specific path handling verified

---

## Extension Points

### Adding New Platforms

```python
# 1. Create detector
class MyPlatformDetector:
    def detect(self, project_path=None):
        # Custom detection logic
        ...

# 2. Register
from py_mcp_installer import PlatformDetectorRegistry, Platform

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
```

---

## Success Metrics

### Functional Requirements
- ✅ Detects 7/8 platforms (Antigravity config location TBD)
- ✅ Installs servers on all detected platforms
- ✅ Validates existing installations
- ✅ Auto-fixes common issues
- ✅ Clear error messages with recovery suggestions

### Non-Functional Requirements
- ✅ Zero dependencies on mcp-ticketer
- ✅ Cross-platform (macOS, Linux, Windows)
- ✅ Type-safe (100% mypy coverage)
- ✅ Well-tested (>90% coverage)
- ✅ Well-documented (API reference + guides)

### Release Criteria (v1.0.0)
- ✅ All 6 implementation phases complete
- ✅ All quality gates passed
- ✅ CI/CD pipeline operational
- ✅ Published to PyPI
- ✅ GitHub release with changelog
- ✅ README and documentation complete

---

## Risk Mitigation

### Known Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Antigravity config location unknown | Medium | Stub implementation, mark as TODO, add to roadmap |
| Platform API changes | High | Version detection, graceful degradation, clear errors |
| Cross-platform compatibility | High | Comprehensive CI testing, pathlib for all paths |
| Breaking CLI changes | Medium | Always provide JSON fallback, test CLI availability |

---

## Post-Release Roadmap

### v1.1.0 (Q2 2025)
- Add Antigravity support (once config location documented)
- Add HTTP/SSE transport support (not just stdio)
- Enhanced validation rules
- Performance improvements

### v1.2.0 (Q3 2025)
- Server lifecycle management (start/stop/restart)
- GUI tool for non-technical users
- Multi-server installation profiles
- Configuration templates

### v2.0.0 (Q4 2025)
- Custom MCP protocol versions
- Advanced dependency management
- Server scaffolding and templates
- Performance monitoring

---

## Next Actions

### Immediate (Today)
1. ✅ **Design Complete**: All design documents created
2. ⏭️ **Review Design**: Stakeholder review and approval
3. ⏭️ **Create Repository**: Initialize GitHub repository

### Week 1 (Phase 1)
1. Set up project structure
2. Implement core abstractions (types, exceptions, utils)
3. Implement ConfigManager with atomic operations
4. Write unit tests for Phase 1 modules

### Weeks 2-6
- Follow implementation plan phase by phase
- Maintain >90% test coverage
- Keep documentation updated
- Run quality gates at end of each phase

---

## Deliverables Summary

### Design Documents (Complete)
- ✅ Architecture Design (`../ARCHITECTURE.md`)
- ✅ Implementation Plan (`../IMPLEMENTATION-PLAN.md`)
- ✅ Project Structure (`../PROJECT-STRUCTURE.md`)
- ✅ Design Summary (`SUMMARY.md`)

### Templates (Ready)
- ✅ `pyproject.toml` - Complete packaging configuration
- ✅ `README.md` - Comprehensive documentation template
- ✅ `Makefile` - Development task automation
- ✅ `__init__.py` - Public API exports
- ✅ `.gitignore` - Python best practices
- ✅ `CHANGELOG.md` - Version tracking

### Implementation (Pending)
- ⏭️ 9 core modules to implement
- ⏭️ 8 platform detectors to implement
- ⏭️ Unit and integration test suites
- ⏭️ CLI tool
- ⏭️ Documentation and examples

---

## Key Design Principles

### 1. Code Minimization
- Leverage existing utilities before writing new code
- Consolidate similar functionality
- Extract common patterns into shared modules

### 2. Type Safety
- 100% type hints on public API
- mypy strict mode enforced
- Runtime validation via dataclasses

### 3. Reliability
- Atomic operations with rollback
- Automatic backups before modifications
- Idempotent operations

### 4. Usability
- Simple high-level API (one-liner installation)
- Clear error messages with recovery suggestions
- Dry-run mode for all operations
- Comprehensive documentation

### 5. Extensibility
- Plugin architecture for platforms
- Strategy pattern for installation methods
- Easy to add new platforms

---

## Conclusion

The py-mcp-installer-service design is **complete and ready for implementation**. The design provides:

1. **Clear Architecture**: 9 well-defined modules with single responsibilities
2. **Detailed Plan**: 6-week phased implementation with acceptance criteria
3. **Complete Templates**: All necessary project files and configurations
4. **Research Foundation**: Based on analysis of 8 real-world platforms
5. **Quality Focus**: >90% test coverage, type safety, cross-platform support

**Estimated Effort**: 6 weeks (42 days) to v1.0.0 production release

**Recommendation**: Proceed with Phase 1 implementation immediately.

---

## Document Metadata

| Attribute | Value |
|-----------|-------|
| Version | 1.0.0 |
| Date | 2025-12-05 |
| Status | Design Complete - Ready for Implementation |
| Architecture | `../ARCHITECTURE.md` |
| Implementation Plan | `../IMPLEMENTATION-PLAN.md` |
| Project Structure | `../PROJECT-STRUCTURE.md` |
| Research | `../research/mcp-server-installation-patterns-2025-12-05.md` |
| Target Python | 3.10+ |
| Target Platforms | 8 (7 documented, 1 planned) |
| License | MIT (recommended) |

---

**Design Status**: ✅ **COMPLETE - READY FOR IMPLEMENTATION**
