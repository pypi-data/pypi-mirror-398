"""Tests for STT FastAPI service.

Note: These tests mock heavy dependencies (whisper, torch) to avoid loading ML
models during testing.
"""

import io
import sys
import wave
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Mock heavy modules before importing STT
mock_whisper = MagicMock()
mock_torch = MagicMock()
sys.modules["whisper"] = mock_whisper
sys.modules["torch"] = mock_torch


class TestSTTHealthEndpoint:
    """Test cases for STT health endpoint."""

    def test_health_endpoint_returns_ok(self):
        """Verify /health returns ok status."""
        with patch("ai_term.stt.main.model_manager") as mock_manager:
            mock_manager.model = None

            from fastapi.testclient import TestClient

            from ai_term.stt.main import app

            client = TestClient(app)
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

    def test_health_shows_model_loaded_status(self):
        """Verify health shows whether model is loaded."""
        with patch("ai_term.stt.main.model_manager") as mock_manager:
            mock_manager.model = "some_model"  # Model is loaded

            from fastapi.testclient import TestClient

            from ai_term.stt.main import app

            client = TestClient(app)
            response = client.get("/health")

            data = response.json()
            assert data["model_loaded"] is True


class TestTranscribeEndpoint:
    """Test cases for /transcribe endpoint."""

    @pytest.fixture
    def sample_wav(self):
        """Generate a sample WAV file for testing."""
        buffer = io.BytesIO()
        sample_rate = 16000
        duration = 0.1

        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())

        buffer.seek(0)
        return buffer.getvalue()

    def test_transcribe_no_file(self):
        """Verify 422 error when no file provided."""
        with patch("ai_term.stt.main.model_manager"):
            from fastapi.testclient import TestClient

            from ai_term.stt.main import app

            client = TestClient(app)
            response = client.post("/transcribe")

            assert response.status_code == 422

    def test_transcribe_returns_text(self, sample_wav):
        """Verify transcription returns text."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Hello world"}

        with patch("ai_term.stt.main.model_manager") as mock_manager:
            mock_manager.get_model.return_value = mock_model

            with patch("ai_term.stt.main.load_audio_from_bytes") as mock_load:
                mock_load.return_value = np.zeros(16000, dtype=np.float32)

                from fastapi.testclient import TestClient

                from ai_term.stt.main import app

                client = TestClient(app)
                response = client.post(
                    "/transcribe",
                    files={"file": ("audio.wav", sample_wav, "audio/wav")},
                )

                assert response.status_code == 200
                assert response.json()["text"] == "Hello world"

    def test_transcribe_uses_model_manager(self, sample_wav):
        """Verify model manager is used to get model."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Test"}

        with patch("ai_term.stt.main.model_manager") as mock_manager:
            mock_manager.get_model.return_value = mock_model

            with patch("ai_term.stt.main.load_audio_from_bytes") as mock_load:
                mock_load.return_value = np.zeros(16000, dtype=np.float32)

                from fastapi.testclient import TestClient

                from ai_term.stt.main import app

                client = TestClient(app)
                client.post(
                    "/transcribe",
                    files={"file": ("audio.wav", sample_wav, "audio/wav")},
                )

                mock_manager.get_model.assert_called()


