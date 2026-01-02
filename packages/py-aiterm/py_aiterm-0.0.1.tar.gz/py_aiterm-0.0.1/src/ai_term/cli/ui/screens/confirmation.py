"""Confirmation modal screen."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmationScreen(ModalScreen[bool]):
    """A screen for confirmation dialogs."""

    BINDINGS = [
        Binding("y", "confirm_yes", "Yes", show=False),
        Binding("n", "confirm_no", "No", show=False),
        Binding("escape", "confirm_no", "Cancel", show=False),
    ]

    def __init__(self, message: str, **kwargs):
        super().__init__(**kwargs)
        self.message = message

    def compose(self) -> ComposeResult:
        dialog = Grid(
            Label(self.message, id="question"),
            Button("Yes", variant="error", id="yes", compact=True),
            Button("No", variant="primary", id="no", compact=True),
            id="dialog",
        )
        dialog.border_title = "Confirm [Y/N]"
        yield dialog

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm_yes(self) -> None:
        """Confirm with Yes."""
        self.dismiss(True)

    def action_confirm_no(self) -> None:
        """Confirm with No."""
        self.dismiss(False)
