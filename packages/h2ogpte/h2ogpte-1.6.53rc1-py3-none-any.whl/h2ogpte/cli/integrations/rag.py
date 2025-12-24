import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from rich.console import Console

from ...h2ogpte import H2OGPTE
from ...h2ogpte_async import H2OGPTEAsync
from ...h2ogpte import PartialChatMessage

console = Console()


class H2OGPTEClient:
    def __init__(self, address: str, api_key: str):
        self.address = address
        self.api_key = api_key
        self.client = H2OGPTE(address=address, api_key=api_key)
        self.async_client = H2OGPTEAsync(address=address, api_key=api_key)
        self.username = None
        self.current_collection_id = None
        self.current_collection_name = None
        self.current_chat_session_id = None
        self.current_chat_session_name = None

    async def test_connection_and_get_meta(self) -> bool:
        try:
            import concurrent.futures

            def get_meta():
                return self.client.get_meta()

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                meta = await asyncio.wait_for(
                    loop.run_in_executor(executor, get_meta), timeout=5.0
                )
                self.username = meta.username
                console.print(
                    f"[green]✓[/green] Connected as user: [cyan]{self.username}[/cyan]"
                )
                return True

        except asyncio.TimeoutError:
            console.print(f"[red]Connection timeout (5s) - network may be slow[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Connection failed: {e}[/red]")
            return False

    async def create_collection(
        self, name: str, description: str = ""
    ) -> Optional[str]:
        try:
            collection_id = await self.async_client.create_collection(
                name=name, description=description
            )
            self.current_collection_id = collection_id
            self.current_collection_name = name
            console.print(f"[green]✓[/green] Collection '[cyan]{name}[/cyan]' created")
            return collection_id

        except Exception as e:
            console.print(f"[red]Error creating collection: {e}[/red]")
            return None

    async def create_chat_session(
        self, collection_id: Optional[str] = None, session_name: str = "chat-session"
    ) -> Optional[str]:
        try:
            chat_session_id = await self.async_client.create_chat_session(collection_id)
            self.current_chat_session_id = chat_session_id
            self.current_chat_session_name = session_name
            console.print(
                f"[green]✓[/green] Chat session '[cyan]{session_name}[/cyan]' created"
            )
            return chat_session_id

        except Exception as e:
            console.print(f"[red]Error creating chat session: {e}[/red]")
            return None

    async def rename_chat_session(self, session_id: str, session_name: str) -> bool:
        try:
            await self.async_client.rename_chat_session(session_id, session_name)
            self.current_chat_session_name = session_name
            console.print(
                f"[green]✓[/green] Chat session renamed to '[cyan]{session_name}[/cyan]'"
            )
            return True

        except Exception as e:
            console.print(f"[red]Error renaming chat session: {e}[/red]")
            return False

    async def query_streaming(
        self,
        message: str,
        timeout: int = 2400,
        use_agent: bool = False,
        agent_type: str = None,
    ) -> Optional[Dict[str, Any]]:
        if not self.current_chat_session_id:
            console.print("[red]No active chat session. Create one first.[/red]")
            return None

        try:
            import re

            accumulated_content = ""
            displayed_turn_count = 0
            last_turn_title = None
            header_shown = False
            final_response_content = ""

            def callback(chat_message):
                nonlocal accumulated_content, displayed_turn_count, last_turn_title, header_shown, final_response_content

                if not isinstance(chat_message, PartialChatMessage):
                    return

                content = chat_message.content
                if not content:
                    return

                accumulated_content += content
                final_response_content = (
                    accumulated_content  # Keep track of full content for final response
                )

                if use_agent:
                    if not header_shown:
                        console.print("[blue]Agentic Analysis[/blue]")
                        header_shown = True

                    chunks = accumulated_content.split("ENDOFTURN\n")
                    completed_chunks = len(chunks) - 1
                    while displayed_turn_count < completed_chunks:
                        chunk = chunks[displayed_turn_count]
                        turn_title = None

                        turn_title_match = re.search(
                            r"<(?:stream_)?turn_title>(.*?)</(?:stream_)?turn_title>",
                            chunk,
                            re.DOTALL,
                        )
                        if turn_title_match:
                            turn_title = turn_title_match.group(1).strip()
                        else:
                            lines = chunk.strip().split("\n")
                            for line in lines:
                                if line.strip():
                                    turn_title = line.strip()
                                    break

                        if turn_title:
                            turn_title = re.sub(
                                r"^[\*#\s\t\n]+", "", turn_title
                            ).strip()
                            turn_title = re.sub(r"\*+$", "", turn_title).strip()

                            if turn_title and turn_title != last_turn_title:
                                console.print(f"  • {turn_title}")
                                last_turn_title = turn_title

                        displayed_turn_count += 1

                    if len(chunks) > displayed_turn_count and chunks[-1].strip():
                        current_chunk = chunks[-1]

                        turn_title_match = re.search(
                            r"<(?:stream_)?turn_title>(.*?)</(?:stream_)?turn_title>",
                            current_chunk,
                            re.DOTALL,
                        )
                        if turn_title_match:
                            new_title = turn_title_match.group(1).strip()
                        else:
                            lines = current_chunk.strip().split("\n")
                            new_title = None
                            for line in lines:
                                if line.strip():
                                    new_title = line.strip()
                                    break

                        if new_title:
                            cleaned_title = re.sub(
                                r"^[\*#\s\t\n]+", "", new_title
                            ).strip()
                            cleaned_title = re.sub(r"\*+$", "", cleaned_title).strip()

                            if cleaned_title and cleaned_title != last_turn_title:
                                console.print(f"  • {cleaned_title}")
                                last_turn_title = cleaned_title
                else:
                    console.print(content, end="")

            if use_agent:
                console.print("\n", end="")
            else:
                console.print("\n[bold green]H2OGPTE:[/bold green] ", end="")

            query_params = {"timeout": timeout, "llm": "auto", "callback": callback}

            if use_agent:
                query_params["llm_args"] = {
                    "use_agent": True,
                }
                if agent_type:
                    query_params["llm_args"]["agent_type"] = agent_type

            async with self.async_client.connect(
                self.current_chat_session_id
            ) as session:
                reply = await session.query(message, **query_params)

            usage = await self.async_client.list_chat_message_meta_part(
                reply.id, "usage_stats"
            )
            usage_dict = json.loads(usage.content)

            if use_agent:
                console.print("\n[blue]Final Response:[/blue]")

                if hasattr(reply, "content") and reply.content:
                    response_content = reply.content
                    if response_content:
                        console.print(response_content)
                else:
                    console.print("No response content available.")

                console.print()
            else:
                console.print()

            return usage_dict

        except Exception as e:
            console.print(f"\n[red]Query error: {e}[/red]")
            return None

    async def upload_files(self, file_paths: List[Path]) -> Dict[str, str]:
        if not self.current_collection_id:
            console.print("[red]No active collection. Create one first.[/red]")
            return {}

        uploaded_files = {}
        upload_ids = []

        try:
            import concurrent.futures

            for file_path in file_paths:

                def upload_file():
                    with open(file_path, "rb") as f:
                        return self.client.upload(file_path.name, f)

                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    upload_id = await loop.run_in_executor(executor, upload_file)
                    uploaded_files[str(file_path)] = upload_id
                    upload_ids.append(upload_id)
                    console.print(f"[green]✓[/green] Uploaded: {file_path.name}")

            last_seen_update = None

            def callback(job):
                nonlocal last_seen_update
                if not job:
                    return

                current_update = job.last_update_date
                if last_seen_update is not None and current_update <= last_seen_update:
                    return

                last_seen_update = current_update
                for s in job.statuses:
                    if not s:
                        continue

                    status_text = getattr(s, "status", None)
                    if status_text:
                        console.print(f"[blue]  {status_text}...[/blue]")

            def ingest_uploads():
                ingest_result = self.client.ingest_uploads(
                    self.current_collection_id, upload_ids, callback=callback
                )
                console.print(f"[green]✓[/green] Ingested {len(upload_ids)} files")
                return ingest_result

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                await loop.run_in_executor(executor, ingest_uploads)

        except Exception as e:
            console.print(f"[red]Upload error: {e}[/red]")

        return uploaded_files


