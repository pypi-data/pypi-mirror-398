"""Pydantic models for all Lifelogger events and summaries."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events that can be captured."""

    KEYPRESS = "keypress"
    MOUSECLICK = "mouseclick"
    SCREENSHOT = "screenshot"
    CRON_SCREENSHOT = "cron_screenshot"


class BaseEvent(BaseModel):
    """Base class for all events."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: EventType
    machine_id: str = Field(default="")  # Set at runtime from hostname


class KeypressEvent(BaseEvent):
    """A keyboard keypress event."""

    event_type: Literal[EventType.KEYPRESS] = EventType.KEYPRESS
    key: str  # The key that was pressed
    key_char: str | None = None  # Character representation if available
    is_special: bool = False  # True for special keys like Ctrl, Alt, etc.
    modifiers: list[str] = Field(default_factory=list)  # Active modifiers


class MouseButton(str, Enum):
    """Mouse button types."""

    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
    UNKNOWN = "unknown"


class MouseClickEvent(BaseEvent):
    """A mouse click event."""

    event_type: Literal[EventType.MOUSECLICK] = EventType.MOUSECLICK
    x: int  # Screen X coordinate
    y: int  # Screen Y coordinate
    button: MouseButton
    pressed: bool  # True for press, False for release
    screenshot_path: str | None = None  # Optional associated screenshot


class ScreenshotEvent(BaseEvent):
    """A screenshot event (triggered by activity)."""

    event_type: Literal[EventType.SCREENSHOT] = EventType.SCREENSHOT
    path: str  # Path to the screenshot file
    width: int
    height: int
    trigger: str = "manual"  # What triggered the screenshot


class CronScreenshotEvent(BaseEvent):
    """A scheduled cron screenshot event."""

    event_type: Literal[EventType.CRON_SCREENSHOT] = EventType.CRON_SCREENSHOT
    path: str  # Path to the screenshot file
    width: int
    height: int
    cron_expression: str  # The cron expression that triggered this


# Union type for all events
Event = Annotated[
    Union[KeypressEvent, MouseClickEvent, ScreenshotEvent, CronScreenshotEvent],
    Field(discriminator="event_type"),
]


class ChunkSummary(BaseModel):
    """Summary of a chunk of events."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    chunk_index: int  # Sequential index of this chunk
    event_count: int
    start_time: datetime
    end_time: datetime
    event_ids: list[UUID]  # IDs of events in this chunk
    summary_text: str  # LLM-generated summary
    key_activities: list[str] = Field(default_factory=list)
    machine_id: str = ""


class CompactState(BaseModel):
    """Compacted running state summarizing all activity."""

    id: UUID = Field(default_factory=uuid4)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1  # Incremented each time state is compacted
    earliest_event: datetime | None = None
    latest_event: datetime | None = None
    total_events: int = 0
    total_chunks: int = 0
    last_chunk_index: int = -1
    summary_text: str = ""  # Running summary of all activity
    key_patterns: list[str] = Field(default_factory=list)  # Detected patterns
    daily_summaries: dict[str, str] = Field(default_factory=dict)  # date -> summary
    machine_id: str = ""


class ProcessorState(BaseModel):
    """State of the summarization processor for crash recovery."""

    last_processed_event_file: str | None = None
    last_processed_line: int = 0
    last_chunk_index: int = -1
    last_compact_version: int = 0
    pending_events: list[UUID] = Field(default_factory=list)
