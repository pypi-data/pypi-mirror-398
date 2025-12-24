# py-mcp-installer-service: Architecture Diagrams

**Version:** 1.0.0
**Date:** 2025-12-05

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Application                         │
│                  (mcp-ticketer, custom projects)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ imports
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    py_mcp_installer Package                      │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              MCPInstaller (Facade)                       │   │
│  │  - auto_detect()                                         │   │
│  │  - install_server()                                      │   │
│  │  - list_servers()                                        │   │
│  │  - validate_installation()                               │   │
│  │  - fix_server()                                          │   │
│  └──────────────┬──────────────┬──────────────┬─────────────┘   │
│                 │              │              │                  │
│       ┌─────────▼────┐  ┌──────▼─────┐  ┌────▼──────────┐     │
│       │  Platform    │  │Installation │  │     MCP       │     │
│       │  Detector    │  │  Strategy   │  │  Inspector    │     │
│       └─────┬────────┘  └──────┬──────┘  └────┬──────────┘     │
│             │                  │              │                  │
│       ┌─────▼────────┐  ┌──────▼──────┐  ┌────▼──────────┐    │
│       │   Config     │  │   Command   │  │   Validator   │    │
│       │   Manager    │  │   Builder   │  │               │    │
│       └──────────────┘  └─────────────┘  └───────────────┘    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ reads/writes
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Configuration Files                           │
│  - Claude Code:    ~/.config/claude/mcp.json                    │
│  - Claude Desktop: ~/Library/Application Support/Claude/...     │
│  - Cursor:         ~/.cursor/mcp.json                           │
│  - Auggie:         ~/.augment/settings.json                     │
│  - Codex:          ~/.codex/config.toml                         │
│  - Gemini:         .gemini/settings.json                        │
│  - Windsurf:       ~/.codeium/windsurf/mcp_config.json          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Interaction Flow

```
┌──────────┐
│  User    │
└────┬─────┘
     │
     │ MCPInstaller.auto_detect()
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│ 1. Platform Detection Phase                              │
│                                                           │
│  PlatformDetectorRegistry                                │
│    │                                                      │
│    ├─► ClaudeCodeDetector.detect()                       │
│    │     ├─ Check ~/.config/claude/mcp.json              │
│    │     ├─ Validate JSON format                         │
│    │     ├─ Check `claude` CLI availability              │
│    │     └─ Calculate confidence score                   │
│    │                                                      │
│    ├─► CursorDetector.detect()                           │
│    │     ├─ Check ~/.cursor/mcp.json                     │
│    │     ├─ Validate JSON format                         │
│    │     └─ Calculate confidence score                   │
│    │                                                      │
│    └─► [6 more platform detectors...]                    │
│                                                           │
│  Returns: List[DetectedPlatform] sorted by confidence    │
└──────────────────────────────────────────────────────────┘
     │
     │ Select best platform
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│ 2. Installation Phase                                     │
│                                                           │
│  installer.install_server(name, env, ...)                │
│    │                                                      │
│    ├─► CommandBuilder.detect_installation_method()       │
│    │     ├─ Check for `uv` in PATH                       │
│    │     ├─ Check for `mcp-ticketer` in PATH             │
│    │     └─ Return (method, command, args)               │
│    │                                                      │
│    ├─► Select InstallationStrategy                       │
│    │     ├─ If platform has CLI → NativeCLIStrategy      │
│    │     ├─ If JSON format → JSONConfigStrategy          │
│    │     └─ If TOML format → TOMLConfigStrategy          │
│    │                                                      │
│    └─► strategy.install(platform, config, ...)           │
│          │                                                │
│          ├─► ConfigManager.load()                        │
│          ├─► ConfigManager.backup()                      │
│          ├─► Update configuration                        │
│          └─► ConfigManager.save() (atomic)               │
│                                                           │
│  Returns: InstallationResult                             │
└──────────────────────────────────────────────────────────┘
     │
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│ 3. Validation Phase (optional)                            │
│                                                           │
│  installer.validate_installation(server_name)            │
│    │                                                      │
│    └─► MCPInspector.validate_server()                    │
│          ├─ Check for legacy format                      │
│          ├─ Check command path exists                    │
│          ├─ Check for missing fields                     │
│          ├─ Check environment variables                  │
│          └─ Return list[ConfigIssue]                     │
│                                                           │
│  Returns: List[ConfigIssue]                              │
└──────────────────────────────────────────────────────────┘
     │
     │ If issues found
     │
     ▼
┌──────────────────────────────────────────────────────────┐
│ 4. Auto-Fix Phase (optional)                             │
│                                                           │
│  installer.fix_server(server_name)                       │
│    │                                                      │
│    └─► MCPInspector.fix_server()                         │
│          ├─ Migrate legacy format to FastMCP             │
│          ├─ Update missing command paths                 │
│          ├─ Fix wrong transport types                    │
│          └─ Apply fixes via ConfigManager.transaction()  │
│                                                           │
│  Returns: InstallationResult                             │
└──────────────────────────────────────────────────────────┘
     │
     │
     ▼
┌──────────┐
│  Done    │
└──────────┘
```

