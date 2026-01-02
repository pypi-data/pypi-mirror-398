"""Tests for ChatAgent class.

Note: These tests mock langchain dependencies to avoid requiring the full
langchain stack during testing.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock langchain modules before importing agent
sys.modules["langchain_ollama"] = MagicMock()
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.messages"] = MagicMock()


class TestChatAgent:
    """Test cases for ChatAgent."""

    @pytest.fixture
    def mock_app_config(self):
        """Create a mock app config."""
        config = MagicMock()
        config.llm.model = "test-model"
        config.llm.base_url = "http://localhost:11434"
        return config

    @pytest.fixture
    def mock_langchain_messages(self):
        """Create mock langchain message classes."""
        return {
            "AIMessage": MagicMock(),
            "HumanMessage": MagicMock(),
            "SystemMessage": MagicMock(),
        }

    def test_init_creates_llm_with_config(self, mock_app_config):
        """Verify ChatAgent initializes LLM with correct config."""
        with patch("ai_term.cli.config.get_app_config", return_value=mock_app_config):
            with patch.dict(sys.modules, {"langchain_ollama": MagicMock()}):
                mock_chat_ollama = MagicMock()
                sys.modules["langchain_ollama"].ChatOllama = mock_chat_ollama

                # Import after mocking
                from ai_term.cli.core.agent import ChatAgent

                ChatAgent()

                mock_chat_ollama.assert_called_once()
                call_kwargs = mock_chat_ollama.call_args.kwargs
                assert call_kwargs["model"] == "test-model"
                assert call_kwargs["base_url"] == "http://localhost:11434"

    def test_init_with_custom_system_prompt(self, mock_app_config):
        """Verify ChatAgent accepts custom system prompt."""
        with patch("ai_term.cli.config.get_app_config", return_value=mock_app_config):
            with patch.dict(sys.modules, {"langchain_ollama": MagicMock()}):
                from ai_term.cli.core.agent import ChatAgent

                custom_prompt = "You are a helpful coding assistant."
                agent = ChatAgent(system_prompt=custom_prompt)

                assert agent.system_prompt == custom_prompt

    def test_add_tool(self, mock_app_config):
        """Verify tools are added and LLM is bound."""
        with patch("ai_term.cli.config.get_app_config", return_value=mock_app_config):
            with patch.dict(sys.modules, {"langchain_ollama": MagicMock()}):
                from ai_term.cli.core.agent import ChatAgent

                agent = ChatAgent()
                original_llm = agent.llm
                mock_tool = MagicMock()
                mock_bound_llm = MagicMock()
                original_llm.bind_tools = MagicMock(return_value=mock_bound_llm)

                agent.add_tool(mock_tool)

                assert mock_tool in agent.tools
                original_llm.bind_tools.assert_called_once_with([mock_tool])

    @pytest.mark.asyncio
    async def test_chat_returns_response_dict(self, mock_app_config):
        """Verify chat returns properly structured response dict."""
        with patch("ai_term.cli.config.get_app_config", return_value=mock_app_config):
            with patch.dict(sys.modules, {"langchain_ollama": MagicMock()}):
                from ai_term.cli.core.agent import ChatAgent

                agent = ChatAgent()

                mock_response = MagicMock()
                mock_response.content = "Test response content"
                mock_response.tool_calls = None
                agent.llm.ainvoke = AsyncMock(return_value=mock_response)

                messages = [{"role": "user", "content": "Hello"}]
                result = await agent.chat(messages)

                assert isinstance(result, dict)
                assert "content" in result
                assert "tool_calls" in result
                assert result["content"] == "Test response content"
                assert result["tool_calls"] is None

    @pytest.mark.asyncio
    async def test_chat_extracts_tool_calls(self, mock_app_config):
        """Verify tool calls are extracted from response."""
        with patch("ai_term.cli.config.get_app_config", return_value=mock_app_config):
            with patch.dict(sys.modules, {"langchain_ollama": MagicMock()}):
                from ai_term.cli.core.agent import ChatAgent

                agent = ChatAgent()

                mock_response = MagicMock()
                mock_response.content = ""
                mock_response.tool_calls = [
                    {"name": "search", "args": {"query": "test"}, "id": "call_123"}
                ]
                agent.llm.ainvoke = AsyncMock(return_value=mock_response)

                messages = [{"role": "user", "content": "Search for test"}]
                result = await agent.chat(messages)

                assert result["tool_calls"] is not None
                assert len(result["tool_calls"]) == 1
                assert result["tool_calls"][0]["name"] == "search"

    @pytest.mark.asyncio
    async def test_generate_title_returns_short_title(self, mock_app_config):
        """Verify generate_title returns a short title."""
        with patch("ai_term.cli.config.get_app_config", return_value=mock_app_config):
            with patch.dict(sys.modules, {"langchain_ollama": MagicMock()}):
                from ai_term.cli.core.agent import ChatAgent

                agent = ChatAgent()

                mock_response = MagicMock()
                mock_response.content = "Python List Comprehensions"
                agent.llm.ainvoke = AsyncMock(return_value=mock_response)

                title = await agent.generate_title(
                    "How do I use list comprehensions in Python?"
                )

                assert title == "Python List Comprehensions"
                assert len(title.split()) <= 6

    @pytest.mark.asyncio
    async def test_generate_title_truncates_long_titles(self, mock_app_config):
        """Verify long titles are truncated to max words."""
        with patch("ai_term.cli.config.get_app_config", return_value=mock_app_config):
            with patch.dict(sys.modules, {"langchain_ollama": MagicMock()}):
                from ai_term.cli.core.agent import ChatAgent

                agent = ChatAgent()

                mock_response = MagicMock()
                mock_response.content = "This is a very long title with many many words"
                agent.llm.ainvoke = AsyncMock(return_value=mock_response)

                title = await agent.generate_title("Some question")

                words = title.split()
                assert len(words) <= 5

    @pytest.mark.asyncio
    async def test_generate_title_fallback_on_error(self, mock_app_config):
        """Verify 'New Chat' fallback on error."""
        with patch("ai_term.cli.config.get_app_config", return_value=mock_app_config):
            with patch.dict(sys.modules, {"langchain_ollama": MagicMock()}):
                from ai_term.cli.core.agent import ChatAgent

                agent = ChatAgent()
                agent.llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))

                title = await agent.generate_title("Some question")

                assert title == "New Chat"

    @pytest.mark.asyncio
    async def test_generate_title_fallback_on_empty_response(self, mock_app_config):
        """Verify 'New Chat' fallback on empty response."""
        with patch("ai_term.cli.config.get_app_config", return_value=mock_app_config):
            with patch.dict(sys.modules, {"langchain_ollama": MagicMock()}):
                from ai_term.cli.core.agent import ChatAgent

                agent = ChatAgent()

                mock_response = MagicMock()
                mock_response.content = ""
                agent.llm.ainvoke = AsyncMock(return_value=mock_response)

                title = await agent.generate_title("Some question")

                assert title == "New Chat"

    @pytest.mark.asyncio
    async def test_stream_chat_yields_chunks(self, mock_app_config):
        """Verify stream_chat yields content chunks."""
        with patch("ai_term.cli.config.get_app_config", return_value=mock_app_config):
            with patch.dict(sys.modules, {"langchain_ollama": MagicMock()}):
                from ai_term.cli.core.agent import ChatAgent

                agent = ChatAgent()

                # Create async generator mock
                async def mock_astream(messages):
                    chunks = [
                        MagicMock(content="Hello"),
                        MagicMock(content=" "),
                        MagicMock(content="World"),
                    ]
                    for chunk in chunks:
                        yield chunk

                agent.llm.astream = mock_astream

                messages = [{"role": "user", "content": "Hello"}]
                chunks = []
                async for chunk in agent.stream_chat(messages):
                    chunks.append(chunk)

                assert chunks == ["Hello", " ", "World"]

    def test_speech_system_prompt_exists(self, mock_app_config):
        """Verify SPEECH_SYSTEM_PROMPT contains TTS optimization info."""
        with patch("ai_term.cli.config.get_app_config", return_value=mock_app_config):
            with patch.dict(sys.modules, {"langchain_ollama": MagicMock()}):
                from ai_term.cli.core.agent import ChatAgent

                # Check the class constant exists and contains expected keywords
                assert hasattr(ChatAgent, "SPEECH_SYSTEM_PROMPT")
                assert "text-to-speech" in ChatAgent.SPEECH_SYSTEM_PROMPT.lower()
