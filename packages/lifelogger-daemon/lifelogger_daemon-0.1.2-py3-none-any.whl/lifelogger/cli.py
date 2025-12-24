"""Command-line interface for Lifelogger."""

import json
import os
import platform
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import click

from .config import Config
from .daemon import LifeloggerDaemon
from .permissions import (
    check_all_permissions,
    print_permission_instructions,
    request_accessibility_permissions,
    request_screen_recording_permissions,
)
from .storage import EventStore, StateStore, SummaryStore

IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"


def _start_background(config: Config) -> None:
    """Start the daemon in the background (cross-platform)."""
    config.ensure_dirs()
    log_file = config.data_dir / "lifelogger.log"

    # Use subprocess on all platforms - fork() doesn't work well with CoreFoundation on macOS
    with open(log_file, "a") as log:
        if IS_WINDOWS:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            proc = subprocess.Popen(
                [sys.executable, "-m", "lifelogger", "start", "-f", "--skip-permission-check"],
                stdout=log,
                stderr=log,
                stdin=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
            )
        else:
            # macOS/Linux: use subprocess to avoid fork() issues with CoreFoundation
            proc = subprocess.Popen(
                [sys.executable, "-m", "lifelogger", "start", "-f", "--skip-permission-check"],
                stdout=log,
                stderr=log,
                stdin=subprocess.DEVNULL,
                start_new_session=True,  # Detach from parent process group
            )

    import time
    time.sleep(0.5)
    running_pid = LifeloggerDaemon.get_running_pid(config)
    if running_pid:
        click.echo(f"Lifelogger started (PID: {running_pid})")
    else:
        click.echo(f"Lifelogger started (PID: {proc.pid})")


@click.group()
@click.option(
    "--data-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Data directory (default: ~/.lifelogger)",
)
@click.pass_context
def main(ctx: click.Context, data_dir: Path | None) -> None:
    """Lifelogger - Personal activity tracking with LLM summarization."""
    ctx.ensure_object(dict)

    # Load or create config
    config = Config.load()
    if data_dir:
        config.data_dir = data_dir

    ctx.obj["config"] = config


@main.command()
@click.option("--foreground", "-f", is_flag=True, help="Run in foreground (don't daemonize)")
@click.option("--skip-permission-check", is_flag=True, help="Skip permission check on macOS")
@click.pass_context
def start(ctx: click.Context, foreground: bool, skip_permission_check: bool) -> None:
    """Start the Lifelogger daemon."""
    config: Config = ctx.obj["config"]

    # Check if already running
    pid = LifeloggerDaemon.get_running_pid(config)
    if pid:
        click.echo(f"Lifelogger is already running (PID: {pid})")
        sys.exit(1)

    # Check permissions on macOS
    if IS_MACOS and not skip_permission_check:
        perms = check_all_permissions(verbose=True)
        if not perms["accessibility"] or not perms["screen_recording"]:
            print_permission_instructions()
            if not perms["accessibility"]:
                click.echo("Opening Accessibility settings...")
                request_accessibility_permissions()
            if not perms["screen_recording"]:
                click.echo("Opening Screen Recording settings...")
                request_screen_recording_permissions()
            click.echo("\nAfter granting permissions, run: lifelogger start")
            sys.exit(1)

    if foreground:
        # Run in foreground
        daemon = LifeloggerDaemon(config)
        daemon.run_forever()
    else:
        # Background the process - cross-platform approach
        _start_background(config)


@main.command()
@click.pass_context
def stop(ctx: click.Context) -> None:
    """Stop the Lifelogger daemon."""
    config: Config = ctx.obj["config"]

    if LifeloggerDaemon.stop_running(config):
        click.echo("Lifelogger stopped.")
    else:
        click.echo("Lifelogger is not running.")


