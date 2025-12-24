# MCP Server Installation Patterns for AI Coding Tools

**Research Date:** 2025-12-05
**Status:** Comprehensive investigation complete
**Scope:** Universal MCP installer library for mcp-ticketer

## Executive Summary

This research documents MCP (Model Context Protocol) server installation and configuration patterns across 7 major AI coding tools: Claude Code, Claude Desktop, Cursor, Auggie, Codex, Gemini CLI, Windsurf, and Antigravity. The findings enable development of a universal installer library that can detect execution environments, determine optimal installation methods, inspect existing installations, and fix/update MCP server configurations.

### Key Findings

1. **Configuration File Diversity**: All 7 tools use different config locations and formats (JSON, TOML)
2. **Scope Variations**: Tools support global-only, project-only, or both configuration scopes
3. **Detection Strategies**: Environment detection requires multi-layered approach (file existence, CLI availability, config validation)
4. **Installation Methods**: Python servers prefer `uv run` > pipx > direct binary; TypeScript servers use npx
5. **Protocol Uniformity**: All tools support stdio transport with Content-Length framing (FastMCP SDK)

---

## 1. Claude Code (Project-Level)

### Configuration Locations

**Primary (New):** `~/.config/claude/mcp.json`
**Legacy:** `~/.claude.json`
**Local Fallback:** `.claude/mcp.local.json` (project directory)

### Structure

```json
{
  "mcpServers": {
    "mcp-ticketer": {
      "type": "stdio",
      "command": "/path/to/mcp-ticketer",
      "args": ["mcp", "--path", "/absolute/project/path"],
      "env": {
        "MCP_TICKETER_ADAPTER": "linear",
        "LINEAR_API_KEY": "***",
        "LINEAR_TEAM_ID": "***"
      }
    }
  }
}
```

**Format Evolution:**
- **New (Flat)**: `~/.config/claude/mcp.json` uses flat `mcpServers` structure
- **Old (Nested)**: `~/.claude.json` uses nested `projects[path].mcpServers` structure

### Detection Strategy

```python
def detect_claude_code() -> DetectedPlatform | None:
    # Priority 1: New global location
    new_config = Path.home() / ".config" / "claude" / "mcp.json"
    old_config = Path.home() / ".claude.json"

    config_path = new_config if new_config.exists() else old_config

    if config_path.exists():
        try:
            with config_path.open() as f:
                content = f.read().strip()
                if content:
                    json.loads(content)  # Validate JSON
            return DetectedPlatform(
                name="claude-code",
                display_name="Claude Code",
                config_path=config_path,
                is_installed=True,
                scope="project"
            )
        except json.JSONDecodeError:
            return DetectedPlatform(..., is_installed=False)
    return None
```

### Installation Methods

**Preferred (Native CLI):**
```bash
claude mcp add \
  --scope local \
  --transport stdio \
  --env LINEAR_API_KEY=*** \
  --env LINEAR_TEAM_ID=*** \
  mcp-ticketer \
  -- mcp-ticketer mcp --path /project/path
```

**Requirements:**
- `claude` CLI available in PATH
- `mcp-ticketer` command available in PATH (for native mode)
- If `mcp-ticketer` not in PATH → fallback to JSON mode with full paths

**Fallback (JSON Manipulation):**
```python
# Use full paths when mcp-ticketer not in PATH
config = {
    "type": "stdio",
    "command": "/absolute/path/to/.local/bin/mcp-ticketer",
    "args": ["mcp", "--path", "/absolute/project/path"],
    "env": {...}
}
```

### Key Insights

- **Dual Mode Operation**: Native CLI (preferred) vs JSON manipulation (fallback)
- **PATH Dependency**: Native mode requires `mcp-ticketer` in PATH; JSON mode uses absolute paths
- **Auto-Migration**: Detects legacy line-delimited JSON servers and auto-migrates to FastMCP
- **Project Isolation**: Each project can have different adapters/credentials
- **Restart Required**: Claude Code restart needed after config changes

---

## 2. Claude Desktop (Global)

