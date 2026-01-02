<div align="center">

![ai_term Banner](https://github.com/vsaravind01/ai-term/blob/master/docs/img/banner.png?raw=true)

**ai_term** is an open-source, voice-enabled terminal assistant that integrates LLMs (Large Language Models), Speech-to-Text (STT), and Text-to-Speech (TTS) into a powerful Command Line Interface (CLI) experience.

[![PyPI version](https://img.shields.io/pypi/v/py-aiterm.svg)](https://pypi.org/project/py-aiterm/)
[![Docs Deployment](https://github.com/vsaravind01/ai-term/actions/workflows/deploy_docs.yml/badge.svg)](https://github.com/vsaravind01/ai-term/actions/workflows/deploy_docs.yml)
[![Docker Images](https://github.com/vsaravind01/ai-term/actions/workflows/docker_images.yml/badge.svg)](https://github.com/vsaravind01/ai-term/actions/workflows/docker_images.yml)

</div>

## Features

- **🗣️ Voice Interaction**: Talk to your terminal and hear responses back.
- **🧠 LLM Integration**: Support for Local (Ollama) and Cloud (OpenAI, Anthropic) models.
- **🔌 MCP Support**: Model Context Protocol client for extensible tool use.
- **🖥️ TUI Interface**: Beautiful, responsive terminal UI built with [Textual](https://textual.textualize.io/).
- **⚙️ Dynamic Configuration**: Easy-to-use settings screen for managing providers and secrets.

## Prerequisites

- Python 3.10+
- `uv` (recommended) or `pip`
- `ffmpeg` (required for audio processing)

## Installation

### From PyPI (Recommended for users)
```bash
pip install py-aiterm
```

### From Source (For development)
1. **Clone the repository:**
   ```bash
   git clone https://github.com/vsaravind01/ai-term.git
   cd ai-term
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   # OR with pip
   pip install -e .
   ```

## Quick Start

The application runs as a distributed system with a main CLI and two support microservices.

### 1. Start Support Services

Run the following command to start the STT and TTS services in the background:

```bash
ai-term start
```

This pulls pre-built Docker images from GHCR and starts the services.

### 2. Check Status (Optional)
You can verify the services are running with:

```bash
ai-term status
```

### 3. Start the CLI
In your main terminal:

```bash
uv run ai-term
```

## Documentation

Full documentation is available in the `docs/` directory. To view it locally:

```bash
uv run mkdocs serve
```

- [**Setup Guide**](docs/setup.md)
- [**Docker Guide**](docs/docker.md)
- [**CLI Documentation**](docs/cli/index.md)
- [**API Reference**](docs/api.md)

## License

[MIT](LICENSE)