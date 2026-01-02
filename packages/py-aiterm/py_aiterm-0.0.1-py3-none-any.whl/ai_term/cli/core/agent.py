"""LangChain Agent with Ollama support."""

from typing import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from ai_term.cli.config import get_app_config


class ChatAgent:
    """Chat agent using LangChain and Ollama."""

    SPEECH_SYSTEM_PROMPT = (
        "You are a helpful AI assistant. Your responses will be read aloud by a "
        "text-to-speech system.\n\n"
        "CRITICAL OUTPUT RULES:\n"
        "- NO markdown: Avoid **, *, `, #, >, -, |, or any formatting symbols\n"
        "- NO emojis or special unicode characters\n"
        "- NO bullet points or numbered lists with symbols; use natural prose instead\n"
        "- NO code blocks; describe code concepts verbally\n"
        "- NO tables; present tabular data as flowing sentences\n\n"
        "SPEECH OPTIMIZATION:\n"
        "- Use short, clear sentences that are easy to follow when heard\n"
        "- Add natural pauses with commas and periods\n"
        "IMPORTANT: Previous messages in this conversation may contain markdown or "
        "formatting. Ignore that formatting in your response. Your output must be "
        "plain, speakable text only."
    )

    def __init__(self, system_prompt: str = "You are a helpful AI assistant."):
        config = get_app_config()
        self.llm = ChatOllama(
            model=config.llm.model,
            base_url=config.llm.base_url,
            temperature=0.7,
        )
        self.system_prompt = system_prompt
        self.tools = []

    def add_tool(self, tool):
        """Add a tool to the agent."""
        self.tools.append(tool)
        self.llm = self.llm.bind_tools(self.tools)

    async def chat(self, messages: list[dict], speech_mode: bool = False) -> dict:
        """
        Send messages to the LLM and get a response.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            speech_mode: Whether to optimize output for text-to-speech.

        Returns:
            Response dict with 'content' and optionally 'tool_calls'.
        """
        # Convert to LangChain message format
        system_prompt = self.SPEECH_SYSTEM_PROMPT if speech_mode else self.system_prompt
        lc_messages = [SystemMessage(content=system_prompt)]

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))

        # Get response from LLM
        response = await self.llm.ainvoke(lc_messages)

        result = {"content": response.content, "tool_calls": None}

        # Check for tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            result["tool_calls"] = [
                {"name": tc["name"], "args": tc["args"], "id": tc.get("id")}
                for tc in response.tool_calls
            ]

        return result

    async def stream_chat(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        """
        Stream response from LLM.

        Args:
            messages: List of message dicts.

        Yields:
            str: Chunks of response content.
        """
        lc_messages = [SystemMessage(content=self.system_prompt)]

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))

        async for chunk in self.llm.astream(lc_messages):
            if chunk.content:
                yield str(chunk.content)

    async def generate_title(self, user_message: str) -> str:
        """
        Generate a short title (3-5 words) for a chat session.

        Args:
            user_message: The user's first message.

        Returns:
            A short descriptive title.
        """
        system_prompt = (
            "Generate a very short title (3-5 words max) for a chat session "
            "based on the user's message. Output ONLY the title, nothing else. "
            "No quotes, no punctuation at the end, no explanation."
        )

        lc_messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        try:
            response = await self.llm.ainvoke(lc_messages)
            title = str(response.content).strip()
            # Ensure it's not too long
            words = title.split()
            if len(words) > 6:
                title = " ".join(words[:5])
            return title or "New Chat"
        except Exception:
            return "New Chat"
