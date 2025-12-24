from ...core.app import get_app_state


async def handle_clear(args: str) -> bool:
    """Clear screen."""
    app = get_app_state()
    app.ui.clear_screen()
    return True