@main.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Check the status of Lifelogger."""
    config: Config = ctx.obj["config"]

    pid = LifeloggerDaemon.get_running_pid(config)
    if pid:
        click.echo(f"Lifelogger is running (PID: {pid})")

        # Show some stats
        state_store = StateStore(config.state_dir)
        compact_state = state_store.load_compact_state()

        click.echo(f"\nStatistics:")
        click.echo(f"  Total events: {compact_state.total_events}")
        click.echo(f"  Total chunks: {compact_state.total_chunks}")
        if compact_state.earliest_event:
            click.echo(f"  Earliest event: {compact_state.earliest_event}")
        if compact_state.latest_event:
            click.echo(f"  Latest event: {compact_state.latest_event}")
    else:
        click.echo("Lifelogger is not running.")


@main.command()
@click.pass_context
def summary(ctx: click.Context) -> None:
    """Show the current activity summary."""
    config: Config = ctx.obj["config"]

    state_store = StateStore(config.state_dir)
    compact_state = state_store.load_compact_state()

    if not compact_state.summary_text:
        click.echo("No activity summary available yet.")
        return

    click.echo("=== Activity Summary ===\n")
    click.echo(compact_state.summary_text)

    if compact_state.key_patterns:
        click.echo("\n=== Key Patterns ===")
        for pattern in compact_state.key_patterns:
            click.echo(f"  - {pattern}")

    if compact_state.daily_summaries:
        click.echo("\n=== Daily Summaries ===")
        for dt, summary in sorted(compact_state.daily_summaries.items()):
            click.echo(f"\n{dt}:")
            click.echo(f"  {summary}")


@main.command()
@click.option("--date", "-d", "event_date", type=str, default=None, help="Date to show (YYYY-MM-DD)")
@click.option("--limit", "-n", type=int, default=50, help="Maximum events to show")
@click.pass_context
def events(ctx: click.Context, event_date: str | None, limit: int) -> None:
    """Show recent events."""
    config: Config = ctx.obj["config"]

    event_store = EventStore(config.events_dir)

    if event_date:
        try:
            dt = date.fromisoformat(event_date)
        except ValueError:
            click.echo(f"Invalid date format: {event_date}", err=True)
            sys.exit(1)
        events_list = event_store.read_date(dt)
    else:
        # Get today's events
        events_list = event_store.read_date(date.today())

    if not events_list:
        click.echo("No events found.")
        return

    click.echo(f"Showing {min(len(events_list), limit)} of {len(events_list)} events:\n")

    for event in events_list[-limit:]:
        ts = event.timestamp.strftime("%H:%M:%S")
        if event.event_type.value == "keypress":
            key_info = event.key
            if event.modifiers:
                key_info = f"{'+'.join(event.modifiers)}+{key_info}"
            click.echo(f"[{ts}] KEY: {key_info}")
        elif event.event_type.value == "mouseclick":
            action = "↓" if event.pressed else "↑"
            click.echo(f"[{ts}] MOUSE: {event.button.value}{action} @ ({event.x}, {event.y})")
        elif event.event_type.value == "screenshot":
            click.echo(f"[{ts}] SCREENSHOT: {event.trigger} -> {event.path}")
        elif event.event_type.value == "cron_screenshot":
            click.echo(f"[{ts}] CRON_SCREENSHOT: {event.path}")


@main.command()
@click.option("--limit", "-n", type=int, default=10, help="Number of chunks to show")
@click.pass_context
def chunks(ctx: click.Context, limit: int) -> None:
    """Show recent chunk summaries."""
    config: Config = ctx.obj["config"]

    summary_store = SummaryStore(config.summaries_dir)
    all_summaries = summary_store.read_all()

    if not all_summaries:
        click.echo("No chunk summaries available yet.")
        return

    click.echo(f"Showing {min(len(all_summaries), limit)} of {len(all_summaries)} chunks:\n")

    for summary in all_summaries[-limit:]:
        click.echo(f"=== Chunk {summary.chunk_index} ===")
        click.echo(f"Time: {summary.start_time.strftime('%Y-%m-%d %H:%M')} - {summary.end_time.strftime('%H:%M')}")
        click.echo(f"Events: {summary.event_count}")
        click.echo(f"Summary: {summary.summary_text}")
        if summary.key_activities:
            click.echo("Activities:")
            for activity in summary.key_activities:
                click.echo(f"  - {activity}")
        click.echo()


@main.command()
@click.pass_context
def config_show(ctx: click.Context) -> None:
    """Show current configuration."""
    config: Config = ctx.obj["config"]
    click.echo(config.model_dump_json(indent=2))


@main.command()
@click.option("--keypress/--no-keypress", default=None, help="Enable/disable keypress capture")
@click.option("--mouseclick/--no-mouseclick", default=None, help="Enable/disable mouseclick capture")
@click.option("--screenshot-on-click/--no-screenshot-on-click", default=None, help="Enable/disable screenshot on click")
@click.option("--cron-screenshot/--no-cron-screenshot", default=None, help="Enable/disable cron screenshots")
@click.option("--cron-schedule", type=str, default=None, help="Cron expression for screenshots")
@click.option("--summarizer/--no-summarizer", default=None, help="Enable/disable LLM summarization")
@click.option("--model", type=str, default=None, help="LLM model for summarization")
@click.option("--openai-key", type=str, default=None, help="OpenAI API key")
@click.pass_context
def config_set(
    ctx: click.Context,
    keypress: bool | None,
    mouseclick: bool | None,
    screenshot_on_click: bool | None,
    cron_screenshot: bool | None,
    cron_schedule: str | None,
    summarizer: bool | None,
    model: str | None,
    openai_key: str | None,
) -> None:
    """Update configuration."""
    config: Config = ctx.obj["config"]

    if keypress is not None:
        config.capture.enable_keypress = keypress
    if mouseclick is not None:
        config.capture.enable_mouseclick = mouseclick
    if screenshot_on_click is not None:
        config.capture.enable_screenshot_on_click = screenshot_on_click
    if cron_screenshot is not None:
        config.cron_screenshot.enabled = cron_screenshot
    if cron_schedule is not None:
        config.cron_screenshot.schedule = cron_schedule
    if summarizer is not None:
        config.summarizer.enabled = summarizer
    if model is not None:
        config.summarizer.model = model
    if openai_key is not None:
        config.openai_api_key = openai_key

    config.save()
    click.echo("Configuration updated.")
    click.echo("\nNote: Restart Lifelogger for changes to take effect.")


@main.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize Lifelogger configuration."""
    config: Config = ctx.obj["config"]
    config.ensure_dirs()
    config.save()

    click.echo(f"Lifelogger initialized.")
    click.echo(f"Data directory: {config.data_dir}")
    click.echo(f"Config file: {config.config_file}")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Set your OpenAI API key:")
    click.echo("     lifelogger config-set --openai-key YOUR_KEY")
    click.echo()
    click.echo("  2. Start the daemon:")
    click.echo("     lifelogger start")


@main.command()
@click.option("--request", "-r", is_flag=True, help="Open system settings to grant permissions")
@click.pass_context
def permissions(ctx: click.Context, request: bool) -> None:
    """Check and request system permissions."""
    perms = check_all_permissions(verbose=True)

    all_granted = all(perms.values())

    if all_granted:
        click.echo("All permissions granted! You can start Lifelogger.")
    else:
        print_permission_instructions()
        if request:
            if not perms["accessibility"]:
                click.echo("Opening Accessibility settings...")
                request_accessibility_permissions()
            if not perms["screen_recording"]:
                click.echo("Opening Screen Recording settings...")
                request_screen_recording_permissions()


@main.command()
@click.pass_context
def logs(ctx: click.Context) -> None:
    """Show daemon logs."""
    config: Config = ctx.obj["config"]
    log_file = config.data_dir / "lifelogger.log"

    if not log_file.exists():
        click.echo("No log file found. Has Lifelogger been started?")
        return

    click.echo(f"=== Logs from {log_file} ===\n")
    with open(log_file) as f:
        # Show last 50 lines
        lines = f.readlines()
        for line in lines[-50:]:
            click.echo(line.rstrip())


if __name__ == "__main__":
    main()
