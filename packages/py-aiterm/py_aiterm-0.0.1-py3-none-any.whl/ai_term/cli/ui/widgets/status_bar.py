"""Status bar footer widget."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from ai_term.cli.ui import constants


class StatusBar(Static):
    """Footer status bar with model, status, and hints."""

    def __init__(
        self,
        provider: str = "UNKNOWN",
        model: str = "UNKNOWN",
        status: str = "Ready",
        hint: str = "Ctrl+K to navigate",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._provider = provider
        self._model = model
        self._status = status
        self._hint = hint

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static(f"{self._provider}", classes="section label")
            yield Static(constants.SEPARATOR, classes="section")
            yield Static(f"{self._model}", classes="section label")
            yield Static(constants.SEPARATOR, classes="section")
            yield Static(f"{self._status}", classes="section value", id="status-text")
            yield Static(constants.SEPARATOR, classes="section")
            yield Static(f"{self._hint}", classes="section hint", id="hint-text")

    def update_model(self, model: str) -> None:
        """Update the model display."""
        self._model = model
        self.refresh()

    def update_status(self, status: str) -> None:
        """Update the status display."""
        self._status = status
        try:
            self.query_one("#status-text", Static).update(status)
        except Exception:
            self.refresh()

    def update_hint(self, hint: str) -> None:
        """Update the hint text."""
        self._hint = hint
        try:
            self.query_one("#hint-text", Static).update(hint)
        except Exception:
            self.refresh()
