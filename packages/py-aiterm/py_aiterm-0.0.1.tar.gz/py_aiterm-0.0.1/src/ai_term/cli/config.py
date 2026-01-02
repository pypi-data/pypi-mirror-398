"""Configuration loader for CLI Chat Application."""

import json
import os
import re
from pathlib import Path
from typing import Any, TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# --- Provider Schemas ---


class FieldSchema(TypedDict, total=False):
    type: str  # "text" | "secret"
    label: str
    default: str
    placeholder: str


ProviderFields = dict[str, FieldSchema]
ProviderCategory = dict[str, ProviderFields]


PROVIDER_SCHEMAS: dict[str, ProviderCategory] = {
    "llm": {
        "ollama": {
            "model": {"type": "text", "label": "Model Name", "default": "llama3.1"},
            "base_url": {
                "type": "text",
                "label": "Base URL",
                "default": "http://localhost:11434",
            },
        },
        "openai": {
            "api_key": {
                "type": "secret",
                "label": "API Key (Env Var)",
                "placeholder": "OPENAI_API_KEY",
            },
            "model": {"type": "text", "label": "Model Name", "default": "gpt-4o"},
        },
        "anthropic": {
            "api_key": {
                "type": "secret",
                "label": "API Key (Env Var)",
                "placeholder": "ANTHROPIC_API_KEY",
            },
            "model": {
                "type": "text",
                "label": "Model Name",
                "default": "claude-3-sonnet-20240229",
            },
        },
    },
    "tts": {
        "coqui": {},
        "elevenlabs": {
            "api_key": {
                "type": "secret",
                "label": "API Key (Env Var)",
                "placeholder": "ELEVEN_API_KEY",
            },
            "voice_id": {
                "type": "text",
                "label": "Voice ID",
                "default": "21m00Tcm4TlvDq8ikWAM",
            },
        },
    },
    "stt": {
        "whisper": {"model": {"type": "text", "label": "Model Size", "default": "base"}}
    },
}


# --- Config Models ---


class LLMConfig(BaseModel):
    provider: str = "ollama"
    model: str = "llama3.1"
    base_url: str = "http://localhost:11434"
    api_key: str | None = None  # Stores env var name (e.g., "OPENAI_API_KEY")


class TTSConfig(BaseModel):
    provider: str = "coqui"
    voice_id: str | None = None
    model_id: str | None = None
    api_key: str | None = None  # Stores env var name


class STTConfig(BaseModel):
    provider: str = "whisper"
    model: str = "base"


class AudioConfig(BaseModel):
    stt_url: str = "http://localhost:8901"
    tts_url: str = "http://localhost:8902"
    speech_mode: bool = False

    stt: STTConfig = Field(default_factory=STTConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)


class DatabaseConfig(BaseModel):
    url: str = "sqlite+aiosqlite:///./.aiterm/chat.db"


class AppearanceConfig(BaseModel):
    theme: str = "textual-dark"
    show_timestamps: bool = True


# --- Environment Management ---

_loaded_env: dict[str, str] = {}


def _load_environment(config_path: Path, config_data: dict[str, Any]) -> dict[str, str]:
    """Load environment variables from various sources."""
    global _loaded_env

    # Start with os.environ
    resolved_env = os.environ.copy()

    # Load .env file if specified
    env_file = config_data.get("dotEnvFilePath")
    if env_file:
        env_path = Path(env_file)
        if not env_path.is_absolute():
            env_path = config_path.parent / env_path

        if env_path.exists():
            load_dotenv(env_path, override=True)
            resolved_env.update(os.environ)

    # Load 'env' dict from config (highest priority)
    if "env" in config_data:
        resolved_env.update(config_data["env"])

    _loaded_env = resolved_env
    return resolved_env


def get_loaded_env() -> dict[str, str]:
    """Get the currently loaded environment variables."""
    global _loaded_env
    if not _loaded_env:
        _loaded_env = os.environ.copy()
    return _loaded_env


def validate_env_var(name: str) -> bool:
    """Check if an environment variable exists."""
    env = get_loaded_env()
    return name in env


def resolve_secret(value: str | None) -> str | None:
    """Resolve an environment variable name to its value."""
    if value is None:
        return None

    # Check if it's a ${VAR} pattern
    match = re.match(r"^\$\{([^}]+)\}$", value)
    if match:
        var_name = match.group(1)
        return get_loaded_env().get(var_name)

    # Otherwise, treat the value itself as an env var name
    return get_loaded_env().get(value)


# --- App Config ---


class AppConfig(BaseSettings):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    appearance: AppearanceConfig = Field(default_factory=AppearanceConfig)

    # Environment configuration
    dotEnvFilePath: str | None = None
    env: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Path | None = None) -> "AppConfig":
        """Load configuration from JSON file (raw values, no substitution)."""
        if config_path is None:
            config_path = Path(__file__).parents[2] / ".aiterm" / "config.json"

        config_data: dict[str, Any] = {}
        if config_path.exists():
            with open(config_path) as f:
                config_data = json.load(f)

        # Load environment (for validation/resolution later)
        _load_environment(config_path, config_data)

        # Create AppConfig with raw values (no substitution here)
        return cls(**config_data)


# --- MCP Config ---


class MCPServerConfig(BaseModel):
    command: str
    args: list[str] = []
    env: dict[str, str] = {}


class MCPConfig(BaseModel):
    mcpServers: dict[str, MCPServerConfig] = {}

    @classmethod
    def load(cls, config_path: Path | None = None) -> "MCPConfig":
        """Load MCP configuration from JSON file."""
        if config_path is None:
            config_path = Path(__file__).parents[2] / ".aiterm" / "mcp.json"

        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
            return cls(**data)
        return cls()


# --- Global Instances ---

_app_config: AppConfig | None = None
_mcp_config: MCPConfig | None = None


def get_app_config() -> AppConfig:
    global _app_config
    if _app_config is None:
        _app_config = AppConfig.load()
    return _app_config


def get_mcp_config() -> MCPConfig:
    global _mcp_config
    if _mcp_config is None:
        _mcp_config = MCPConfig.load()
    return _mcp_config


def save_app_config(config: AppConfig | None = None) -> None:
    """Save app configuration to JSON file (preserves raw env var names)."""
    global _app_config
    if config is not None:
        _app_config = config

    if _app_config is None:
        return

    config_path = Path(__file__).parents[3] / ".aiterm" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = _app_config.model_dump()

    with open(config_path, "w") as f:
        json.dump(data, f, indent=4)
