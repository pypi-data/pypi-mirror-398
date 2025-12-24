import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from typing import Optional


class StatusBar:
    def __init__(self):
        self.console = Console()
        self.username: Optional[str] = None
        self.collection: Optional[str] = None
        self.session: Optional[str] = None
        self.is_connected: bool = False

    def update_connection_status(self, connected: bool, username: Optional[str] = None):
        self.is_connected = connected
        self.username = username

    def update_collection(self, collection: Optional[str] = None):
        self.collection = collection

    def update_session(self, session: Optional[str] = None):
        self.session = session

    def _create_status_section(
        self,
        label: str,
        value: Optional[str],
        icon: str,
        connected_style: str = "green",
        disconnected_style: str = "dim red",
    ) -> Text:
        if value:
            status_text = Text()
            status_text.append(f"{icon} ", style="cyan")
            status_text.append(f"{label}: ", style="dim")
            status_text.append(f"{value}", style=connected_style)
            return status_text
        else:
            status_text = Text()
            status_text.append(f"{icon} ", style="dim")
            status_text.append(f"{label}: ", style="dim")
            status_text.append("Not set", style=disconnected_style)
            return status_text

    def render_fixed_bottom(self) -> str:
        console = Console()
        width = console.size.width

        parts = []

        if self.is_connected:
            parts.append("🟢 Connected")
        else:
            parts.append("🔴 Disconnected")

        if self.username and self.is_connected:
            parts.append(f"👤 {self.username}")
        else:
            parts.append("👤 —")

        if self.collection:
            parts.append(f"📚 {self.collection}")
        else:
            parts.append("📚 —")

        if self.session:
            parts.append(f"💬 {self.session}")
        else:
            parts.append("💬 —")

        status_content = " │ ".join(parts)
        if len(status_content) > width - 2:
            status_content = status_content[: width - 5] + "..."
        else:
            status_content = status_content.ljust(width - 2)

        return status_content

    def render_separator(self) -> str:
        console = Console()
        width = console.size.width
        return "─" * width

    def print_status_line(self):
        console = Console()

        separator = self.render_separator()
        if self.is_connected:
            console.print(separator, style="green")
        else:
            console.print(separator, style="dim red")

        status = self.render_fixed_bottom()
        if self.is_connected:
            console.print(f" {status} ", style="white on green")
        else:
            console.print(f" {status} ", style="white on red")

    def render_compact(self) -> str:
        parts = []

        if self.is_connected:
            parts.append("🟢")
        else:
            parts.append("🔴")

        if self.username and self.is_connected:
            parts.append(f"👤 {self.username}")
        else:
            parts.append("👤 —")

        if self.collection:
            parts.append(f"📚 {self.collection}")
        else:
            parts.append("📚 —")

        if self.session:
            parts.append(f"💬 {self.session}")
        else:
            parts.append("💬 —")

        return " │ ".join(parts)

    def clear(self):
        self.username = None
        self.collection = None
        self.session = None
        self.is_connected = False
