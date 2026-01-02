#!/usr/bin/env python
"""TUI chat with Claude Code.

Run with:
    uv run python examples/claude_code_chat.py
"""

from textual.app import App, ComposeResult

from textual_chat import Chat


class ClaudeCodeChatApp(App):
    """Chat app that talks to Claude Code."""

    CSS = """
    Screen {
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        yield Chat(
            model="claude-code-acp",
            adapter="acp",
            show_token_usage=False,
            show_model_selector=False,
        )


if __name__ == "__main__":
    ClaudeCodeChatApp().run()
