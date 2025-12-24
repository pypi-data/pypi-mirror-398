from pathlib import Path
from typing import Optional

import toml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from rich.console import Console

from .encryption import SecureStorage

console = Console()


class RAGConfig(BaseModel):
    """RAG system configuration."""

    endpoint: str = Field(default="", description="RAG system endpoint URL")
    api_key: str = Field(default="", description="API key for RAG system")
    collection_name: str = Field(
        default="default", description="Collection name in RAG"
    )
    chunk_size: int = Field(
        default=1000, description="Chunk size for document processing"
    )
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")


class AgentConfig(BaseModel):
    """Agent system configuration."""

    endpoint: str = Field(default="", description="Agent system endpoint URL")
    api_key: str = Field(default="", description="API key for agent system")
    model: str = Field(default="gpt-4", description="Model to use for agent")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: int = Field(default=2000, description="Maximum tokens for response")
    timeout: int = Field(default=300, description="Timeout in seconds")


class UIConfig(BaseModel):
    """UI configuration."""

    theme: str = Field(default="monokai", description="Syntax highlighting theme")
    show_progress: bool = Field(default=True, description="Show progress bars")
    auto_complete: bool = Field(default=True, description="Enable autocomplete")
    history_size: int = Field(default=1000, description="Command history size")
    animation: bool = Field(default=True, description="Enable animations")


class Settings(BaseSettings):
    """Main application settings."""

    app_name: str = "h2oGPTe-CLI"
    debug: bool = False

    config_dir: Path = Field(default_factory=lambda: Path.home() / ".h2ogpte-cli")
    data_dir: Path = Field(
        default_factory=lambda: Path.home() / ".h2ogpte-cli" / "data"
    )
    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".h2ogpte-cli" / "cache"
    )
    logs_dir: Path = Field(
        default_factory=lambda: Path.home() / ".h2ogpte-cli" / "logs"
    )

    rag: RAGConfig = Field(default_factory=RAGConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    ui: UIConfig = Field(default_factory=UIConfig)

    _secure_storage: Optional[SecureStorage] = None

    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            ".env.production",
            ".env.test",
            ".env.development",
            ".env.local",
        ),
        env_prefix="H2OGPTE_CLI_",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    def _get_secure_storage(self) -> SecureStorage:
        """Get or create secure storage instance."""
        if self._secure_storage is None:
            self._secure_storage = SecureStorage(self.config_dir)
        return self._secure_storage

    def get_rag_api_key(self) -> str:
        """Get decrypted RAG API key."""
        storage = self._get_secure_storage()
        if storage.is_encrypted(self.rag.api_key):
            return storage.decrypt(self.rag.api_key)
        return self.rag.api_key

    def get_agent_api_key(self) -> str:
        """Get decrypted Agent API key."""
        storage = self._get_secure_storage()
        if storage.is_encrypted(self.agent.api_key):
            return storage.decrypt(self.agent.api_key)
        return self.agent.api_key

    def set_rag_api_key(self, api_key: str):
        """Set encrypted RAG API key."""
        storage = self._get_secure_storage()
        self.rag.api_key = storage.encrypt(api_key)

    def set_agent_api_key(self, api_key: str):
        """Set encrypted Agent API key."""
        storage = self._get_secure_storage()
        self.agent.api_key = storage.encrypt(api_key)

    def save(self, path: Optional[Path] = None):
        """Save configuration to file."""
        if path is None:
            path = self.config_dir / "config.toml"

        path.parent.mkdir(parents=True, exist_ok=True)

        config_dict = {
            "app": {
                "name": self.app_name,
                "debug": self.debug,
            },
            "directories": {
                "config": str(self.config_dir),
                "data": str(self.data_dir),
                "cache": str(self.cache_dir),
                "logs": str(self.logs_dir),
            },
            "rag": self.rag.model_dump(),
            "agent": self.agent.model_dump(),
            "ui": self.ui.model_dump(),
        }

        with open(path, "w") as f:
            toml.dump(config_dict, f)

        console.print(f"[green]✓[/green] Configuration saved to {path}")

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Settings":
        """Load configuration from file."""
        if path is None:
            path = Path.home() / ".h2ogpte-cli" / "config.toml"

        if not path.exists():
            return cls()

        try:
            with open(path, "r") as f:
                config_dict = toml.load(f)

            # Flatten the configuration
            flat_config = {}

            if "app" in config_dict:
                app_config = config_dict["app"]
                # Map config fields to Settings fields
                if "name" in app_config:
                    flat_config["app_name"] = app_config["name"]
                if "version" in app_config:
                    flat_config["version"] = app_config["version"]
                if "debug" in app_config:
                    flat_config["debug"] = app_config["debug"]

            if "directories" in config_dict:
                dirs = config_dict["directories"]
                for key in ["config_dir", "data_dir", "cache_dir", "logs_dir"]:
                    if key.replace("_dir", "") in dirs:
                        flat_config[key] = Path(dirs[key.replace("_dir", "")])

            if "rag" in config_dict:
                flat_config["rag"] = RAGConfig(**config_dict["rag"])

            if "agent" in config_dict:
                flat_config["agent"] = AgentConfig(**config_dict["agent"])

            if "ui" in config_dict:
                flat_config["ui"] = UIConfig(**config_dict["ui"])

            return cls(**flat_config)

        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Error loading config: {e}")
            return cls()

    def ensure_directories(self):
        """Ensure all required directories exist."""
        for dir_path in [self.config_dir, self.data_dir, self.cache_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings.load()