### Configuration Locations

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%/Claude/claude_desktop_config.json`

### Structure

```json
{
  "mcpServers": {
    "mcp-ticketer": {
      "type": "stdio",
      "command": "/path/to/mcp-ticketer",
      "args": ["mcp"],
      "env": {
        "MCP_TICKETER_ADAPTER": "linear",
        "LINEAR_API_KEY": "***"
      }
    }
  }
}
```

### Detection Strategy

```python
def detect_claude_desktop() -> DetectedPlatform | None:
    if sys.platform == "darwin":
        config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "win32":
        config_path = Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        config_path = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

    if config_path.exists():
        # Validate JSON and return detection result
        ...
```

### Installation Methods

**Native CLI:**
```bash
claude mcp add \
  --scope user \
  --transport stdio \
  --env LINEAR_API_KEY=*** \
  mcp-ticketer \
  -- mcp-ticketer mcp
```

**JSON Manipulation:**
```python
# Global config - no project path
config = {
    "type": "stdio",
    "command": "/absolute/path/to/mcp-ticketer",
    "args": ["mcp"],
    "env": {...}
}
```

### Key Insights

- **Global Scope Only**: All projects share same adapter configuration
- **Platform-Specific Paths**: Different config locations per OS
- **Desktop App**: GUI application, not CLI
- **Same Dual Mode**: Native CLI + JSON fallback like Claude Code

---

## 3. Cursor (Project-Level)

### Configuration Location

`~/.cursor/mcp.json` (global location with flat structure)

### Structure

```json
{
  "mcpServers": {
    "mcp-ticketer": {
      "type": "stdio",
      "command": "/path/to/mcp-ticketer",
      "args": ["mcp", "--path", "/project/path"],
      "env": {...},
      "cwd": "/project/path"
    }
  }
}
```

### Detection Strategy

```python
def detect_cursor() -> DetectedPlatform | None:
    config_path = Path.home() / ".cursor" / "mcp.json"

    if config_path.exists():
        try:
            with config_path.open() as f:
                content = f.read().strip()
                if content:
                    json.loads(content)
            return DetectedPlatform(
                name="cursor",
                display_name="Cursor",
                config_path=config_path,
                is_installed=True,
                scope="project"
            )
        except json.JSONDecodeError:
            return DetectedPlatform(..., is_installed=False)
    return None
```

### Installation Method

**JSON Only (No CLI):**
```python
config = {
    "type": "stdio",
    "command": "/absolute/path/to/mcp-ticketer",
    "args": ["mcp", "--path", "/absolute/project/path"],
    "env": {...},
    "cwd": "/absolute/project/path"
}
```

### Key Insights

- **No Native CLI**: Cursor doesn't provide CLI for MCP management
- **Explicit Type Required**: Must include `"type": "stdio"`
- **Working Directory**: Supports `cwd` field for project context
- **Flat Structure**: Similar to Claude Code's new format

---

## 4. Auggie (Global Only)

### Configuration Location

`~/.augment/settings.json` (global only)

### Structure

```json
{
  "mcpServers": {
    "mcp-ticketer": {
      "command": "/path/to/mcp-ticketer",
      "args": ["mcp", "--path", "/project/path"],
      "env": {...}
    }
  }
}
```

### Detection Strategy

```python
def detect_auggie() -> DetectedPlatform | None:
    executable_path = shutil.which("auggie")
    if not executable_path:
        return None

    config_path = Path.home() / ".augment" / "settings.json"
    is_installed = True  # CLI exists

    if config_path.exists():
        try:
            with config_path.open() as f:
                content = f.read().strip()
                if content:
                    json.loads(content)
        except json.JSONDecodeError:
            is_installed = False

    return DetectedPlatform(
        name="auggie",
        display_name="Auggie",
        config_path=config_path,
        is_installed=is_installed,
        scope="global",
        executable_path=executable_path
    )
