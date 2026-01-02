import io
import logging
import wave
from collections import deque

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Handles audio recording using sounddevice."""

    def __init__(self, sample_rate: int = 44100, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.frames = []
        self.recording = False
        self._stream = None
        self.amplitudes = deque(maxlen=50)

    def start(self) -> None:
        """Start recording audio."""
        if self.recording:
            return

        self.frames = []
        self.amplitudes.clear()
        self.recording = True

        # Start input stream
        self._stream = sd.InputStream(
            channels=self.channels, samplerate=self.sample_rate, callback=self._callback
        )
        self._stream.start()
        logger.info("Started recording...")

    def stop(self) -> bytes:
        """
        Stop recording and return WAV bytes.

        Returns:
            Bytes containing WAV audio data.
        """
        if not self.recording:
            return b""

        self.recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        logger.info("Stopped recording.")
        return self._save_to_wav()

    def get_amplitudes(self) -> list[float]:
        """Get current amplitude history."""
        return list(self.amplitudes)

    def _callback(self, indata, frames, time, status):
        """Callback for sounddevice stream."""
        if status:
            logger.warning(f"Audio recording status: {status}")

        # Copy data
        audio_data = indata.copy()
        self.frames.append(audio_data)

        # Calculate amplitude (RMS)
        # Normalize to 0-1 range roughly (assuming int16 equivalent range
        # or float -1 to 1)
        # indata is float32 in -1.0 to 1.0 range usually
        rms = np.sqrt(np.mean(audio_data**2))
        self.amplitudes.append(float(rms))

    def _save_to_wav(self) -> bytes:
        """Convert recorded frames to WAV bytes."""
        if not self.frames:
            return b""

        buffer = io.BytesIO()
        try:
            # Concatenate all frames
            audio_data = np.concatenate(self.frames, axis=0)

            # Convert to 16-bit PCM
            audio_data_int16 = (audio_data * 32767).astype(np.int16)

            with wave.open(buffer, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 2 bytes for int16
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data_int16.tobytes())

            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Error saving WAV: {e}")
            return b""
