from rich.table import Table

from ...core.app import get_app_state


async def handle_config(args: str) -> bool:
    """Configure settings."""
    app = get_app_state()

    try:
        categories = ["RAG", "Agent", "UI", "View Current", "Save & Exit"]
        choice = app.ui.prompt.select_from_list(
            categories, "Select configuration category:"
        )

        if choice == "RAG":
            app.console.print("[cyan]RAG Configuration[/cyan]")

            current_endpoint = app.settings.rag.endpoint or "not set"
            new_endpoint = app.ui.prompt.get_input(
                f"RAG Endpoint [{current_endpoint}]: "
            )
            if new_endpoint:
                app.settings.rag.endpoint = new_endpoint

            current_key = "*" * 8 if app.settings.rag.api_key else "not set"
            new_key = app.ui.prompt.get_input(f"API Key [{current_key}]: ")
            if new_key:
                app.settings.rag.api_key = new_key

            current_collection = app.settings.rag.collection_name
            new_collection = app.ui.prompt.get_input(
                f"Collection [{current_collection}]: "
            )
            if new_collection:
                app.settings.rag.collection_name = new_collection

        elif choice == "Agent":
            app.console.print("[cyan]Agent Configuration[/cyan]")

            current_endpoint = app.settings.agent.endpoint or "not set"
            new_endpoint = app.ui.prompt.get_input(
                f"Agent Endpoint [{current_endpoint}]: "
            )
            if new_endpoint:
                app.settings.agent.endpoint = new_endpoint

            current_key = "*" * 8 if app.settings.agent.api_key else "not set"
            new_key = app.ui.prompt.get_input(f"API Key [{current_key}]: ")
            if new_key:
                app.settings.agent.api_key = new_key

            current_model = app.settings.agent.model
            new_model = app.ui.prompt.get_input(f"Model [{current_model}]: ")
            if new_model:
                app.settings.agent.model = new_model

        elif choice == "UI":
            app.console.print("[cyan]UI Configuration[/cyan]")

            current_theme = app.settings.ui.theme
            new_theme = app.ui.prompt.get_input(f"Theme [{current_theme}]: ")
            if new_theme:
                app.settings.ui.theme = new_theme

            app.settings.ui.show_progress = app.ui.prompt.confirm(
                "Show progress bars", default=app.settings.ui.show_progress
            )

            app.settings.ui.animation = app.ui.prompt.confirm(
                "Enable animations", default=app.settings.ui.animation
            )

        elif choice == "View Current":
            _show_current_config(app)

        if choice not in ["View Current", "Save & Exit"]:
            try:
                app.settings.save()
                app.ui.show_success("Configuration saved")
                # Update status bar after config changes
                app.update_status_bar()
            except Exception as e:
                app.ui.show_error(f"Failed to save configuration: {e}")

    except Exception as e:
        app.ui.show_error(f"Configuration error: {e}")

    return True


def _show_current_config(app):
    """Show current configuration."""
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    # RAG settings
    table.add_row("RAG Endpoint", app.settings.rag.endpoint or "not set")
    table.add_row("RAG API Key", "*" * 8 if app.settings.rag.api_key else "not set")
    table.add_row("RAG Collection", app.settings.rag.collection_name)

    # Agent settings
    table.add_row("Agent Endpoint", app.settings.agent.endpoint or "not set")
    table.add_row("Agent API Key", "*" * 8 if app.settings.agent.api_key else "not set")
    table.add_row("Agent Model", app.settings.agent.model)

    # UI settings
    table.add_row("UI Theme", app.settings.ui.theme)
    table.add_row("Show Progress", str(app.settings.ui.show_progress))
    table.add_row("Animations", str(app.settings.ui.animation))

    app.console.print(table)