```

### Installation Method

**JSON Only:**
```python
config = {
    "command": "/absolute/path/to/mcp-ticketer",
    "args": ["mcp", "--path", "/project/path"],
    "env": {...}
}
```

### Key Insights

- **Global Only**: No project-level configuration support
- **CLI Requirement**: Must have `auggie` command in PATH
- **No Type Field**: Unlike Cursor, doesn't require `"type": "stdio"`
- **Project Path in Args**: Global config but includes project path in arguments

---

## 5. Codex (Global Only)

### Configuration Location

`~/.codex/config.toml` (TOML format, not JSON)

### Structure

```toml
[mcp_servers.mcp-ticketer]
command = "/path/to/mcp-ticketer"
args = ["mcp", "--path", "/project/path"]
```

**Note:** Uses `mcp_servers` (underscore), not `mcpServers` (camelCase)

### Detection Strategy

```python
def detect_codex() -> DetectedPlatform | None:
    executable_path = shutil.which("codex")
    if not executable_path:
        return None

    config_path = Path.home() / ".codex" / "config.toml"
    is_installed = True

    if config_path.exists():
        try:
            with config_path.open() as f:
                f.read()  # Check readable
        except OSError:
            is_installed = False

    return DetectedPlatform(
        name="codex",
        display_name="Codex",
        config_path=config_path,
        is_installed=is_installed,
        scope="global",
        executable_path=executable_path
    )
```

### Installation Method

**TOML Manipulation:**
```python
import tomli_w
import tomllib

config = {
    "mcp_servers": {
        "mcp-ticketer": {
            "command": "/absolute/path/to/mcp-ticketer",
            "args": ["mcp", "--path", "/project/path"]
        }
    }
}

with open(config_path, "wb") as f:
    tomli_w.dump(config, f)
```

### Key Insights

- **TOML Format**: Only tool using TOML instead of JSON
- **Snake Case**: Uses `mcp_servers` not `mcpServers`
- **No Environment Variables**: Minimal config structure
- **CLI Requirement**: Must have `codex` command in PATH
- **Global Only**: No project-level support

---

## 6. Gemini CLI (Project + Global)

### Configuration Locations

**Project:** `.gemini/settings.json` (current directory)
**Global:** `~/.gemini/settings.json`

### Structure

```json
{
  "mcpServers": {
    "mcp-ticketer": {
      "command": "/path/to/mcp-ticketer",
      "args": ["mcp", "--path", "/project/path"],
      "env": {...},
      "timeout": 15000,
      "trust": false
    }
  }
}
```

### Detection Strategy

```python
def detect_gemini(project_path: Path | None = None) -> DetectedPlatform | None:
    executable_path = shutil.which("gemini")
    if not executable_path:
        return None

    project_config = None
    global_config = Path.home() / ".gemini" / "settings.json"

    if project_path:
        project_config = project_path / ".gemini" / "settings.json"

    # Priority: project > global
    config_path = global_config
    scope = "global"

    if project_config and project_config.exists():
        config_path = project_config
        scope = "project"
    elif global_config.exists():
        config_path = global_config

    # Check if both exist
    if project_config and project_config.exists() and global_config.exists():
        scope = "both"

    return DetectedPlatform(
        name="gemini",
        display_name="Gemini",
        config_path=config_path,
        is_installed=True,
        scope=scope,
        executable_path=executable_path
    )
```

### Installation Method

**JSON with Additional Fields:**
```python
config = {
    "command": "/absolute/path/to/mcp-ticketer",
    "args": ["mcp", "--path", "/project/path"],
    "env": {...},
    "timeout": 15000,  # Gemini-specific
    "trust": False     # Gemini-specific
}

# Auto-add .gemini/ to .gitignore for project-level config
if scope == "project":
    gitignore_path = Path.cwd() / ".gitignore"
    if ".gemini" not in gitignore_path.read_text():
        with open(gitignore_path, "a") as f:
            f.write("\n# Gemini CLI\n.gemini/\n")
```

### Key Insights

- **Dual Scope**: Supports both project and global configurations
- **Priority Order**: Project config overrides global config
- **Additional Fields**: `timeout` and `trust` fields specific to Gemini
- **CLI Requirement**: Must have `gemini` command in PATH
- **Auto Gitignore**: Installer auto-adds `.gemini/` to `.gitignore`

---

## 7. Windsurf (Project-Level)

### Configuration Location

`~/.codeium/windsurf/mcp_config.json`

### Structure

```json
{
  "mcpServers": {
    "mcp-ticketer": {
      "command": "/path/to/mcp-ticketer",
      "args": ["mcp"],
      "env": {...}
    }
  }
}
```

### Detection Strategy

```python
def detect_windsurf() -> DetectedPlatform | None:
    config_path = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"

    if config_path.exists():
        try:
            with config_path.open() as f:
                content = f.read().strip()
                if content:
                    json.loads(content)
            return DetectedPlatform(
                name="windsurf",
                display_name="Windsurf",
                config_path=config_path,
                is_installed=True,
                scope="project"
            )
        except json.JSONDecodeError:
            return DetectedPlatform(..., is_installed=False)
    return None