class RAGManager:
    def __init__(self):
        self.client: Optional[H2OGPTEClient] = None
        self.connected = False

    async def auto_reconnect(self, settings) -> bool:
        if not settings.rag.endpoint:
            return False

        api_key = settings.get_rag_api_key()
        if not api_key:
            return False

        console.print(f"[blue]Reconnecting to {settings.rag.endpoint}...[/blue]")
        return await self.connect_and_get_user(settings.rag.endpoint, api_key)

    async def connect_and_get_user(self, address: str, api_key: str) -> bool:
        console.print(f"[blue]Connecting to H2OGPTE at {address}...[/blue]")

        try:
            self.client = H2OGPTEClient(address, api_key)

            if await self.client.test_connection_and_get_meta():
                self.connected = True
                console.print("[green]✓[/green] Successfully connected to H2OGPTE")
                return True
            else:
                self.connected = False
                console.print("[red]✗[/red] Failed to connect to H2OGPTE")
                return False

        except ImportError as e:
            console.print(f"[red]✗[/red] {e}")
            return False
        except Exception as e:
            console.print(f"[red]✗[/red] Unexpected error: {e}")
            self.connected = False
            return False

    async def switch_to_collection(self, collection_name: str) -> bool:
        if not self.connected or not self.client:
            console.print("[red]Not connected to H2OGPTE. Use /register first.[/red]")
            return False

        collection_id = await self.client.create_collection(
            name=collection_name, description=f"CLI-Collection: {collection_name}"
        )

        if collection_id:
            self.client.current_chat_session_id = None
            self.client.current_chat_session_name = None
            console.print("[green]✓[/green] Collection switched successfully")
            return True
        else:
            console.print("[red]✗[/red] Failed to switch to collection")
            return False

    async def get_username(self) -> Optional[str]:
        if self.client:
            return self.client.username
        return None

    async def get_collection_name(self) -> Optional[str]:
        if self.client:
            return self.client.current_collection_name
        return None

    async def get_chat_session_name(self) -> Optional[str]:
        if self.client:
            return self.client.current_chat_session_name
        return None

    async def create_chat_session(self, session_name: str) -> bool:
        if not self.connected or not self.client:
            console.print("[red]Not connected to H2OGPTE. Use /register first.[/red]")
            return False

        session_id = await self.client.create_chat_session(
            collection_id=self.client.current_collection_id, session_name=session_name
        )
        return session_id is not None

    async def create_chat_session_with_name(self, session_name: str) -> Optional[str]:
        if not self.connected or not self.client:
            console.print("[red]Not connected to H2OGPTE. Use /register first.[/red]")
            return None

        session_id = await self.client.create_chat_session(
            collection_id=self.client.current_collection_id, session_name=session_name
        )

        if session_id and session_name != "chat-session":
            await self.client.rename_chat_session(session_id, session_name)

        return session_id

    async def send_message(
        self, message: str, use_agent: bool = False, agent_type: str = None
    ) -> Optional[Dict[str, Any]]:
        if not self.connected or not self.client:
            console.print("[red]Not connected to H2OGPTE. Use /register first.[/red]")
            return None

        if not self.client.current_collection_id:
            console.print("[blue]Creating default collection...[/blue]")
            collection_id = await self.client.create_collection(
                name="CLI-Collection",
                description="CLI automatically created collection",
            )
            if not collection_id:
                console.print("[red]Failed to create collection[/red]")
                return None

        if not self.client.current_chat_session_id:
            import datetime

            session_name = f"chat-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
            console.print(f"[blue]Creating chat session '{session_name}'...[/blue]")
            session_id = await self.client.create_chat_session(
                collection_id=self.client.current_collection_id,
                session_name=session_name,
            )
            if session_id:
                await self.client.rename_chat_session(session_id, session_name)

        return await self.client.query_streaming(
            message, use_agent=use_agent, agent_type=agent_type
        )

    async def upload_files(self, paths: List[Path]) -> Dict[str, str]:
        if not self.connected or not self.client:
            console.print("[red]Not connected to H2OGPTE. Use /register first.[/red]")
            return {}

        console.print(f"[blue]Uploading {len(paths)} file(s)...[/blue]")
        return await self.client.upload_files(paths)

    async def close(self):
        self.connected = False
        self.client = None
