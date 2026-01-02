"""Tests for database engine module."""

from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from ai_term.cli.db.engine import cleanup_engine


@pytest.fixture(autouse=True)
async def cleanup_database():
    """Ensure database engine is cleaned up after each test."""
    yield
    await cleanup_engine()


class TestGetEngine:
    """Test cases for get_engine function."""

    def test_get_engine_singleton(self):
        """Verify engine is a singleton."""
        with patch("ai_term.cli.db.engine.get_app_config") as mock_config:
            mock_config.return_value.database.url = "sqlite+aiosqlite:///:memory:"

            # Reset the global engine
            import ai_term.cli.db.engine as engine_module

            engine_module._engine = None
            engine_module._session_factory = None

            engine1 = engine_module.get_engine()
            engine2 = engine_module.get_engine()

            assert engine1 is engine2

    def test_get_engine_uses_config_url(self):
        """Verify engine uses URL from config."""
        with patch("ai_term.cli.db.engine.get_app_config") as mock_config:
            mock_config.return_value.database.url = "sqlite+aiosqlite:///test.db"

            import ai_term.cli.db.engine as engine_module

            engine_module._engine = None
            engine_module._session_factory = None

            engine = engine_module.get_engine()

            assert "test.db" in str(engine.url)


class TestGetSessionFactory:
    """Test cases for get_session_factory function."""

    def test_get_session_factory_returns_sessionmaker(self):
        """Verify session factory returns correct type."""
        with patch("ai_term.cli.db.engine.get_app_config") as mock_config:
            mock_config.return_value.database.url = "sqlite+aiosqlite:///:memory:"

            import ai_term.cli.db.engine as engine_module

            engine_module._engine = None
            engine_module._session_factory = None

            factory = engine_module.get_session_factory()

            assert isinstance(factory, async_sessionmaker)

    def test_get_session_factory_singleton(self):
        """Verify session factory is a singleton."""
        with patch("ai_term.cli.db.engine.get_app_config") as mock_config:
            mock_config.return_value.database.url = "sqlite+aiosqlite:///:memory:"

            import ai_term.cli.db.engine as engine_module

            engine_module._engine = None
            engine_module._session_factory = None

            factory1 = engine_module.get_session_factory()
            factory2 = engine_module.get_session_factory()

            assert factory1 is factory2


class TestInitDb:
    """Test cases for init_db function."""

    @pytest.mark.asyncio
    async def test_init_db_creates_tables(self):
        """Verify init_db() creates all tables."""
        with patch("ai_term.cli.db.engine.get_app_config") as mock_config:
            mock_config.return_value.database.url = "sqlite+aiosqlite:///:memory:"

            import ai_term.cli.db.engine as engine_module

            engine_module._engine = None
            engine_module._session_factory = None

            await engine_module.init_db()

            engine = engine_module.get_engine()

            # Verify tables exist by checking metadata

            async with engine.connect() as conn:
                # Get table names
                def get_tables(connection):
                    from sqlalchemy import inspect

                    inspector = inspect(connection)
                    return inspector.get_table_names()

                tables = await conn.run_sync(get_tables)

                assert "sessions" in tables
                assert "messages" in tables

    @pytest.mark.asyncio
    async def test_init_db_idempotent(self):
        """Verify init_db() is idempotent (can be called multiple times)."""
        with patch("ai_term.cli.db.engine.get_app_config") as mock_config:
            mock_config.return_value.database.url = "sqlite+aiosqlite:///:memory:"

            import ai_term.cli.db.engine as engine_module

            engine_module._engine = None
            engine_module._session_factory = None

            # Call init_db twice
            await engine_module.init_db()
            await engine_module.init_db()  # Should not raise an error

            # Tables should still exist
            engine = engine_module.get_engine()

            async with engine.connect() as conn:

                def get_tables(connection):
                    from sqlalchemy import inspect

                    inspector = inspect(connection)
                    return inspector.get_table_names()

                tables = await conn.run_sync(get_tables)

                assert "sessions" in tables
