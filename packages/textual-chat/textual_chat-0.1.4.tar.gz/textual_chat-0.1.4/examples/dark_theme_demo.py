#!/usr/bin/env python3
"""Demo showing darker background theme for chat messages - theme-aware."""

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static, Footer

DEMO_CSS = """
Screen {
    background: $surface;
}

#chat-container {
    height: 1fr;
    padding: 1;
    background: $surface;
}

.message {
    width: 100%;
    padding: 1;
    margin: 0 0 1 0;
    background: $surface-lighten-1;  /* Messages slightly lighter than background */
    border: round $surface-lighten-2;
}

.message.user {
    background: $primary-background;
    border: round $primary;
}

.message.assistant {
    background: $surface-lighten-1;
    border: round $accent;
}

#info {
    dock: bottom;
    height: 3;
    padding: 1;
    color: $text-muted;
}
"""


class DarkThemeDemo(App):
    CSS = DEMO_CSS
    BINDINGS = [("q", "quit", "Quit"), ("d", "toggle_dark", "Toggle dark/light")]

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="chat-container"):
            yield Static("How do I reverse a list in Python?", classes="message user")
            yield Static(
                "You can reverse a list in Python using several methods:\n\n"
                "1. `my_list.reverse()` - modifies in place\n"
                "2. `my_list[::-1]` - creates a new reversed list\n"
                "3. `list(reversed(my_list))` - also creates new list",
                classes="message assistant",
            )
            yield Static("What about sorting?", classes="message user")
            yield Static(
                "For sorting:\n\n"
                "1. `my_list.sort()` - sorts in place\n"
                "2. `sorted(my_list)` - returns new sorted list\n\n"
                "Both accept `reverse=True` for descending order.",
                classes="message assistant",
            )
        yield Static(
            "Press 'd' to toggle dark/light theme",
            id="info",
        )
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"


if __name__ == "__main__":
    DarkThemeDemo().run()