---

## 3. Platform Detection Decision Tree

```
                    Start Detection
                          │
                          ▼
              ┌───────────────────────┐
              │ For each platform:    │
              │ - Claude Code         │
              │ - Claude Desktop      │
              │ - Cursor              │
              │ - Auggie              │
              │ - Codex               │
              │ - Gemini              │
              │ - Windsurf            │
              │ - Antigravity         │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Layer 1:              │
              │ Config file exists?   │
              └──────┬────────────────┘
                     │
            ┌────────┴────────┐
            │                 │
           NO                YES
            │                 │
            ▼                 ▼
    ┌─────────────┐   ┌─────────────────┐
    │ confidence  │   │ Layer 2:        │
    │ = 0.0       │   │ Valid format?   │
    │             │   │ (JSON/TOML)     │
    │ Return None │   └────────┬────────┘
    └─────────────┘            │
                      ┌────────┴────────┐
                      │                 │
                     NO                YES
                      │                 │
                      ▼                 ▼
              ┌─────────────┐   ┌─────────────────┐
              │ confidence  │   │ Layer 3:        │
              │ = 0.4       │   │ CLI available?  │
              │             │   │ (if applicable) │
              │ Return with │   └────────┬────────┘
              │ issues      │            │
              └─────────────┘   ┌────────┴────────┐
                                │                 │
                               NO                YES
                                │                 │
                                ▼                 ▼
                        ┌─────────────┐   ┌─────────────┐
                        │ confidence  │   │ confidence  │
                        │ = 0.8       │   │ = 1.0       │
                        │             │   │             │
                        │ Return with │   │ Return      │
                        │ is_installed│   │ fully ready │
                        │ = True      │   └─────────────┘
                        └─────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Sort all platforms by │
                    │ confidence (desc)     │
                    │                       │
                    │ Return best match     │
                    └───────────────────────┘
```

---

## 4. Installation Strategy Selection

```
                    Start Installation
                          │
                          ▼
              ┌───────────────────────┐
              │ Which platform?       │
              └───────────┬───────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Claude Code   │ │ Cursor        │ │ Codex         │
│ Claude Desktop│ │ Auggie        │ │               │
│               │ │ Windsurf      │ │               │
│               │ │ Gemini        │ │               │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Has native    │ │ JSON-based    │ │ TOML-based    │
│ CLI?          │ │ configuration │ │ configuration │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
┌───────┴───────┐         │                 │
│               │         │                 │
▼               ▼         ▼                 ▼
┌──────────┐  ┌──────────────────┐  ┌───────────────┐
│ `claude` │  │ JSON Config      │  │ TOML Config   │
│ CLI      │  │ Strategy         │  │ Strategy      │
│ exists?  │  │                  │  │               │
└────┬─────┘  │ - Load JSON      │  │ - Load TOML   │
     │        │ - Backup         │  │ - Backup      │
     │        │ - Update         │  │ - Update      │
     │        │ - Save (atomic)  │  │ - Save        │
     │        └──────────────────┘  └───────────────┘
┌────┴─────┐
│          │
YES        NO
│          │
▼          ▼
┌──────────────────┐  ┌──────────────────┐
│ Native CLI       │  │ JSON Config      │
│ Strategy         │  │ Strategy         │
│                  │  │ (fallback)       │
│ - Build CLI cmd  │  │                  │
│ - Execute        │  │ Same as above    │
│ - If fails,      │  └──────────────────┘
│   fallback to    │
│   JSON strategy  │
└──────────────────┘
```

---

## 5. Configuration Manager Atomic Write Flow

