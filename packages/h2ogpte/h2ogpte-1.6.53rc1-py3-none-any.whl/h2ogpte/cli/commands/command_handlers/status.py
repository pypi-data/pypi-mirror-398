from rich.table import Table

from ...core.app import get_app_state


async def handle_status(args: str) -> bool:
    """Show session status."""
    app = get_app_state()

    # Show session status
    app.session.display_status()

    # Show connection status
    status_table = Table(title="Connection Status", show_header=False)
    status_table.add_column("Service", style="cyan")
    status_table.add_column("Status", style="white")

    rag_status = (
        "[green]Connected[/green]"
        if app.rag_manager.connected
        else "[red]Disconnected[/red]"
    )
    agent_status = (
        "[green]Connected[/green]"
        if app.agent_manager.connected
        else "[red]Disconnected[/red]"
    )

    status_table.add_row("RAG System", rag_status)
    status_table.add_row("Agent System", agent_status)

    app.console.print(status_table)
    return True
