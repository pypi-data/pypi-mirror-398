"""
Omium TUI Application - Main Textual app for interactive terminal interface.

This provides a rich terminal dashboard for managing Omium workflows and executions.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, DataTable, Label, ProgressBar
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import Screen
from rich.text import Text
from rich.panel import Panel
import asyncio
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any


class ExecutionRow:
    """Data class for execution table rows."""
    def __init__(self, data: dict):
        self.id = data.get("id", "")[:20]
        self.full_id = data.get("id", "")
        self.status = data.get("status", "unknown")
        self.workflow_id = data.get("workflow_id", "")[:25]
        self.created_at = self._format_time(data.get("created_at", ""))
    
    @staticmethod
    def _format_time(timestamp: str) -> str:
        if not timestamp:
            return ""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return timestamp[:16]


class StatusPanel(Static):
    """Widget showing current connection status and stats."""
    
    connected = reactive(False)
    execution_count = reactive(0)
    running_count = reactive(0)
    
    def render(self) -> Panel:
        status_icon = "🟢" if self.connected else "🔴"
        status_text = "Connected" if self.connected else "Disconnected"
        
        content = f"""
{status_icon} {status_text}
📊 Executions: {self.execution_count}
⟳  Running: {self.running_count}
"""
        return Panel(content.strip(), title="Status", border_style="blue")


class ExecutionsTable(DataTable):
    """Interactive table of executions."""
    
    BINDINGS = [
        Binding("enter", "select_execution", "View Details"),
        Binding("r", "refresh", "Refresh"),
        Binding("l", "view_logs", "View Logs"),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executions: List[ExecutionRow] = []
    
    def on_mount(self) -> None:
        self.add_columns("ID", "Status", "Workflow", "Created")
        self.cursor_type = "row"
    
    def update_executions(self, executions: List[dict]) -> None:
        """Update the table with new execution data."""
        self.clear()
        self.executions = [ExecutionRow(e) for e in executions]
        
        for row in self.executions:
            # Format status with style
            if row.status == "completed":
                status = Text("✓ completed", style="green")
            elif row.status == "failed":
                status = Text("✗ failed", style="red")
            elif row.status == "running":
                status = Text("⟳ running", style="blue bold")
            else:
                status = Text(row.status)
            
            self.add_row(row.id, status, row.workflow_id, row.created_at, key=row.full_id)
    
    def get_selected_execution_id(self) -> Optional[str]:
        """Get the ID of the currently selected execution."""
        if self.cursor_row is not None and self.cursor_row < len(self.executions):
            return self.executions[self.cursor_row].full_id
        return None


class WelcomePanel(Static):
    """Welcome panel with keyboard shortcuts."""
    
    def render(self) -> Panel:
        content = """
[bold cyan]Welcome to Omium TUI[/bold cyan]

[dim]Keyboard Shortcuts:[/dim]
  [bold]↑/↓[/bold]  Navigate executions
  [bold]Enter[/bold]  View execution details
  [bold]l[/bold]      View logs
  [bold]r[/bold]      Refresh list
  [bold]n[/bold]      New workflow
  [bold]q[/bold]      Quit

[dim]Fault-tolerant operating system for multi-agent AI[/dim]
"""
        return Panel(content.strip(), title="🚀 Omium", border_style="cyan")


class DashboardScreen(Screen):
    """Main dashboard screen showing executions and status."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("n", "new_workflow", "New Workflow"),
        Binding("?", "show_help", "Help"),
    ]
    
    def __init__(self, execution_engine_url: str = "http://localhost:8000"):
        super().__init__()
        self.execution_engine_url = execution_engine_url
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal():
            with Vertical(id="sidebar"):
                yield WelcomePanel()
                yield StatusPanel(id="status-panel")
            
            with Vertical(id="main-content"):
                yield Label("Recent Executions", id="table-title")
                yield ExecutionsTable(id="executions-table")
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Load initial data when screen mounts."""
        await self.refresh_executions()
        # Start auto-refresh timer
        self.set_interval(5.0, self.refresh_executions)
    
    async def refresh_executions(self) -> None:
        """Fetch and display executions from the execution engine."""
        table = self.query_one("#executions-table", ExecutionsTable)
        status_panel = self.query_one("#status-panel", StatusPanel)
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.execution_engine_url}/api/v1/executions",
                    params={"limit": 20}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    executions = data.get("executions", [])
                    table.update_executions(executions)
                    
                    # Update status panel
                    status_panel.connected = True
                    status_panel.execution_count = data.get("total", len(executions))
                    status_panel.running_count = sum(
                        1 for e in executions if e.get("status") == "running"
                    )
                else:
                    status_panel.connected = False
                    
        except Exception:
            status_panel.connected = False
    
    def action_refresh(self) -> None:
        """Refresh executions list."""
        asyncio.create_task(self.refresh_executions())
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def action_new_workflow(self) -> None:
        """Create a new workflow (placeholder)."""
        self.notify("New workflow feature coming soon!", severity="information")
    
    def action_show_help(self) -> None:
        """Show help."""
        self.notify("Press q to quit, r to refresh, Enter to view details")


class OmiumApp(App):
    """Main Omium TUI Application."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #sidebar {
        width: 35;
        height: 100%;
        dock: left;
        padding: 1;
    }
    
    #main-content {
        width: 1fr;
        height: 100%;
        padding: 1;
    }
    
    #table-title {
        text-style: bold;
        padding: 1 0;
        color: $primary;
    }
    
    ExecutionsTable {
        height: 1fr;
        border: round $primary;
    }
    
    StatusPanel {
        height: auto;
        margin-top: 1;
    }
    
    WelcomePanel {
        height: auto;
    }
    
    DataTable > .datatable--cursor {
        background: $primary 30%;
    }
    """
    
    TITLE = "Omium TUI"
    SUB_TITLE = "Fault-tolerant OS for Multi-Agent AI"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("d", "toggle_dark", "Dark/Light", show=True),
    ]
    
    def __init__(self, execution_engine_url: str = "http://localhost:8000"):
        super().__init__()
        self.execution_engine_url = execution_engine_url
    
    def on_mount(self) -> None:
        """Set up the app on mount."""
        self.push_screen(DashboardScreen(self.execution_engine_url))
    
    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark


def run_tui(execution_engine_url: str = "http://localhost:8000") -> None:
    """Run the Omium TUI application."""
    app = OmiumApp(execution_engine_url=execution_engine_url)
    app.run()
