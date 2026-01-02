"""TTS FastAPI Service with Provider Adapter Pattern."""

import logging
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from ai_term.tts.interface import TTSProvider
from ai_term.tts.providers.coqui import CoquiTTSProvider
from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

app = FastAPI()

logger = logging.getLogger(__name__)

# Default provider (Coqui) for backward compatibility
_default_provider: TTSProvider | None = None


class ProviderConfigRequest(BaseModel):
    """Provider configuration passed from client."""

    provider: str = "coqui"  # "coqui" or "elevenlabs"
    api_key: str | None = None
    voice_id: str | None = None
    model_id: str | None = None


class TTSRequest(BaseModel):
    """TTS generation request."""

    text: str
    previous_text: str | None = None
    speaker_id: str = ""  # Optional, for multi-speaker models
    language_id: str = ""  # Optional
    provider_config: ProviderConfigRequest | None = None


def get_default_provider() -> TTSProvider:
    """Get or create the default (Coqui) provider."""
    global _default_provider
    if _default_provider is None:
        _default_provider = CoquiTTSProvider()
    return _default_provider


def create_provider(config: ProviderConfigRequest) -> TTSProvider:
    """Create a provider based on configuration."""
    if config.provider == "elevenlabs":
        if not config.api_key:
            raise ValueError("ElevenLabs requires an API key")
        return ElevenLabsTTSProvider(
            api_key=config.api_key,
            voice_id=config.voice_id,
            model_id=config.model_id,
        )
    elif config.provider == "coqui":
        return get_default_provider()
    else:
        raise ValueError(f"Unknown provider: {config.provider}")


@app.post("/generate")
def generate_speech(request: TTSRequest):
    """Generate speech from text using the specified provider."""
    text = request.text.strip()
    previous_text = request.previous_text.strip() if request.previous_text else ""
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    logger.debug(f"Generating speech for: {text}")

    try:
        # Determine which provider to use
        if request.provider_config:
            provider = create_provider(request.provider_config)
        else:
            provider = get_default_provider()

        logger.info(f"Using provider: {provider.name}")

        # Generate audio
        audio_bytes = provider.generate(text, previous_text=previous_text)

        # Determine media type based on provider
        media_type = "audio/mpeg" if provider.name == "elevenlabs" else "audio/wav"

        return Response(content=audio_bytes, media_type=media_type)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "default_provider": "coqui"}
