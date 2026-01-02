"""Tests for ElevenLabs TTS provider."""

from unittest.mock import MagicMock, patch

import pytest


class TestElevenLabsTTSProvider:
    """Test cases for ElevenLabsTTSProvider."""

    def test_name_property(self):
        """Verify provider name is 'elevenlabs'."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        provider = ElevenLabsTTSProvider(api_key="test-key")

        assert provider.name == "elevenlabs"

    def test_init_requires_api_key(self):
        """Verify ValueError without API key."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        with pytest.raises(ValueError, match="API key"):
            ElevenLabsTTSProvider(api_key="")

        with pytest.raises(ValueError, match="API key"):
            ElevenLabsTTSProvider(api_key=None)

    def test_init_uses_default_voice_id(self):
        """Verify default voice ID is used when not specified."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        provider = ElevenLabsTTSProvider(api_key="test-key")

        assert provider._voice_id == ElevenLabsTTSProvider.DEFAULT_VOICE_ID

    def test_init_uses_custom_voice_id(self):
        """Verify custom voice ID is used when specified."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        provider = ElevenLabsTTSProvider(
            api_key="test-key", voice_id="custom-voice-123"
        )

        assert provider._voice_id == "custom-voice-123"

    def test_init_uses_default_model_id(self):
        """Verify default model ID is used when not specified."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        provider = ElevenLabsTTSProvider(api_key="test-key")

        assert provider._model_id == "eleven_flash_v2_5"

    def test_init_uses_custom_model_id(self):
        """Verify custom model ID is used when specified."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        provider = ElevenLabsTTSProvider(api_key="test-key", model_id="eleven_turbo_v2")

        assert provider._model_id == "eleven_turbo_v2"

    def test_generate_makes_api_call(self):
        """Verify correct API call is made."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        mock_response = MagicMock()
        mock_response.content = b"fake audio data"

        with patch(
            "ai_term.tts.providers.elevenlabs.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            provider = ElevenLabsTTSProvider(api_key="test-api-key")
            result = provider.generate("Hello world")

            assert result == b"fake audio data"
            mock_client.post.assert_called_once()

            # Check URL contains voice ID
            call_args = mock_client.post.call_args
            url = call_args[0][0]
            assert provider._voice_id in url

    def test_generate_sends_correct_headers(self):
        """Verify correct headers are sent."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        mock_response = MagicMock()
        mock_response.content = b"audio"

        with patch(
            "ai_term.tts.providers.elevenlabs.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            provider = ElevenLabsTTSProvider(api_key="my-api-key")
            provider.generate("Test")

            call_kwargs = mock_client.post.call_args.kwargs
            headers = call_kwargs["headers"]

            assert headers["xi-api-key"] == "my-api-key"
            assert headers["Accept"] == "audio/mpeg"
            assert headers["Content-Type"] == "application/json"

    def test_generate_sends_correct_payload(self):
        """Verify correct payload is sent."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        mock_response = MagicMock()
        mock_response.content = b"audio"

        with patch(
            "ai_term.tts.providers.elevenlabs.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            provider = ElevenLabsTTSProvider(api_key="test-key")
            provider.generate("Hello world")

            call_kwargs = mock_client.post.call_args.kwargs
            payload = call_kwargs["json"]

            assert payload["text"] == "Hello world"
            assert payload["model_id"] == "eleven_flash_v2_5"
            assert "voice_settings" in payload
            assert "stability" in payload["voice_settings"]

    def test_generate_with_previous_text(self):
        """Verify previous_text is included in payload."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        mock_response = MagicMock()
        mock_response.content = b"audio"

        with patch(
            "ai_term.tts.providers.elevenlabs.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            provider = ElevenLabsTTSProvider(api_key="test-key")
            provider.generate("Hello", previous_text="Previous context")

            call_kwargs = mock_client.post.call_args.kwargs
            payload = call_kwargs["json"]

            assert payload["previous_text"] == "Previous context"

    def test_generate_without_previous_text(self):
        """Verify previous_text is not included when not specified."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        mock_response = MagicMock()
        mock_response.content = b"audio"

        with patch(
            "ai_term.tts.providers.elevenlabs.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            provider = ElevenLabsTTSProvider(api_key="test-key")
            provider.generate("Hello")

            call_kwargs = mock_client.post.call_args.kwargs
            payload = call_kwargs["json"]

            assert "previous_text" not in payload

    def test_voice_id_override(self):
        """Verify voice_id can be overridden in generate call."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        mock_response = MagicMock()
        mock_response.content = b"audio"

        with patch(
            "ai_term.tts.providers.elevenlabs.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            provider = ElevenLabsTTSProvider(
                api_key="test-key", voice_id="default-voice"
            )
            provider.generate("Hello", voice_id="override-voice")

            call_args = mock_client.post.call_args
            url = call_args[0][0]

            assert "override-voice" in url
            assert "default-voice" not in url

    def test_model_id_override(self):
        """Verify model_id can be overridden in generate call."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        mock_response = MagicMock()
        mock_response.content = b"audio"

        with patch(
            "ai_term.tts.providers.elevenlabs.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            provider = ElevenLabsTTSProvider(
                api_key="test-key", model_id="default-model"
            )
            provider.generate("Hello", model_id="override-model")

            call_kwargs = mock_client.post.call_args.kwargs
            payload = call_kwargs["json"]

            assert payload["model_id"] == "override-model"

    def test_provider_is_tts_provider_subclass(self):
        """Verify ElevenLabsTTSProvider is a TTSProvider subclass."""
        from ai_term.tts.interface import TTSProvider
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        assert issubclass(ElevenLabsTTSProvider, TTSProvider)

    def test_voice_settings_values(self):
        """Verify voice settings have expected values."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        mock_response = MagicMock()
        mock_response.content = b"audio"

        with patch(
            "ai_term.tts.providers.elevenlabs.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            provider = ElevenLabsTTSProvider(api_key="test-key")
            provider.generate("Hello")

            call_kwargs = mock_client.post.call_args.kwargs
            voice_settings = call_kwargs["json"]["voice_settings"]

            assert voice_settings["stability"] == 0.5
            assert voice_settings["similarity_boost"] == 0.65
            assert voice_settings["speed"] == 1.13

    def test_api_base_url(self):
        """Verify correct API base URL is used."""
        from ai_term.tts.providers.elevenlabs import ElevenLabsTTSProvider

        mock_response = MagicMock()
        mock_response.content = b"audio"

        with patch(
            "ai_term.tts.providers.elevenlabs.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client

            provider = ElevenLabsTTSProvider(api_key="test-key")
            provider.generate("Hello")

            call_args = mock_client.post.call_args
            url = call_args[0][0]

            assert url.startswith(ElevenLabsTTSProvider.API_BASE_URL)
