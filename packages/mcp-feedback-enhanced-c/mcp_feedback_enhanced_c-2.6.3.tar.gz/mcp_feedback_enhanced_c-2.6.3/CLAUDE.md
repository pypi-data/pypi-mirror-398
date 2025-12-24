# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Feedback Enhanced is an MCP (Model Context Protocol) server that provides interactive user feedback collection for AI-assisted development. It features dual interface support (Web UI and Desktop Application via Tauri) with intelligent environment detection (local, SSH Remote, WSL) and cross-platform compatibility.

## Development Commands

### Installation
```bash
uv sync              # Install dependencies
uv sync --dev        # Install with dev dependencies
```

### Testing
```bash
uv run pytest                    # Run all unit tests
uv run pytest -m "not slow"      # Run fast tests only
uv run pytest --cov=src/mcp_feedback_enhanced --cov-report=html  # With coverage

# Functional testing
uv run python -m mcp_feedback_enhanced test --web      # Test Web UI
uv run python -m mcp_feedback_enhanced test --desktop  # Test desktop app
```

### Code Quality
```bash
uv run ruff check .              # Lint
uv run ruff check . --fix        # Lint with auto-fix
uv run ruff format .             # Format
uv run mypy                      # Type check
make check                       # Run all checks (lint, format, type-check)
make quick-check                 # Quick check with auto-fix
```

### Desktop Application (Tauri)
```bash
make build-desktop               # Build debug version
make build-desktop-release       # Build release version
make clean-desktop               # Clean build artifacts
```

### Building & Publishing
```bash
uv build                         # Build package
uv run twine check dist/*        # Verify built package
```

## Architecture

The project uses a **four-layer architecture**:

1. **MCP Service Layer** (`src/mcp_feedback_enhanced/server.py`)
   - Implements MCP protocol with FastMCP
   - Core tool: `interactive_feedback` - collects user feedback with text, images, and commands
   - Environment detection (SSH, WSL, local)
   - i18n support (`i18n.py`)

2. **Web UI Management Layer** (`src/mcp_feedback_enhanced/web/main.py`)
   - `WebUIManager` - singleton managing web server and sessions
   - Single active session mode for performance
   - WebSocket connection management with tab persistence
   - Smart browser opening (detects existing tabs)

3. **Web Service Layer** (`src/mcp_feedback_enhanced/web/`)
   - FastAPI application with routes in `routes/main_routes.py`
   - Models in `models/` (FeedbackSession, FeedbackResult)
   - Utilities: port management, browser control, compression

4. **Frontend Layer** (`src/mcp_feedback_enhanced/web/static/`, `templates/`)
   - Modular JavaScript architecture
   - Features: prompt management, auto-submit, session tracking, audio notifications
   - Responsive design with i18n support

**Desktop Application** (`src-tauri/`):
- Tauri-based cross-platform desktop app
- Wraps the Web UI with native window management
- Python bindings in `src-tauri/python/`

## Key Patterns

- **Single Active Session**: Only one feedback session is active at a time, improving performance and UX
- **WebSocket Persistence**: Browser tabs stay connected across AI calls; new sessions send refresh notifications
- **Environment Detection**: `is_remote_environment()` and `is_wsl_environment()` in server.py detect execution context
- **Unified Debug Logging**: Use `debug_log()` functions from `debug.py` for consistent logging
- **Error Handling**: Use `ErrorHandler` from `utils/error_handler.py` for structured error management

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `MCP_DEBUG` | Enable debug logging | `false` |
| `MCP_WEB_HOST` | Web UI host binding | `127.0.0.1` |
| `MCP_WEB_PORT` | Web UI port | `8765` |
| `MCP_DESKTOP_MODE` | Enable desktop application mode | `false` |
| `MCP_LANGUAGE` | Force UI language (zh-TW/zh-CN/en) | auto-detect |

## Project Structure

```
src/mcp_feedback_enhanced/
├── server.py          # MCP server entry, core tools
├── __main__.py        # CLI entry point (test, version commands)
├── i18n.py            # Internationalization
├── debug.py           # Unified debug logging
├── web/
│   ├── main.py        # WebUIManager, session management
│   ├── routes/        # FastAPI routes
│   ├── models/        # Data models
│   ├── utils/         # Browser, network, port utilities
│   ├── static/        # Frontend JS/CSS
│   └── templates/     # Jinja2 HTML templates
├── utils/
│   ├── error_handler.py
│   ├── memory_monitor.py
│   └── resource_manager.py
└── desktop_app/       # Desktop mode launcher

src-tauri/             # Tauri desktop application (Rust + Python)
tests/                 # Unit and integration tests
```

## MCP Tool Interface

The primary MCP tool `interactive_feedback` accepts:
- `project_directory`: Project path for context
- `summary`: AI work summary (supports Markdown)
- `timeout`: Feedback timeout in seconds (default: 600)

Returns a list of `TextContent` and `ImageContent` objects representing user feedback.
