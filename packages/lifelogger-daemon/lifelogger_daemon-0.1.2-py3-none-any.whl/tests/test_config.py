"""Tests for configuration module."""

import tempfile
from pathlib import Path

from lifelogger.config import Config, CaptureConfig, CronScreenshotConfig, SummarizerConfig


def test_default_config():
    """Test default configuration values."""
    config = Config()
    assert config.data_dir == Path.home() / ".lifelogger"
    assert config.openai_api_key is None


def test_capture_config_defaults():
    """Test capture configuration defaults."""
    config = CaptureConfig()
    assert config.enable_keypress is True
    assert config.enable_mouseclick is True
    assert config.enable_screenshot_on_click is False
    assert config.screenshot_quality == 85
    assert config.screenshot_format == "jpg"


def test_cron_screenshot_config_defaults():
    """Test cron screenshot configuration defaults."""
    config = CronScreenshotConfig()
    assert config.enabled is True
    assert config.schedule == "*/5 * * * *"


def test_summarizer_config_defaults():
    """Test summarizer configuration defaults."""
    config = SummarizerConfig()
    assert config.enabled is True
    assert config.chunk_size == 100
    assert config.chunk_interval_seconds == 300


def test_config_directories():
    """Test directory path properties."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(data_dir=Path(tmpdir))
        assert config.events_dir == Path(tmpdir) / "events"
        assert config.screenshots_dir == Path(tmpdir) / "screenshots"
        assert config.summaries_dir == Path(tmpdir) / "summaries"
        assert config.state_dir == Path(tmpdir) / "state"


def test_ensure_dirs():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(data_dir=Path(tmpdir) / "lifelogger")
        config.ensure_dirs()

        assert config.data_dir.exists()
        assert config.events_dir.exists()
        assert config.screenshots_dir.exists()
        assert config.summaries_dir.exists()
        assert config.state_dir.exists()


def test_config_save_and_load():
    """Test configuration save and load."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(data_dir=Path(tmpdir))
        config.openai_api_key = "test-key"
        config.capture.enable_keypress = False
        config.save()

        # Load and verify
        loaded = Config.model_validate_json(config.config_file.read_text())
        assert loaded.openai_api_key == "test-key"
        assert loaded.capture.enable_keypress is False
