"""Chat screen for conversation display."""

from datetime import datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Input, ListView, Sparkline

from ai_term.cli.config import get_app_config, save_app_config
from ai_term.cli.ui import constants
from ai_term.cli.ui.screens.confirmation import ConfirmationScreen
from ai_term.cli.ui.widgets.input_area import InputArea
from ai_term.cli.ui.widgets.message import MessageItem
from ai_term.cli.ui.widgets.sidebar import Sidebar
from ai_term.cli.ui.widgets.status_bar import StatusBar
from ai_term.cli.ui.widgets.thinking_indicator import ThinkingIndicator


class ChatScreen(Screen):
    """Main chat screen with retro cyberpunk theme."""

    BINDINGS = [
        Binding("ctrl+s", "toggle_sidebar", "Toggle Sidebar", priority=True),
        Binding("ctrl+n", "new_chat", "New Chat", priority=True),
        Binding("ctrl+v", "toggle_voice_input", "Voice Input", priority=True),
        Binding("ctrl+shift+v", "toggle_voice_output", "Voice Output", priority=True),
        Binding("escape", "unfocus_input", "Unfocus", show=False, priority=True),
        Binding("slash", "focus_input", "Focus Input", show=False),
        Binding("question_mark", "show_help", "Help"),
        Binding("ctrl+comma", "show_settings", "Settings", priority=True),
        Binding("ctrl+e", "focus_sessions", "Sessions", priority=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.voice_output_enabled = get_app_config().audio.speech_mode
        self.current_session_id: int | None = None
        self.current_session_title = constants.DEFAULT_SESSION_TITLE
        self._sparkline_timer = None

    def compose(self) -> ComposeResult:
        yield Sidebar(id="sidebar")
        with Vertical(id="chat-container"):
            with Vertical(id="chat-frame"):
                yield ScrollableContainer(id="chat-area")
            yield InputArea(id="input-area")
            yield StatusBar(
                provider=get_app_config().llm.provider,
                model=get_app_config().llm.model,
                status=constants.STATUS_VOICE_ON
                if self.voice_output_enabled
                else constants.STATUS_VOICE_OFF,
                hint=constants.HINT_NAVIGATE,
                id="status-bar",
            )

    def _update_sparkline(self) -> None:
        """Update sparkline with audio data."""
        try:
            # Check for audio_recorder on app
            if hasattr(self.app, "audio_recorder"):
                amplitudes = self.app.audio_recorder.get_amplitudes()  # type: ignore
                input_area = self.query_one("#input-area", InputArea)
                sparkline = input_area.query_one("#voice-sparkline", Sparkline)
                sparkline.data = amplitudes
        except Exception:
            pass

    async def on_input_area_voice_toggled(self, event: InputArea.VoiceToggled) -> None:
        """Handle voice toggle event."""
        input_area = self.query_one("#input-area", InputArea)
        sparkline = input_area.query_one("#voice-sparkline", Sparkline)
        message_input = input_area.query_one("#message-input", Input)

        # Cast app to ChatApp to access custom methods
        # typing: ignore
        if hasattr(self.app, "start_recording"):
            if event.enabled:
                # Show sparkline, hide input
                message_input.add_class("hidden")
                sparkline.remove_class("hidden")

                await self.app.start_recording()  # type: ignore
                self._sparkline_timer = self.set_interval(0.1, self._update_sparkline)
            else:
                # Stop timer
                if self._sparkline_timer:
                    self._sparkline_timer.stop()
                    self._sparkline_timer = None

                text = await self.app.stop_recording()  # type: ignore

                # Hide sparkline, show input
                sparkline.add_class("hidden")
                message_input.remove_class("hidden")

                if text:
                    if message_input.value:
                        if not message_input.value.endswith(" "):
                            message_input.value += " "
                        message_input.value += text
                    else:
                        message_input.value = text
                    input_area.focus_input()

    def on_mount(self) -> None:
        """Set border title on mount."""
        self._update_chat_title()

    def _update_chat_title(self) -> None:
        """Update the chat frame border title."""
        try:
            chat_frame = self.query_one("#chat-frame")
            chat_frame.border_title = (
                f"{constants.BORDER_TITLE_PREFIX}{self.current_session_title}"
            )
        except Exception:
            pass

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        self.query_one("#sidebar", Sidebar).toggle()

    def action_new_chat(self) -> None:
        """Create a new chat session."""
        self.app.run_worker(self.app.create_new_session(), exclusive=False)

    def action_toggle_voice_input(self) -> None:
        """Toggle voice input mode."""
        self.query_one("#input-area", InputArea).toggle_voice_mode()

    def action_toggle_voice_output(self) -> None:
        """Toggle voice output mode."""
        self.voice_output_enabled = not self.voice_output_enabled
        status = (
            constants.STATUS_VOICE_ON
            if self.voice_output_enabled
            else constants.STATUS_VOICE_OFF
        )
        self.query_one("#status-bar", StatusBar).update_status(status)

        # Also update and save the config so Settings reflects this change
        config = get_app_config()
        config.audio.speech_mode = self.voice_output_enabled
        save_app_config(config)

    def action_unfocus_input(self) -> None:
        """Unfocus the input area."""
        self.screen.set_focus(None)

    def action_focus_input(self) -> None:
        """Focus the message input."""
        input_area = self.query_one("#input-area", InputArea)
        input_area.focus_input()

    def action_show_help(self) -> None:
        """Show help screen."""
        self.app.push_screen("help")

    def action_show_settings(self) -> None:
        """Show settings screen."""
        self.app.push_screen("settings")

    def action_focus_sessions(self) -> None:
        """Focus the sessions list in the sidebar."""
        try:
            sidebar = self.query_one("#sidebar", Sidebar)
            if sidebar.has_class("hidden"):
                sidebar.toggle()

            # Find the list view inside the sidebar and focus it
            list_view = sidebar.query_one("#session-list", ListView)
            list_view.focus()
        except Exception:
            pass

    def add_message(
        self, content: str, role: str = "user", timestamp: datetime | None = None
    ):
        """Add a message to the chat area."""
        chat_area = self.query_one("#chat-area", ScrollableContainer)
        msg = MessageItem(content, role=role, timestamp=timestamp)
        chat_area.mount(msg)
        chat_area.scroll_end()

    def clear_messages(self):
        """Clear all messages from chat area."""
        chat_area = self.query_one("#chat-area", ScrollableContainer)
        for child in list(chat_area.children):
            child.remove()

    def set_session_title(self, title: str) -> None:
        """Set the session title in the border."""
        self.current_session_title = title
        self._update_chat_title()

    def show_thinking_indicator(self) -> None:
        """Show the AI thinking indicator in the chat area."""
        chat_area = self.query_one("#chat-area", ScrollableContainer)
        # Only add if not already present
        if not chat_area.query("ThinkingIndicator"):
            indicator = ThinkingIndicator(id="thinking-indicator")
            chat_area.mount(indicator)
            chat_area.scroll_end()

    def hide_thinking_indicator(self) -> None:
        """Remove the AI thinking indicator from the chat area."""
        try:
            indicator = self.query_one("#thinking-indicator", ThinkingIndicator)
            indicator.remove()
        except Exception:
            pass  # Indicator not found, already removed

    def on_input_area_message_submitted(
        self, event: InputArea.MessageSubmitted
    ) -> None:
        """Handle submitted message."""
        self.app.run_worker(self.app.send_message(event.text), exclusive=False)

    def on_sidebar_session_selected(self, event: Sidebar.SessionSelected) -> None:
        """Handle session selection."""
        self.app.run_worker(
            self.app.load_session(event.session_id, event.title), exclusive=False
        )

    def on_sidebar_new_chat_requested(self, event: Sidebar.NewChatRequested) -> None:
        """Handle new chat request."""
        self.app.run_worker(self.app.create_new_session(), exclusive=False)

    def on_sidebar_session_delete_requested(
        self, event: Sidebar.SessionDeleteRequested
    ) -> None:
        """Handle session deletion request."""

        def check_confirm(confirm: bool | None) -> None:
            if confirm:
                self.app.run_worker(
                    self.app.delete_session(event.session_id), exclusive=False
                )

        self.app.push_screen(
            ConfirmationScreen(
                f"Are you sure you want to delete the session '{event.title}'?"
            ),
            check_confirm,
        )