```

### Installation Method

**JSON Manipulation:**
```python
config = {
    "command": "/absolute/path/to/mcp-ticketer",
    "args": ["mcp"],
    "env": {...}
}
```

**GUI Integration:**
- Press `Cmd/Ctrl + Shift + P`
- Search for "MCP: Add Server"
- Windsurf includes MCP Store for one-click installation

### Key Insights

- **Codeium Integration**: Part of Codeium's Windsurf editor (Wave 3+)
- **GUI-First**: Supports command palette for MCP management
- **MCP Store**: Built-in marketplace for curated MCP servers
- **Streamable HTTP Support**: Also supports HTTP servers (not just stdio)
- **Released Feb 2025**: Very recent MCP integration (Wave 3)

---

## 8. Antigravity (Google's Agentic Platform)

### Configuration Location

**MCP Config:** Custom location accessed via MCP Store
**Format:** JSON (mcp_config.json)

### Structure

```json
{
  "mcpServers": {
    "mcp-ticketer": {
      "command": "/path/to/mcp-ticketer",
      "args": ["mcp"],
      "env": {...}
    }
  }
}
```

### Detection Strategy

```python
def detect_antigravity() -> DetectedPlatform | None:
    # Antigravity detection requires checking for:
    # 1. Antigravity process running
    # 2. MCP config location (platform-specific)

    # Platform-specific config locations (not yet documented):
    # macOS: TBD
    # Windows: TBD
    # Linux: TBD

    # For now, return None (not implemented)
    return None
```

### Installation Method

**GUI-Based:**
1. Open MCP Store in Antigravity
2. Select "Manage MCP Servers"
3. Click "View raw config"
4. Edit `mcp_config.json` directly

**JSON Structure:**
```python
config = {
    "command": "/absolute/path/to/mcp-ticketer",
    "args": ["mcp"],
    "env": {...}
}
```

### Key Insights

- **Released Nov 2025**: Very new (Gemini 3 Pro powered)
- **Native MCP Support**: Built-in MCP Store and protocol support
- **Agent-First**: Autonomous agents can use MCP tools
- **Model Optionality**: Supports Gemini 3 Pro, Claude Sonnet 4.5, GPT-OSS
- **Cross-Platform**: macOS, Windows, Linux support
- **Free Preview**: No cost for individuals
- **Config Location Unknown**: Exact config file location not yet documented

---

## Installation Method Detection

### Priority Order for Python MCP Servers

1. **`uv run` (Preferred)**
   - Fastest, Rust-powered package manager
   - Automatic dependency isolation
   - Command: `uv run mcp-ticketer mcp`
   - Detection: `shutil.which("uv")`

2. **`pipx` (Recommended)**
   - Isolated virtual environments
   - Global binary installation
   - Command: `mcp-ticketer mcp` (binary in PATH)
   - Detection: `shutil.which("mcp-ticketer")` + verify venv

3. **Direct Binary**
   - Installed via pip/pipx
   - Command available in PATH
   - Command: `mcp-ticketer mcp`
   - Detection: `shutil.which("mcp-ticketer")`

4. **Python Module (Fallback)**
   - Full path to Python + module invocation
   - Command: `/path/to/python -m mcp_ticketer.mcp.server`
   - Detection: Read shebang from binary or use sys.executable

### Detection Logic

```python
def detect_installation_method() -> tuple[str, list[str]]:
    """Detect optimal installation method for mcp-ticketer.

    Returns:
        Tuple of (command, args)
    """
    # Priority 1: Check for uv
    if shutil.which("uv"):
        return ("uv", ["run", "mcp-ticketer", "mcp"])

    # Priority 2: Check for mcp-ticketer in PATH
    if shutil.which("mcp-ticketer"):
        return ("mcp-ticketer", ["mcp"])

    # Priority 3: Check for Python with mcp_ticketer module
    python_path = get_mcp_ticketer_python()
    if validate_python_executable(python_path):
        return (python_path, ["-m", "mcp_ticketer.mcp.server"])

    # No valid installation found
    raise FileNotFoundError("mcp-ticketer not found in any location")