```
                Start save_config(config)
                          │
                          ▼
              ┌───────────────────────┐
              │ Config file exists?   │
              └───────────┬───────────┘
                          │
                    ┌─────┴─────┐
                   YES           NO
                    │             │
                    ▼             │
          ┌─────────────────┐    │
          │ Create backup:  │    │
          │ .backup/{name}  │    │
          │ .{timestamp}    │    │
          └─────────┬───────┘    │
                    │             │
                    └─────┬───────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Create temp file:     │
              │ .{name}.{random}.tmp  │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Write config to       │
              │ temp file             │
              │ (JSON or TOML)        │
              └───────────┬───────────┘
                          │
                    ┌─────┴─────┐
                    │           │
                 Success      Error
                    │           │
                    │           ▼
                    │   ┌─────────────────┐
                    │   │ Delete temp     │
                    │   │ file            │
                    │   │                 │
                    │   │ Raise exception │
                    │   └─────────────────┘
                    │
                    ▼
          ┌─────────────────────┐
          │ Atomic rename:      │
          │ temp → config_path  │
          │                     │
          │ (os.replace)        │
          └─────────┬───────────┘
                    │
                    ▼
          ┌─────────────────────┐
          │ Clean old backups   │
          │ (keep last 10)      │
          └─────────┬───────────┘
                    │
                    ▼
                  Done
```

---

## 6. Legacy Server Migration Flow

```
            Start validate_server(name)
                      │
                      ▼
          ┌───────────────────────┐
          │ Load server config    │
          └───────────┬───────────┘
                      │
                      ▼
          ┌───────────────────────┐
          │ Check args for:       │
          │ ["-m",                │
          │  "mcp_ticketer.mcp.   │
          │   server"]            │
          └───────────┬───────────┘
                      │
                ┌─────┴─────┐
                │           │
            Not Found     Found
                │           │
                │           ▼
                │   ┌─────────────────────┐
                │   │ Issue Type:         │
                │   │ LEGACY_SERVER       │
                │   │                     │
                │   │ Severity: CRITICAL  │
                │   │                     │
                │   │ Auto-fixable: TRUE  │
                │   └─────────┬───────────┘
                │             │
                │             │ User calls fix_server()
                │             │
                │             ▼
                │   ┌─────────────────────┐
                │   │ Create backup of    │
                │   │ config file         │
                │   └─────────┬───────────┘
                │             │
                │             ▼
                │   ┌─────────────────────┐
                │   │ Detect best command:│
                │   │ 1. Check for `uv`   │
                │   │ 2. Check for binary │
                │   │ 3. Use Python       │
                │   └─────────┬───────────┘
                │             │
                │             ▼
                │   ┌─────────────────────┐
                │   │ Update config:      │
                │   │ command = detected  │
                │   │ args = ["mcp"]      │
                │   │                     │
                │   │ Preserve:           │
                │   │ - env vars          │
                │   │ - project path      │
                │   └─────────┬───────────┘
                │             │
                │             ▼
                │   ┌─────────────────────┐
                │   │ Save config         │
                │   │ (atomic write)      │
                │   └─────────┬───────────┘
                │             │
                │             ▼
                │   ┌─────────────────────┐
                │   │ Return success:     │
                │   │ "Migrated to        │
                │   │  FastMCP format"    │
                │   └─────────────────────┘
                │
                └─────────► No migration needed
```

---

## 7. Command Building Strategy

```
        Start detect_installation_method()
                      │
                      ▼
          ┌───────────────────────┐
          │ Check: `uv` in PATH?  │
          └───────────┬───────────┘
                      │
                ┌─────┴─────┐
               YES           NO
                │             │
                ▼             │
    ┌────────────────────┐   │
    │ Method: UV_RUN     │   │
    │ Command: "uv"      │   │
    │ Args: ["run",      │   │
    │        "mcp-       │   │
    │         ticketer", │   │
    │        "mcp"]      │   │
    └────────────────────┘   │
                             │
                             ▼
                 ┌───────────────────────┐
                 │ Check: `mcp-ticketer` │
                 │        in PATH?       │
                 └───────────┬───────────┘
                             │
                       ┌─────┴─────┐
                      YES           NO
                       │             │
                       ▼             │
          ┌────────────────────┐    │
          │ Method:            │    │
          │ DIRECT_BINARY      │    │
          │                    │    │
          │ Command:           │    │
          │ /abs/path/to/      │    │
          │ mcp-ticketer       │    │
          │                    │    │
          │ Args: ["mcp"]      │    │
          └────────────────────┘    │
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Detect Python with    │
                        │ mcp_ticketer module   │
                        │                       │
                        │ Priority:             │
                        │ 1. Project venv       │
                        │ 2. pipx venv          │
                        │ 3. Binary shebang     │
                        │ 4. sys.executable     │
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │ Method:               │
                        │ PYTHON_MODULE         │
                        │                       │
                        │ Command:              │
                        │ /path/to/python       │
                        │                       │
                        │ Args: ["-m",          │
                        │  "mcp_ticketer.mcp.   │
                        │   server"]            │
                        └───────────────────────┘
```

