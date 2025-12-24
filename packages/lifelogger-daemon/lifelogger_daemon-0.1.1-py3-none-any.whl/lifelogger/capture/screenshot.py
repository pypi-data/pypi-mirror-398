"""Screenshot capture and cron scheduling."""

import io
import socket
import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import mss
from croniter import croniter
from PIL import Image

from ..models import CronScreenshotEvent, ScreenshotEvent


class ScreenshotCapture:
    """Captures screenshots and saves them to disk."""

    def __init__(
        self,
        screenshots_dir: Path,
        quality: int = 85,
        format: str = "jpg",
    ):
        """Initialize screenshot capture.

        Args:
            screenshots_dir: Directory to save screenshots.
            quality: JPEG quality (1-100).
            format: Image format ('png' or 'jpg').
        """
        self.screenshots_dir = screenshots_dir
        self.quality = quality
        self.format = format
        self.machine_id = socket.gethostname()
        self._lock = threading.Lock()

    def _generate_filename(self, prefix: str = "screenshot") -> str:
        """Generate a unique filename for a screenshot."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        return f"{prefix}_{timestamp}.{self.format}"

    def capture(self, trigger: str = "manual") -> ScreenshotEvent | None:
        """Capture a screenshot and return a ScreenshotEvent.

        Args:
            trigger: What triggered this screenshot.

        Returns:
            ScreenshotEvent or None if capture failed.
        """
        with self._lock:
            try:
                with mss.mss() as sct:
                    # Capture all monitors
                    monitor = sct.monitors[0]  # Combined view of all monitors
                    sct_img = sct.grab(monitor)

                    # Convert to PIL Image
                    img = Image.frombytes(
                        "RGB",
                        sct_img.size,
                        sct_img.bgra,
                        "raw",
                        "BGRX",
                    )

                    # Save to file
                    filename = self._generate_filename()
                    filepath = self.screenshots_dir / filename
                    self.screenshots_dir.mkdir(parents=True, exist_ok=True)

                    if self.format == "jpg":
                        img.save(filepath, "JPEG", quality=self.quality)
                    else:
                        img.save(filepath, "PNG")

                    return ScreenshotEvent(
                        timestamp=datetime.utcnow(),
                        machine_id=self.machine_id,
                        path=str(filepath),
                        width=img.width,
                        height=img.height,
                        trigger=trigger,
                    )
            except Exception as e:
                # Log error but don't crash
                print(f"Screenshot capture failed: {e}")
                return None

    def capture_for_click(self, x: int, y: int) -> str | None:
        """Capture a screenshot triggered by a mouse click.

        Args:
            x: Mouse X coordinate.
            y: Mouse Y coordinate.

        Returns:
            Path to the screenshot file, or None if capture failed.
        """
        event = self.capture(trigger=f"click@{x},{y}")
        return event.path if event else None


class CronScreenshotScheduler:
    """Schedules periodic screenshots based on cron expressions."""

    def __init__(
        self,
        cron_expression: str,
        screenshots_dir: Path,
        on_event: Callable[[CronScreenshotEvent], None],
        quality: int = 85,
        format: str = "jpg",
    ):
        """Initialize cron screenshot scheduler.

        Args:
            cron_expression: Cron expression for scheduling (e.g., "*/5 * * * *").
            screenshots_dir: Directory to save screenshots.
            on_event: Callback for emitting CronScreenshotEvent.
            quality: JPEG quality (1-100).
            format: Image format ('png' or 'jpg').
        """
        self.cron_expression = cron_expression
        self.screenshots_dir = screenshots_dir
        self.on_event = on_event
        self.quality = quality
        self.format = format
        self.machine_id = socket.gethostname()

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def _generate_filename(self) -> str:
        """Generate a unique filename for a cron screenshot."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        return f"cron_{timestamp}.{self.format}"

    def _capture(self) -> CronScreenshotEvent | None:
        """Capture a cron screenshot."""
        with self._lock:
            try:
                with mss.mss() as sct:
                    monitor = sct.monitors[0]
                    sct_img = sct.grab(monitor)

                    img = Image.frombytes(
                        "RGB",
                        sct_img.size,
                        sct_img.bgra,
                        "raw",
                        "BGRX",
                    )

                    filename = self._generate_filename()
                    filepath = self.screenshots_dir / filename
                    self.screenshots_dir.mkdir(parents=True, exist_ok=True)

                    if self.format == "jpg":
                        img.save(filepath, "JPEG", quality=self.quality)
                    else:
                        img.save(filepath, "PNG")

                    return CronScreenshotEvent(
                        timestamp=datetime.utcnow(),
                        machine_id=self.machine_id,
                        path=str(filepath),
                        width=img.width,
                        height=img.height,
                        cron_expression=self.cron_expression,
                    )
            except Exception as e:
                print(f"Cron screenshot capture failed: {e}")
                return None

    def _run(self) -> None:
        """Main scheduler loop."""
        cron = croniter(self.cron_expression, datetime.now())

        while not self._stop_event.is_set():
            next_time = cron.get_next(datetime)
            now = datetime.now()

            # Wait until next scheduled time
            wait_seconds = (next_time - now).total_seconds()
            if wait_seconds > 0:
                # Check stop event periodically while waiting
                if self._stop_event.wait(timeout=min(wait_seconds, 1.0)):
                    break
                if wait_seconds > 1.0:
                    continue  # Re-check the time

            # Capture screenshot
            event = self._capture()
            if event:
                self.on_event(event)

    def start(self) -> None:
        """Start the cron scheduler."""
        if self._thread is not None:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the cron scheduler."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._thread is not None and self._thread.is_alive()
