"""Simple hello world plan demonstration."""

from textual.app import App, ComposeResult
from textual.widgets import Footer

from textual_chat import Chat


class HelloPlanApp(App):
    """Simple app to demonstrate the plan pane."""
    
    BINDINGS = [("ctrl+q", "quit", "Quit")]
    
    def compose(self) -> ComposeResult:
        """Compose the application."""
        # Create a chat instance with thinking enabled to show plans
        chat = Chat(
            model="claude-sonnet-4-20250514",  # Claude models work well with thinking/planning
            thinking=True,  # This enables the plan pane
        )
        
        yield chat
        yield Footer()


if __name__ == "__main__":
    app = HelloPlanApp()
    app.run()