from ...core.app import get_app_state


async def handle_help(args: str) -> bool:
    """Show help information."""
    app = get_app_state()
    app.ui.show_help()
    return True
