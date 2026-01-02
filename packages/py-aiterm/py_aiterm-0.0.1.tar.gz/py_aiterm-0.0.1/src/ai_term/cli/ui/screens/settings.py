"""Settings screen with multiple tabs."""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static, TabbedContent, TabPane

from ...config import (
    PROVIDER_SCHEMAS,
    AppConfig,
    AppearanceConfig,
    AudioConfig,
    LLMConfig,
    TTSConfig,
    get_app_config,
    save_app_config,
    validate_env_var,
)
from ...ui import constants


class LLMTabContent(VerticalScroll):
    """Scrollable LLM configuration tab with dynamic fields."""

    DEFAULT_CSS = """
    LLMTabContent {
        scrollbar-color: $primary;
        scrollbar-color-hover: $primary-lighten-1;
    }
    """

    def __init__(self, config: AppConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        yield Static("🧠 LLM CONFIGURATION", classes="section-title")

        providers = list(PROVIDER_SCHEMAS.get("llm", {}).keys())
        provider_options = [(p.title(), p) for p in providers]

        with Horizontal(classes="settings-row"):
            yield Label("Provider:", classes="settings-label")
            yield Select(
                provider_options,
                value=self.config.llm.provider,
                id="llm-provider-select",
                classes="settings-select",
            )

        # Dynamic fields based on provider
        schema = PROVIDER_SCHEMAS.get("llm", {}).get(self.config.llm.provider, {})

        for field_name, field_schema in schema.items():
            label_text = field_schema.get("label", field_name.replace("_", " ").title())
            default = field_schema.get("default", "")
            placeholder = field_schema.get("placeholder", "")

            current_value = getattr(self.config.llm, field_name, "") or ""
            value = current_value or default

            with Horizontal(classes="settings-row"):
                yield Label(f"{label_text}:", classes="settings-label")
                yield Input(
                    value=value,
                    placeholder=placeholder,
                    id=f"llm-{field_name}",
                    classes="settings-input",
                )


class AudioTabContent(VerticalScroll):
    """Scrollable Audio configuration tab with dynamic TTS fields."""

    DEFAULT_CSS = """
    AudioTabContent {
        scrollbar-color: $primary;
        scrollbar-color-hover: $primary-lighten-1;
    }
    """

    def __init__(self, config: AppConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        yield Static("🔊 AUDIO SETTINGS", classes="section-title")

        with Horizontal(classes="settings-row"):
            yield Label("Speech Mode:", classes="settings-label")
            speech_val = "enabled" if self.config.audio.speech_mode else "disabled"
            yield Select(
                [("Enabled", "enabled"), ("Disabled", "disabled")],
                value=speech_val,
                id="speech-mode",
                classes="settings-select",
            )

        with Horizontal(classes="settings-row"):
            yield Label("STT URL:", classes="settings-label")
            yield Input(
                value=self.config.audio.stt_url, id="stt-url", classes="settings-input"
            )

        with Horizontal(classes="settings-row"):
            yield Label("TTS URL:", classes="settings-label")
            yield Input(
                value=self.config.audio.tts_url, id="tts-url", classes="settings-input"
            )

        # TTS Provider Configuration
        yield Static("🎤 TTS PROVIDER", classes="section-title")

        providers = list(PROVIDER_SCHEMAS.get("tts", {}).keys())
        provider_options = [(p.title(), p) for p in providers]

        with Horizontal(classes="settings-row"):
            yield Label("TTS Provider:", classes="settings-label")
            yield Select(
                provider_options,
                value=self.config.audio.tts.provider,
                id="tts-provider-select",
                classes="settings-select",
            )

        # Dynamic TTS fields based on provider
        schema = PROVIDER_SCHEMAS.get("tts", {}).get(self.config.audio.tts.provider, {})

        for field_name, field_schema in schema.items():
            label_text = field_schema.get("label", field_name.replace("_", " ").title())
            default = field_schema.get("default", "")
            placeholder = field_schema.get("placeholder", "")

            current_value = getattr(self.config.audio.tts, field_name, "") or ""
            value = current_value or default

            with Horizontal(classes="settings-row"):
                yield Label(f"{label_text}:", classes="settings-label")
                yield Input(
                    value=value,
                    placeholder=placeholder,
                    id=f"tts-{field_name}",
                    classes="settings-input",
                )


class AppearanceTabContent(VerticalScroll):
    """Scrollable Appearance configuration tab."""

    DEFAULT_CSS = """
    AppearanceTabContent {
        scrollbar-color: $primary;
        scrollbar-color-hover: $primary-lighten-1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("🎨 APPEARANCE", classes="section-title")

        with Horizontal(classes="settings-row"):
            yield Label("Theme:", classes="settings-label")
            yield Select(
                [],  # Will be populated on mount
                id="theme-select",
                classes="settings-select",
            )

        with Horizontal(classes="settings-row"):
            yield Label("Timestamps:", classes="settings-label")
            yield Select(
                [("Yes", "yes"), ("No", "no")],
                value="yes",
                id="show-times",
                classes="settings-select",
            )


class SettingsScreen(ModalScreen):
    """Settings configuration screen with tabbed interface."""

    BINDINGS = [
        ("escape", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        config = get_app_config()

        with Vertical(classes="settings-container"):
            with TabbedContent():
                with TabPane("LLM Config", id="tab-llm"):
                    yield LLMTabContent(config=config, id="llm-tab-content")
                with TabPane("Audio", id="tab-audio"):
                    yield AudioTabContent(config=config, id="audio-tab-content")
                with TabPane("Appearance", id="tab-appearance"):
                    yield AppearanceTabContent(id="appearance-tab-content")

            with Horizontal(classes="button-row"):
                yield Button("Save", variant="success", id="save-btn", compact=True)
                yield Button("Cancel", variant="primary", id="cancel-btn", compact=True)

    def on_mount(self) -> None:
        """Initial setup on mount."""
        container = self.query_one(".settings-container")
        container.border_title = "⚙️ SETTINGS"

        # Populate theme dropdown
        theme_select = self.query_one("#theme-select", Select)
        available_themes = list(self.app.available_themes.keys())
        theme_options = [
            (theme.replace("-", " ").title(), theme)
            for theme in sorted(available_themes)
        ]
        theme_select.set_options(theme_options)

        # Load config values
        self._load_config_values()

    def on_screen_resume(self) -> None:
        """Reload config values each time screen is shown."""
        self._load_config_values()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle provider selection changes - recompose the tab."""
        if event.select.id == "llm-provider-select":
            llm_tab = self.query_one("#llm-tab-content", LLMTabContent)
            new_provider = str(event.value)
            # Only recompose if provider actually changed
            if llm_tab.config.llm.provider != new_provider:
                llm_tab.config.llm.provider = new_provider
                llm_tab.refresh(recompose=True)
        elif event.select.id == "tts-provider-select":
            audio_tab = self.query_one("#audio-tab-content", AudioTabContent)
            new_provider = str(event.value)
            # Only recompose if provider actually changed
            if audio_tab.config.audio.tts.provider != new_provider:
                audio_tab.config.audio.tts.provider = new_provider
                audio_tab.refresh(recompose=True)

    def _load_config_values(self) -> None:
        """Load current config values into form fields."""
        config = get_app_config()

        # Update reactive providers (triggers recompose)
        llm_tab = self.query_one("#llm-tab-content", LLMTabContent)
        if llm_tab.config.llm.provider != config.llm.provider:
            llm_tab.config.llm.provider = config.llm.provider
            llm_tab.refresh(recompose=True)

        audio_tab = self.query_one("#audio-tab-content", AudioTabContent)
        if audio_tab.config.audio.tts.provider != config.audio.tts.provider:
            audio_tab.config.audio.tts.provider = config.audio.tts.provider
            audio_tab.refresh(recompose=True)

        # Appearance tab
        self.query_one("#theme-select", Select).value = config.appearance.theme
        show_times = "yes" if config.appearance.show_timestamps else "no"
        self.query_one("#show-times", Select).value = show_times

    def _validate_secrets(self) -> bool:
        """Validate all secret fields (env var names). Returns True if valid."""
        validation_errors = []

        # Check LLM secrets
        llm_tab = self.query_one("#llm-tab-content", LLMTabContent)
        llm_schema = PROVIDER_SCHEMAS.get("llm", {}).get(
            llm_tab.config.llm.provider, {}
        )

        for field_name, field_schema in llm_schema.items():
            if field_schema.get("type") == "secret":
                try:
                    input_widget = self.query_one(f"#llm-{field_name}", Input)
                    env_var_name = input_widget.value.strip()
                    if env_var_name and not validate_env_var(env_var_name):
                        validation_errors.append(
                            f"LLM: Environment variable '{env_var_name}' not found"
                        )
                except Exception:
                    pass

        # Check TTS secrets
        audio_tab = self.query_one("#audio-tab-content", AudioTabContent)
        tts_schema = PROVIDER_SCHEMAS.get("tts", {}).get(
            audio_tab.config.audio.tts.provider, {}
        )

        for field_name, field_schema in tts_schema.items():
            if field_schema.get("type") == "secret":
                try:
                    input_widget = self.query_one(f"#tts-{field_name}", Input)
                    env_var_name = input_widget.value.strip()
                    if env_var_name and not validate_env_var(env_var_name):
                        validation_errors.append(
                            f"TTS: Environment variable '{env_var_name}' not found"
                        )
                except Exception:
                    pass

        if validation_errors:
            for error in validation_errors:
                self.notify(error, severity="error", timeout=5)
            return False

        return True

    def _save_settings(self) -> bool:
        """Save settings to config file. Returns True if successful."""
        # Validate secrets first
        if not self._validate_secrets():
            return False

        config = get_app_config()

        # LLM settings from dynamic fields
        llm_tab = self.query_one("#llm-tab-content", LLMTabContent)
        llm_schema = PROVIDER_SCHEMAS.get("llm", {}).get(
            llm_tab.config.llm.provider, {}
        )

        llm_kwargs: dict[str, Any] = {"provider": llm_tab.config.llm.provider}
        for field_name in ["model", "base_url", "api_key"]:
            if field_name in llm_schema:
                try:
                    input_widget = self.query_one(f"#llm-{field_name}", Input)
                    llm_kwargs[field_name] = input_widget.value or None
                except Exception:
                    pass

        config.llm = LLMConfig(**llm_kwargs)

        # Audio settings
        stt_url = self.query_one("#stt-url", Input).value
        tts_url = self.query_one("#tts-url", Input).value
        speech_mode = self.query_one("#speech-mode", Select).value

        # TTS Settings from dynamic fields
        audio_tab = self.query_one("#audio-tab-content", AudioTabContent)
        tts_schema = PROVIDER_SCHEMAS.get("tts", {}).get(
            audio_tab.config.audio.tts.provider, {}
        )

        tts_kwargs: dict[str, Any] = {"provider": audio_tab.config.audio.tts.provider}
        for field_name in ["api_key", "voice_id", "model_id"]:
            if field_name in tts_schema:
                try:
                    input_widget = self.query_one(f"#tts-{field_name}", Input)
                    tts_kwargs[field_name] = input_widget.value or None
                except Exception:
                    pass

        config.audio = AudioConfig(
            stt_url=stt_url or "http://localhost:8001",
            tts_url=tts_url or "http://localhost:8002",
            speech_mode=speech_mode == "enabled",
            stt=config.audio.stt,
            tts=TTSConfig(**tts_kwargs),
        )

        # Appearance settings
        theme = self.query_one("#theme-select", Select).value
        show_times = self.query_one("#show-times", Select).value

        config.appearance = AppearanceConfig(
            theme=str(theme) if theme else "textual-dark",
            show_timestamps=show_times == "yes",
        )

        # Save to file
        save_app_config(config)

        # Apply theme immediately
        if theme:
            self.app.theme = str(theme)

        # Update ChatScreen voice output state
        try:
            chat_screen = self.app.get_screen("chat")
            if hasattr(chat_screen, "voice_output_enabled"):
                chat_screen.voice_output_enabled = config.audio.speech_mode  # type: ignore
                status = (
                    constants.STATUS_VOICE_ON
                    if config.audio.speech_mode
                    else constants.STATUS_VOICE_OFF
                )
                if hasattr(chat_screen, "query_one"):
                    from ...ui.widgets.status_bar import StatusBar

                    try:
                        chat_screen.query_one("#status-bar", StatusBar).update_status(
                            status
                        )
                    except Exception:
                        pass
        except Exception:
            pass

        self.notify("Settings saved!", severity="information", timeout=2)
        return True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            if self._save_settings():
                self.app.pop_screen()
        elif event.button.id == "cancel-btn":
            self.app.pop_screen()

    def action_close(self) -> None:
        self.app.pop_screen()
