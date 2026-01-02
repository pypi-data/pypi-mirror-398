"""Help screen with keyboard shortcuts."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Link, Markdown

HELLO_MARKDOWN = """
# **`Hello!`**

This is **`ai_term`**, a command-line interface for interacting with AI Assistants.
Think of it like Claude Desktop, but for the command line 💻
Feel free to open an issue on GitHub if you have any questions or feedback or even
would like to contribute!
"""

HELP_MARKDOWN = """
# Shortcuts

## General
- **`Ctrl+N`** : Start a new chat session
- **`Ctrl+S`** : Toggle the sidebar
- **`Ctrl+Q`** : Quit the application
- **`?`**      : Show this help screen

## Settings
- **`Ctrl+,`** : Open settings

## Voice Controls
- **`Ctrl+V`**       : Toggle voice input
- **`Ctrl+Shift+V`** : Toggle voice output (TTS)
"""


class HelpScreen(ModalScreen):
    """Help and keyboard shortcuts screen."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("question_mark", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="help-container"):
            yield Markdown(HELLO_MARKDOWN)
            yield Link("GitHub", url="https://github.com/vsaravind01/ai-term")
            yield Markdown(HELP_MARKDOWN)
            yield Button(
                "Close",
                variant="primary",
                classes="back-btn",
                id="close-btn",
                compact=True,
            )

    def on_mount(self) -> None:
        """Set border title on mount."""
        container = self.query_one(".help-container")
        container.border_title = "Help & Shortcuts"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-btn":
            self.app.pop_screen()

    def action_close(self) -> None:
        self.app.pop_screen()
