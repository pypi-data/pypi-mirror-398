from ...core.app import get_app_state


async def handle_create_collection(args: str) -> bool:
    """Create a new collection and switch to it."""
    app = get_app_state()

    if not app.rag_manager.connected:
        app.ui.show_error("Not connected to H2OGPTE. Use /register first.")
        return True

    if not args:
        collection_name = app.ui.prompt.get_input_with_default(
            "Enter collection name", "CLI-Collection"
        )
    else:
        collection_name = args.strip()

    if collection_name:
        app.ui.show_info(f"Creating and switching to collection '{collection_name}'...")
        success = await app.rag_manager.switch_to_collection(collection_name)

        if success:
            await app.update_status_bar()
            app.ui.show_success(f"Collection '{collection_name}' created and activated")
            app.ui.show_info("Chat session reset - ready for new conversation")
        else:
            app.ui.show_error("Failed to create collection")
    else:
        app.ui.show_error("Collection name is required")

    return True


async def handle_new_chat(args: str) -> bool:
    """Create a new chat session."""
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

    if not args:
        import datetime

        session_name = f"chat-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    else:
        session_name = args.strip()

    app.ui.show_info(f"Creating new chat session '{session_name}'...")
    success = await app.rag_manager.create_chat_session(session_name)

    if success:
        await app.update_status_bar()
        app.ui.show_success(f"Chat session '{session_name}' created and activated")
    else:
        app.ui.show_error("Failed to create chat session")

    return True
