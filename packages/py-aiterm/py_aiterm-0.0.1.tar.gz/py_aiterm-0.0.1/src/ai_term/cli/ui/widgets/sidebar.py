"""Sidebar widget for session management."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Label, ListItem, ListView, Static


class SessionItem(ListItem):
    """A session item in the sidebar."""

    class DeleteClicked(Message):
        """Message when delete is clicked on a session."""

        def __init__(self, session_id: int):
            super().__init__()
            self.session_id = session_id

    def __init__(self, session_id: int, title: str, is_active: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.session_id = session_id
        self.title = title
        self._is_active = is_active

    def compose(self) -> ComposeResult:
        # Arrow indicator for active session
        with Horizontal(classes="session-item"):
            yield Label("[-]", id="delete-btn", classes="delete-btn")
            yield Label(self.title, id="session-label")

    def set_active(self, active: bool) -> None:
        """Update the active state and refresh the label."""
        self._is_active = active
        if active:
            self.add_class("-active")
        else:
            self.remove_class("-active")
        # Update the label text
        try:
            label = self.query_one("#session-label", Label)
            prefix = "▶ " if active else "  "
            label.update(f"{prefix}{self.title}")
        except Exception:
            pass

    def on_click(self, event) -> None:
        """Handle click on the session item."""
        # Check if the delete button was clicked using the widget attribute
        # The widget attribute contains the widget that was actually clicked
        if hasattr(event, "widget") and event.widget is not None:
            if event.widget.id == "delete-btn":
                self.post_message(self.DeleteClicked(self.session_id))
                event.stop()
                return
        # Fallback: check by querying
        try:
            delete_btn = self.query_one("#delete-btn", Label)
            if delete_btn.region.contains(event.x, event.y):
                self.post_message(self.DeleteClicked(self.session_id))
                event.stop()
        except Exception:
            pass


class Sidebar(Static):
    """Sidebar for session management."""

    class SessionSelected(Message):
        """Message when a session is selected."""

        def __init__(self, session_id: int, title: str):
            super().__init__()
            self.session_id = session_id
            self.title = title

    class SessionDeleteRequested(Message):
        """Message when a session delete is requested."""

        def __init__(self, session_id: int, title: str):
            super().__init__()
            self.session_id = session_id
            self.title = title

    class NewChatRequested(Message):
        """Message when new chat is requested."""

        pass

    BINDINGS = [
        Binding("minus", "delete_selected_session", "Delete Session", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield ListView(id="session-list")
            yield Button("[ + New Chat ]", id="new-chat-btn")

    def on_mount(self) -> None:
        """Set border title on mount."""
        self.border_title = "SESSIONS"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-chat-btn":
            self.post_message(self.NewChatRequested())
            event.stop()

    def on_session_item_delete_clicked(self, event: SessionItem.DeleteClicked) -> None:
        """Handle delete click from SessionItem."""
        # Find the session item to get its title
        for item in self.query(SessionItem):
            if item.session_id == event.session_id:
                self.post_message(
                    self.SessionDeleteRequested(event.session_id, item.title)
                )
                event.stop()
                return

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, SessionItem):
            self.post_message(
                self.SessionSelected(event.item.session_id, event.item.title)
            )

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Handle list view highlight to show delete button."""
        # Remove highlighted class from all items
        for item in self.query(SessionItem):
            item.remove_class("-highlighted")

        # Add to current item
        if isinstance(event.item, SessionItem):
            event.item.add_class("-highlighted")

    def on_blur(self, event) -> None:
        """Handle when sidebar or its children lose focus."""
        # Check if focus moved outside the session list
        try:
            list_view = self.query_one("#session-list", ListView)
            # If the list view doesn't have focus, remove all highlights
            if not list_view.has_focus:
                for item in self.query(SessionItem):
                    item.remove_class("-highlighted")
        except Exception:
            pass

    def add_session(self, session_id: int, title: str, is_active: bool = False):
        """Add a session to the list."""
        list_view = self.query_one("#session-list", ListView)
        item = SessionItem(session_id, title, is_active=is_active)
        list_view.append(item)

    def set_active_session(self, session_id: int) -> None:
        """Mark a session as active and update the UI."""
        for item in self.query(SessionItem):
            item.set_active(item.session_id == session_id)

    def clear_sessions(self):
        """Clear all sessions from the list."""
        list_view = self.query_one("#session-list", ListView)
        list_view.clear()

    def toggle(self):
        """Toggle sidebar visibility."""
        self.toggle_class("hidden")

    def action_delete_selected_session(self) -> None:
        """Delete the currently selected/highlighted session."""
        list_view = self.query_one("#session-list", ListView)
        if list_view.highlighted_child:
            item = list_view.highlighted_child
            if isinstance(item, SessionItem):
                self.post_message(
                    self.SessionDeleteRequested(item.session_id, item.title)
                )
