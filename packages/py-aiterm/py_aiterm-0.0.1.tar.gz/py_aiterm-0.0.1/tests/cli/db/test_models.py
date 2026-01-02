"""Tests for database ORM models."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as SQLSession

from ai_term.cli.db.models import Base, Message, Session


class TestSession:
    """Test cases for Session model."""

    def test_session_creation(self):
        """Verify Session model creates correctly."""
        session = Session(title="Test Chat")

        assert session.title == "Test Chat"
        assert session.messages == []

    def test_session_default_title_column(self):
        """Verify default title Column is configured with 'New Chat'."""
        # SQLAlchemy Column defaults are applied on INSERT, not object creation
        # So we verify the Column has the correct default
        from ai_term.cli.db.models import Session

        title_column = Session.__table__.columns["title"]
        assert title_column.default.arg == "New Chat"

    def test_session_repr(self):
        """Verify Session.__repr__ format."""
        session = Session(id=1, title="Test Chat")

        repr_str = repr(session)

        assert "Session" in repr_str
        assert "id=1" in repr_str
        assert "Test Chat" in repr_str

    def test_session_created_at_default(self):
        """Verify created_at defaults to current time."""
        # SQLAlchemy Column defaults are applied on INSERT, not object creation
        # So we verify the Column has the correct default configuration
        created_at_column = Session.__table__.columns["created_at"]
        assert created_at_column.default.arg.__name__ == "utcnow"


class TestMessage:
    """Test cases for Message model."""

    def test_message_creation(self):
        """Verify Message model creates correctly."""
        message = Message(session_id=1, role="user", content="Hello, world!")

        assert message.session_id == 1
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.tool_calls is None

    def test_message_with_tool_calls(self):
        """Verify Message can store tool calls as JSON."""
        tool_calls = [{"name": "search", "args": {"query": "test"}}]
        message = Message(
            session_id=1, role="assistant", content="", tool_calls=tool_calls
        )

        assert message.tool_calls == tool_calls

    def test_message_repr(self):
        """Verify Message.__repr__ format."""
        message = Message(
            id=1, role="user", content="This is a test message that is quite long"
        )

        repr_str = repr(message)

        assert "Message" in repr_str
        assert "id=1" in repr_str
        assert "role='user'" in repr_str
        # Content should be truncated
        assert "..." in repr_str

    def test_message_roles(self):
        """Verify different message roles are supported."""
        roles = ["user", "assistant", "system", "tool"]

        for role in roles:
            message = Message(session_id=1, role=role, content="test")
            assert message.role == role


class TestSessionMessageRelationship:
    """Test cases for Session-Message relationship."""

    @pytest.fixture
    def in_memory_db(self):
        """Create an in-memory SQLite database."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine

    def test_session_message_relationship(self, in_memory_db):
        """Verify relationship between Session and Messages."""
        with SQLSession(in_memory_db) as db_session:
            # Create a session
            chat_session = Session(title="Test Chat")
            db_session.add(chat_session)
            db_session.commit()

            # Create messages
            msg1 = Message(session_id=chat_session.id, role="user", content="Hello")
            msg2 = Message(
                session_id=chat_session.id, role="assistant", content="Hi there!"
            )
            db_session.add_all([msg1, msg2])
            db_session.commit()

            # Refresh to load relationship
            db_session.refresh(chat_session)

            # Verify relationship
            assert len(chat_session.messages) == 2
            assert chat_session.messages[0].content == "Hello"
            assert chat_session.messages[1].content == "Hi there!"

    def test_cascade_delete(self, in_memory_db):
        """Verify messages are deleted when session is deleted."""
        with SQLSession(in_memory_db) as db_session:
            # Create a session with messages
            chat_session = Session(title="Test Chat")
            db_session.add(chat_session)
            db_session.commit()

            msg = Message(session_id=chat_session.id, role="user", content="Hello")
            db_session.add(msg)
            db_session.commit()

            session_id = chat_session.id

            # Delete the session
            db_session.delete(chat_session)
            db_session.commit()

            # Verify messages are also deleted
            remaining = db_session.query(Message).filter_by(session_id=session_id).all()
            assert len(remaining) == 0

    def test_message_back_populates_session(self, in_memory_db):
        """Verify message.session back-populates correctly."""
        with SQLSession(in_memory_db) as db_session:
            chat_session = Session(title="Test Chat")
            db_session.add(chat_session)
            db_session.commit()

            msg = Message(session_id=chat_session.id, role="user", content="Hello")
            db_session.add(msg)
            db_session.commit()

            db_session.refresh(msg)

            assert msg.session is not None
            assert msg.session.title == "Test Chat"
