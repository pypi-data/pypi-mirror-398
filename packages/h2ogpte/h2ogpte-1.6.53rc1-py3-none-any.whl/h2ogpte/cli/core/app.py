from typing import Optional
from rich.console import Console

from .config import settings
from .session import Session
from ..integrations.rag import RAGManager
from ..integrations.agent import AgentManager
from ..utils.file_manager import FileManager, FileUploader, DirectoryAnalyzer
from ..ui.prompts import UIManager


class AppState:
    """Global application state container."""

    def __init__(self):
        self.console = Console()
        self.session = Session()
        self.ui = UIManager()
        self.settings = settings
        self.rag_manager = RAGManager()
        self.agent_manager = AgentManager()
        self.file_manager = FileManager()
        self.file_uploader = FileUploader(self.file_manager)
        self.dir_analyzer = DirectoryAnalyzer(self.file_manager)
        self._cleanup_done = False

        # Register interrupt handler
        self.session.register_interrupt_handler(self._handle_interrupt)

    async def try_auto_reconnect(self):
        """Try to automatically reconnect using saved credentials."""
        try:
            if await self.rag_manager.auto_reconnect(self.settings):
                await self.update_status_bar()
                self.ui.show_success(
                    f"Reconnected as: {await self.rag_manager.get_username()}"
                )
                return True
        except Exception as e:
            # Silent failure - just continue without connection
            pass
        return False

    def _handle_interrupt(self):
        """Handle interrupt signal."""
        if self.agent_manager.session:
            self.agent_manager.session.interrupt()

    async def update_status_bar(self):
        """Update the status bar with current connection info."""
        # Check if we have connection info
        connected = self.rag_manager.connected or self.agent_manager.connected

        # Get actual username from RAG manager
        username = None
        collection = None
        chat_session = None
        if self.rag_manager.connected:
            username = await self.rag_manager.get_username()
            collection = await self.rag_manager.get_collection_name()
            chat_session = await self.rag_manager.get_chat_session_name()

        # Use RAG chat session if available, otherwise use manual session
        session = chat_session or getattr(self, "_current_session", None)

        self.ui.update_status(
            connected=connected,
            username=username,
            collection=collection,
            session=session,
        )

    async def set_session(self, session_name: str):
        """Set the current session name."""
        self._current_session = session_name
        await self.update_status_bar()

    async def cleanup(self):
        """Clean up all resources."""
        if self._cleanup_done:
            return

        await self.rag_manager.close()
        await self.agent_manager.close()
        self.session.save_session()
        self._cleanup_done = True


# Global app instance - initialized once
app_state: Optional[AppState] = None


def get_app_state() -> AppState:
    """Get the global app state instance."""
    global app_state
    if app_state is None:
        app_state = AppState()
    return app_state


def initialize_app() -> AppState:
    """Initialize the global app state."""
    global app_state
    app_state = AppState()
    return app_state
