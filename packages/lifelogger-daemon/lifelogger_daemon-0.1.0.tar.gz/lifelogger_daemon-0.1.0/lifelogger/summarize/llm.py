"""LLM-based summarization using OpenAI."""

from datetime import datetime

from openai import OpenAI

from ..models import ChunkSummary, CompactState, Event


class LLMSummarizer:
    """Summarizes events and compacts state using OpenAI LLMs."""

    CHUNK_SYSTEM_PROMPT = """You are a personal activity summarizer. You analyze sequences of computer activity events (keypresses, mouse clicks, screenshots) and produce concise summaries of what the user was doing.

Focus on:
- High-level activities (writing code, browsing web, reading documents, etc.)
- Key actions and patterns
- Notable context from any screenshots described

Be concise but informative. Output a 2-3 sentence summary and a list of key activities."""

    COMPACT_SYSTEM_PROMPT = """You are a personal activity state manager. You maintain a running summary of a user's computer activity over time.

You will receive:
1. The current running state summary
2. New chunk summaries since the last update

Your task is to update the running summary to incorporate the new information while:
- Maintaining a coherent narrative of activity patterns
- Identifying and tracking recurring patterns
- Keeping the summary concise (under 500 words)
- Updating daily summaries appropriately

Output an updated summary that captures the full history."""

    def __init__(self, api_key: str, model: str = "gpt-5.2-nano"):
        """Initialize LLM summarizer.

        Args:
            api_key: OpenAI API key.
            model: Model to use for summarization.
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _format_events_for_prompt(self, events: list[Event]) -> str:
        """Format events into a readable string for the LLM."""
        lines = []
        for event in events:
            ts = event.timestamp.strftime("%H:%M:%S")
            if event.event_type.value == "keypress":
                key_info = event.key
                if event.modifiers:
                    key_info = f"{'+'.join(event.modifiers)}+{key_info}"
                lines.append(f"[{ts}] KEYPRESS: {key_info}")
            elif event.event_type.value == "mouseclick":
                action = "pressed" if event.pressed else "released"
                lines.append(
                    f"[{ts}] MOUSE: {event.button.value} {action} at ({event.x}, {event.y})"
                )
            elif event.event_type.value in ("screenshot", "cron_screenshot"):
                lines.append(f"[{ts}] SCREENSHOT: {event.path}")
        return "\n".join(lines)

    def summarize_chunk(
        self,
        events: list[Event],
        chunk_index: int,
    ) -> ChunkSummary:
        """Summarize a chunk of events.

        Args:
            events: List of events to summarize.
            chunk_index: Index of this chunk.

        Returns:
            ChunkSummary with LLM-generated summary.
        """
        if not events:
            return ChunkSummary(
                chunk_index=chunk_index,
                event_count=0,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                event_ids=[],
                summary_text="No events in this chunk.",
                key_activities=[],
            )

        events_text = self._format_events_for_prompt(events)

        prompt = f"""Analyze these computer activity events and provide a summary:

{events_text}

Respond in this exact format:
SUMMARY: <2-3 sentence summary of what the user was doing>
KEY_ACTIVITIES:
- <activity 1>
- <activity 2>
- <activity 3 if applicable>"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.CHUNK_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.3,
            )

            content = response.choices[0].message.content or ""

            # Parse response
            summary_text = ""
            key_activities = []

            lines = content.strip().split("\n")
            in_activities = False

            for line in lines:
                if line.startswith("SUMMARY:"):
                    summary_text = line.replace("SUMMARY:", "").strip()
                elif line.startswith("KEY_ACTIVITIES:"):
                    in_activities = True
                elif in_activities and line.strip().startswith("-"):
                    key_activities.append(line.strip().lstrip("- "))

        except Exception as e:
            summary_text = f"Summarization failed: {e}"
            key_activities = []

        return ChunkSummary(
            chunk_index=chunk_index,
            event_count=len(events),
            start_time=min(e.timestamp for e in events),
            end_time=max(e.timestamp for e in events),
            event_ids=[e.id for e in events],
            summary_text=summary_text,
            key_activities=key_activities,
            machine_id=events[0].machine_id if events else "",
        )

    def compact_state(
        self,
        current_state: CompactState,
        new_summaries: list[ChunkSummary],
    ) -> CompactState:
        """Compact the running state with new chunk summaries.

        Args:
            current_state: Current compact state.
            new_summaries: New chunk summaries to incorporate.

        Returns:
            Updated CompactState.
        """
        if not new_summaries:
            return current_state

        # Format current state
        current_summary = current_state.summary_text or "No previous activity recorded."

        # Format new summaries
        new_summaries_text = "\n\n".join(
            f"Chunk {s.chunk_index} ({s.start_time.strftime('%Y-%m-%d %H:%M')} - {s.end_time.strftime('%H:%M')}):\n{s.summary_text}"
            for s in new_summaries
        )

        prompt = f"""Current running summary:
{current_summary}

New activity summaries to incorporate:
{new_summaries_text}

Please provide an updated running summary that incorporates the new information.

Respond in this exact format:
UPDATED_SUMMARY: <comprehensive summary under 500 words>
KEY_PATTERNS:
- <pattern 1>
- <pattern 2>
DAILY_UPDATES:
<date1>: <brief daily summary>
<date2>: <brief daily summary>"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.COMPACT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.3,
            )

            content = response.choices[0].message.content or ""

            # Parse response
            updated_summary = ""
            key_patterns = []
            daily_summaries = dict(current_state.daily_summaries)

            lines = content.strip().split("\n")
            section = None

            for line in lines:
                if line.startswith("UPDATED_SUMMARY:"):
                    updated_summary = line.replace("UPDATED_SUMMARY:", "").strip()
                    section = "summary"
                elif line.startswith("KEY_PATTERNS:"):
                    section = "patterns"
                elif line.startswith("DAILY_UPDATES:"):
                    section = "daily"
                elif section == "patterns" and line.strip().startswith("-"):
                    key_patterns.append(line.strip().lstrip("- "))
                elif section == "daily" and ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        date_str = parts[0].strip()
                        summary = parts[1].strip()
                        if date_str and summary:
                            daily_summaries[date_str] = summary

        except Exception as e:
            updated_summary = f"{current_summary}\n\n[Update failed: {e}]"
            key_patterns = list(current_state.key_patterns)
            daily_summaries = dict(current_state.daily_summaries)

        # Calculate totals
        total_events = current_state.total_events + sum(s.event_count for s in new_summaries)
        total_chunks = current_state.total_chunks + len(new_summaries)
        last_chunk_index = max(s.chunk_index for s in new_summaries)

        earliest = current_state.earliest_event
        latest = current_state.latest_event

        for s in new_summaries:
            if earliest is None or s.start_time < earliest:
                earliest = s.start_time
            if latest is None or s.end_time > latest:
                latest = s.end_time

        return CompactState(
            version=current_state.version + 1,
            earliest_event=earliest,
            latest_event=latest,
            total_events=total_events,
            total_chunks=total_chunks,
            last_chunk_index=last_chunk_index,
            summary_text=updated_summary,
            key_patterns=key_patterns,
            daily_summaries=daily_summaries,
            machine_id=new_summaries[0].machine_id if new_summaries else current_state.machine_id,
        )
