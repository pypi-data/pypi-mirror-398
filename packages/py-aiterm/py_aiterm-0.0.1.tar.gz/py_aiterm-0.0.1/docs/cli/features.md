# Features

## Chat Interface

The main screen is the **Chat Screen**. It mimics a standard messaging interface but runs entirely in the terminal.

- **Message History**: Persisted in SQLite.
- **Sessions**: Multiple chat sessions support.
- **Thinking Indicator**: Visual feedback while waiting for LLM.

::: ai_term.cli.ui.app.ChatApp

## Settings Screen

The **Settings Screen** (`ai_term.cli.ui.screens.settings`) is dynamically generated based on `AppConfig` and `PROVIDER_SCHEMAS`.

- **Dynamic Forms**: Fields change based on selected provider.
- **Secret Management**: API keys are validated against environment variables.

::: ai_term.cli.ui.screens.settings.SettingsScreen

## Voice Interaction

- **Speech Mode**: When enabled, valid AI responses are automatically spoken.
- **Recording**: Hold `Space` (or configured key) to record voice input.

::: ai_term.cli.core.audio_recorder.AudioRecorder
