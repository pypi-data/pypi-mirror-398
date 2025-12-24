"""Continuous summarization processor with crash recovery."""

import socket
import threading
import time
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

from ..config import Config
from ..models import ChunkSummary, CompactState, Event, ProcessorState
from ..storage.jsonl import EventStore, StateStore, SummaryStore
from .llm import LLMSummarizer


class SummarizationProcessor:
    """Processes events into chunk summaries and compacts running state.

    Designed for crash recovery - all state is persisted to filesystem.
    """

    def __init__(
        self,
        config: Config,
        event_store: EventStore,
        summary_store: SummaryStore,
        state_store: StateStore,
        on_chunk_summary: Callable[[ChunkSummary], None] | None = None,
        on_state_update: Callable[[CompactState], None] | None = None,
    ):
        """Initialize summarization processor.

        Args:
            config: Application configuration.
            event_store: Store for reading events.
            summary_store: Store for writing chunk summaries.
            state_store: Store for compact state.
            on_chunk_summary: Optional callback when a chunk is summarized.
            on_state_update: Optional callback when state is compacted.
        """
        self.config = config
        self.event_store = event_store
        self.summary_store = summary_store
        self.state_store = state_store
        self.on_chunk_summary = on_chunk_summary
        self.on_state_update = on_state_update

        self._summarizer: LLMSummarizer | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._pending_events: list[Event] = []
        self._last_process_time = datetime.utcnow()

    def _get_summarizer(self) -> LLMSummarizer | None:
        """Get or create the LLM summarizer."""
        if not self.config.summarizer.enabled:
            return None

        if self._summarizer is None:
            api_key = self.config.openai_api_key
            if not api_key:
                print("Warning: OpenAI API key not configured, summarization disabled")
                return None

            self._summarizer = LLMSummarizer(
                api_key=api_key,
                model=self.config.summarizer.model,
            )

        return self._summarizer

    def _load_state(self) -> tuple[ProcessorState, CompactState]:
        """Load processor and compact state from disk."""
        processor_state = self.state_store.load_processor_state()
        compact_state = self.state_store.load_compact_state()
        return processor_state, compact_state

    def _save_processor_state(self, state: ProcessorState) -> None:
        """Save processor state for crash recovery."""
        self.state_store.save_processor_state(state)

    def _collect_pending_events(self, processor_state: ProcessorState) -> list[Event]:
        """Collect events that haven't been processed yet.

        Uses processor state to resume from last position.
        """
        events = []

        # Determine starting point
        start_date = None
        start_line = 0

        if processor_state.last_processed_event_file:
            # Parse date from filename
            try:
                date_str = processor_state.last_processed_event_file.replace(
                    "events_", ""
                ).replace(".jsonl", "")
                start_date = date.fromisoformat(date_str)
                start_line = processor_state.last_processed_line + 1
            except ValueError:
                pass

        # Iterate from the starting point
        for filename, line_num, event in self.event_store.iter_events(
            start_date=start_date,
            start_line=start_line if start_date else 0,
        ):
            events.append(event)

            # Update processor state tracking
            processor_state.last_processed_event_file = filename
            processor_state.last_processed_line = line_num

        return events

    def _process_chunk(
        self,
        events: list[Event],
        chunk_index: int,
    ) -> ChunkSummary | None:
        """Process a chunk of events into a summary.

        Args:
            events: Events in this chunk.
            chunk_index: Index of this chunk.

        Returns:
            ChunkSummary or None if summarization is disabled/failed.
        """
        summarizer = self._get_summarizer()

        if summarizer is None:
            # Create a basic summary without LLM
            if not events:
                return None

            return ChunkSummary(
                chunk_index=chunk_index,
                event_count=len(events),
                start_time=min(e.timestamp for e in events),
                end_time=max(e.timestamp for e in events),
                event_ids=[e.id for e in events],
                summary_text=f"Chunk of {len(events)} events (LLM summarization disabled)",
                key_activities=[],
                machine_id=events[0].machine_id if events else socket.gethostname(),
            )

        return summarizer.summarize_chunk(events, chunk_index)

    def _maybe_compact_state(
        self,
        compact_state: CompactState,
        force: bool = False,
    ) -> CompactState:
        """Compact state if enough chunks have accumulated.

        Args:
            compact_state: Current compact state.
            force: Force compaction regardless of chunk count.

        Returns:
            Updated compact state.
        """
        summarizer = self._get_summarizer()

        # Get new summaries since last compact
        new_summaries = self.summary_store.read_since(compact_state.last_chunk_index)

        if not new_summaries:
            return compact_state

        # Check if we should compact
        if not force and len(new_summaries) < self.config.summarizer.compact_interval_chunks:
            return compact_state

        if summarizer is None:
            # Basic compaction without LLM
            total_events = compact_state.total_events + sum(
                s.event_count for s in new_summaries
            )
            return CompactState(
                version=compact_state.version + 1,
                earliest_event=compact_state.earliest_event
                or (new_summaries[0].start_time if new_summaries else None),
                latest_event=new_summaries[-1].end_time if new_summaries else compact_state.latest_event,
                total_events=total_events,
                total_chunks=compact_state.total_chunks + len(new_summaries),
                last_chunk_index=new_summaries[-1].chunk_index if new_summaries else compact_state.last_chunk_index,
                summary_text=compact_state.summary_text
                + f"\n\n[+{len(new_summaries)} chunks, LLM disabled]",
                key_patterns=compact_state.key_patterns,
                daily_summaries=compact_state.daily_summaries,
                machine_id=compact_state.machine_id or socket.gethostname(),
            )

        return summarizer.compact_state(compact_state, new_summaries)

    def process_pending(self) -> None:
        """Process all pending events.

        Called periodically or when event threshold is reached.
        """
        processor_state, compact_state = self._load_state()

        # Collect pending events
        new_events = self._collect_pending_events(processor_state)
        self._pending_events.extend(new_events)

        # Check if we should create a new chunk
        chunk_size = self.config.summarizer.chunk_size
        chunk_interval = self.config.summarizer.chunk_interval_seconds

        time_elapsed = (datetime.utcnow() - self._last_process_time).total_seconds()
        should_chunk = (
            len(self._pending_events) >= chunk_size
            or (self._pending_events and time_elapsed >= chunk_interval)
        )

        if should_chunk and self._pending_events:
            # Get next chunk index
            chunk_index = self.summary_store.get_latest_index() + 1

            # Process the chunk
            chunk_events = self._pending_events[:chunk_size]
            self._pending_events = self._pending_events[chunk_size:]

            summary = self._process_chunk(chunk_events, chunk_index)

            if summary:
                # Save chunk summary
                self.summary_store.append(summary)
                processor_state.last_chunk_index = chunk_index

                if self.on_chunk_summary:
                    self.on_chunk_summary(summary)

            self._last_process_time = datetime.utcnow()

        # Maybe compact state
        new_compact_state = self._maybe_compact_state(compact_state)

        if new_compact_state.version > compact_state.version:
            self.state_store.save_compact_state(new_compact_state)
            processor_state.last_compact_version = new_compact_state.version

            if self.on_state_update:
                self.on_state_update(new_compact_state)

        # Save processor state
        self._save_processor_state(processor_state)

    def _run(self) -> None:
        """Main processor loop."""
        while not self._stop_event.is_set():
            try:
                self.process_pending()
            except Exception as e:
                print(f"Summarization processor error: {e}")

            # Wait before next check
            self._stop_event.wait(timeout=30.0)

    def start(self) -> None:
        """Start the summarization processor."""
        if self._thread is not None:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the summarization processor."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=10.0)
            self._thread = None

        # Final processing
        try:
            self.process_pending()
            # Force compact on shutdown
            processor_state, compact_state = self._load_state()
            final_state = self._maybe_compact_state(compact_state, force=True)
            if final_state.version > compact_state.version:
                self.state_store.save_compact_state(final_state)
        except Exception as e:
            print(f"Error during final processing: {e}")

    def is_running(self) -> bool:
        """Check if processor is running."""
        return self._thread is not None and self._thread.is_alive()
