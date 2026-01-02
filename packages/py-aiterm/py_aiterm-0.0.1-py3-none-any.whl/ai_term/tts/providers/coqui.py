"""Coqui TTS Provider implementation."""

import io
import logging

import numpy as np
import scipy.io.wavfile as wav
from TTS.api import TTS

from ai_term.common.model_manager import ModelManager
from ai_term.tts.interface import TTSProvider

logger = logging.getLogger(__name__)


def _load_tts_model():
    """Load the Coqui TTS model."""
    logger.debug("Loading Coqui TTS model...")
    return TTS("tts_models/en/ljspeech/glow-tts", gpu=False)


# Shared model manager for Coqui TTS
_model_manager = ModelManager(load_model_fn=_load_tts_model)


class CoquiTTSProvider(TTSProvider):
    """TTS Provider using Coqui TTS library."""

    def __init__(self):
        """Initialize CoquiTTSProvider."""
        self._model_manager = _model_manager

    @property
    def name(self) -> str:
        return "coqui"

    def generate(self, text: str, **kwargs) -> bytes:
        """
        Generate speech using Coqui TTS.

        Args:
            text: Text to synthesize.
            **kwargs: Ignored for this provider.

        Returns:
            Audio bytes in WAV format.
        """
        model = self._model_manager.get_model()

        # tts.tts() returns a list of floats
        wav_data = model.tts(text)

        # Convert to numpy array
        wav_np = np.array(wav_data, dtype=np.float32)

        # Write to buffer
        buffer = io.BytesIO()

        # Get sample rate
        try:
            if hasattr(model, "synthesizer") and hasattr(
                model.synthesizer, "output_sample_rate"
            ):
                rate = model.synthesizer.output_sample_rate
            else:
                rate = 22050
        except Exception:
            rate = 22050

        wav.write(buffer, rate, wav_np)
        buffer.seek(0)

        return buffer.read()
