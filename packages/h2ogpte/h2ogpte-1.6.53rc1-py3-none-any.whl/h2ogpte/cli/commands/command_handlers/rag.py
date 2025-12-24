from pathlib import Path

from ...core.app import get_app_state


async def handle_register(args: str) -> bool:
    """Register H2OGPTE system."""
    app = get_app_state()

    # Parse arguments or prompt for them
    parts = args.split()

    if len(parts) < 2:
        # Check if user explicitly wants to clear credentials (special keyword)
        if args.strip().lower() in ["clear", "disconnect", "reset"]:
            app.ui.show_info("Clearing credentials...")
            # Clear existing connection
            if app.rag_manager.connected:
                await app.rag_manager.close()

            # Clear credentials
            app.settings.rag.endpoint = ""
            app.settings.rag.api_key = ""
            app.settings.rag.collection_name = "default"
            app.settings.save()

            # Update status bar
            await app.update_status_bar()

            app.ui.show_success(
                "Credentials cleared. Use /register <address> <api_key> to reconnect"
            )
            return True

        # Interactive mode with defaults and secure input
        address = app.ui.prompt.get_input_with_default(
            "H2OGPTE Address", "https://h2ogpte.genai.h2o.ai"
        )
        api_key = app.ui.prompt.get_secret("API Key")

        # If user cancels input, don't proceed
        if not address or not api_key:
            app.ui.show_info("Registration cancelled")
            return True
    else:
        address = parts[0]
        api_key = parts[1]

    # Step 1: Connect and get username only
    app.ui.show_info("Step 1: Connecting and retrieving user information...")

    # Save to settings with encrypted API key
    app.settings.rag.endpoint = address
    app.settings.set_rag_api_key(api_key)

    # Try to connect and get username (without creating collection yet)
    success = await app.rag_manager.connect_and_get_user(address, api_key)

    if success:
        # Get username and update status bar
        username = await app.rag_manager.get_username()
        if username:
            app.ui.show_success(f"Connected as user: {username}")

            # Save settings on successful connection
            app.settings.save()

            # Update status bar with username
            await app.update_status_bar()
            app.ui.show_success("Connected successfully! Ready to chat.")

        else:
            app.ui.show_error("Connected but failed to get username")
    else:
        app.ui.show_error("Failed to connect to H2OGPTE")

    return True


async def handle_upload(args: str) -> bool:
    """Upload files to RAG."""
    app = get_app_state()

    if not args:
        # Interactive file selection
        path = app.ui.prompt.get_path("Select file or directory to upload: ")
        if not path:
            return True
    else:
        path = Path(args.strip())

    if not path.exists():
        app.ui.show_error(f"Path not found: {path}")
        return True

    # Collect files
    if path.is_file():
        files = [path]
    else:
        # Scan directory
        patterns = app.ui.prompt.get_multiselect(
            ["*.py", "*.js", "*.txt", "*.md", "*.json", "*"],
            "Select file patterns to include:",
        )
        files = app.file_manager.scan_directory(
            path, patterns if patterns != ["*"] else None
        )

    if not files:
        app.ui.show_warning("No files to upload")
        return True

    # Display files to upload
    app.file_manager.display_file_list(files, show_details=False)

    if not app.ui.prompt.confirm(f"Upload {len(files)} file(s)?", default=True):
        return True

    # Upload files
    await app.rag_manager.upload_files(files)
    return True


async def handle_analyze(args: str) -> bool:
    """Analyze directory."""
    app = get_app_state()

    if not args:
        path = Path.cwd()
    else:
        path = Path(args.strip())

    if not path.exists() or not path.is_dir():
        app.ui.show_error(f"Invalid directory: {path}")
        return True

    # Analyze directory
    analysis = await app.dir_analyzer.analyze(path)

    # Ask if user wants to upload
    if analysis["total_files"] > 0:
        if app.ui.prompt.confirm("Upload directory contents to RAG?"):
            files = app.file_manager.scan_directory(path)
            await app.rag_manager.upload_files(files)

    return True
