#!/usr/bin/env python3
"""
Example of using the PlanPane widget with a "hello world" demonstration.
"""

import asyncio
from textual.app import App
from textual.widgets import Header, Footer
from textual.containers import Horizontal, Vertical
from textual_chat.widgets import PlanPane


class HelloWorldPlanApp(App):
    """A simple app to demonstrate the PlanPane with hello world."""
    
    def compose(self) -> ComposeResult:
        """Compose the application."""
        yield Header()
        yield Horizontal(
            Vertical(id="main-content"),
            PlanPane(id="plan-pane"),
        )
        yield Footer()
    
    async def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Show the plan pane
        plan_pane = self.query_one("#plan-pane", PlanPane)
        plan_pane.show()
        
        # Create a simple hello world plan
        hello_plan = [
            {"content": "Say Hello to the world", "status": "pending", "priority": "high"},
            {"content": "Display greeting message", "status": "pending", "priority": "medium"},
            {"content": "Add some color and styling", "status": "pending", "priority": "low"},
        ]
        
        # Update the plan with initial entries
        await plan_pane.update_plan(hello_plan)
        
        # Simulate progress - mark first item as in progress
        await asyncio.sleep(1)
        hello_plan[0]["status"] = "in_progress"
        await plan_pane.update_plan(hello_plan)
        
        # Simulate completion - mark first item as completed
        await asyncio.sleep(1)
        hello_plan[0]["status"] = "completed"
        hello_plan[1]["status"] = "in_progress"
        await plan_pane.update_plan(hello_plan)
        
        # Complete all items
        await asyncio.sleep(1)
        for item in hello_plan:
            item["status"] = "completed"
        await plan_pane.update_plan(hello_plan)
        
        # Add a final message
        await asyncio.sleep(1)
        final_plan = hello_plan + [
            {"content": "🌍 Hello World Plan Complete!", "status": "completed", "priority": "high"}
        ]
        await plan_pane.update_plan(final_plan)


if __name__ == "__main__":
    app = HelloWorldPlanApp()
    app.run()