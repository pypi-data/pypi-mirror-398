"""Tests for TTS FastAPI service.

Note: These tests mock TTS dependencies to avoid loading heavy ML models during testing.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock TTS module before importing
mock_tts_module = MagicMock()
sys.modules["TTS"] = mock_tts_module
sys.modules["TTS.api"] = mock_tts_module


class TestTTSHealthEndpoint:
    """Test cases for TTS health endpoint."""

    def test_health_endpoint_returns_ok(self):
        """Verify /health returns ok status."""
        with patch("ai_term.tts.providers.coqui._model_manager"):
            from fastapi.testclient import TestClient

            from ai_term.tts.main import app

            client = TestClient(app)
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["default_provider"] == "coqui"


class TestCreateProvider:
    """Test cases for create_provider function."""

    def test_create_provider_coqui(self):
        """Verify Coqui provider creation uses default provider."""
        with patch("ai_term.tts.providers.coqui._model_manager"):
            from ai_term.tts.main import (
                ProviderConfigRequest,
                create_provider,
            )

            config = ProviderConfigRequest(provider="coqui")

            mock_provider = MagicMock()
            with patch(
                "ai_term.tts.main.get_default_provider", return_value=mock_provider
            ):
                provider = create_provider(config)

                assert provider is mock_provider

    def test_create_provider_elevenlabs(self):
        """Verify ElevenLabs provider creation."""
        with patch("ai_term.tts.providers.coqui._model_manager"):
            from ai_term.tts.main import ProviderConfigRequest, create_provider

            config = ProviderConfigRequest(
                provider="elevenlabs", api_key="test-api-key", voice_id="voice-123"
            )

            provider = create_provider(config)

            assert provider.name == "elevenlabs"

    def test_create_provider_elevenlabs_no_key(self):
        """Verify error when ElevenLabs API key is missing."""
        with patch("ai_term.tts.providers.coqui._model_manager"):
            from ai_term.tts.main import ProviderConfigRequest, create_provider

            config = ProviderConfigRequest(provider="elevenlabs")  # No api_key

            with pytest.raises(ValueError, match="API key"):
                create_provider(config)

    def test_create_provider_unknown(self):
        """Verify error for unknown provider."""
        with patch("ai_term.tts.providers.coqui._model_manager"):
            from ai_term.tts.main import ProviderConfigRequest, create_provider

            config = ProviderConfigRequest(provider="unknown-provider")

            with pytest.raises(ValueError, match="Unknown provider"):
                create_provider(config)


class TestGenerateSpeechEndpoint:
    """Test cases for /generate endpoint."""

    def test_generate_empty_text(self):
        """Verify 400 error for empty text."""
        with patch("ai_term.tts.providers.coqui._model_manager"):
            from fastapi.testclient import TestClient

            from ai_term.tts.main import app

            client = TestClient(app)
            response = client.post("/generate", json={"text": ""})

            assert response.status_code == 400
            assert "empty" in response.json()["detail"].lower()

    def test_generate_whitespace_text(self):
        """Verify 400 error for whitespace-only text."""
        with patch("ai_term.tts.providers.coqui._model_manager"):
            from fastapi.testclient import TestClient

            from ai_term.tts.main import app

            client = TestClient(app)
            response = client.post("/generate", json={"text": "   "})

            assert response.status_code == 400

    def test_generate_uses_default_provider(self):
        """Verify default provider is used when no config specified."""
        mock_provider = MagicMock()
        mock_provider.name = "coqui"
        mock_provider.generate.return_value = b"fake audio data"

        with patch("ai_term.tts.providers.coqui._model_manager"):
            with patch(
                "ai_term.tts.main.get_default_provider", return_value=mock_provider
            ):
                from fastapi.testclient import TestClient

                from ai_term.tts.main import app

                client = TestClient(app)
                response = client.post("/generate", json={"text": "Hello world"})

                assert response.status_code == 200
                mock_provider.generate.assert_called_once()

    def test_generate_uses_specified_provider(self):
        """Verify specified provider is used."""
        mock_provider = MagicMock()
        mock_provider.name = "elevenlabs"
        mock_provider.generate.return_value = b"fake audio data"

        with patch("ai_term.tts.providers.coqui._model_manager"):
            with patch("ai_term.tts.main.create_provider", return_value=mock_provider):
                from fastapi.testclient import TestClient

                from ai_term.tts.main import app

                client = TestClient(app)
                response = client.post(
                    "/generate",
                    json={
                        "text": "Hello world",
                        "provider_config": {
                            "provider": "elevenlabs",
                            "api_key": "test-key",
                        },
                    },
                )

                assert response.status_code == 200
                mock_provider.generate.assert_called_once()

    def test_generate_returns_correct_media_type_coqui(self):
        """Verify WAV media type for Coqui provider."""
        mock_provider = MagicMock()
        mock_provider.name = "coqui"
        mock_provider.generate.return_value = b"fake wav data"

        with patch("ai_term.tts.providers.coqui._model_manager"):
            with patch(
                "ai_term.tts.main.get_default_provider", return_value=mock_provider
            ):
                from fastapi.testclient import TestClient

                from ai_term.tts.main import app

                client = TestClient(app)
                response = client.post("/generate", json={"text": "Hello"})

                assert response.headers["content-type"] == "audio/wav"

    def test_generate_returns_correct_media_type_elevenlabs(self):
        """Verify MP3 media type for ElevenLabs provider."""
        mock_provider = MagicMock()
        mock_provider.name = "elevenlabs"
        mock_provider.generate.return_value = b"fake mp3 data"

        with patch("ai_term.tts.providers.coqui._model_manager"):
            with patch("ai_term.tts.main.create_provider", return_value=mock_provider):
                from fastapi.testclient import TestClient

                from ai_term.tts.main import app

                client = TestClient(app)
                response = client.post(
                    "/generate",
                    json={
                        "text": "Hello",
                        "provider_config": {
                            "provider": "elevenlabs",
                            "api_key": "test-key",
                        },
                    },
                )

                assert response.headers["content-type"] == "audio/mpeg"

    def test_generate_passes_previous_text(self):
        """Verify previous_text is passed to provider."""
        mock_provider = MagicMock()
        mock_provider.name = "coqui"
        mock_provider.generate.return_value = b"fake audio"

        with patch("ai_term.tts.providers.coqui._model_manager"):
            with patch(
                "ai_term.tts.main.get_default_provider", return_value=mock_provider
            ):
                from fastapi.testclient import TestClient

                from ai_term.tts.main import app

                client = TestClient(app)
                response = client.post(
                    "/generate",
                    json={"text": "Hello", "previous_text": "Previous context"},
                )

                assert response.status_code == 200
                call_kwargs = mock_provider.generate.call_args.kwargs
                assert call_kwargs.get("previous_text") == "Previous context"

    def test_generate_handles_provider_error(self):
        """Verify proper error handling for provider errors."""
        mock_provider = MagicMock()
        mock_provider.name = "coqui"
        mock_provider.generate.side_effect = Exception("Provider error")

        with patch("ai_term.tts.providers.coqui._model_manager"):
            with patch(
                "ai_term.tts.main.get_default_provider", return_value=mock_provider
            ):
                from fastapi.testclient import TestClient

                from ai_term.tts.main import app

                client = TestClient(app)
                response = client.post("/generate", json={"text": "Hello"})

                assert response.status_code == 500
                assert "Provider error" in response.json()["detail"]


class TestProviderConfigRequest:
    """Test cases for ProviderConfigRequest model."""

    def test_default_values(self):
        """Verify default values."""
        with patch("ai_term.tts.providers.coqui._model_manager"):
            from ai_term.tts.main import ProviderConfigRequest

            config = ProviderConfigRequest()

            assert config.provider == "coqui"
            assert config.api_key is None
            assert config.voice_id is None
            assert config.model_id is None

    def test_custom_values(self):
        """Verify custom values can be set."""
        with patch("ai_term.tts.providers.coqui._model_manager"):
            from ai_term.tts.main import ProviderConfigRequest

            config = ProviderConfigRequest(
                provider="elevenlabs",
                api_key="test-key",
                voice_id="voice-123",
                model_id="eleven_v2",
            )

            assert config.provider == "elevenlabs"
            assert config.api_key == "test-key"
            assert config.voice_id == "voice-123"
            assert config.model_id == "eleven_v2"


class TestTTSRequest:
    """Test cases for TTSRequest model."""

    def test_required_text(self):
        """Verify text is required."""
        with patch("ai_term.tts.providers.coqui._model_manager"):
            from ai_term.tts.main import TTSRequest

            request = TTSRequest(text="Hello world")

            assert request.text == "Hello world"

    def test_optional_fields(self):
        """Verify optional fields have defaults."""
        with patch("ai_term.tts.providers.coqui._model_manager"):
            from ai_term.tts.main import TTSRequest

            request = TTSRequest(text="Hello")

            assert request.previous_text is None
            assert request.speaker_id == ""
            assert request.language_id == ""
            assert request.provider_config is None
