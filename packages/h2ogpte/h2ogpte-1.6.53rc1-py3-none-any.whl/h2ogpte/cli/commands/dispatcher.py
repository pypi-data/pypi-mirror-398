from typing import Dict, Callable, Awaitable

from .command_handlers.help import handle_help
from .command_handlers.status import handle_status
from .command_handlers.clear import handle_clear
from .command_handlers.history import handle_history
from .command_handlers.exit import handle_exit
from .command_handlers.config import handle_config
from .command_handlers.rag import handle_register, handle_upload, handle_analyze
from .command_handlers.agent import handle_agent
from .command_handlers.chat import handle_chat
from .command_handlers.research_agent import handle_research_agent
from .command_handlers.session import handle_save, handle_load, handle_session
from .command_handlers.collection import handle_create_collection
from .command_handlers.disconnect import handle_disconnect

from ..core.app import get_app_state


def _sanitize_command_for_history(command: str, cmd: str) -> str:
    if cmd == "/register":
        return "/register [hidden credentials]"
    elif cmd in ["/config"] and "api" in command.lower():
        return f"{cmd} [hidden sensitive data]"
    else:
        return command


COMMAND_HANDLERS: Dict[str, Callable[[str], Awaitable[bool]]] = {
    "/help": handle_help,
    "/status": handle_status,
    "/clear": handle_clear,
    "/history": handle_history,
    "/exit": handle_exit,
    "/quit": handle_exit,
    "/config": handle_config,
    "/register": handle_register,
    "/upload": handle_upload,
    "/analyze": handle_analyze,
    "/agent": handle_agent,
    "/research": handle_research_agent,
    "/save": handle_save,
    "/load": handle_load,
    "/session": handle_session,
    "/collection": handle_create_collection,
    "/disconnect": handle_disconnect,
}


async def dispatch_command(command: str) -> bool:
    if not command:
        return True

    app = get_app_state()
    parts = command.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    history_command = _sanitize_command_for_history(command, cmd)
    app.session.add_to_history(history_command, None)

    if cmd in COMMAND_HANDLERS:
        try:
            result = await COMMAND_HANDLERS[cmd](args)
            return result if result is not None else True
        except Exception as e:
            app.ui.show_error(f"Command failed: {e}")
            app.console.print(f"[dim]Debug: {type(e).__name__}: {e}[/dim]")
            return True
    else:
        if command.startswith("/"):
            app.ui.show_error(f"Unknown command: {cmd}")
            app.ui.show_info("Type /help for available commands")
        else:
            try:
                await handle_chat(command)
            except Exception as e:
                app.ui.show_error(f"Chat failed: {e}")
        return True
