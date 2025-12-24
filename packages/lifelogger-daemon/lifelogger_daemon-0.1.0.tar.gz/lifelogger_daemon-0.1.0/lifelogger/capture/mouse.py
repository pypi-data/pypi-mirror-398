"""Mouse event capture using pynput."""

import socket
from collections.abc import Callable
from datetime import datetime

from pynput import mouse

from ..models import MouseButton, MouseClickEvent


class MouseCapture:
    """Captures mouse click events and emits MouseClickEvent objects."""

    BUTTON_MAP = {
        mouse.Button.left: MouseButton.LEFT,
        mouse.Button.right: MouseButton.RIGHT,
        mouse.Button.middle: MouseButton.MIDDLE,
    }

    def __init__(
        self,
        on_event: Callable[[MouseClickEvent], None],
        on_click_screenshot: Callable[[int, int], str | None] | None = None,
    ):
        """Initialize mouse capture.

        Args:
            on_event: Callback function called with each MouseClickEvent.
            on_click_screenshot: Optional callback to take screenshot on click.
                Takes (x, y) coordinates, returns screenshot path or None.
        """
        self.on_event = on_event
        self.on_click_screenshot = on_click_screenshot
        self.machine_id = socket.gethostname()
        self._listener: mouse.Listener | None = None

    def _on_click(self, x: int, y: int, button, pressed: bool) -> None:
        """Handle mouse click event."""
        screenshot_path = None

        # Only take screenshot on press, not release
        if pressed and self.on_click_screenshot is not None:
            screenshot_path = self.on_click_screenshot(x, y)

        mouse_button = self.BUTTON_MAP.get(button, MouseButton.UNKNOWN)

        event = MouseClickEvent(
            timestamp=datetime.utcnow(),
            machine_id=self.machine_id,
            x=int(x),
            y=int(y),
            button=mouse_button,
            pressed=pressed,
            screenshot_path=screenshot_path,
        )

        self.on_event(event)

    def start(self) -> None:
        """Start capturing mouse events."""
        if self._listener is not None:
            return

        self._listener = mouse.Listener(on_click=self._on_click)
        self._listener.start()

    def stop(self) -> None:
        """Stop capturing mouse events."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def is_running(self) -> bool:
        """Check if capture is running."""
        return self._listener is not None and self._listener.is_alive()
