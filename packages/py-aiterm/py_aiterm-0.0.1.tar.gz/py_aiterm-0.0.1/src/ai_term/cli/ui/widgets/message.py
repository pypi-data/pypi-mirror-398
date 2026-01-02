"""Message widget for chat display."""

from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Label, Markdown, Static


class MessageItem(Vertical):
    """A single chat message with timestamp and markdown content."""

    def __init__(
        self,
        content: str,
        role: str = "user",
        timestamp: datetime | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.content = content
        self.role = role
        self.timestamp = timestamp or datetime.now()

        # Add class for role-based styling
        if self.role == "user":
            self.add_class("role-user")
        else:
            self.add_class("role-assistant")

    def compose(self) -> ComposeResult:
        with Horizontal(classes="message-header"):
            # Timestamp
            time_str = self.timestamp.strftime("%I:%M %p")
            yield Label(time_str, classes="timestamp")

            # Role Label
            role_display = "USER" if self.role == "user" else "ASSISTANT"
            yield Label(role_display, classes="role-label")

        # Message Content
        yield Markdown(self.content, classes="message-content")


class MCPAlert(Static):
    """MCP tool activity alert box."""

    def __init__(self, tool_name: str, description: str, **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.description = description
        self.add_class("mcp-alert")

    def compose(self) -> ComposeResult:
        yield Static("🔧 MCP ACTIVITY", classes="title")
        yield Static(f"⚡ {self.description}", classes="content")

    def on_mount(self) -> None:
        self.border_title = "🔧 MCP ACTIVITY"
