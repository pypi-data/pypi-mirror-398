"""Tests for MCPManager class."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest


class TestMCPManager:
    """Test cases for MCPManager."""

    @pytest.fixture
    def mock_mcp_config(self):
        """Create a mock MCP config."""
        config = MagicMock()
        config.mcpServers = {
            "test-server": MagicMock(
                command="node", args=["server.js"], env={"DEBUG": "true"}
            ),
            "another-server": MagicMock(
                command="python", args=["-m", "server"], env={}
            ),
        }
        return config

    @pytest.fixture
    def manager(self, mock_mcp_config):
        """Create an MCPManager instance with mocked config."""
        with patch(
            "ai_term.cli.core.mcp_manager.get_mcp_config", return_value=mock_mcp_config
        ):
            from ai_term.cli.core.mcp_manager import MCPManager

            return MCPManager()

    def test_init_loads_config(self, mock_mcp_config):
        """Verify manager loads MCP config on init."""
        with patch(
            "ai_term.cli.core.mcp_manager.get_mcp_config", return_value=mock_mcp_config
        ):
            from ai_term.cli.core.mcp_manager import MCPManager

            manager = MCPManager()

            assert manager.config is mock_mcp_config
            assert manager.processes == {}
            assert manager.tools == []

    def test_get_server_names(self, manager):
        """Verify server names are returned from config."""
        names = manager.get_server_names()

        assert "test-server" in names
        assert "another-server" in names
        assert len(names) == 2

    def test_get_server_names_empty_config(self):
        """Verify empty list for empty config."""
        config = MagicMock()
        config.mcpServers = {}

        with patch("ai_term.cli.core.mcp_manager.get_mcp_config", return_value=config):
            from ai_term.cli.core.mcp_manager import MCPManager

            manager = MCPManager()

            names = manager.get_server_names()

            assert names == []

    @pytest.mark.asyncio
    async def test_start_server_success(self, manager):
        """Verify server process starts successfully."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running

        with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
            result = await manager.start_server("test-server")

            assert result is True
            assert "test-server" in manager.processes
            mock_popen.assert_called_once()

            # Verify command and args
            call_args = mock_popen.call_args
            assert call_args[0][0] == ["node", "server.js"]

    @pytest.mark.asyncio
    async def test_start_server_already_running(self, manager):
        """Verify already running server returns True without restarting."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process is running

        manager.processes["test-server"] = mock_process

        with patch("subprocess.Popen") as mock_popen:
            result = await manager.start_server("test-server")

            assert result is True
            # Popen should not be called since server is already running
            mock_popen.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_server_unknown(self, manager):
        """Verify unknown server returns False."""
        result = await manager.start_server("nonexistent-server")

        assert result is False

    @pytest.mark.asyncio
    async def test_start_server_with_env(self, manager):
        """Verify server starts with environment variables."""
        mock_process = MagicMock()

        with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
            await manager.start_server("test-server")

            call_kwargs = mock_popen.call_args.kwargs
            assert "env" in call_kwargs
            assert call_kwargs["env"]["DEBUG"] == "true"

    @pytest.mark.asyncio
    async def test_start_server_exception(self, manager):
        """Verify exception handling when starting server fails."""
        with patch(
            "subprocess.Popen", side_effect=FileNotFoundError("command not found")
        ):
            result = await manager.start_server("test-server")

            assert result is False
            assert "test-server" not in manager.processes

    @pytest.mark.asyncio
    async def test_stop_server(self, manager):
        """Verify server process is terminated."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Initially running

        manager.processes["test-server"] = mock_process

        await manager.stop_server("test-server")

        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=5)
        assert "test-server" not in manager.processes

    @pytest.mark.asyncio
    async def test_stop_server_already_stopped(self, manager):
        """Verify stopping already-stopped server is safe."""
        mock_process = MagicMock()
        mock_process.poll.return_value = 0  # Process has exited

        manager.processes["test-server"] = mock_process

        await manager.stop_server("test-server")

        # terminate should not be called since process already exited
        mock_process.terminate.assert_not_called()
        assert "test-server" not in manager.processes

    @pytest.mark.asyncio
    async def test_stop_server_timeout_kills(self, manager):
        """Verify server is killed if terminate times out."""
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.wait.side_effect = subprocess.TimeoutExpired(cmd="node", timeout=5)

        manager.processes["test-server"] = mock_process

        await manager.stop_server("test-server")

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_server_not_in_processes(self, manager):
        """Verify stopping non-existent server is safe."""
        # Should not raise an error
        await manager.stop_server("nonexistent-server")

    @pytest.mark.asyncio
    async def test_stop_all(self, manager):
        """Verify all servers are stopped."""
        mock_process1 = MagicMock()
        mock_process1.poll.return_value = None
        mock_process2 = MagicMock()
        mock_process2.poll.return_value = None

        manager.processes = {
            "test-server": mock_process1,
            "another-server": mock_process2,
        }

        await manager.stop_all()

        mock_process1.terminate.assert_called_once()
        mock_process2.terminate.assert_called_once()
        assert len(manager.processes) == 0

    def test_get_tools_returns_list(self, manager):
        """Verify get_tools returns a list."""
        tools = manager.get_tools()

        assert isinstance(tools, list)
        assert tools == []  # Initially empty

    def test_get_tools_with_added_tools(self, manager):
        """Verify get_tools returns added tools."""
        mock_tool = MagicMock()
        manager.tools.append(mock_tool)

        tools = manager.get_tools()

        assert mock_tool in tools

    @pytest.mark.asyncio
    async def test_start_server_sets_stdio_pipes(self, manager):
        """Verify server starts with stdin/stdout/stderr pipes."""
        mock_process = MagicMock()

        with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
            await manager.start_server("test-server")

            call_kwargs = mock_popen.call_args.kwargs
            assert call_kwargs["stdin"] == subprocess.PIPE
            assert call_kwargs["stdout"] == subprocess.PIPE
            assert call_kwargs["stderr"] == subprocess.PIPE
