# CLI Documentation

The CLI is the core interface of **ai_term**. It interacts with the users via text or voice, manages the chat history, and orchestrates calls to LLM, STT, and TTS services.

## Overview

The CLI is built using [Textual](https://textual.textualize.io/), a TUI framework for Python.

### Entry Point

The application uses [Typer](https://typer.tiangolo.com/) for its CLI interface. The main entry point is `src/ai_term/cli/main.py`.

```bash
# Start the TUI application (default)
ai-term

# Start background services
ai-term start

# Check service status
ai-term status
```

## Commands

### `ai-term` (default)
Launches the full-screen terminal user interface for chatting with the AI.

### `ai-term start`
Starts the Docker-based STT and TTS services.
- `--build`: Force rebuild of Docker images.
- `--detach` / `-d`: Run in detached mode (default).

### `ai-term status`
Displays a formatted table showing the current state and port mappings of the backend services.

## Structure

- **`src/ai_term/cli/ui`**: Contains all UI components (Screens, Widgets, Styles).
- **`src/ai_term/cli/core`**: Contains business logic (Agent, Audio Client, MCP Manager).
- **`src/ai_term/cli/db`**: Database models and engine using `SQLAlchemy` and `aiosqlite`.
- **`src/ai_term/cli/config.py`**: Configuration management.

## API Reference

::: ai_term.cli.main
