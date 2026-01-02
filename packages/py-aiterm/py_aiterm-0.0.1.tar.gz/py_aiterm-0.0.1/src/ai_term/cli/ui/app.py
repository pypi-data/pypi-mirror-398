"""Main Textual Application."""

import asyncio

from sqlalchemy import select
from textual.app import App
from textual.binding import Binding

from ai_term.cli.config import get_app_config, save_app_config
from ai_term.cli.core.agent import ChatAgent
from ai_term.cli.core.audio_client import AudioClient
from ai_term.cli.core.audio_player import AudioPlayer
from ai_term.cli.core.audio_recorder import AudioRecorder
from ai_term.cli.core.mcp_manager import MCPManager
from ai_term.cli.db.engine import get_session_factory, init_db
from ai_term.cli.db.models import Message, Session
from ai_term.cli.ui import constants
from ai_term.cli.ui.screens.chat import ChatScreen
from ai_term.cli.ui.screens.help import HelpScreen
from ai_term.cli.ui.screens.settings import SettingsScreen


class ChatApp(App):
    """Interactive CLI Chat Application."""

    TITLE = constants.APP_TITLE
    CSS_PATH = "styles.tcss"

    SCREENS = {
        "chat": ChatScreen,
        "settings": SettingsScreen,
        "help": HelpScreen,
    }

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.config = get_app_config()
        self.agent = ChatAgent()
        self.audio_client = AudioClient()
        self.audio_player = AudioPlayer()
        self.audio_recorder = AudioRecorder()
        self.mcp_manager = MCPManager()
        self.current_session_id: int | None = None
        self.messages: list[dict] = []

    async def action_quit(self) -> None:
        """Quit with proper cleanup."""
        await self.mcp_manager.stop_all()
        self.exit()

    async def on_mount(self) -> None:
        """Initialize app on mount."""
        # Load saved theme from config
        self.theme = self.config.appearance.theme

        # Initialize database
        await init_db()

        # Push chat screen first
        self.push_screen("chat")

        # Load sessions into sidebar (after screen is mounted)
        await self.load_sessions()

    def watch_theme(self, theme: str) -> None:
        """Save theme when it changes."""
        if hasattr(self, "config") and self.config.appearance.theme != theme:
            self.config.appearance.theme = theme
            save_app_config(self.config)

    async def load_sessions(self) -> None:
        """Load all sessions into sidebar."""
        session_factory = get_session_factory()
        async with session_factory() as db_session:
            result = await db_session.execute(
                select(Session).order_by(Session.created_at.desc())
            )
            sessions = result.scalars().all()

            try:
                chat_screen = self.screen
                sidebar = chat_screen.query_one("#sidebar")
                sidebar.clear_sessions()
                for session in sessions:
                    is_active = session.id == self.current_session_id
                    sidebar.add_session(session.id, session.title, is_active=is_active)
            except Exception:
                pass  # Sidebar not yet mounted

    async def delete_session(self, session_id: int) -> None:
        """Delete a chat session."""
        # Remember if we're deleting the current session
        was_current = self.current_session_id == session_id

        session_factory = get_session_factory()
        async with session_factory() as db_session:
            result = await db_session.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                await db_session.delete(session)
                await db_session.commit()

        # Reload sidebar first
        await self.load_sessions()

        # If we deleted the current session, create a new one or clear the chat
        if was_current:
            # Check if there are other sessions to switch to
            session_factory = get_session_factory()
            async with session_factory() as db_session:
                result = await db_session.execute(
                    select(Session).order_by(Session.created_at.desc()).limit(1)
                )
                remaining = result.scalar_one_or_none()

            if remaining:
                # Switch to the most recent remaining session
                await self.load_session(remaining.id, remaining.title)
            else:
                # No sessions left, create a new one
                await self.create_new_session()

    async def create_new_session(self) -> None:
        """Create a new chat session."""
        session_factory = get_session_factory()
        async with session_factory() as db_session:
            new_session = Session(title=constants.DEFAULT_SESSION_TITLE)
            db_session.add(new_session)
            await db_session.commit()
            await db_session.refresh(new_session)

            self.current_session_id = new_session.id
            self.messages = []

            # Update UI
            chat_screen = self.get_screen("chat")
            chat_screen.clear_messages()
            chat_screen.current_session_id = new_session.id

            # Reload sessions
            await self.load_sessions()

    async def load_session(self, session_id: int, session_title: str) -> None:
        """Load an existing session."""
        self.current_session_id = session_id
        self.messages = []

        session_factory = get_session_factory()
        async with session_factory() as db_session:
            result = await db_session.execute(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.timestamp)
            )
            messages = result.scalars().all()

            chat_screen = self.get_screen("chat")
            chat_screen.clear_messages()
            chat_screen.set_session_title(session_title)
            chat_screen.current_session_id = session_id

            for msg in messages:
                self.messages.append({"role": msg.role, "content": msg.content})
                chat_screen.add_message(msg.content, msg.role)

            # Update sidebar to show active session
            try:
                sidebar = chat_screen.query_one("#sidebar")
                sidebar.set_active_session(session_id)
            except Exception:
                pass

    async def send_message(self, text: str) -> None:
        """Send a message and get AI response."""
        is_first_message = not self.current_session_id

        if not self.current_session_id:
            await self.create_new_session()

        # Add user message to UI
        chat_screen = self.get_screen("chat")
        chat_screen.add_message(text, "user")

        # Save user message
        await self.save_message(text, "user")

        # Add to context
        self.messages.append({"role": "user", "content": text})

        # Generate title for new sessions (async, don't block)
        if is_first_message:
            # Run title generation in background
            asyncio.create_task(self._update_session_title(text))

        # Show thinking indicator
        chat_screen.show_thinking_indicator()  # type: ignore[attr-defined]

        # Get AI response
        try:
            # Determine if speech mode is enabled (global setting)
            speech_mode = chat_screen.voice_output_enabled  # type: ignore[attr-defined]

            response = await self.agent.chat(self.messages, speech_mode=speech_mode)
            content = response.get("content", "")
            tool_calls = response.get("tool_calls")

            # Hide thinking indicator
            chat_screen.hide_thinking_indicator()  # type: ignore[attr-defined]

            # Save to DB
            await self.save_message(content, "assistant", tool_calls)
            # Add to UI and history
            chat_screen.add_message(content, "assistant")
            self.messages.append({"role": "assistant", "content": content})

            # Speak if enabled
            if speech_mode and content:
                # Content is already speech-optimized by the agent's system prompt
                audio_bytes = await self.audio_client.speak(content, text)
                await self.audio_player.play(audio_bytes)

        except Exception as e:
            # Hide thinking indicator on error too
            chat_screen.hide_thinking_indicator()  # type: ignore[attr-defined]
            self.notify(f"Error: {e}", severity="error", timeout=5)

    async def start_recording(self) -> None:
        """Start audio recording."""
        self.audio_recorder.start()

    async def stop_recording(self) -> str:
        """
        Stop recording and transcribe.

        Returns:
            Transcribed text.
        """
        audio_bytes = self.audio_recorder.stop()
        if not audio_bytes:
            return ""

        try:
            text = await self.audio_client.transcribe(audio_bytes)
            return text
        except Exception as e:
            self.notify(f"Transcription Error: {e}", severity="error", timeout=5)
            return ""

    async def save_message(
        self, content: str, role: str, tool_calls: list | None = None
    ) -> None:
        """Save message to database."""
        if not self.current_session_id:
            return

        session_factory = get_session_factory()
        async with session_factory() as db_session:
            message = Message(
                session_id=self.current_session_id,
                role=role,
                content=content,
                tool_calls=tool_calls,
            )
            db_session.add(message)
            await db_session.commit()

    async def _update_session_title(self, user_message: str) -> None:
        """Generate and update session title based on user's first message."""
        if not self.current_session_id:
            return

        try:
            title = await self.agent.generate_title(user_message)

            session_factory = get_session_factory()
            async with session_factory() as db_session:
                result = await db_session.execute(
                    select(Session).where(Session.id == self.current_session_id)
                )
                session = result.scalar_one_or_none()
                if session:
                    session.title = title  # type: ignore[assignment]
                    await db_session.commit()

            # Reload sessions to update sidebar
            await self.load_sessions()
        except Exception as e:
            print(f"Error generating title: {e}")


def main():
    """Entry point for the CLI app."""
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    main()
