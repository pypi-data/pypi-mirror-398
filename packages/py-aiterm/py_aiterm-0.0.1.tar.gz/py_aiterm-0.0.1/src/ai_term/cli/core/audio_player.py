"""Audio player for playing audio bytes."""

import asyncio
import io
import logging

import sounddevice as sd
import soundfile as sf

logger = logging.getLogger(__name__)


class AudioPlayer:
    """Handles audio playback."""

    async def play(self, audio_bytes: bytes) -> None:
        """
        Play audio bytes (WAV format).

        Args:
            audio_bytes: Raw audio data in WAV format.
        """
        try:
            await asyncio.to_thread(self._play_sync, audio_bytes)
        except Exception as e:
            logger.error(f"Error playing audio: {e}")

    def _play_sync(self, audio_bytes: bytes) -> None:
        """Synchronous audio playback."""
        try:
            # Create a file-like object from bytes
            audio_file = io.BytesIO(audio_bytes)

            # Read audio data
            data, samplerate = sf.read(audio_file)

            # Play audio
            sd.play(data, samplerate)
            sd.wait()  # Wait until playback is finished

        except Exception as e:
            logger.error(f"Error in synchronous playback: {e}")
            raise
