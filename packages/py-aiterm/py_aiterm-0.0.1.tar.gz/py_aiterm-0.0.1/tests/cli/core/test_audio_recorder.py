"""Tests for AudioRecorder class."""

import io
import wave
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import ai_term.cli.core.audio_recorder  # noqa: F401


class TestAudioRecorder:
    """Test cases for AudioRecorder."""

    @pytest.fixture
    def recorder(self):
        """Create an AudioRecorder instance with mocked sounddevice."""
        with patch("ai_term.cli.core.audio_recorder.sd"):
            from ai_term.cli.core.audio_recorder import AudioRecorder

            return AudioRecorder()

    def test_init_custom_values(self):
        """Verify custom initialization values."""
        with patch("ai_term.cli.core.audio_recorder.sd"):
            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder(sample_rate=16000, channels=2)

            assert recorder.sample_rate == 16000
            assert recorder.channels == 2

    def test_start_creates_stream(self):
        """Verify start() creates an input stream."""
        with patch("ai_term.cli.core.audio_recorder.sd") as mock_sd:
            mock_stream = MagicMock()
            mock_sd.InputStream.return_value = mock_stream

            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder()

            recorder.start()

            assert recorder.recording is True
            mock_sd.InputStream.assert_called_once()
            mock_stream.start.assert_called_once()

    def test_start_clears_previous_data(self):
        """Verify start() clears previous frames and amplitudes."""
        with patch("ai_term.cli.core.audio_recorder.sd") as mock_sd:
            mock_stream = MagicMock()
            mock_sd.InputStream.return_value = mock_stream

            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder()

            # Add some data
            recorder.frames = [np.array([1, 2, 3])]
            recorder.amplitudes.append(0.5)

            recorder.start()

            assert recorder.frames == []
            assert len(recorder.amplitudes) == 0

    def test_double_start_is_noop(self):
        """Verify calling start() twice doesn't create multiple streams."""
        with patch("ai_term.cli.core.audio_recorder.sd") as mock_sd:
            mock_stream = MagicMock()
            mock_sd.InputStream.return_value = mock_stream

            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder()

            recorder.start()
            recorder.start()  # Second call

            # InputStream should only be called once
            assert mock_sd.InputStream.call_count == 1

    def test_stop_returns_wav_bytes(self, sample_audio_frames):
        """Verify stop() returns valid WAV bytes."""
        with patch("ai_term.cli.core.audio_recorder.sd") as mock_sd:
            mock_stream = MagicMock()
            mock_sd.InputStream.return_value = mock_stream

            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder()

            # Simulate recording
            recorder.recording = True
            recorder._stream = mock_stream
            recorder.frames = sample_audio_frames

            wav_bytes = recorder.stop()

            assert recorder.recording is False
            mock_stream.stop.assert_called_once()
            mock_stream.close.assert_called_once()

            # Verify WAV format
            assert len(wav_bytes) > 0
            assert wav_bytes[:4] == b"RIFF"

    def test_stop_without_start_returns_empty(self, recorder):
        """Verify stop() without start() returns empty bytes."""
        result = recorder.stop()

        assert result == b""
        assert recorder.recording is False

    def test_empty_recording_returns_empty_bytes(self):
        """Verify empty frames return empty bytes."""
        with patch("ai_term.cli.core.audio_recorder.sd") as mock_sd:
            mock_stream = MagicMock()
            mock_sd.InputStream.return_value = mock_stream

            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder()

            recorder.recording = True
            recorder._stream = mock_stream
            recorder.frames = []  # No frames recorded

            wav_bytes = recorder.stop()

            assert wav_bytes == b""

    def test_callback_stores_frames(self):
        """Verify callback stores audio frames."""
        with patch("ai_term.cli.core.audio_recorder.sd"):
            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder()

            # Simulate callback data
            indata = np.random.uniform(-0.5, 0.5, (1024, 1)).astype(np.float32)

            recorder._callback(indata, 1024, None, None)

            assert len(recorder.frames) == 1
            assert recorder.frames[0].shape == indata.shape

    def test_callback_calculates_amplitude(self):
        """Verify callback calculates RMS amplitude."""
        with patch("ai_term.cli.core.audio_recorder.sd"):
            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder()

            # Create audio data with known amplitude
            indata = np.ones((1024, 1), dtype=np.float32) * 0.5

            recorder._callback(indata, 1024, None, None)

            assert len(recorder.amplitudes) == 1
            # RMS of constant 0.5 should be 0.5
            assert abs(recorder.amplitudes[0] - 0.5) < 0.01

    def test_get_amplitudes_returns_list(self):
        """Verify get_amplitudes returns a list."""
        with patch("ai_term.cli.core.audio_recorder.sd"):
            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder()

            recorder.amplitudes.append(0.1)
            recorder.amplitudes.append(0.2)
            recorder.amplitudes.append(0.3)

            result = recorder.get_amplitudes()

            assert isinstance(result, list)
            assert result == [0.1, 0.2, 0.3]

    def test_wav_format_headers(self, sample_audio_frames):
        """Verify WAV format has correct headers."""
        with patch("ai_term.cli.core.audio_recorder.sd") as mock_sd:
            mock_stream = MagicMock()
            mock_sd.InputStream.return_value = mock_stream

            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder(sample_rate=44100, channels=1)

            recorder.recording = True
            recorder._stream = mock_stream
            recorder.frames = sample_audio_frames

            wav_bytes = recorder.stop()

            # Parse WAV headers
            audio_file = io.BytesIO(wav_bytes)
            with wave.open(audio_file, "rb") as wf:
                assert wf.getnchannels() == 1
                assert wf.getsampwidth() == 2  # 16-bit
                assert wf.getframerate() == 44100

    def test_amplitude_deque_maxlen(self):
        """Verify amplitudes deque has maxlen of 50."""
        with patch("ai_term.cli.core.audio_recorder.sd"):
            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder()

            # Add more than 50 amplitudes
            for i in range(60):
                recorder.amplitudes.append(float(i))

            assert len(recorder.amplitudes) == 50
            # Should contain the last 50 values (10-59)
            assert recorder.amplitudes[0] == 10.0
            assert recorder.amplitudes[-1] == 59.0

    def test_callback_handles_status_warnings(self, caplog):
        """Verify callback handles status warnings."""
        with patch("ai_term.cli.core.audio_recorder.sd"):
            import logging

            from ai_term.cli.core.audio_recorder import AudioRecorder

            recorder = AudioRecorder()
            indata = np.zeros((1024, 1), dtype=np.float32)

            # Simulate a status warning
            with caplog.at_level(logging.WARNING):
                recorder._callback(indata, 1024, None, "input underflow")

            # Frame should still be recorded
            assert len(recorder.frames) == 1
