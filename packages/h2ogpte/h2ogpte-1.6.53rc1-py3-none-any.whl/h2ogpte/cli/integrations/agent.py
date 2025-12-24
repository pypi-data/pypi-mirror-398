import asyncio
import httpx
import json
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

console = Console()


class AgentClient:
    """Client for interacting with AI agent systems."""

    def __init__(self, endpoint: str, api_key: str, model: str = "gpt-4"):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(300.0),
        )
        self.conversation_history: List[Dict[str, str]] = []

    async def test_connection(self) -> bool:
        """Test connection to agent system."""
        try:
            response = await self.client.get(f"{self.endpoint}/models")
            return response.status_code == 200
        except Exception as e:
            console.print(f"[red]Connection failed: {e}[/red]")
            return False

    async def send_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = True,
    ) -> AsyncGenerator[str, None]:
        """Send a message to the agent and stream the response."""
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": message})

        # Prepare request
        request_data = {
            "model": self.model,
            "messages": self.conversation_history,
            "stream": stream,
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        if context:
            request_data["context"] = context

        try:
            if stream:
                async with self.client.stream(
                    "POST", f"{self.endpoint}/chat/completions", json=request_data
                ) as response:
                    response.raise_for_status()
                    full_response = ""

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break

                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    content = (
                                        chunk["choices"][0]
                                        .get("delta", {})
                                        .get("content", "")
                                    )
                                    if content:
                                        full_response += content
                                        yield content
                            except json.JSONDecodeError:
                                continue

                    # Add assistant response to history
                    self.conversation_history.append(
                        {"role": "assistant", "content": full_response}
                    )

            else:
                response = await self.client.post(
                    f"{self.endpoint}/chat/completions", json=request_data
                )
                response.raise_for_status()
                data = response.json()

                if "choices" in data and data["choices"]:
                    content = data["choices"][0]["message"]["content"]
                    self.conversation_history.append(
                        {"role": "assistant", "content": content}
                    )
                    yield content

        except httpx.HTTPError as e:
            yield f"[ERROR] HTTP error occurred: {e}"
        except Exception as e:
            yield f"[ERROR] An error occurred: {e}"

    async def execute_action(
        self, action: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific action through the agent."""
        request_data = {"action": action, "parameters": parameters, "model": self.model}

        try:
            response = await self.client.post(
                f"{self.endpoint}/actions", json=request_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "success": False}

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history.copy()

    async def close(self):
        """Close the client connection."""
        await self.client.aclose()


class AgentSession:
    """Manages an interactive agent session."""

    def __init__(self, client: AgentClient):
        self.client = client
        self.is_active = False
        self.current_task: Optional[asyncio.Task] = None
        self.interrupted = False

    async def start_conversation(self, initial_prompt: Optional[str] = None):
        """Start an interactive conversation with the agent."""
        self.is_active = True
        console.print(
            Panel(
                "[bold cyan]Agent Session Started[/bold cyan]\n"
                "[dim]Type your message and press Enter. Use /end to exit session.[/dim]",
                border_style="cyan",
            )
        )

        if initial_prompt:
            await self.send_and_display(initial_prompt)

    async def send_and_display(self, message: str):
        """Send message and display streaming response."""
        # Display user message
        console.print(f"\n[bold blue]You:[/bold blue] {message}")

        # Create a live display for streaming response
        response_text = Text()
        panel = Panel(
            response_text,
            title="[bold green]Agent[/bold green]",
            border_style="green",
            expand=False,
        )

        with Live(panel, refresh_per_second=10, console=console) as live:
            try:
                async for chunk in self.client.send_message(message):
                    if self.interrupted:
                        break
                    response_text.append(chunk)
                    live.update(
                        Panel(
                            response_text,
                            title="[bold green]Agent[/bold green]",
                            border_style="green",
                            expand=False,
                        )
                    )
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def interrupt(self):
        """Interrupt the current operation."""
        self.interrupted = True
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()

    async def end_session(self):
        """End the agent session."""
        self.is_active = False
        console.print(
            Panel(
                "[bold yellow]Agent Session Ended[/bold yellow]", border_style="yellow"
            )
        )


class AgentManager:
    """Manager for agent operations with UI integration."""

    def __init__(self):
        self.client: Optional[AgentClient] = None
        self.session: Optional[AgentSession] = None
        self.connected = False

    async def connect(self, endpoint: str, api_key: str, model: str = "gpt-4") -> bool:
        """Connect to agent system."""
        console.print(f"[blue]Connecting to agent system at {endpoint}...[/blue]")

        self.client = AgentClient(endpoint, api_key, model)

        if await self.client.test_connection():
            self.connected = True
            console.print(
                f"[green]✓[/green] Connected to agent system (model: {model})"
            )
            return True
        else:
            self.connected = False
            console.print("[red]✗[/red] Failed to connect to agent system")
            return False

    async def start_session(self, initial_prompt: Optional[str] = None):
        """Start an interactive agent session."""
        if not self.connected or not self.client:
            console.print(
                "[red]Not connected to agent system. Configure in settings first.[/red]"
            )
            return

        self.session = AgentSession(self.client)
        await self.session.start_conversation(initial_prompt)

    async def send_message(self, message: str) -> str:
        """Send a single message to the agent."""
        if not self.connected or not self.client:
            console.print("[red]Not connected to agent system.[/red]")
            return ""

        response = ""
        async for chunk in self.client.send_message(message, stream=False):
            response += chunk

        return response

    async def execute_action(self, action: str, parameters: Dict[str, Any]):
        """Execute an action through the agent."""
        if not self.connected or not self.client:
            console.print("[red]Not connected to agent system.[/red]")
            return None

        console.print(f"[blue]Executing action: {action}[/blue]")

        with console.status("[bold green]Processing..."):
            result = await self.client.execute_action(action, parameters)

        if result.get("success"):
            console.print("[green]✓[/green] Action completed successfully")
            self._display_action_result(result)
        else:
            console.print(
                f"[red]✗[/red] Action failed: {result.get('error', 'Unknown error')}"
            )

        return result

    def _display_action_result(self, result: Dict[str, Any]):
        """Display action result."""
        if "output" in result:
            console.print(
                Panel(str(result["output"]), title="Output", border_style="green")
            )

        if "metadata" in result:
            from rich.table import Table

            table = Table(title="Metadata", show_header=False)
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="white")

            for key, value in result["metadata"].items():
                table.add_row(key, str(value))

            console.print(table)

    def show_history(self):
        """Display conversation history."""
        if not self.client:
            console.print("[yellow]No active session[/yellow]")
            return

        history = self.client.get_history()
        if not history:
            console.print("[yellow]No conversation history[/yellow]")
            return

        for entry in history:
            role = entry["role"]
            content = (
                entry["content"][:200] + "..."
                if len(entry["content"]) > 200
                else entry["content"]
            )

            if role == "user":
                console.print(f"[bold blue]User:[/bold blue] {content}")
            else:
                console.print(f"[bold green]Agent:[/bold green] {content}")

    def clear_history(self):
        """Clear conversation history."""
        if self.client:
            self.client.clear_history()
            console.print("[green]✓[/green] Conversation history cleared")

    async def close(self):
        """Close agent connection."""
        if self.session:
            await self.session.end_session()

        if self.client:
            await self.client.close()
            self.connected = False
