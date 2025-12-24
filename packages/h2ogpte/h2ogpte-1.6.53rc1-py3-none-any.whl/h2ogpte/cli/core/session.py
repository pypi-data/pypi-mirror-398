import asyncio
import signal
import sys
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from pathlib import Path
import json
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()


class Session:
    """Manages a CLI session with state, history, and interruption handling."""

    def __init__(self):
        self.start_time = datetime.now()
        self.history: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.is_running = False
        self.interrupted = False
        self.current_task: Optional[asyncio.Task] = None
        self.interrupt_handlers: List[Callable] = []
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )

        # Setup interrupt handling
        signal.signal(signal.SIGINT, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        """Handle interrupt signal (Ctrl+C)."""
        self.interrupted = True
        console.print("\n[yellow]⚠[/yellow] Interrupt received. Processing...")

        # Call registered interrupt handlers
        for handler in self.interrupt_handlers:
            try:
                handler()
            except Exception as e:
                console.print(f"[red]Error in interrupt handler: {e}[/red]")

        # Cancel current task if running
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()

    def register_interrupt_handler(self, handler: Callable):
        """Register a handler to be called on interrupt."""
        self.interrupt_handlers.append(handler)

    def add_to_history(self, command: str, result: Any, success: bool = True):
        """Add a command and its result to history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "result": str(result) if result else None,
            "success": success,
        }
        self.history.append(entry)

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a value from session context."""
        return self.context.get(key, default)

    def set_context(self, key: str, value: Any):
        """Set a value in session context."""
        self.context[key] = value

    def clear_context(self):
        """Clear session context."""
        self.context.clear()

    async def run_with_interrupt(self, coro, description: str = "Processing..."):
        """Run a coroutine with interrupt handling."""
        self.is_running = True
        self.interrupted = False

        task_id = self.progress.add_task(description, total=None)

        try:
            with self.progress:
                self.current_task = asyncio.create_task(coro)
                result = await self.current_task
                self.progress.update(task_id, completed=100)
                return result

        except asyncio.CancelledError:
            console.print("[yellow]✗[/yellow] Task cancelled")
            return None

        except Exception as e:
            console.print(f"[red]✗[/red] Error: {e}")
            return None

        finally:
            self.is_running = False
            self.current_task = None
            self.progress.remove_task(task_id)

    def save_session(self, path: Optional[Path] = None):
        """Save session to file."""
        if path is None:
            from .config import settings

            path = (
                settings.data_dir
                / f"session_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
            )

        path.parent.mkdir(parents=True, exist_ok=True)

        session_data = {
            "start_time": self.start_time.isoformat(),
            "history": self.history,
            "context": self.context,
        }

        with open(path, "w") as f:
            json.dump(session_data, f, indent=2, default=str)

        # console.print(f"[green]✓[/green] Session saved to {path}")

    @classmethod
    def load_session(cls, path: Path) -> "Session":
        """Load session from file."""
        with open(path, "r") as f:
            session_data = json.load(f)

        session = cls()
        session.start_time = datetime.fromisoformat(session_data["start_time"])
        session.history = session_data["history"]
        session.context = session_data["context"]

        return session

    def display_status(self):
        """Display current session status."""
        layout = Layout()

        # Session info
        info_table = Table(title="Session Information", show_header=False)
        info_table.add_row("Started", self.start_time.strftime("%Y-%m-%d %H:%M:%S"))
        info_table.add_row(
            "Duration", str(datetime.now() - self.start_time).split(".")[0]
        )
        info_table.add_row("Commands", str(len(self.history)))
        info_table.add_row("Context Items", str(len(self.context)))

        # Recent history
        history_table = Table(title="Recent History")
        history_table.add_column("Time", style="dim")
        history_table.add_column("Command")
        history_table.add_column("Status")

        for entry in self.history[-5:]:
            time_str = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
            status = "[green]✓[/green]" if entry["success"] else "[red]✗[/red]"
            history_table.add_row(time_str, entry["command"][:50], status)

        layout.split_column(Layout(Panel(info_table)), Layout(Panel(history_table)))

        console.print(layout)