```

### Virtual Environment Context

```python
def get_mcp_ticketer_python(project_path: Path | None = None) -> str:
    """Get correct Python executable for mcp-ticketer.

    Priority:
    1. Project venv (.venv/bin/python)
    2. Current Python if in pipx venv
    3. Python from mcp-ticketer binary shebang
    4. Current Python (fallback)
    """
    # Check project venv
    if project_path:
        venv_python = project_path / ".venv" / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)

    # Check if in pipx venv
    if "/pipx/venvs/" in sys.executable:
        return sys.executable

    # Check mcp-ticketer binary shebang
    mcp_binary = shutil.which("mcp-ticketer")
    if mcp_binary:
        with open(mcp_binary) as f:
            shebang = f.readline().strip()
            if shebang.startswith("#!") and "python" in shebang:
                python_path = shebang[2:].strip()
                if os.path.exists(python_path):
                    return python_path

    # Fallback
    return sys.executable
```

---

## Configuration File Patterns

### Common Structure

All JSON-based configs share similar patterns:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable-path",
      "args": ["arg1", "arg2"],
      "env": {
        "VAR1": "value1",
        "VAR2": "value2"
      }
    }
  }
}
```

### Transport Protocol

**All tools use stdio transport:**
- Standard input/output streaming
- Content-Length framing (FastMCP SDK)
- JSON-RPC 2.0 messages

**Legacy (Deprecated):**
- Line-delimited JSON (incompatible with modern clients)
- Python module: `python -m mcp_ticketer.mcp.server`
- Causes connection failures with Claude Desktop/Code, Cursor, Windsurf

**Modern (Required):**
- Content-Length framing
- CLI command: `mcp-ticketer mcp`
- FastMCP SDK implementation

### Environment Variables

**Common Variables:**
```python
env_vars = {
    # Adapter selection
    "MCP_TICKETER_ADAPTER": "linear",  # or github, jira, aitrackdown

    # Linear
    "LINEAR_API_KEY": "***",
    "LINEAR_TEAM_ID": "***",
    "LINEAR_TEAM_KEY": "***",

    # GitHub
    "GITHUB_TOKEN": "***",
    "GITHUB_OWNER": "owner-name",
    "GITHUB_REPO": "repo-name",

    # JIRA
    "JIRA_API_TOKEN": "***",
    "JIRA_EMAIL": "user@example.com",
    "JIRA_URL": "https://company.atlassian.net",

    # Project context
    "PYTHONPATH": "/project/path"
}
```

---

## Command Patterns for mcp-ticketer

### Standard Command

```bash
mcp-ticketer mcp
```
- JSON-RPC stdio transport
- FastMCP SDK with Content-Length framing
- Loads config from `.mcp-ticketer/config.json`

### With Project Path

```bash
mcp-ticketer mcp --path /absolute/project/path
```
- Specifies project directory
- Loads project-specific config
- Required for project-level configurations

### With UV

```bash
uv run mcp-ticketer mcp
```
- Fastest execution (Rust-powered)
- Automatic dependency isolation
- Recommended for development

### Legacy (Deprecated)

```bash
python -m mcp_ticketer.mcp.server
```
- Line-delimited JSON (incompatible)
- Causes connection failures
- Should auto-migrate to FastMCP

---

## Error Handling Patterns

### Invalid JSON Config

```python
def load_config(config_path: Path) -> dict:
    if config_path.exists():
        try:
            with config_path.open() as f:
                content = f.read().strip()
                if not content:
                    return {"mcpServers": {}}
                return json.loads(content)
        except json.JSONDecodeError as e:
            console.print(f"[yellow]⚠ Invalid JSON: {e}[/yellow]")
            console.print("[yellow]Creating new configuration...[/yellow]")

    return {"mcpServers": {}}
```

### Legacy Server Detection

```python
def detect_legacy_server(config: dict) -> bool:
    """Detect line-delimited JSON server (incompatible)."""
    for server_name, server_config in config.get("mcpServers", {}).items():
        args = server_config.get("args", [])
        # Check for: ["-m", "mcp_ticketer.mcp.server", ...]
        if len(args) >= 2 and args[0] == "-m" and "mcp_ticketer.mcp.server" in args[1]:
            return True
    return False
```

