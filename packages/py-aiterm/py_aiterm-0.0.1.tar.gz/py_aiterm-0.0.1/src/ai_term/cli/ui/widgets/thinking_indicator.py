"""Thinking indicator widget for AI response loading."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, LoadingIndicator


class ThinkingIndicator(Vertical):
    """AI thinking indicator styled like an assistant message."""

    DEFAULT_CSS = """
    ThinkingIndicator {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        padding: 0 1;
        align: left top;
    }

    ThinkingIndicator .message-header {
        width: auto;
        height: 1;
        margin-bottom: 0;
        margin-left: 1;
    }

    ThinkingIndicator .elapsed-time {
        color: $text-muted;
        margin-right: 1;
    }

    ThinkingIndicator .role-label {
        text-style: bold;
        color: $success;
    }

    ThinkingIndicator .thinking-content {
        width: 20;
        height: 3;
        padding: 0 1;
        border: round $success;
        background: $surface;
        align: center middle;
    }

    ThinkingIndicator .thinking-content LoadingIndicator {
        width: 100%;
        height: 1;
        color: $success;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = datetime.now()
        self._timer = None

    def compose(self) -> ComposeResult:
        # Message header with elapsed time
        with Horizontal(classes="message-header"):
            yield Label("0s", id="elapsed-label", classes="elapsed-time")
            yield Label("ASSISTANT", classes="role-label")

        # Thinking content box - use Vertical instead of Horizontal
        with Vertical(classes="thinking-content"):
            yield LoadingIndicator()

    def on_mount(self) -> None:
        """Start the elapsed time timer."""
        self._timer = self.set_interval(1.0, self._update_elapsed)

    def _update_elapsed(self) -> None:
        """Update the elapsed time display."""
        elapsed = (datetime.now() - self.start_time).seconds
        try:
            label = self.query_one("#elapsed-label", Label)
            label.update(f"{elapsed}s")
        except Exception:
            pass

    def on_unmount(self) -> None:
        """Stop the timer when removed."""
        if self._timer:
            self._timer.stop()
