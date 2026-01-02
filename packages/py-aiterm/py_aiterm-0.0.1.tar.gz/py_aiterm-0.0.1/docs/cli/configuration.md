# Configuration

ai_term uses a robust configuration system based on `pydantic-settings`.

## AppConfig

The `AppConfig` class manages all application settings, including LLM providers, audio settings, and appearance.

### Environment Variables

Configuration is loaded from several sources in this order:
1. System Environment Variables
2. `.env` file (if configured)
3. Internal `env` dictionary in `config.json`

### Provider Schemas

The application supports dynamic configuration for different providers (LLM, TTS, STT).
The schemas are defined in `PROVIDER_SCHEMAS`.

::: ai_term.cli.config.AppConfig
    options:
      show_root_heading: true

```json
{
  "llm": {
    "ollama": {
      "model": { "type": "text", "label": "Model Name", "default": "llama3.1" },
      "base_url": { "type": "text", "label": "Base URL", "default": "http://localhost:11434" }
    },
    "openai": {
      "api_key": { "type": "secret", "label": "API Key (Env Var)", "placeholder": "OPENAI_API_KEY" },
      "model": { "type": "text", "label": "Model Name", "default": "gpt-4o" }
    },
    "anthropic": {
      "api_key": { "type": "secret", "label": "API Key (Env Var)", "placeholder": "ANTHROPIC_API_KEY" },
      "model": { "type": "text", "label": "Model Name", "default": "claude-3-sonnet-20240229" }
    }
  },
  "tts": {
    "coqui": {},
    "elevenlabs": {
      "api_key": { "type": "secret", "label": "API Key (Env Var)", "placeholder": "ELEVEN_API_KEY" },
      "voice_id": { "type": "text", "label": "Voice ID", "default": "21m00Tcm4TlvDq8ikWAM" }
    }
  },
  "stt": {
    "whisper": {
      "model": { "type": "text", "label": "Model Size", "default": "base" }
    }
  }
}
```
