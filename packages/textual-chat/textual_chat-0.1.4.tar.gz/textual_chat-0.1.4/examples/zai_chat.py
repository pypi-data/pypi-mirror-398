#!/usr/bin/env python
"""TUI chat with ZAI.

Run with:
    uv run python examples/zai_chat.py
"""

from textual.app import App, ComposeResult

from textual_chat import Chat


class ZAIChatApp(App):
    """Chat app that talks to ZAI."""

    CSS = """
    Screen {
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        yield Chat(
            model="openai/GLM-4.5-air",
            show_token_usage=False,
            show_model_selector=False,
        )


if __name__ == "__main__":
    ZAIChatApp().run()
