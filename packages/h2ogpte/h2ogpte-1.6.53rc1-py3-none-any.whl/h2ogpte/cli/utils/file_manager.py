import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional

import aiofiles
import git
import pathspec
from rich.console import Console
from rich.filesize import decimal
from rich.table import Table
from rich.tree import Tree

console = Console()


class FileManager:
    """Manages file operations and directory scanning."""

    def __init__(self):
        self.default_ignore_patterns = [
            "__pycache__",
            "*.pyc",
            ".git",
            ".svn",
            ".hg",
            "node_modules",
            "venv",
            ".env",
            "*.log",
            ".DS_Store",
            "Thumbs.db",
            ".idea",
            ".vscode",
            "*.swp",
            "*.swo",
            "*~",
            ".cache",
            "dist",
            "build",
            "*.egg-info",
        ]

    def get_gitignore_spec(self, directory: Path) -> Optional[pathspec.PathSpec]:
        """Get gitignore pathspec for a directory."""
        gitignore_path = directory / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                return pathspec.PathSpec.from_lines("gitwildmatch", f)
        return None

    def should_ignore(
        self, path: Path, gitignore_spec: Optional[pathspec.PathSpec] = None
    ) -> bool:
        """Check if a path should be ignored."""
        # Check default ignore patterns
        spec = pathspec.PathSpec.from_lines(
            "gitwildmatch", self.default_ignore_patterns
        )
        if spec.match_file(path.name):
            return True

        # Check gitignore
        if gitignore_spec and gitignore_spec.match_file(str(path)):
            return True

        return False

    def scan_directory(
        self,
        directory: Path,
        patterns: Optional[List[str]] = None,
        recursive: bool = True,
        include_hidden: bool = False,
        respect_gitignore: bool = True,
    ) -> List[Path]:
        """Scan directory for files matching patterns."""
        if not directory.exists():
            console.print(f"[red]Directory not found: {directory}[/red]")
            return []

        files = []
        gitignore_spec = (
            self.get_gitignore_spec(directory) if respect_gitignore else None
        )

        def scan_dir(dir_path: Path):
            try:
                for item in dir_path.iterdir():
                    # Skip hidden files if not included
                    if not include_hidden and item.name.startswith("."):
                        continue

                    # Check if should ignore
                    if self.should_ignore(item, gitignore_spec):
                        continue

                    if item.is_file():
                        # Check patterns if provided
                        if patterns:
                            if any(item.match(pattern) for pattern in patterns):
                                files.append(item)
                        else:
                            files.append(item)
                    elif item.is_dir() and recursive:
                        scan_dir(item)
            except PermissionError:
                console.print(f"[yellow]Permission denied: {dir_path}[/yellow]")

        scan_dir(directory)
        return sorted(files)

    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get detailed information about a file."""
        if not file_path.exists():
            return {}

        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(str(file_path))

        return {
            "path": str(file_path),
            "name": file_path.name,
            "size": stat.st_size,
            "size_human": decimal(stat.st_size),
            "mime_type": mime_type,
            "extension": file_path.suffix,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_text": self.is_text_file(file_path),
            "hash": self.get_file_hash(file_path),
        }

    def is_text_file(self, file_path: Path) -> bool:
        """Check if a file is a text file."""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                return not bool(chunk.translate(None, bytes(range(32, 127))))
        except:
            return False

    def get_file_hash(self, file_path: Path, algorithm: str = "md5") -> str:
        """Calculate file hash."""
        hash_func = hashlib.new(algorithm)
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except:
            return ""

    def display_file_tree(self, directory: Path, max_depth: int = 3):
        """Display directory structure as a tree."""
        tree = Tree(f"[bold cyan]{directory}[/bold cyan]")

        def add_directory(tree_node, path: Path, depth: int = 0):
            if depth >= max_depth:
                return

            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                for item in items:
                    if item.name.startswith("."):
                        continue

                    if item.is_dir():
                        branch = tree_node.add(f"[blue]{item.name}/[/blue]")
                        add_directory(branch, item, depth + 1)
                    else:
                        size = decimal(item.stat().st_size)
                        tree_node.add(f"{item.name} [dim]({size})[/dim]")
            except PermissionError:
                tree_node.add("[red]Permission Denied[/red]")

        add_directory(tree, directory)
        console.print(tree)

    def display_file_list(self, files: List[Path], show_details: bool = True):
        """Display list of files in a table."""
        if not files:
            console.print("[yellow]No files found[/yellow]")
            return

        if show_details:
            table = Table(title=f"Files ({len(files)} total)")
            table.add_column("Name", style="cyan")
            table.add_column("Size", style="white", justify="right")
            table.add_column("Type", style="dim")
            table.add_column("Modified", style="dim")

            for file in files[:50]:  # Limit display to 50 files
                info = self.get_file_info(file)
                table.add_row(
                    file.name,
                    info.get("size_human", ""),
                    info.get("extension", ""),
                    self._format_timestamp(info.get("modified", 0)),
                )

            console.print(table)

            if len(files) > 50:
                console.print(f"[dim]... and {len(files) - 50} more files[/dim]")
        else:
            for file in files:
                console.print(f"  • {file}")

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp for display."""
        from datetime import datetime

        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")


