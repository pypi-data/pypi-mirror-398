"""JSONL storage for events, summaries, and state."""

import fcntl
import json
import threading
from collections.abc import Iterator
from datetime import date, datetime
from pathlib import Path
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel, TypeAdapter

from ..models import (
    ChunkSummary,
    CompactState,
    CronScreenshotEvent,
    Event,
    KeypressEvent,
    MouseClickEvent,
    ProcessorState,
    ScreenshotEvent,
)


T = TypeVar("T", bound=BaseModel)


class JSONLWriter:
    """Thread-safe JSONL file writer with atomic appends."""

    def __init__(self, filepath: Path):
        """Initialize JSONL writer.

        Args:
            filepath: Path to the JSONL file.
        """
        self.filepath = filepath
        self._lock = threading.Lock()

    def append(self, model: BaseModel) -> None:
        """Append a Pydantic model to the JSONL file.

        Args:
            model: Pydantic model to serialize and append.
        """
        with self._lock:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)

            # Open in append mode with exclusive lock
            with open(self.filepath, "a") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(model.model_dump_json() + "\n")
                    f.flush()
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)


class JSONLReader:
    """JSONL file reader with support for resumable reading."""

    def __init__(self, filepath: Path):
        """Initialize JSONL reader.

        Args:
            filepath: Path to the JSONL file.
        """
        self.filepath = filepath

    def read_all(self, model_type: type[T]) -> list[T]:
        """Read all records from the JSONL file.

        Args:
            model_type: Pydantic model type to deserialize into.

        Returns:
            List of deserialized models.
        """
        if not self.filepath.exists():
            return []

        adapter = TypeAdapter(model_type)
        results = []

        with open(self.filepath) as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(adapter.validate_json(line))

        return results

    def read_lines(
        self,
        model_type: type[T],
        start_line: int = 0,
        limit: int | None = None,
    ) -> Iterator[tuple[int, T]]:
        """Read records from a specific line number.

        Args:
            model_type: Pydantic model type to deserialize into.
            start_line: Line number to start from (0-indexed).
            limit: Maximum number of records to read.

        Yields:
            Tuples of (line_number, model).
        """
        if not self.filepath.exists():
            return

        adapter = TypeAdapter(model_type)
        count = 0

        with open(self.filepath) as f:
            for line_num, line in enumerate(f):
                if line_num < start_line:
                    continue

                if limit is not None and count >= limit:
                    break

                line = line.strip()
                if line:
                    yield line_num, adapter.validate_json(line)
                    count += 1

    def count_lines(self) -> int:
        """Count total lines in the file."""
        if not self.filepath.exists():
            return 0

        with open(self.filepath) as f:
            return sum(1 for line in f if line.strip())


# Type adapter for the Event union type
EventAdapter = TypeAdapter(Event)


class EventStore:
    """Storage for events organized by date."""

    def __init__(self, events_dir: Path):
        """Initialize event store.

        Args:
            events_dir: Directory for event JSONL files.
        """
        self.events_dir = events_dir
        self._writers: dict[str, JSONLWriter] = {}
        self._lock = threading.Lock()

    def _get_filename(self, dt: datetime | date | None = None) -> str:
        """Get filename for a date."""
        if dt is None:
            dt = datetime.utcnow()
        if isinstance(dt, datetime):
            dt = dt.date()
        return f"events_{dt.isoformat()}.jsonl"

    def _get_writer(self, dt: datetime | None = None) -> JSONLWriter:
        """Get or create writer for a date."""
        filename = self._get_filename(dt)
        with self._lock:
            if filename not in self._writers:
                self._writers[filename] = JSONLWriter(self.events_dir / filename)
            return self._writers[filename]

    def append(self, event: Event) -> None:
        """Append an event to the store.

        Args:
            event: Event to store.
        """
        writer = self._get_writer(event.timestamp)
        writer.append(event)

    def read_date(self, dt: date) -> list[Event]:
        """Read all events for a specific date.

        Args:
            dt: Date to read events for.

        Returns:
            List of events.
        """
        filepath = self.events_dir / self._get_filename(dt)
        reader = JSONLReader(filepath)

        results = []
        with open(filepath) if filepath.exists() else open("/dev/null") as f:
            if not filepath.exists():
                return []

        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(EventAdapter.validate_json(line))

        return results

    def list_dates(self) -> list[date]:
        """List all dates with events.

        Returns:
            Sorted list of dates.
        """
        dates = []
        for filepath in self.events_dir.glob("events_*.jsonl"):
            try:
                date_str = filepath.stem.replace("events_", "")
                dates.append(date.fromisoformat(date_str))
            except ValueError:
                continue
        return sorted(dates)

    def iter_events(
        self,
        start_date: date | None = None,
        start_line: int = 0,
    ) -> Iterator[tuple[str, int, Event]]:
        """Iterate over all events from a starting point.

        Args:
            start_date: Date to start from.
            start_line: Line number to start from in the first file.

        Yields:
            Tuples of (filename, line_number, event).
        """
        dates = self.list_dates()

        if start_date:
            dates = [d for d in dates if d >= start_date]

        for i, dt in enumerate(dates):
            filepath = self.events_dir / self._get_filename(dt)
            first_line = start_line if i == 0 else 0

            if not filepath.exists():
                continue

            with open(filepath) as f:
                for line_num, line in enumerate(f):
                    if line_num < first_line:
                        continue

                    line = line.strip()
                    if line:
                        event = EventAdapter.validate_json(line)
                        yield filepath.name, line_num, event


