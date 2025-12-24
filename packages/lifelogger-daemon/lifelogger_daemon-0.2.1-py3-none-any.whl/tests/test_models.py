"""Tests for data models."""

from datetime import datetime

from lifelogger.models import (
    EventType,
    MouseButton,
    KeypressEvent,
    MouseClickEvent,
    ScreenshotEvent,
    CronScreenshotEvent,
)


def test_keypress_event():
    """Test KeypressEvent creation."""
    event = KeypressEvent(
        timestamp=datetime.utcnow(),
        machine_id="test-machine",
        key="a",
        key_char="a",
        is_special=False,
        modifiers=["ctrl"],
    )
    assert event.event_type == EventType.KEYPRESS
    assert event.key == "a"
    assert event.modifiers == ["ctrl"]


def test_mouse_click_event():
    """Test MouseClickEvent creation."""
    event = MouseClickEvent(
        timestamp=datetime.utcnow(),
        machine_id="test-machine",
        x=100,
        y=200,
        button=MouseButton.LEFT,
        pressed=True,
    )
    assert event.event_type == EventType.MOUSECLICK
    assert event.x == 100
    assert event.y == 200
    assert event.button == MouseButton.LEFT


def test_screenshot_event():
    """Test ScreenshotEvent creation."""
    event = ScreenshotEvent(
        timestamp=datetime.utcnow(),
        machine_id="test-machine",
        path="/tmp/screenshot.jpg",
        width=1920,
        height=1080,
        trigger="click@100,200",
    )
    assert event.event_type == EventType.SCREENSHOT
    assert event.width == 1920
    assert event.height == 1080


def test_cron_screenshot_event():
    """Test CronScreenshotEvent creation."""
    event = CronScreenshotEvent(
        timestamp=datetime.utcnow(),
        machine_id="test-machine",
        path="/tmp/cron_screenshot.jpg",
        width=1920,
        height=1080,
        cron_expression="*/5 * * * *",
    )
    assert event.event_type == EventType.CRON_SCREENSHOT
    assert event.cron_expression == "*/5 * * * *"
