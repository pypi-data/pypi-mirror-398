"""Audio client for STT and TTS servers."""

from typing import Optional

import httpx

from ai_term.cli.config import get_app_config


class AudioClient:
    """Client for interacting with STT and TTS servers."""

    def __init__(self):
        config = get_app_config()
        self.stt_url = config.audio.stt_url
        self.tts_url = config.audio.tts_url

    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Send audio to STT server and get transcription.

        Args:
            audio_bytes: Raw audio data (WAV format).

        Returns:
            Transcribed text.
        """
        async with httpx.AsyncClient() as client:
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            response = await client.post(
                f"{self.stt_url}/transcribe", files=files, timeout=30.0
            )
            response.raise_for_status()
            return response.json().get("text", "")

    async def speak(self, ai_response: str, user_query: Optional[str] = None) -> bytes:
        """
        Send text to TTS server and get audio bytes.

        Args:
            ai_response: AI response text to synthesize.
            user_query: User query text to synthesize (optional).

        Returns:
            Audio bytes (WAV or MP3 format depending on provider).
        """
        config = get_app_config()
        tts_config = config.audio.tts

        # Build request payload
        payload: dict = {"text": ai_response, "previous_text": user_query}

        if tts_config:
            # Resolve the api_key from env var name to actual value
            from ai_term.cli.config import resolve_secret

            payload["provider_config"] = {
                "provider": tts_config.provider,
                "api_key": resolve_secret(tts_config.api_key),
                "voice_id": tts_config.voice_id,
                "model_id": tts_config.model_id,
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.tts_url}/generate", json=payload, timeout=60.0
            )
            response.raise_for_status()
            return response.content