---

## 8. Error Handling & Recovery

```
                    Operation Start
                          │
                          ▼
              ┌───────────────────────┐
              │ Try: Load config      │
              └───────────┬───────────┘
                          │
                    ┌─────┴─────┐
                    │           │
                Success      Error
                    │           │
                    │           ▼
                    │   ┌─────────────────┐
                    │   │ ConfigurationError│
                    │   │ - Invalid JSON?  │
                    │   │ - Invalid TOML?  │
                    │   │ - Permission?    │
                    │   └─────────┬────────┘
                    │             │
                    │             ▼
                    │   ┌─────────────────┐
                    │   │ Provide:        │
                    │   │ - Error message │
                    │   │ - Recovery      │
                    │   │   suggestion    │
                    │   │ - Config path   │
                    │   └─────────────────┘
                    │
                    ▼
          ┌─────────────────────┐
          │ Try: Create backup  │
          └─────────┬───────────┘
                    │
              ┌─────┴─────┐
              │           │
          Success      Error
              │           │
              │           ▼
              │   ┌─────────────────┐
              │   │ BackupError     │
              │   │ - Disk full?    │
              │   │ - Permission?   │
              │   └─────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │ Try: Update config  │
    └─────────┬───────────┘
              │
        ┌─────┴─────┐
        │           │
    Success      Error
        │           │
        │           ▼
        │   ┌─────────────────┐
        │   │ Restore backup  │
        │   │                 │
        │   │ Raise exception │
        │   │ with details    │
        │   └─────────────────┘
        │
        ▼
┌─────────────────────┐
│ Success             │
│                     │
│ Return result with: │
│ - Success status    │
│ - Message           │
│ - Next steps        │
└─────────────────────┘
```

---

## 9. Type System Hierarchy

```
                    Types Module
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    Enums           Dataclasses        Protocols
        │                 │                 │
        ├─ Platform       ├─ DetectedPlatform    ├─ PlatformDetector
        ├─ ConfigScope    ├─ MCPServerConfig     ├─ InstallationStrategy
        ├─ InstallMethod  ├─ InstallationResult  │
        ├─ ConfigFormat   ├─ ConfigIssue         │
        ├─ IssueType      ├─ InstalledServer     │
        └─ IssueSeverity  │                       │
                          │                       │
                          ▼                       ▼
                   Used throughout          Extension points
                   all modules              for plugins
```

---

## 10. Package Dependencies Graph

```
                    User Application
                          │
                          │ import
                          ▼
                  py_mcp_installer
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   installer.py    types.py          exceptions.py
        │                                   │
        │ uses                              │
        │                                   │
        ├──────────────┬──────────┬─────────┤
        │              │          │         │
        ▼              ▼          ▼         ▼
platform_detector  installation  mcp_    utils.py
     .py            _strategy.py inspector.py
        │              │          │
        │              │          │
        ▼              ▼          ▼
   platforms/    command_builder config_manager
   (8 modules)        .py           .py
                                     │
                                     │ uses
                                     ▼
                              ┌─────────────┐
                              │  tomli      │
                              │  tomli-w    │
                              │ (external)  │
                              └─────────────┘
```

---

## 11. Data Flow: Full Installation

```
User Code
    │
    │ MCPInstaller.auto_detect()
    │
    ├──► PlatformDetectorRegistry.detect_all()
    │       │
    │       ├──► ClaudeCodeDetector.detect() → DetectedPlatform(confidence=1.0)
    │       ├──► CursorDetector.detect() → DetectedPlatform(confidence=0.8)
    │       └──► ... (6 more detectors)
    │       │
    │       └──► Sort by confidence → Return [ClaudeCode, Cursor, ...]
    │
    ├──► Select best: ClaudeCode (confidence=1.0)
    │
    │ installer.install_server(name="mcp-ticketer", env={...})
    │
    ├──► CommandBuilder.detect_installation_method()
    │       │
    │       ├──► Check `uv` → Found!
    │       └──► Return (UV_RUN, "uv", ["run", "mcp-ticketer", "mcp"])
    │
    ├──► Create MCPServerConfig(
    │       name="mcp-ticketer",
    │       command="uv",
    │       args=["run", "mcp-ticketer", "mcp"],
    │       env={...}
    │    )
    │
    ├──► Select strategy: NativeCLIStrategy (Claude Code has CLI)
    │
    ├──► NativeCLIStrategy.install()
    │       │
    │       ├──► Build CLI command: `claude mcp add --scope local ...`
    │       ├──► Execute command
    │       └──► If success → Return InstallationResult(success=True)
    │            If failure → Fallback to JSONConfigStrategy
    │
    └──► Return InstallationResult to user
            │
            ├─ success: True
            ├─ platform: Platform.CLAUDE_CODE
            ├─ server_name: "mcp-ticketer"
            ├─ config_path: ~/.config/claude/mcp.json
            ├─ method: InstallMethod.UV_RUN
            ├─ message: "Successfully installed via native CLI"
            └─ next_steps: ["Restart Claude Code"]
```

---

## 12. Class Diagram: Core Classes

```
┌─────────────────────────────────────────────────────────────┐
│                      MCPInstaller                           │
├─────────────────────────────────────────────────────────────┤
│ - platform_detector: PlatformDetectorRegistry               │
│ - target_platform: Optional[DetectedPlatform]               │
├─────────────────────────────────────────────────────────────┤
│ + __init__(platform: Optional[Platform])                    │
│ + auto_detect(project_path: Optional[Path]) → MCPInstaller  │
│ + list_platforms() → list[DetectedPlatform]                 │
│ + install_server(...) → InstallationResult                  │
│ + list_servers() → list[InstalledServer]                    │
│ + validate_installation(name) → list[ConfigIssue]           │
│ + fix_server(name) → InstallationResult                     │
│ + uninstall_server(name) → InstallationResult               │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ uses
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│PlatformDetector  │ │InstallationStrategy│ │  MCPInspector   │
│     Registry     │ │                  │ │                  │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│- detectors: dict │ │+ supports_       │ │- platform:       │
│                  │ │  platform()      │ │  DetectedPlatform│
├──────────────────┤ │+ install()       │ ├──────────────────┤
│+ register()      │ │+ uninstall()     │ │+ list_servers()  │
│+ detect_all()    │ │+ update()        │ │+ validate_server│
│+ detect_one()    │ └──────────────────┘ │+ suggest_fixes() │
└──────────────────┘          │            │+ fix_server()    │
        │                     │            └──────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ClaudeCodeDetector│ │NativeCLIStrategy │ │  ConfigManager   │
│CursorDetector    │ │JSONConfigStrategy│ │                  │
│... (8 total)     │ │TOMLConfigStrategy│ ├──────────────────┤
├──────────────────┤ └──────────────────┘ │- config_path     │
│+ detect()        │          │            │- format          │
└──────────────────┘          │            ├──────────────────┤
                              │            │+ load()          │
                              ▼            │+ save()          │
                     ┌──────────────────┐ │+ validate()      │
                     │ CommandBuilder   │ │+ transaction()   │
                     ├──────────────────┤ └──────────────────┘
                     │+ detect_         │
                     │  installation_   │
                     │  method()        │
                     │+ build_server_   │
                     │  command()       │
                     │+ resolve_        │
                     │  absolute_path() │
                     └──────────────────┘
```

---

## Summary

These diagrams illustrate:

1. **System Architecture**: High-level component organization
2. **Interaction Flow**: Step-by-step execution sequence
3. **Decision Trees**: Platform detection and strategy selection logic
4. **Data Flow**: How data moves through the system
5. **Error Handling**: Recovery mechanisms
6. **Type System**: Type hierarchy and relationships
7. **Dependencies**: Module dependencies and imports
8. **Class Relationships**: Object-oriented design

All diagrams support the architecture defined in `ARCHITECTURE.md`.

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-05
