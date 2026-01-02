# Text-to-Speech Service

The TTS Service is a standalone FastAPI application that generates speech from text using various providers.

## Overview

The service listens on port `8002` by default. It supports a pluggable provider architecture.

### Supported Providers

- **Coqui TTS**: Local, high-quality TTS (Default).
- **ElevenLabs**: Cloud-based, ultra-realistic TTS.

## API Reference

### Data Models

::: ai_term.tts.main.TTSRequest
::: ai_term.tts.main.ProviderConfigRequest

### Endpoints

- **`POST /generate`**: Generate audio from text.
- **`GET /health`**: Health check.

### Implementation

::: ai_term.tts.main
    options:
      members:
        - generate_speech
        - get_default_provider
        - create_provider
