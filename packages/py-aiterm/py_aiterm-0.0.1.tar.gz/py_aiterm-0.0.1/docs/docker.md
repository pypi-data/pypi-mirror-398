# Docker Guide

ai_term uses Docker to run the STT (Speech-to-Text) and TTS (Text-to-Speech) backend services.

## Pre-built Images

Official Docker images are available on GitHub Container Registry:

| Service | Image |
|---------|-------|
| STT | `ghcr.io/vsaravind01/ai-term-stt:latest` |
| TTS | `ghcr.io/vsaravind01/ai-term-tts:latest` |

## Quick Start

The easiest way to start the services is using the built-in CLI command:

```bash
ai-term start
```

This pulls the pre-built images and starts both services in the background.

To check the status of running services:

```bash
ai-term status
```

## Port Configuration

| Service | Container Port | Host Port |
|---------|----------------|-----------|
| STT     | 8001           | 8901      |
| TTS     | 8002           | 8902      |

## Manual Docker Compose

If you prefer to run Docker Compose directly:

```bash
docker compose up -d
```

To force rebuild of images:

```bash
ai-term start --build
```

## Volumes and Caching

To speed up startup, the services mount local cache directories:

- **Whisper Models**: `~/.cache/whisper` -> `/root/.cache/whisper`
- **TTS Models**: `~/.local/share/tts` -> `/root/.local/share/tts`

## GPU Support

If you have an NVIDIA GPU, you can enable hardware acceleration by modifying the `Dockerfile` and `docker-compose.yml` to use CUDA-enabled base images.

> [!NOTE]
> The default setup uses CPU for maximum compatibility.
