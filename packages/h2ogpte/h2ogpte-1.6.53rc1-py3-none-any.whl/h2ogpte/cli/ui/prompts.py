from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from typing import Optional


class UIManager:
    def __init__(self):
        self.console = Console()
        from .hbot_prompt import HBOTPrompt
        from .status_bar import StatusBar

        self.prompt = HBOTPrompt()
        self.status_bar = StatusBar()
        self.prompt._status_bar = self.status_bar

    def show_welcome(self):
        welcome_text = """
        [bold cyan]╔═══════════════════════════════════════╗[/bold cyan]
        [bold cyan]║[/bold cyan]      [bold white]H2OGPTE CLI Tool[/bold white]                 [bold cyan]║[/bold cyan]
        [bold cyan]║[/bold cyan]     [dim]RAG & AI Agent Operations[/dim]         [bold cyan]║[/bold cyan]
        [bold cyan]╚═══════════════════════════════════════╝[/bold cyan]

        [green]Type /help for commands or start typing your prompt[/green]

        [dim]Live Suggestions:
        • Type [white]/[/white] to see all commands below the input
        • Use [white]↑↓[/white] arrows to navigate suggestions
        • Press [white]Tab[/white] or [white]Enter[/white] to select[/dim]
        """
        self.console.print(Panel(welcome_text, border_style="cyan"))

    def show_help(self):
        help_table = Table(title="Available Commands", show_header=True)
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")
        help_table.add_column("Usage", style="dim")

        commands = [
            ("/help", "Show this help message", "/help"),
            ("/register", "Connect to H2OGPTE", "/register [address] [api_key]"),
            ("/register", "Clear credentials", "/register clear"),
            ("/disconnect", "Disconnect and clear creds", "/disconnect"),
            ("", "Chat with H2OGPTE (RAG)", "Type any message"),
            ("/collection", "Switch/create collection", "/collection [name]"),
            ("/upload", "Upload files to collection", "/upload <file_path>"),
            ("/analyze", "Analyze directory", "/analyze [directory]"),
            ("/agent", "Use AI agent mode", "/agent <message>"),
            ("/research", "Deep research with AI agent", "/research <query>"),
            ("/config", "Configure settings", "/config"),
            ("/status", "Show session status", "/status"),
            ("/history", "Show command history", "/history [n]"),
            ("/clear", "Clear screen", "/clear"),
            ("/save", "Save current session", "/save [filename]"),
            ("/load", "Load saved session", "/load <filename>"),
            ("/session", "Create chat session", "/session [name]"),
            ("/exit", "Exit H2OGPTE CLI", "/exit [y]"),
            ("/quit", "Exit H2OGPTE CLI (same as /exit)", "/quit [y]"),
        ]

        for cmd, desc, usage in commands:
            help_table.add_row(cmd, desc, usage)

        self.console.print(help_table)

        shortcuts_table = Table(title="Keyboard Shortcuts", show_header=False)
        shortcuts_table.add_column("Key", style="cyan")
        shortcuts_table.add_column("Action", style="white")

        shortcuts = [
            ("Ctrl+C", "Interrupt current operation"),
            ("Ctrl+D", "Exit (when line is empty)"),
            ("Tab", "Autocomplete"),
            ("↑/↓", "Navigate suggestions"),
            ("Enter", "Select suggestion or execute"),
        ]

        for key, action in shortcuts:
            shortcuts_table.add_row(key, action)

        self.console.print(shortcuts_table)

    def show_error(self, message: str, details: Optional[str] = None):
        error_panel = Panel(
            f"[red bold]✗ Error:[/red bold] {message}", border_style="red", expand=False
        )
        self.console.print(error_panel)

        if details:
            self.console.print(f"[dim]{details}[/dim]")

    def show_success(self, message: str):
        self.console.print(f"[green]✓[/green] {message}")

    def show_info(self, message: str):
        self.console.print(f"[blue]ℹ[/blue] {message}")

    def show_warning(self, message: str):
        self.console.print(f"[yellow]⚠[/yellow] {message}")

    def show_code(self, code: str, language: str = "python"):
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title=f"[{language}]", border_style="blue"))

    def show_markdown(self, content: str):
        md = Markdown(content)
        self.console.print(Panel(md, border_style="green"))

    def clear_screen(self):
        self.console.clear()

    def show_status_bar(self):
        self.status_bar.print_status_line()

    def update_status(
        self,
        connected: bool = None,
        username: str = None,
        collection: str = None,
        session: str = None,
    ):
        if connected is not None:
            self.status_bar.update_connection_status(connected, username)
        if collection is not None:
            self.status_bar.update_collection(collection)
        if session is not None:
            self.status_bar.update_session(session)