class SummaryStore:
    """Storage for chunk summaries."""

    def __init__(self, summaries_dir: Path):
        """Initialize summary store.

        Args:
            summaries_dir: Directory for summary files.
        """
        self.summaries_dir = summaries_dir
        self._writer: JSONLWriter | None = None

    @property
    def summaries_file(self) -> Path:
        """Path to the main summaries file."""
        return self.summaries_dir / "chunk_summaries.jsonl"

    def _get_writer(self) -> JSONLWriter:
        """Get or create the summary writer."""
        if self._writer is None:
            self._writer = JSONLWriter(self.summaries_file)
        return self._writer

    def append(self, summary: ChunkSummary) -> None:
        """Append a chunk summary.

        Args:
            summary: ChunkSummary to store.
        """
        writer = self._get_writer()
        writer.append(summary)

    def read_all(self) -> list[ChunkSummary]:
        """Read all chunk summaries.

        Returns:
            List of chunk summaries.
        """
        reader = JSONLReader(self.summaries_file)
        return reader.read_all(ChunkSummary)

    def read_since(self, chunk_index: int) -> list[ChunkSummary]:
        """Read summaries since a chunk index.

        Args:
            chunk_index: Read summaries after this index.

        Returns:
            List of chunk summaries.
        """
        all_summaries = self.read_all()
        return [s for s in all_summaries if s.chunk_index > chunk_index]

    def get_latest_index(self) -> int:
        """Get the latest chunk index.

        Returns:
            Latest chunk index or -1 if no summaries.
        """
        summaries = self.read_all()
        if not summaries:
            return -1
        return max(s.chunk_index for s in summaries)


class StateStore:
    """Storage for compacted running state and processor state."""

    def __init__(self, state_dir: Path):
        """Initialize state store.

        Args:
            state_dir: Directory for state files.
        """
        self.state_dir = state_dir

    @property
    def compact_state_file(self) -> Path:
        """Path to the compact state file."""
        return self.state_dir / "compact_state.json"

    @property
    def compact_history_file(self) -> Path:
        """Path to compact state history."""
        return self.state_dir / "compact_history.jsonl"

    @property
    def processor_state_file(self) -> Path:
        """Path to processor state file."""
        return self.state_dir / "processor_state.json"

    def save_compact_state(self, state: CompactState) -> None:
        """Save the current compact state.

        Also appends to history for recovery.

        Args:
            state: CompactState to save.
        """
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Save current state
        self.compact_state_file.write_text(state.model_dump_json(indent=2))

        # Append to history
        writer = JSONLWriter(self.compact_history_file)
        writer.append(state)

    def load_compact_state(self) -> CompactState:
        """Load the current compact state.

        Returns:
            CompactState (existing or new).
        """
        if self.compact_state_file.exists():
            return CompactState.model_validate_json(
                self.compact_state_file.read_text()
            )
        return CompactState()

    def save_processor_state(self, state: ProcessorState) -> None:
        """Save processor state for crash recovery.

        Args:
            state: ProcessorState to save.
        """
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.processor_state_file.write_text(state.model_dump_json(indent=2))

    def load_processor_state(self) -> ProcessorState:
        """Load processor state.

        Returns:
            ProcessorState (existing or new).
        """
        if self.processor_state_file.exists():
            return ProcessorState.model_validate_json(
                self.processor_state_file.read_text()
            )
        return ProcessorState()