class TestLoadAudioFromBytes:
    """Test cases for load_audio_from_bytes function."""

    def test_load_audio_returns_numpy_array(self):
        """Verify audio is converted to numpy array."""
        # Mock subprocess to return valid audio data
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            np.zeros(16000, dtype=np.int16).tobytes(),
            b"",
        )

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("ai_term.stt.main.model_manager"):
                from ai_term.stt.main import load_audio_from_bytes

                result = load_audio_from_bytes(b"fake wav bytes")

                assert isinstance(result, np.ndarray)
                assert result.dtype == np.float32

    def test_load_audio_normalizes_to_float32(self):
        """Verify audio is normalized to float32 range."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        # Create int16 data at max value
        int16_data = np.array([32767, -32768, 0], dtype=np.int16)
        mock_process.communicate.return_value = (int16_data.tobytes(), b"")

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("ai_term.stt.main.model_manager"):
                from ai_term.stt.main import load_audio_from_bytes

                result = load_audio_from_bytes(b"fake audio")

                # Values should be normalized to approximately -1 to 1
                assert result.max() <= 1.0
                assert result.min() >= -1.0

    def test_load_audio_ffmpeg_error(self):
        """Verify error handling when ffmpeg fails."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b"", b"ffmpeg error message")

        with patch("subprocess.Popen", return_value=mock_process):
            with patch("ai_term.stt.main.model_manager"):
                from fastapi import HTTPException

                from ai_term.stt.main import load_audio_from_bytes

                with pytest.raises((RuntimeError, HTTPException)):
                    load_audio_from_bytes(b"invalid audio")

    def test_load_audio_uses_correct_ffmpeg_args(self):
        """Verify correct ffmpeg arguments are used."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (
            np.zeros(16000, dtype=np.int16).tobytes(),
            b"",
        )

        with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
            with patch("ai_term.stt.main.model_manager"):
                from ai_term.stt.main import load_audio_from_bytes

                load_audio_from_bytes(b"test audio", sr=16000)

                call_args = mock_popen.call_args[0][0]

                assert call_args[0] == "ffmpeg"
                assert "pipe:0" in call_args  # Input from stdin
                assert "-ar" in call_args  # Sample rate argument
                assert "16000" in call_args  # Target sample rate


class TestLoadWhisperModel:
    """Test cases for load_whisper_model function."""

    def test_load_whisper_model_creates_model(self):
        """Verify load_whisper_model creates a whisper model."""
        with patch("ai_term.stt.main.torch") as mock_torch_local:
            with patch("ai_term.stt.main.whisper") as mock_whisper_local:
                mock_torch_local.cuda.is_available.return_value = False
                mock_torch_local.backends.mps.is_available.return_value = False

                from ai_term.stt.main import load_whisper_model

                load_whisper_model()

                mock_whisper_local.load_model.assert_called_once()

    def test_load_whisper_model_uses_cpu_fallback(self):
        """Verify CPU is used when no GPU available."""
        with patch("ai_term.stt.main.torch") as mock_torch_local:
            with patch("ai_term.stt.main.whisper") as mock_whisper_local:
                mock_torch_local.cuda.is_available.return_value = False
                mock_torch_local.backends.mps.is_available.return_value = False

                from ai_term.stt.main import load_whisper_model

                load_whisper_model()

                call_kwargs = mock_whisper_local.load_model.call_args.kwargs
                assert call_kwargs["device"] == "cpu"

    def test_load_whisper_model_uses_cuda_if_available(self):
        """Verify CUDA is used if available."""
        with patch("ai_term.stt.main.torch") as mock_torch_local:
            with patch("ai_term.stt.main.whisper") as mock_whisper_local:
                mock_torch_local.cuda.is_available.return_value = True

                from ai_term.stt.main import load_whisper_model

                load_whisper_model()

                call_kwargs = mock_whisper_local.load_model.call_args.kwargs
                assert call_kwargs["device"] == "cuda"

    def test_load_whisper_model_uses_mps_if_available(self):
        """Verify MPS is used if available (Mac)."""
        with patch("ai_term.stt.main.torch") as mock_torch_local:
            with patch("ai_term.stt.main.whisper") as mock_whisper_local:
                mock_torch_local.cuda.is_available.return_value = False
                mock_torch_local.backends.mps.is_available.return_value = True

                from ai_term.stt.main import load_whisper_model

                load_whisper_model()

                call_kwargs = mock_whisper_local.load_model.call_args.kwargs
                assert call_kwargs["device"] == "mps"

    def test_load_whisper_model_uses_base_model(self):
        """Verify 'base' model is loaded."""
        with patch("ai_term.stt.main.torch") as mock_torch_local:
            with patch("ai_term.stt.main.whisper") as mock_whisper_local:
                mock_torch_local.cuda.is_available.return_value = False
                mock_torch_local.backends.mps.is_available.return_value = False

                from ai_term.stt.main import load_whisper_model

                load_whisper_model()

                call_args = mock_whisper_local.load_model.call_args[0]
                assert call_args[0] == "base"
