"""Tests for Coqui TTS provider.

Note: These tests mock TTS dependencies to avoid loading heavy ML models during testing.
"""

import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Mock TTS module before importing coqui provider
mock_tts_module = MagicMock()
sys.modules["TTS"] = mock_tts_module
sys.modules["TTS.api"] = mock_tts_module


class TestCoquiTTSProvider:
    """Test cases for CoquiTTSProvider."""

    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock model manager."""
        manager = MagicMock()
        mock_model = MagicMock()
        # tts() returns a list of floats (audio samples)
        mock_model.tts.return_value = [0.0] * 22050  # 1 second of silence
        mock_model.synthesizer.output_sample_rate = 22050
        manager.get_model.return_value = mock_model
        return manager

    def test_name_property(self, mock_model_manager):
        """Verify provider name is 'coqui'."""
        with patch("ai_term.tts.providers.coqui._model_manager", mock_model_manager):
            from ai_term.tts.providers.coqui import CoquiTTSProvider

            provider = CoquiTTSProvider()
            provider._model_manager = mock_model_manager

            assert provider.name == "coqui"

    def test_generate_returns_bytes(self, mock_model_manager):
        """Verify generate returns bytes."""
        with patch("ai_term.tts.providers.coqui._model_manager", mock_model_manager):
            from ai_term.tts.providers.coqui import CoquiTTSProvider

            provider = CoquiTTSProvider()
            provider._model_manager = mock_model_manager

            result = provider.generate("Hello world")

            assert isinstance(result, bytes)
            assert len(result) > 0

    def test_generate_returns_wav_format(self, mock_model_manager):
        """Verify output is valid WAV format."""
        # Create more realistic audio data
        mock_model = mock_model_manager.get_model()
        mock_model.tts.return_value = np.sin(np.linspace(0, 100, 22050)).tolist()

        with patch("ai_term.tts.providers.coqui._model_manager", mock_model_manager):
            from ai_term.tts.providers.coqui import CoquiTTSProvider

            provider = CoquiTTSProvider()
            provider._model_manager = mock_model_manager

            result = provider.generate("Hello world")

            # Should start with RIFF header
            assert result[:4] == b"RIFF"

    def test_generate_uses_model_manager(self, mock_model_manager):
        """Verify model manager get_model is called."""
        with patch("ai_term.tts.providers.coqui._model_manager", mock_model_manager):
            from ai_term.tts.providers.coqui import CoquiTTSProvider

            provider = CoquiTTSProvider()
            provider._model_manager = mock_model_manager

            provider.generate("Test text")

            mock_model_manager.get_model.assert_called()

    def test_generate_calls_model_tts(self, mock_model_manager):
        """Verify model.tts is called with text."""
        mock_model = mock_model_manager.get_model()

        with patch("ai_term.tts.providers.coqui._model_manager", mock_model_manager):
            from ai_term.tts.providers.coqui import CoquiTTSProvider

            provider = CoquiTTSProvider()
            provider._model_manager = mock_model_manager

            provider.generate("Hello world")

            mock_model.tts.assert_called_once_with("Hello world")

    def test_generate_handles_missing_sample_rate_attribute(self):
        """Verify fallback sample rate when synthesizer attribute is missing."""
        mock_manager = MagicMock()
        mock_model = MagicMock()
        mock_model.tts.return_value = [0.0] * 1000
        # Make synthesizer access raise AttributeError
        type(mock_model).synthesizer = property(
            lambda self: (_ for _ in ()).throw(AttributeError())
        )
        mock_manager.get_model.return_value = mock_model

        with patch("ai_term.tts.providers.coqui._model_manager", mock_manager):
            from ai_term.tts.providers.coqui import CoquiTTSProvider

            provider = CoquiTTSProvider()
            provider._model_manager = mock_manager

            result = provider.generate("Test")

            # Should still work with fallback rate
            assert isinstance(result, bytes)
            assert len(result) > 0

    def test_generate_ignores_kwargs(self, mock_model_manager):
        """Verify extra kwargs are ignored."""
        mock_model = mock_model_manager.get_model()

        with patch("ai_term.tts.providers.coqui._model_manager", mock_model_manager):
            from ai_term.tts.providers.coqui import CoquiTTSProvider

            provider = CoquiTTSProvider()
            provider._model_manager = mock_model_manager

            # Should not raise an error
            provider.generate("Hello", voice_id="some-voice", extra_param="ignored")

            # tts should still be called with just the text
            mock_model.tts.assert_called_once_with("Hello")

    def test_provider_is_tts_provider_subclass(self):
        """Verify CoquiTTSProvider is a TTSProvider subclass."""
        from ai_term.tts.interface import TTSProvider

        with patch("ai_term.tts.providers.coqui._model_manager"):
            from ai_term.tts.providers.coqui import CoquiTTSProvider

            assert issubclass(CoquiTTSProvider, TTSProvider)
