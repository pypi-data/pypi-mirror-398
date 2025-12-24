from rich.panel import Panel

from ...core.app import get_app_state


async def handle_exit(args: str) -> bool:
    """Exit the application."""
    app = get_app_state()

    # Check if user provided 'y' as an argument for immediate exit
    if args and args.strip().lower() in ["y", "yes"]:
        # Exit immediately without confirmation
        await app.cleanup()

        app.console.print(
            Panel(
                "[bold cyan]Thank you for using H2OGPTE CLI![/bold cyan]\n"
                "[dim]Session saved automatically[/dim]",
                border_style="cyan",
            )
        )
        return False

    # Otherwise, ask for confirmation
    if app.ui.prompt.confirm("Are you sure you want to exit?", default=False):
        # Clean up
        await app.cleanup()

        app.console.print(
            Panel(
                "[bold cyan]Thank you for using H2OGPTE CLI![/bold cyan]\n"
                "[dim]Session saved automatically[/dim]",
                border_style="cyan",
            )
        )
        return False
    return True
