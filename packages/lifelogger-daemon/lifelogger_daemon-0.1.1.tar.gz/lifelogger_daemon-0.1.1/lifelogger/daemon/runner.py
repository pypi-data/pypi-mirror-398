"""Main daemon runner that orchestrates all components."""

import atexit
import os
import platform
import signal
import sys
import threading
import time
from pathlib import Path

from ..capture import CronScreenshotScheduler, KeyboardCapture, MouseCapture, ScreenshotCapture
from ..config import Config
from ..models import ChunkSummary, CompactState, Event
from ..storage import EventStore, StateStore, SummaryStore
from ..summarize import SummarizationProcessor

IS_WINDOWS = platform.system() == "Windows"


class LifeloggerDaemon:
    """Main daemon that coordinates all capture and summarization components."""

    def __init__(self, config: Config):
        """Initialize the daemon.

        Args:
            config: Application configuration.
        """
        self.config = config
        config.ensure_dirs()

        # Initialize stores
        self.event_store = EventStore(config.events_dir)
        self.summary_store = SummaryStore(config.summaries_dir)
        self.state_store = StateStore(config.state_dir)

        # Initialize screenshot capture
        self.screenshot_capture = ScreenshotCapture(
            screenshots_dir=config.screenshots_dir,
            quality=config.capture.screenshot_quality,
            format=config.capture.screenshot_format,
        )

        # Initialize keyboard capture
        self.keyboard_capture: KeyboardCapture | None = None
        if config.capture.enable_keypress:
            self.keyboard_capture = KeyboardCapture(on_event=self._on_event)

        # Initialize mouse capture
        self.mouse_capture: MouseCapture | None = None
        if config.capture.enable_mouseclick:
            screenshot_callback = None
            if config.capture.enable_screenshot_on_click:
                screenshot_callback = self.screenshot_capture.capture_for_click

            self.mouse_capture = MouseCapture(
                on_event=self._on_event,
                on_click_screenshot=screenshot_callback,
            )

        # Initialize cron screenshot scheduler
        self.cron_scheduler: CronScreenshotScheduler | None = None
        if config.cron_screenshot.enabled:
            self.cron_scheduler = CronScreenshotScheduler(
                cron_expression=config.cron_screenshot.schedule,
                screenshots_dir=config.screenshots_dir,
                on_event=self._on_event,
                quality=config.capture.screenshot_quality,
                format=config.capture.screenshot_format,
            )

        # Initialize summarization processor
        self.summarizer = SummarizationProcessor(
            config=config,
            event_store=self.event_store,
            summary_store=self.summary_store,
            state_store=self.state_store,
            on_chunk_summary=self._on_chunk_summary,
            on_state_update=self._on_state_update,
        )

        self._running = False
        self._stop_event = threading.Event()

    def _on_event(self, event: Event) -> None:
        """Handle captured events."""
        self.event_store.append(event)

    def _on_chunk_summary(self, summary: ChunkSummary) -> None:
        """Handle new chunk summaries."""
        print(f"[Chunk {summary.chunk_index}] {summary.event_count} events: {summary.summary_text[:100]}...")

    def _on_state_update(self, state: CompactState) -> None:
        """Handle state updates."""
        print(f"[State v{state.version}] {state.total_events} total events, {state.total_chunks} chunks")

    def _write_pid_file(self) -> None:
        """Write PID file for daemon management."""
        self.config.pid_file.write_text(str(os.getpid()))

    def _remove_pid_file(self) -> None:
        """Remove PID file on shutdown."""
        if self.config.pid_file.exists():
            self.config.pid_file.unlink()

    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        if not IS_WINDOWS:
            signal.signal(signal.SIGTERM, signal_handler)
        else:
            # Windows: SIGTERM not fully supported, use SIGBREAK if available
            if hasattr(signal, "SIGBREAK"):
                signal.signal(signal.SIGBREAK, signal_handler)

    def start(self) -> None:
        """Start all daemon components."""
        if self._running:
            return

        print(f"Starting Lifelogger daemon...")
        print(f"Data directory: {self.config.data_dir}")

        self._running = True
        self._write_pid_file()
        atexit.register(self._remove_pid_file)
        self._setup_signal_handlers()

        # Start capture components
        if self.keyboard_capture:
            self.keyboard_capture.start()
            print("  - Keyboard capture: enabled")

        if self.mouse_capture:
            self.mouse_capture.start()
            print("  - Mouse capture: enabled")

        if self.cron_scheduler:
            self.cron_scheduler.start()
            print(f"  - Cron screenshots: enabled ({self.config.cron_screenshot.schedule})")

        # Start summarization
        if self.config.summarizer.enabled:
            self.summarizer.start()
            print(f"  - Summarization: enabled (model: {self.config.summarizer.model})")
        else:
            print("  - Summarization: disabled")

        print("\nLifelogger is running. Press Ctrl+C to stop.")

    def stop(self) -> None:
        """Stop all daemon components."""
        if not self._running:
            return

        print("Stopping Lifelogger daemon...")
        self._running = False
        self._stop_event.set()

        # Stop capture components
        if self.keyboard_capture:
            self.keyboard_capture.stop()

        if self.mouse_capture:
            self.mouse_capture.stop()

        if self.cron_scheduler:
            self.cron_scheduler.stop()

        # Stop summarization (will do final processing)
        self.summarizer.stop()

        self._remove_pid_file()
        print("Lifelogger stopped.")

    def run_forever(self) -> None:
        """Run the daemon until stopped."""
        self.start()

        try:
            while self._running and not self._stop_event.is_set():
                self._stop_event.wait(timeout=1.0)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def is_running(self) -> bool:
        """Check if daemon is running."""
        return self._running

    @classmethod
    def get_running_pid(cls, config: Config) -> int | None:
        """Get PID of running daemon if any.

        Args:
            config: Configuration to find PID file.

        Returns:
            PID if daemon is running, None otherwise.
        """
        if not config.pid_file.exists():
            return None

        try:
            pid = int(config.pid_file.read_text().strip())

            # Check if process is actually running
            os.kill(pid, 0)
            return pid
        except (ValueError, ProcessLookupError, PermissionError):
            # PID file exists but process is not running
            config.pid_file.unlink(missing_ok=True)
            return None

    @classmethod
    def stop_running(cls, config: Config) -> bool:
        """Stop a running daemon.

        Args:
            config: Configuration to find PID file.

        Returns:
            True if daemon was stopped, False if not running.
        """
        pid = cls.get_running_pid(config)
        if pid is None:
            return False

        try:
            if IS_WINDOWS:
                # Windows: use taskkill or subprocess
                import subprocess
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F"],
                    capture_output=True,
                    check=False,
                )
            else:
                os.kill(pid, signal.SIGTERM)

            # Wait for process to exit
            for _ in range(50):  # 5 seconds max
                time.sleep(0.1)
                try:
                    os.kill(pid, 0)
                except (ProcessLookupError, PermissionError, OSError):
                    break

            config.pid_file.unlink(missing_ok=True)
            return True
        except (ProcessLookupError, PermissionError, OSError):
            config.pid_file.unlink(missing_ok=True)
            return False
