"""ElevenLabs TTS Provider implementation."""

import httpx

from ai_term.tts.interface import TTSProvider


class ElevenLabsTTSProvider(TTSProvider):
    """TTS Provider using ElevenLabs API."""

    # Default voice ID (Rachel - a popular default voice)
    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
    API_BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(
        self, api_key: str, voice_id: str | None = None, model_id: str | None = None
    ):
        """
        Initialize ElevenLabsTTSProvider.

        Args:
        Args:
            api_key: ElevenLabs API key.
            voice_id: Voice ID to use (optional, uses default if not provided).
            model_id: Model ID to use (optional, uses eleven_monolingual_v1 if not
                provided).
        """
        if not api_key:
            raise ValueError("ElevenLabs API key is required")

        self._api_key = api_key
        self._voice_id = voice_id or self.DEFAULT_VOICE_ID
        self._model_id = model_id or "eleven_flash_v2_5"

    @property
    def name(self) -> str:
        return "elevenlabs"

    def generate(self, text: str, **kwargs) -> bytes:
        """
        Generate speech using ElevenLabs API.

        Args:
            text: Text to synthesize.
            **kwargs: Additional options:
                - voice_id: Override voice ID for this request.
                - model_id: Override model ID for this request.

        Returns:
            Audio bytes in MP3 format (ElevenLabs default).
        """
        voice_id = kwargs.get("voice_id", self._voice_id)
        model_id = kwargs.get("model_id", self._model_id)

        url = f"{self.API_BASE_URL}/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self._api_key,
        }

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.65,
                "speed": 1.13,
            },
        }

        if kwargs.get("previous_text"):
            payload["previous_text"] = kwargs["previous_text"]

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.content
