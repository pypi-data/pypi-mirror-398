"""Shared pytest fixtures for all tests."""

import io
import json
import wave
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary directory with config files."""
    aiterm_dir = tmp_path / ".aiterm"
    aiterm_dir.mkdir()
    return tmp_path


@pytest.fixture
def sample_config_json(temp_config_dir):
    """Create a sample config.json file."""
    config = {
        "llm": {
            "provider": "ollama",
            "model": "test-model",
            "base_url": "http://localhost:11434",
        },
        "audio": {
            "stt_url": "http://localhost:8001",
            "tts_url": "http://localhost:8002",
            "speech_mode": False,
        },
        "database": {"url": "sqlite+aiosqlite:///test.db"},
        "appearance": {"theme": "textual-dark", "show_timestamps": True},
    }
    config_path = temp_config_dir / ".aiterm" / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)
    return config_path


@pytest.fixture
def sample_mcp_config_json(temp_config_dir):
    """Create a sample mcp.json file."""
    config = {
        "mcpServers": {
            "test-server": {
                "command": "node",
                "args": ["server.js"],
                "env": {"DEBUG": "true"},
            }
        }
    }
    config_path = temp_config_dir / ".aiterm" / "mcp.json"
    with open(config_path, "w") as f:
        json.dump(config, f)
    return config_path


@pytest.fixture
def sample_wav_bytes():
    """Generate sample WAV audio bytes for testing."""
    # Create a simple sine wave
    sample_rate = 44100
    duration = 0.1  # 100ms
    frequency = 440  # Hz (A4 note)

    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())

    return buffer.getvalue()


@pytest.fixture
def sample_audio_frames():
    """Generate sample numpy audio frames for testing AudioRecorder."""
    # Create 3 frames of audio data (float32, -1 to 1 range)
    frames = [
        np.random.uniform(-0.5, 0.5, (1024, 1)).astype(np.float32) for _ in range(3)
    ]
    return frames


@pytest.fixture
def mock_async_session():
    """Create a mocked async SQLAlchemy session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response object."""
    response = MagicMock()
    response.content = "Test response from LLM"
    response.tool_calls = None
    return response


@pytest.fixture
def mock_stream_chunks():
    """Create mock streaming chunks from LLM."""
    chunks = [
        MagicMock(content="Hello"),
        MagicMock(content=" "),
        MagicMock(content="World"),
        MagicMock(content="!"),
    ]
    return chunks