### Auto-Migration

```python
def auto_migrate_legacy_server(config_path: Path, force: bool = True):
    """Auto-migrate legacy line-delimited JSON server to FastMCP."""
    if detect_legacy_server(config):
        console.print("[yellow]⚠ LEGACY CONFIGURATION DETECTED[/yellow]")
        console.print("[cyan]✨ Automatically migrating to FastMCP...[/cyan]")
        force = True  # Enable force mode for migration
        # ... proceed with new config creation
```

---

## Best Practices

### 1. Path Handling

**Always use absolute paths:**
```python
# ✅ Good
config = {
    "command": "/Users/user/.local/bin/mcp-ticketer",
    "args": ["mcp", "--path", "/Users/user/projects/my-app"]
}

# ❌ Bad (relative paths fail)
config = {
    "command": "mcp-ticketer",
    "args": ["mcp", "--path", "./my-app"]
}
```

### 2. Environment Detection

**Multi-layered validation:**
```python
def is_platform_installed(platform_name: str) -> bool:
    # Layer 1: Check config file exists
    platform = detect_platform(platform_name)
    if not platform:
        return False

    # Layer 2: Validate config is readable
    if not platform.config_path.exists():
        return False

    # Layer 3: Validate JSON/TOML is parseable
    try:
        load_platform_config(platform.config_path)
    except Exception:
        return False

    # Layer 4: Check CLI availability (if applicable)
    if platform.executable_path:
        if not shutil.which(platform.executable_path):
            return False

    return True
```

### 3. Credential Security

**Never log sensitive values:**
```python
# ✅ Good: Mask credentials
masked_cmd = []
for arg in cmd:
    if "API_KEY" in arg or "TOKEN" in arg:
        key, _ = arg.split("=", 1)
        masked_cmd.append(f"{key}=***")
    else:
        masked_cmd.append(arg)

console.print(f"Executing: {' '.join(masked_cmd)}")

# ❌ Bad: Exposes secrets
console.print(f"Executing: {' '.join(cmd)}")
```

### 4. Graceful Degradation

**Fallback chains:**
```python
def install_mcp_server():
    # Try native CLI first
    if is_native_cli_available():
        try:
            return install_via_native_cli()
        except Exception as e:
            console.print(f"[yellow]Native CLI failed: {e}[/yellow]")
            console.print("[yellow]Falling back to JSON mode...[/yellow]")

    # Fallback to JSON manipulation
    return install_via_json()
```

### 5. User Communication

**Clear status messages:**
```python
console.print("[cyan]🔍 Finding mcp-ticketer Python executable...[/cyan]")
console.print(f"[green]✓[/green] Found: {python_path}")
console.print("[dim]Using project-specific venv[/dim]")

console.print("\n[bold cyan]Next Steps:[/bold cyan]")
console.print("1. Restart Claude Code")
console.print("2. Open this project in Claude Code")
console.print("3. mcp-ticketer tools will be available in the MCP menu")
```

---

## Summary Table

| Tool | Config Location | Format | Scope | CLI | Detection Method |
|------|----------------|--------|-------|-----|------------------|
| **Claude Code** | `~/.config/claude/mcp.json` | JSON | Project | `claude` | File + CLI check |
| **Claude Desktop** | Platform-specific | JSON | Global | `claude` | File + platform check |
| **Cursor** | `~/.cursor/mcp.json` | JSON | Project | None | File only |
| **Auggie** | `~/.augment/settings.json` | JSON | Global | `auggie` | CLI + file |
| **Codex** | `~/.codex/config.toml` | TOML | Global | `codex` | CLI + file |
| **Gemini** | `.gemini/settings.json` or `~/.gemini/` | JSON | Both | `gemini` | CLI + file |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | JSON | Project | GUI | File only |
| **Antigravity** | Via MCP Store | JSON | Both | GUI | TBD |

---

## Universal Installer Library Design

### Core Components

