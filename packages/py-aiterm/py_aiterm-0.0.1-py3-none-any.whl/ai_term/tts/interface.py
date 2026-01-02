"""Abstract base class for TTS providers."""

from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """Abstract TTS Provider interface."""

    @abstractmethod
    def generate(self, text: str, **kwargs) -> bytes:
        """
        Generate speech audio from text.

        Args:
            text: The text to synthesize.
            **kwargs: Provider-specific options.

        Returns:
            Audio bytes (WAV format).
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass
