from pathlib import Path
import datetime

from ...core.app import get_app_state


async def handle_session(args: str) -> bool:
    """Create a new chat session with optional name."""
    app = get_app_state()

    if not app.rag_manager.connected:
        app.ui.show_error("Not connected to H2OGPTE. Use /register first.")
        return True

    # Ensure we have a collection first
    if not await app.rag_manager.get_collection_name():
        app.ui.show_info("No active collection. Creating default collection...")
        success = await app.rag_manager.switch_to_collection("CLI-Collection")
        if not success:
            app.ui.show_error("Failed to create collection")
            return True

    # Determine session name
    if not args:
        session_name = f"chat-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    else:
        session_name = args.strip()

    app.ui.show_info(f"Creating new chat session '{session_name}'...")

    # Create the chat session and get the session ID
    session_id = await app.rag_manager.create_chat_session_with_name(session_name)

    if session_id:
        await app.update_status_bar()
        app.ui.show_success(f"Chat session '{session_name}' created and activated")
    else:
        app.ui.show_error("Failed to create chat session")

    return True


async def handle_save(args: str) -> bool:
    """Save session."""
    app = get_app_state()

    if args:
        path = Path(args)
    else:
        path = None

    app.session.save_session(path)
    return True


async def handle_load(args: str) -> bool:
    """Load session."""
    app = get_app_state()

    if not args:
        app.ui.show_error("Please provide a session file path")
        return True

    path = Path(args)
    if not path.exists():
        app.ui.show_error(f"Session file not found: {path}")
        return True

    try:
        from ...core.session import Session

        app.session = Session.load_session(path)
        app.ui.show_success(f"Session loaded from {path}")
    except Exception as e:
        app.ui.show_error(f"Failed to load session: {e}")

    return True
