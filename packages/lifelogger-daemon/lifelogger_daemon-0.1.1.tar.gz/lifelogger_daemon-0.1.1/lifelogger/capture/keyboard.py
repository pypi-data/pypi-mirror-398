"""Keyboard event capture using pynput."""

import socket
import threading
from collections.abc import Callable
from datetime import datetime

from pynput import keyboard

from ..models import KeypressEvent


class KeyboardCapture:
    """Captures keyboard events and emits KeypressEvent objects."""

    SPECIAL_KEYS = {
        keyboard.Key.alt,
        keyboard.Key.alt_l,
        keyboard.Key.alt_r,
        keyboard.Key.alt_gr,
        keyboard.Key.ctrl,
        keyboard.Key.ctrl_l,
        keyboard.Key.ctrl_r,
        keyboard.Key.shift,
        keyboard.Key.shift_l,
        keyboard.Key.shift_r,
        keyboard.Key.cmd,
        keyboard.Key.cmd_l,
        keyboard.Key.cmd_r,
    }

    MODIFIER_MAP = {
        keyboard.Key.alt: "alt",
        keyboard.Key.alt_l: "alt",
        keyboard.Key.alt_r: "alt",
        keyboard.Key.alt_gr: "alt_gr",
        keyboard.Key.ctrl: "ctrl",
        keyboard.Key.ctrl_l: "ctrl",
        keyboard.Key.ctrl_r: "ctrl",
        keyboard.Key.shift: "shift",
        keyboard.Key.shift_l: "shift",
        keyboard.Key.shift_r: "shift",
        keyboard.Key.cmd: "cmd",
        keyboard.Key.cmd_l: "cmd",
        keyboard.Key.cmd_r: "cmd",
    }

    def __init__(self, on_event: Callable[[KeypressEvent], None]):
        """Initialize keyboard capture.

        Args:
            on_event: Callback function called with each KeypressEvent.
        """
        self.on_event = on_event
        self.machine_id = socket.gethostname()
        self._listener: keyboard.Listener | None = None
        self._active_modifiers: set[str] = set()
        self._lock = threading.Lock()

    def _get_key_info(self, key) -> tuple[str, str | None, bool]:
        """Extract key information.

        Returns:
            Tuple of (key_name, key_char, is_special)
        """
        if isinstance(key, keyboard.KeyCode):
            char = key.char
            if char is not None:
                return char, char, False
            # Key with vk but no char (e.g., numpad)
            return f"vk_{key.vk}", None, True
        else:
            # Special key
            return key.name, None, True

    def _on_press(self, key) -> None:
        """Handle key press event."""
        with self._lock:
            # Update modifiers
            if key in self.MODIFIER_MAP:
                self._active_modifiers.add(self.MODIFIER_MAP[key])

            key_name, key_char, is_special = self._get_key_info(key)

            event = KeypressEvent(
                timestamp=datetime.utcnow(),
                machine_id=self.machine_id,
                key=key_name,
                key_char=key_char,
                is_special=is_special,
                modifiers=list(self._active_modifiers),
            )

            self.on_event(event)

    def _on_release(self, key) -> None:
        """Handle key release event."""
        with self._lock:
            if key in self.MODIFIER_MAP:
                self._active_modifiers.discard(self.MODIFIER_MAP[key])

    def start(self) -> None:
        """Start capturing keyboard events."""
        if self._listener is not None:
            return

        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

    def stop(self) -> None:
        """Stop capturing keyboard events."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def is_running(self) -> bool:
        """Check if capture is running."""
        return self._listener is not None and self._listener.is_alive()
