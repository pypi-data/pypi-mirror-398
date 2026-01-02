# Installation & Setup

## Prerequisites

- Python 3.10 or higher
- `uv` (recommended) or `pip`
- `ffmpeg` (for audio processing)

## Installation

### Method 1: Docker (Recommended)

The easiest way to run ai_term is using the built-in CLI commands.

1. **Install ai_term:**
   ```bash
   pip install py-aiterm
   ```

2. **Start the services:**
   ```bash
   ai-term start
   ```

   This pulls pre-built Docker images and starts the STT/TTS services.

3. **Verify services are running:**
   ```bash
   ai-term status
   ```

   For more Docker configurations, see the [Docker Guide](docker.md).

### Method 2: Local Installation

If you prefer to run locally without Docker:

1. **Install dependencies:**
   Using `uv` (recommended):
   ```bash
   uv sync
   ```
   Or `pip`:
   ```bash
   pip install -e .
   ```

## Running the Application

If you are not using Docker, you need to run the services manually.

### 1. Start Support Services
Open two separate terminal windows/tabs:

**Terminal 1 (STT Service):**
```bash
uv run uvicorn ai_term.stt.main:app --port 8901
```

**Terminal 2 (TTS Service):**
```bash
uv run uvicorn ai_term.tts.main:app --port 8902
```

### 2. Start the CLI
In your main terminal:

```bash
uv run ai-term
# OR
uv run python -m ai_term.cli.main
```

## Configuration

You can configure providers and API keys directly in the application Settings screen (press `Ctrl+S` or click Settings).

For more details, see [Configuration Guide](cli/configuration.md).
