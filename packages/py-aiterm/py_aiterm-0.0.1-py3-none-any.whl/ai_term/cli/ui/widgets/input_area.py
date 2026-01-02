"""Input area widget with voice toggle."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Button, Input, Label, Sparkline, Static


class InputArea(Static):
    """Input area with "> " prompt prefix and voice toggle."""

    class MessageSubmitted(Message):
        """Message when text is submitted."""

        def __init__(self, text: str):
            super().__init__()
            self.text = text

    class VoiceToggled(Message):
        """Message when voice mode is toggled."""

        def __init__(self, enabled: bool):
            super().__init__()
            self.enabled = enabled

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.voice_active = False

    def compose(self) -> ComposeResult:
        with Horizontal(id="input-box"):
            yield Label("> ", id="prompt-prefix")
            yield Input(placeholder="Type a message...", id="message-input")
            yield Sparkline(
                [], summary_function=max, id="voice-sparkline", classes="hidden"
            )
            yield Button("🎙️", id="voice-btn")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            self.post_message(self.MessageSubmitted(event.value))
            event.input.value = ""

    def toggle_voice_mode(self) -> None:
        """Toggle voice mode and emit event."""
        self.voice_active = not self.voice_active
        self.query_one("#voice-btn").toggle_class("recording")
        self.post_message(self.VoiceToggled(self.voice_active))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "voice-btn":
            self.toggle_voice_mode()

    def focus_input(self):
        """Focus the message input."""
        self.query_one("#message-input", Input).focus()
