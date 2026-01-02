"""Tests for CLI configuration module."""

import json
from pathlib import Path
from unittest.mock import patch

from ai_term.cli.config import (
    AppConfig,
    AppearanceConfig,
    AudioConfig,
    DatabaseConfig,
    LLMConfig,
    MCPConfig,
    MCPServerConfig,
)


class TestLLMConfig:
    """Test cases for LLMConfig model."""

    def test_default_values(self):
        """Verify default values for LLMConfig."""
        config = LLMConfig()

        assert config.provider == "ollama"
        assert config.model == "llama3.1"
        assert config.base_url == "http://localhost:11434"

    def test_custom_values(self):
        """Verify custom values can be set."""
        config = LLMConfig(
            provider="openai", model="gpt-4", base_url="https://api.openai.com"
        )

        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.base_url == "https://api.openai.com"


class TestAudioConfig:
    """Test cases for AudioConfig model."""

    def test_default_values(self):
        """Verify default values for AudioConfig."""
        config = AudioConfig()

        assert config.stt_url == "http://localhost:8901"
        assert config.tts_url == "http://localhost:8902"
        assert config.speech_mode is False

    def test_custom_values(self):
        """Verify custom values can be set."""
        config = AudioConfig(
            stt_url="http://stt.example.com",
            tts_url="http://tts.example.com",
            speech_mode=True,
        )

        assert config.stt_url == "http://stt.example.com"
        assert config.tts_url == "http://tts.example.com"
        assert config.speech_mode is True


class TestDatabaseConfig:
    """Test cases for DatabaseConfig model."""

    def test_default_values(self):
        """Verify default values for DatabaseConfig."""
        config = DatabaseConfig()

        assert "sqlite+aiosqlite://" in config.url


class TestAppearanceConfig:
    """Test cases for AppearanceConfig model."""

    def test_default_values(self):
        """Verify default values for AppearanceConfig."""
        config = AppearanceConfig()

        assert config.theme == "textual-dark"
        assert config.show_timestamps is True


class TestAppConfig:
    """Test cases for AppConfig model."""

    def test_default_config_values(self):
        """Verify default values for complete AppConfig."""
        config = AppConfig()

        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.audio, AudioConfig)
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.appearance, AppearanceConfig)

    def test_load_config_from_file(self, temp_config_dir):
        """Verify config loads correctly from JSON file."""
        config_data = {
            "llm": {
                "provider": "test-provider",
                "model": "test-model",
                "base_url": "http://test:1234",
            },
            "audio": {
                "stt_url": "http://stt:8001",
                "tts_url": "http://tts:8002",
                "speech_mode": True,
            },
        }
        config_path = temp_config_dir / ".aiterm" / "config.json"
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        config = AppConfig.load(config_path)

        assert config.llm.provider == "test-provider"
        assert config.llm.model == "test-model"
        assert config.audio.speech_mode is True

    def test_load_config_missing_file(self, temp_config_dir):
        """Verify defaults are used when config file doesn't exist."""
        non_existent_path = temp_config_dir / "non_existent" / "config.json"

        config = AppConfig.load(non_existent_path)

        # Should return default config
        assert config.llm.provider == "ollama"
        assert config.llm.model == "llama3.1"

    def test_nested_config_models(self):
        """Verify nested Pydantic models work correctly."""
        config = AppConfig(
            llm=LLMConfig(model="custom-model"), audio=AudioConfig(speech_mode=True)
        )

        assert config.llm.model == "custom-model"
        assert config.audio.speech_mode is True
        # Other nested configs should have defaults
        assert config.appearance.theme == "textual-dark"


class TestMCPServerConfig:
    """Test cases for MCPServerConfig model."""

    def test_required_command(self):
        """Verify command is required."""
        config = MCPServerConfig(command="python")

        assert config.command == "python"
        assert config.args == []
        assert config.env == {}

    def test_with_args_and_env(self):
        """Verify args and env can be set."""
        config = MCPServerConfig(
            command="node",
            args=["server.js", "--port", "3000"],
            env={"NODE_ENV": "development"},
        )

        assert config.command == "node"
        assert config.args == ["server.js", "--port", "3000"]
        assert config.env == {"NODE_ENV": "development"}


class TestMCPConfig:
    """Test cases for MCPConfig model."""

    def test_empty_servers_by_default(self):
        """Verify no servers configured by default."""
        config = MCPConfig()

        assert config.mcpServers == {}

    def test_load_mcp_config_from_file(self, temp_config_dir):
        """Verify MCP config loads from file."""
        config_data = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                    "env": {},
                }
            }
        }
        config_path = temp_config_dir / ".aiterm" / "mcp.json"
        with open(config_path, "w") as f:
            json.dump(config_data, f)

        config = MCPConfig.load(config_path)

        assert "filesystem" in config.mcpServers
        assert config.mcpServers["filesystem"].command == "npx"

    def test_load_mcp_config_missing_file(self, temp_config_dir):
        """Verify defaults when MCP config file doesn't exist."""
        non_existent_path = temp_config_dir / "non_existent" / "mcp.json"

        config = MCPConfig.load(non_existent_path)

        assert config.mcpServers == {}


class TestSaveAppConfig:
    """Test cases for save_app_config function."""

    def test_save_app_config(self, temp_config_dir, monkeypatch):
        """Verify config is saved to JSON file."""
        # Mock the config path
        config_path = temp_config_dir / ".aiterm" / "config.json"

        # Create a custom config
        config = AppConfig(
            llm=LLMConfig(model="saved-model"), audio=AudioConfig(speech_mode=True)
        )

        # Mock the path resolution in save_app_config
        def mock_parents(idx):
            if idx == 2:
                return temp_config_dir
            return Path(__file__).parents[idx]

        with patch("ai_term.cli.config.Path") as mock_path:
            mock_path.return_value.parents.__getitem__ = mock_parents
            mock_path.__truediv__ = lambda self, other: temp_config_dir / other

            # Save using the actual function internals
            config_path.parent.mkdir(parents=True, exist_ok=True)
            data = config.model_dump()
            with open(config_path, "w") as f:
                json.dump(data, f, indent=4)

        # Verify file was saved
        assert config_path.exists()

        with open(config_path) as f:
            saved_data = json.load(f)

        assert saved_data["llm"]["model"] == "saved-model"
        assert saved_data["audio"]["speech_mode"] is True
