#!/usr/bin/env python
"""TUI chat with OpenCode.

Run with:
    uv run python examples/opencode_chat.py
"""

from textual.app import App, ComposeResult

from textual_chat import Chat


class OpenCodeChatApp(App):
    """Chat app that talks to OpenCode."""

    CSS = """
    Screen {
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        yield Chat(
            model="opencode",
            adapter="acp",
            show_token_usage=False,
            show_model_selector=False,
        )


if __name__ == "__main__":
    OpenCodeChatApp().run()
