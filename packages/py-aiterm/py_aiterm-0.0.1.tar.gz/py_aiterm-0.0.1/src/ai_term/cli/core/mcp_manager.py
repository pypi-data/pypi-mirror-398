"""MCP Server Manager."""

import subprocess
from typing import Any

from ai_term.cli.config import get_mcp_config


class MCPManager:
    """Manages MCP server connections and tool discovery."""

    def __init__(self):
        self.config = get_mcp_config()
        self.processes: dict[str, subprocess.Popen] = {}
        self.tools: list[Any] = []

    def get_server_names(self) -> list[str]:
        """Get list of configured MCP server names."""
        return list(self.config.mcpServers.keys())

    async def start_server(self, name: str) -> bool:
        """
        Start an MCP server by name.

        Args:
            name: Server name from config.

        Returns:
            True if started successfully.
        """
        if name not in self.config.mcpServers:
            return False

        if name in self.processes and self.processes[name].poll() is None:
            return True  # Already running

        server_config = self.config.mcpServers[name]

        env = dict(server_config.env)

        try:
            process = subprocess.Popen(
                [server_config.command] + server_config.args,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.processes[name] = process
            return True
        except Exception as e:
            print(f"Failed to start MCP server {name}: {e}")
            return False

    async def stop_server(self, name: str):
        """Stop an MCP server."""
        if name in self.processes:
            proc = self.processes[name]
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            del self.processes[name]

    async def stop_all(self):
        """Stop all running MCP servers."""
        for name in list(self.processes.keys()):
            await self.stop_server(name)

    def get_tools(self) -> list[Any]:
        """Get tools from all connected MCP servers."""
        # TODO: Implement MCP protocol communication to discover tools
        # For now, return empty list. Will be populated when servers are connected.
        return self.tools
