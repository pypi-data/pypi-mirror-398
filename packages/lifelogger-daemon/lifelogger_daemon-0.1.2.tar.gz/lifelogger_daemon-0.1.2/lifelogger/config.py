"""Configuration management for Lifelogger."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CaptureConfig(BaseSettings):
    """Configuration for what to capture."""

    model_config = SettingsConfigDict(env_prefix="LIFELOGGER_CAPTURE_")

    enable_keypress: bool = True
    enable_mouseclick: bool = True
    enable_screenshot_on_click: bool = False
    screenshot_quality: int = Field(default=85, ge=1, le=100)
    screenshot_format: Literal["png", "jpg"] = "jpg"


class CronScreenshotConfig(BaseSettings):
    """Configuration for periodic screenshots."""

    model_config = SettingsConfigDict(env_prefix="LIFELOGGER_CRON_")

    enabled: bool = True
    schedule: str = "*/5 * * * *"  # Every 5 minutes by default


class SummarizerConfig(BaseSettings):
    """Configuration for LLM summarization."""

    model_config = SettingsConfigDict(env_prefix="LIFELOGGER_SUMMARIZER_")

    enabled: bool = True
    model: str = "gpt-5.2-nano"  # As requested; fallback to gpt-4o-mini if unavailable
    chunk_size: int = 100  # Number of events per chunk
    chunk_interval_seconds: int = 300  # Also summarize every 5 minutes
    compact_interval_chunks: int = 10  # Compact every N chunk summaries


class Config(BaseSettings):
    """Main configuration for Lifelogger."""

    model_config = SettingsConfigDict(
        env_prefix="LIFELOGGER_",
        env_nested_delimiter="__",
    )

    data_dir: Path = Field(default_factory=lambda: Path.home() / ".lifelogger")
    openai_api_key: str | None = None

    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    cron_screenshot: CronScreenshotConfig = Field(default_factory=CronScreenshotConfig)
    summarizer: SummarizerConfig = Field(default_factory=SummarizerConfig)

    @property
    def events_dir(self) -> Path:
        """Directory for raw event JSONL files."""
        return self.data_dir / "events"

    @property
    def screenshots_dir(self) -> Path:
        """Directory for screenshot images."""
        return self.data_dir / "screenshots"

    @property
    def summaries_dir(self) -> Path:
        """Directory for chunk summaries."""
        return self.data_dir / "summaries"

    @property
    def state_dir(self) -> Path:
        """Directory for compacted running state."""
        return self.data_dir / "state"

    @property
    def config_file(self) -> Path:
        """Path to config file."""
        return self.data_dir / "config.json"

    @property
    def pid_file(self) -> Path:
        """Path to daemon PID file."""
        return self.data_dir / "lifelogger.pid"

    def ensure_dirs(self) -> None:
        """Create all required directories."""
        for d in [
            self.data_dir,
            self.events_dir,
            self.screenshots_dir,
            self.summaries_dir,
            self.state_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def save(self) -> None:
        """Save configuration to file."""
        self.ensure_dirs()
        self.config_file.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file or create default."""
        default_path = Path.home() / ".lifelogger" / "config.json"
        if default_path.exists():
            return cls.model_validate_json(default_path.read_text())
        config = cls()
        config.ensure_dirs()
        return config
