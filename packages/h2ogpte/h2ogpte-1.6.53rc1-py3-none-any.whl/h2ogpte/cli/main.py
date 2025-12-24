import asyncio
import sys
from rich.traceback import install
from rich.console import Console

from .core.app import initialize_app
from .commands.dispatcher import dispatch_command

install(show_locals=True)


async def main_loop():
    try:
        app = initialize_app()
        app.settings.ensure_directories()
        app.ui.show_welcome()
        await app.try_auto_reconnect()

        exit_attempts = 0
        while True:
            try:
                command = app.ui.prompt.get_input("❯ ")

                if not command.strip():
                    continue

                if command in ["/exit", "/quit"]:
                    exit_attempts += 1
                    if exit_attempts > 1 and not sys.stdin.isatty():
                        app.console.print(
                            "[cyan]Non-interactive mode: Exiting without confirmation[/cyan]"
                        )
                        break

                should_continue = await dispatch_command(command)
                if not should_continue:
                    break

                if command not in ["/exit", "/quit"]:
                    exit_attempts = 0

            except KeyboardInterrupt:
                app.console.print(
                    "\n[yellow]⚠ Interrupted. Use /exit to quit or continue typing.[/yellow]"
                )
                continue
            except EOFError:
                app.console.print("\n[cyan]Goodbye![/cyan]")
                break
            except Exception as e:
                app.console.print(f"[red]Unexpected error: {e}[/red]")
                app.console.print("[dim]Type /exit to quit or try again[/dim]")
                continue

        try:
            await app.cleanup()
        except Exception as e:
            app.console.print(
                f"[yellow]Warning: Could not clean up properly: {e}[/yellow]"
            )

    except Exception as e:
        Console().print(f"[red]Critical error in main loop: {e}[/red]")


def main():
    try:
        try:
            loop = asyncio.get_running_loop()
            Console().print(
                "[yellow]Running in existing event loop, creating task...[/yellow]"
            )
            task = loop.create_task(main_loop())
            loop.run_until_complete(task)
        except RuntimeError:
            asyncio.run(main_loop())
    except KeyboardInterrupt:
        Console().print("\n[yellow]Interrupted[/yellow]")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"[red]Fatal error: {e}[/red]")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
