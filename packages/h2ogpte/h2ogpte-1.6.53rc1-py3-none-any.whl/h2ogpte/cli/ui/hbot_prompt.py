import sys
import os
import termios
import tty
from typing import List, Optional, Dict
from rich.console import Console

console = Console()


class HBOTPrompt:
    def __init__(self):
        self.commands = {
            "/help": "Show help information",
            "/register": "Connect/disconnect H2OGPTE",
            "/disconnect": "Disconnect and clear credentials",
            "/upload": "Upload files to collection",
            "/analyze": "Analyze directory",
            "/agent": "Use AI agent mode",
            "/research": "Deep research with AI agent",
            "/config": "Configure settings",
            "/status": "Show session status",
            "/clear": "Clear screen",
            "/exit": "Exit H2OGPTE CLI",
            "/quit": "Exit H2OGPTE CLI",
            "/history": "Show command history",
            "/save": "Save session",
            "/load": "Load session",
            "/session": "Create chat session",
            "/collection": "Create new collection",
        }
        self.max_suggestions_shown = 5
        self.command_history = []
        self.history_position = -1
        self._status_bar = None

    def getch(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def get_matching_commands(self, text: str) -> List[str]:
        if not text.startswith("/"):
            return []
        return [cmd for cmd in self.commands.keys() if cmd.startswith(text)]

    def add_to_history(self, command: str):
        if command and command.strip():
            # Remove if it's already the last command to avoid duplicates
            if self.command_history and self.command_history[-1] == command:
                return
            # Remove from middle if it exists
            if command in self.command_history:
                self.command_history.remove(command)
            # Add to end
            self.command_history.append(command)
            # Keep only last 100 commands
            if len(self.command_history) > 100:
                self.command_history = self.command_history[-100:]

    def update_suggestions(self, current_text: str, selected: int = 0):
        matches = self.get_matching_commands(current_text)

        # Clear lines below
        print("\033[J", end="")

        if matches and current_text.startswith("/"):
            # Show suggestions without separator - cleaner look
            print()  # One newline to separate from input

            # Calculate scrolling window
            total_matches = len(matches)

            if total_matches <= self.max_suggestions_shown:
                # Show all matches if they fit
                start_idx = 0
                end_idx = total_matches
                scroll_indicator = ""
            else:
                # Calculate scrolling window around selected item
                if selected < self.max_suggestions_shown // 2:
                    # Near the beginning
                    start_idx = 0
                    end_idx = self.max_suggestions_shown
                elif selected >= total_matches - (self.max_suggestions_shown // 2):
                    # Near the end
                    start_idx = total_matches - self.max_suggestions_shown
                    end_idx = total_matches
                else:
                    # In the middle
                    start_idx = selected - (self.max_suggestions_shown // 2)
                    end_idx = start_idx + self.max_suggestions_shown

                # Create scroll indicator
                scroll_indicator = (
                    f"    \033[90m[{selected + 1}/{total_matches}] ↕ scroll\033[0m"
                )

            # Show the visible window of suggestions
            for i in range(start_idx, end_idx):
                cmd = matches[i]
                desc = self.commands.get(cmd, "")
                if i == selected:
                    # Highlighted selection
                    print(f"\033[K  → \033[92m{cmd}\033[0m  {desc}")
                else:
                    # Normal display
                    print(f"\033[K    \033[36m{cmd}\033[0m  \033[90m{desc}\033[0m")

            # Show scroll indicator if there are more items
            if scroll_indicator:
                print(f"\033[K{scroll_indicator}")

            # Move cursor back to input line
            lines_up = min(total_matches, self.max_suggestions_shown) + 1
            if scroll_indicator:
                lines_up += 1
            print(f"\033[{lines_up}A", end="")

        sys.stdout.flush()

    def _show_status_bar(self):
        if self._status_bar and sys.stdin.isatty():
            self._status_bar.print_status_line()

    def get_input(self, prompt_text: str = "❯ ") -> str:
        # Non-interactive mode fallback
        if not sys.stdin.isatty():
            try:
                user_input = input(prompt_text).strip()
                return user_input if user_input else ""
            except EOFError:
                return "/exit"

        # Show status bar right before input prompt
        self._show_status_bar()

        # Show prompt (no extra newline)
        print(f"{prompt_text}", end="", flush=True)

        current_text = ""
        cursor_pos = 0
        selected_suggestion = 0

        while True:
            char = self.getch()

            # Handle special characters
            if ord(char) == 3:  # Ctrl+C
                print("\033[J", end="")  # Clear below
                print()  # Single newline
                raise KeyboardInterrupt()

            elif ord(char) == 4:  # Ctrl+D
                print("\033[J", end="")  # Clear below
                print()  # Single newline
                return "/exit"

            elif char == "\r" or char == "\n":  # Enter
                matches = self.get_matching_commands(current_text)

                # If there are suggestions and current text is incomplete, auto-complete first
                if (
                    matches
                    and selected_suggestion < len(matches)
                    and current_text != matches[selected_suggestion]
                ):
                    # Auto-complete the selected suggestion
                    current_text = matches[selected_suggestion]
                    cursor_pos = len(current_text)

                    # Add a space for easy argument typing
                    current_text += " "
                    cursor_pos += 1

                    # Redraw with the completed command
                    print(f"\r{prompt_text}{current_text}", end="", flush=True)

                    # Clear suggestions and reset selection
                    print("\033[J", end="")
                    selected_suggestion = 0
                    continue  # Don't return, let user continue typing or press Enter again

                else:
                    # No suggestions or already completed - execute the command
                    print("\033[J", end="")  # Clear suggestions
                    print()  # Single newline only
                    command = current_text.strip()
                    if command:
                        self.add_to_history(command)
                        # Reset history position for next command
                        self.history_position = -1
                    return command

            elif ord(char) == 127 or ord(char) == 8:  # Backspace/Delete
                if cursor_pos > 0:
                    # Reset history position when user modifies text
                    self.history_position = -1

                    # Delete character
                    current_text = (
                        current_text[: cursor_pos - 1] + current_text[cursor_pos:]
                    )
                    cursor_pos -= 1

                    # Clear and redraw the line properly
                    print(f"\r\033[K{prompt_text}{current_text}", end="", flush=True)

                    # Reset selection and update suggestions
                    selected_suggestion = 0
                    self.update_suggestions(current_text, selected_suggestion)

            elif char == "\t":  # Tab - auto-complete
                matches = self.get_matching_commands(current_text)
                if matches:
                    current_text = (
                        matches[selected_suggestion]
                        if selected_suggestion < len(matches)
                        else matches[0]
                    )
                    cursor_pos = len(current_text)
                    print(f"\r{prompt_text}{current_text}", end="", flush=True)
                    selected_suggestion = 0
                    self.update_suggestions(current_text, selected_suggestion)

            elif char == "\033":  # Escape sequence (arrow keys)
                next1 = self.getch()
                next2 = self.getch()

                if next1 == "[":
                    if next2 == "A":  # Up arrow
                        if current_text == "":
                            # Navigate command history ONLY when text is empty
                            if self.command_history:
                                if self.history_position == -1:
                                    # From empty, go to most recent command
                                    self.history_position = (
                                        len(self.command_history) - 1
                                    )
                                elif self.history_position > 0:
                                    # Go to previous command in history
                                    self.history_position -= 1
                                # else: already at oldest command, stay there

                                if (
                                    0
                                    <= self.history_position
                                    < len(self.command_history)
                                ):
                                    current_text = self.command_history[
                                        self.history_position
                                    ]
                                    cursor_pos = len(current_text)
                                    print(
                                        f"\r{prompt_text}{current_text}",
                                        end="",
                                        flush=True,
                                    )
                                    print("\033[J", end="")  # Clear suggestions
                        else:
                            # Navigate command suggestions when user has typed something
                            matches = self.get_matching_commands(current_text)
                            if matches and selected_suggestion > 0:
                                selected_suggestion -= 1
                                self.update_suggestions(
                                    current_text, selected_suggestion
                                )

                    elif next2 == "B":  # Down arrow
                        if current_text == "":
                            # Navigate command history ONLY when text is empty
                            if self.command_history:
                                if self.history_position == -1:
                                    # From empty, can't go down further, stay empty
                                    pass
                                elif (
                                    self.history_position
                                    < len(self.command_history) - 1
                                ):
                                    # Go to next command in history
                                    self.history_position += 1
                                    current_text = self.command_history[
                                        self.history_position
                                    ]
                                    cursor_pos = len(current_text)
                                    print(
                                        f"\r{prompt_text}{current_text}",
                                        end="",
                                        flush=True,
                                    )
                                    print("\033[J", end="")  # Clear suggestions
                                else:
                                    # At newest command, go back to empty
                                    self.history_position = -1
                                    current_text = ""
                                    cursor_pos = 0
                                    print(f"\r{prompt_text}", end="", flush=True)
                                    print("\033[J", end="")  # Clear suggestions
                        else:
                            # Navigate command suggestions when user has typed something
                            matches = self.get_matching_commands(current_text)
                            if matches and selected_suggestion < len(matches) - 1:
                                selected_suggestion += 1
                                self.update_suggestions(
                                    current_text, selected_suggestion
                                )

                    elif next2 == "C":  # Right arrow
                        if cursor_pos < len(current_text):
                            cursor_pos += 1
                            print("\033[C", end="", flush=True)

                    elif next2 == "D":  # Left arrow
                        if cursor_pos > 0:
                            cursor_pos -= 1
                            print("\033[D", end="", flush=True)

            elif char.isprintable():  # Regular character
                # Reset history position when user starts typing
                self.history_position = -1

                # Add character
                current_text = (
                    current_text[:cursor_pos] + char + current_text[cursor_pos:]
                )
                cursor_pos += 1

                # Redraw line
                print(f"\r{prompt_text}{current_text}", end="", flush=True)

                # Reset selection and update suggestions
                selected_suggestion = 0
                self.update_suggestions(current_text, selected_suggestion)

    def confirm(self, message: str, default: bool = False) -> bool:
        """Get confirmation from user."""
        if not sys.stdin.isatty():
            console.print(f"{message} (non-interactive mode, using default: {default})")
            return default

        default_str = "Y/n" if default else "y/N"
        try:
            response = input(f"{message} ({default_str}): ").strip().lower()
            if not response:
                return default
            return response in ["y", "yes", "true", "1"]
        except (EOFError, KeyboardInterrupt):
            return False

    def select_from_list(
        self, choices: List[str], message: str = "Select an option:"
    ) -> str:
        """Present a selection list."""
        if not choices:
            return ""

        console.print(f"{message}")
        for i, choice in enumerate(choices, 1):
            console.print(f"  {i}. {choice}")

        while True:
            try:
                selection = input("Enter choice number: ").strip()
                if selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(choices):
                        return choices[idx]
                console.print("[red]Please enter a valid number[/red]")
            except (EOFError, KeyboardInterrupt):
                return choices[0] if choices else ""

    def get_multiselect(
        self, choices: List[str], message: str = "Select options:"
    ) -> List[str]:
        """Present a multi-selection list."""
        if not choices:
            return []

        console.print(f"{message}")
        console.print("[dim]Enter numbers separated by commas[/dim]")
        for i, choice in enumerate(choices, 1):
            console.print(f"  {i}. {choice}")

        try:
            selection = input("Enter choices: ").strip()
            selected = []
            for num in selection.split(","):
                try:
                    idx = int(num.strip()) - 1
                    if 0 <= idx < len(choices):
                        selected.append(choices[idx])
                except ValueError:
                    continue
            return selected
        except (EOFError, KeyboardInterrupt):
            return []

    def get_secret(self, message: str, default: str = "") -> str:
        """Get secret input (like API keys) - doesn't go to history."""
        try:
            import getpass

            # Use getpass to hide input
            user_input = getpass.getpass(f"{message}: ").strip()
            return user_input if user_input else default
        except (EOFError, KeyboardInterrupt):
            return ""

    def get_input_with_default(self, message: str, default: str = "") -> str:
        """Get input with a default value shown in prompt."""
        try:
            prompt_with_default = f"{message}"
            if default:
                prompt_with_default += f" [{default}]"
            prompt_with_default += ": "

            user_input = input(prompt_with_default).strip()
            return user_input if user_input else default
        except (EOFError, KeyboardInterrupt):
            return default

    def get_path(self, message: str = "Enter path:", only_directories: bool = False):
        """Get a file or directory path."""
        from pathlib import Path

        try:
            path_str = input(f"{message} ").strip()
            return Path(path_str) if path_str else None
        except (EOFError, KeyboardInterrupt):
            return None