```python
class MCPInstaller:
    """Universal MCP installer for mcp-ticketer."""

    def detect_environment(self) -> list[DetectedPlatform]:
        """Detect all installed AI coding tools."""
        detector = PlatformDetector()
        return detector.detect_all()

    def determine_installation_method(self) -> InstallationMethod:
        """Determine optimal installation method (uv/pipx/binary)."""
        if shutil.which("uv"):
            return InstallationMethod.UV_RUN
        elif shutil.which("mcp-ticketer"):
            return InstallationMethod.DIRECT_BINARY
        else:
            return InstallationMethod.PYTHON_MODULE

    def inspect_installation(self, platform: str) -> InstalledConfig:
        """Inspect existing MCP server configuration."""
        platform_info = get_platform_by_name(platform)
        config = load_platform_config(platform_info.config_path)
        return InstalledConfig.from_config(config)

    def install(self, platform: str, **kwargs) -> InstallResult:
        """Install mcp-ticketer for specified platform."""
        platform_info = get_platform_by_name(platform)

        if platform_info.supports_native_cli:
            return self._install_via_cli(platform_info, **kwargs)
        else:
            return self._install_via_config(platform_info, **kwargs)

    def fix_installation(self, platform: str) -> FixResult:
        """Fix/update existing installation."""
        # Detect legacy servers
        # Auto-migrate to FastMCP
        # Update credentials
        # Validate configuration
        ...
```

### Platform Abstraction

```python
@dataclass
class PlatformConfig:
    """Platform-specific configuration handler."""

    name: str
    display_name: str
    config_location: Path
    config_format: ConfigFormat  # JSON, TOML
    scope: ConfigScope  # PROJECT, GLOBAL, BOTH
    native_cli: bool
    cli_command: str | None

    def load_config(self) -> dict:
        """Load configuration file."""
        ...

    def save_config(self, config: dict) -> None:
        """Save configuration file."""
        ...

    def create_server_config(self, **kwargs) -> dict:
        """Create platform-specific server configuration."""
        ...

    def validate_config(self, config: dict) -> ValidationResult:
        """Validate configuration structure."""
        ...
```

### Installation Method Strategy

```python
class InstallationStrategy(ABC):
    """Abstract installation strategy."""

    @abstractmethod
    def install(self, platform: PlatformConfig, **kwargs) -> InstallResult:
        """Install MCP server."""
        pass

    @abstractmethod
    def remove(self, platform: PlatformConfig) -> RemoveResult:
        """Remove MCP server."""
        pass

    @abstractmethod
    def update(self, platform: PlatformConfig, **kwargs) -> UpdateResult:
        """Update MCP server configuration."""
        pass

class NativeCLIStrategy(InstallationStrategy):
    """Installation via native CLI (Claude, Antigravity)."""
    ...

class JSONConfigStrategy(InstallationStrategy):
    """Installation via JSON manipulation (Cursor, Windsurf, Auggie)."""
    ...

class TOMLConfigStrategy(InstallationStrategy):
    """Installation via TOML manipulation (Codex)."""
    ...
```

---

## Conclusion

This comprehensive research provides the foundation for building a universal MCP installer library that can:

1. **Detect** all 8 major AI coding tools with high accuracy
2. **Determine** optimal installation methods based on environment
3. **Inspect** existing installations and identify issues
4. **Install** mcp-ticketer across all platforms with proper configuration
5. **Fix** legacy installations by auto-migrating to FastMCP
6. **Update** configurations when credentials or settings change

### Next Steps

1. Implement `PlatformDetector` class with all 8 platform detection methods
2. Create `InstallationStrategy` implementations for each platform type
3. Build `MCPInstaller` orchestration layer
4. Add comprehensive error handling and user communication
5. Implement auto-migration for legacy line-delimited JSON servers
6. Add validation and testing for each platform
7. Create CLI interface for universal installer

### Key Challenges

1. **Antigravity Config Location**: Exact file path not yet documented (requires testing)
2. **Platform Version Compatibility**: Different versions may have different config locations
3. **Credential Management**: Securely handling API keys and tokens across platforms
4. **Auto-Migration Safety**: Ensuring legacy server migration doesn't break existing setups
5. **Cross-Platform Testing**: Validating on macOS, Linux, Windows for all tools

---

**Research Status:** ✅ Complete
**Coverage:** 8/8 platforms documented (Antigravity config location TBD)
**Confidence:** High (based on production codebase analysis + web research)
**Recommended Action:** Proceed with universal installer library implementation
