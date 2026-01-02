"""Tests for ACP adapter configuration."""

import pytest

from textual_chat import Chat


class TestACPAdapterConfig:
    """Unit tests for ACP adapter configuration."""

    def test_acp_rejects_system_prompt(self) -> None:
        """ACP adapter raises ValueError when system prompt is provided."""
        with pytest.raises(ValueError) as exc_info:
            Chat(adapter="acp", system="You are a helpful assistant.")

        assert "System prompts are not supported with the ACP adapter" in str(
            exc_info.value
        )

    def test_acp_accepts_no_system_prompt(self) -> None:
        """ACP adapter works when no system prompt is provided."""
        chat = Chat(adapter="acp", model="test-agent")
        assert chat._adapter.__name__ == "textual_chat.llm_adapter_acp"

    def test_litellm_allows_system_prompt(self) -> None:
        """LiteLLM adapter accepts system prompts."""
        chat = Chat(adapter="litellm", system="You are a helpful assistant.")
        assert chat.system == "You are a helpful assistant."
