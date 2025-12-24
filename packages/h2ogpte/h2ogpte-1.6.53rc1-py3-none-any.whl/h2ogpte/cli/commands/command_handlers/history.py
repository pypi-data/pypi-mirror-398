from datetime import datetime
from rich.table import Table

from ...core.app import get_app_state


async def handle_history(args: str) -> bool:
    """Show command history."""
    app = get_app_state()
    limit = int(args) if args.isdigit() else 20

    history = app.session.history[-limit:]
    if not history:
        app.ui.show_info("No command history")
        return True

    table = Table(title=f"Command History (last {len(history)} entries)")
    table.add_column("#", style="dim")
    table.add_column("Time", style="cyan")
    table.add_column("Command", style="white")
    table.add_column("Status", style="white")

    for i, entry in enumerate(history, 1):
        time_str = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
        status = "[green]✓[/green]" if entry["success"] else "[red]✗[/red]"
        table.add_row(str(i), time_str, entry["command"][:50], status)

    app.console.print(table)
    return True