class FileUploader:
    """Handles file upload operations."""

    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager

    async def prepare_files(
        self, paths: List[Path], chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """Prepare files for upload with chunking if needed."""
        prepared_files = []

        for path in paths:
            if not path.exists():
                console.print(f"[red]File not found: {path}[/red]")
                continue

            info = self.file_manager.get_file_info(path)

            if info.get("is_text"):
                chunks = await self.chunk_text_file(path, chunk_size, chunk_overlap)
                for i, chunk in enumerate(chunks):
                    prepared_files.append(
                        {
                            "path": path,
                            "content": chunk,
                            "metadata": {
                                **info,
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                            },
                        }
                    )
            else:
                # For binary files, just add metadata
                prepared_files.append({"path": path, "content": None, "metadata": info})

        return prepared_files

    async def chunk_text_file(
        self, file_path: Path, chunk_size: int, chunk_overlap: int
    ) -> List[str]:
        """Split text file into chunks."""
        chunks = []

        async with aiofiles.open(
            file_path, "r", encoding="utf-8", errors="ignore"
        ) as f:
            content = await f.read()

        # Simple chunking by character count
        start = 0
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]

            # Try to break at sentence boundary
            if end < len(content):
                last_period = chunk.rfind(".")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > chunk_size // 2:
                    chunk = content[start : start + break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk)
            start = end - chunk_overlap

        return chunks


class DirectoryAnalyzer:
    """Analyzes directory structure and content."""

    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager

    async def analyze(self, directory: Path) -> Dict[str, Any]:
        """Analyze directory structure and content."""
        console.print(f"[blue]Analyzing directory: {directory}[/blue]")

        files = self.file_manager.scan_directory(directory)

        # Categorize files
        categories = {
            "code": [],
            "documents": [],
            "data": [],
            "config": [],
            "other": [],
        }

        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".go",
            ".rs",
            ".rb",
        }
        doc_extensions = {".md", ".txt", ".pdf", ".docx", ".rst"}
        data_extensions = {".json", ".csv", ".xml", ".yaml", ".yml"}
        config_extensions = {".toml", ".ini", ".env", ".config"}

        total_size = 0
        for file in files:
            info = self.file_manager.get_file_info(file)
            total_size += info.get("size", 0)

            ext = file.suffix.lower()
            if ext in code_extensions:
                categories["code"].append(file)
            elif ext in doc_extensions:
                categories["documents"].append(file)
            elif ext in data_extensions:
                categories["data"].append(file)
            elif ext in config_extensions:
                categories["config"].append(file)
            else:
                categories["other"].append(file)

        # Check for git repository
        is_git_repo = (directory / ".git").exists()
        git_info = {}
        if is_git_repo:
            try:
                repo = git.Repo(directory)
                git_info = {
                    "branch": repo.active_branch.name,
                    "commits": len(list(repo.iter_commits())),
                    "remotes": [remote.name for remote in repo.remotes],
                    "modified_files": len(repo.index.diff(None)),
                    "untracked_files": len(repo.untracked_files),
                }
            except:
                pass

        analysis = {
            "directory": str(directory),
            "total_files": len(files),
            "total_size": total_size,
            "total_size_human": decimal(total_size),
            "categories": {k: len(v) for k, v in categories.items()},
            "file_types": categories,
            "is_git_repo": is_git_repo,
            "git_info": git_info,
        }

        self.display_analysis(analysis)
        return analysis

    def display_analysis(self, analysis: Dict[str, Any]):
        """Display directory analysis results."""
        # Basic stats
        stats_table = Table(title="Directory Analysis", show_header=False)
        stats_table.add_column("Property", style="cyan")
        stats_table.add_column("Value", style="white")

        stats_table.add_row("Directory", analysis["directory"])
        stats_table.add_row("Total Files", str(analysis["total_files"]))
        stats_table.add_row("Total Size", analysis["total_size_human"])

        console.print(stats_table)

        # File categories
        cat_table = Table(title="File Categories")
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Count", style="white", justify="right")

        for category, count in analysis["categories"].items():
            if count > 0:
                cat_table.add_row(category.capitalize(), str(count))

        console.print(cat_table)

        # Git info if available
        if analysis["is_git_repo"] and analysis["git_info"]:
            git_table = Table(title="Git Repository Info", show_header=False)
            git_table.add_column("Property", style="cyan")
            git_table.add_column("Value", style="white")

            git_info = analysis["git_info"]
            git_table.add_row("Branch", git_info.get("branch", "N/A"))
            git_table.add_row("Commits", str(git_info.get("commits", 0)))
            git_table.add_row("Modified Files", str(git_info.get("modified_files", 0)))
            git_table.add_row(
                "Untracked Files", str(git_info.get("untracked_files", 0))
            )

            console.print(git_table)
