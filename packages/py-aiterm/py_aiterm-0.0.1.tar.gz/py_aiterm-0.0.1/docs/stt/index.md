# Speech-to-Text Service

The STT Service is a standalone FastAPI application that handles audio transcription using OpenAI's Whisper model.

## Overview

The service listens on port `8001` by default. It accepts audio files via HTTP POST and returns the transcribed text.

### Endpoints

- **`POST /transcribe`**: Upload an audio file for transcription.
- **`GET /health`**: Health check endpoint.

## Implementation Details

The service uses `fastapi` for the web server and `openai-whisper` for the model. It handles audio processing using `ffmpeg` (via `subprocess`).

### Model Management

The `ModelManager` ensures the heavy Whisper model is loaded only once and reused.

::: ai_term.stt.main
