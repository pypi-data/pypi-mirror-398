from ...core.app import get_app_state


async def handle_disconnect(args: str) -> bool:
    """Disconnect from H2OGPTE and clear saved credentials."""
    app = get_app_state()

    if not app.rag_manager.connected:
        app.ui.show_info("Already disconnected from H2OGPTE")
        return True

    # Confirm disconnection
    if not app.ui.prompt.confirm(
        "Disconnect and clear saved credentials?", default=False
    ):
        app.ui.show_info("Disconnection cancelled")
        return True

    # Disconnect from RAG manager
    await app.rag_manager.close()

    # Clear credentials from settings
    app.settings.rag.endpoint = ""
    app.settings.rag.api_key = ""
    app.settings.rag.collection_name = "default"

    # Save cleared settings
    app.settings.save()

    # Update status bar
    await app.update_status_bar()

    app.ui.show_success("Disconnected and credentials cleared")
    app.ui.show_info("Use /register to connect again")

    return True
