# Lifelogger

Personal activity tracking daemon with LLM summarization.

[![CI](https://github.com/JacobFV/lifelogger/actions/workflows/ci.yml/badge.svg)](https://github.com/JacobFV/lifelogger/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/lifelogger-daemon.svg)](https://pypi.org/project/lifelogger-daemon/)
[![Python](https://img.shields.io/pypi/pyversions/lifelogger-daemon.svg)](https://pypi.org/project/lifelogger-daemon/)

## Features

- Keyboard and mouse event capture
- Automatic screenshots (on click and/or cron schedule)
- LLM-powered activity summarization
- Cross-platform (macOS, Windows, Linux)
- Background daemon with CLI control

## Installation

```bash
pip install lifelogger-daemon
```

## Quick Start

```bash
# Initialize configuration
lifelogger init

# (Optional) Set your OpenAI API key for summarization
lifelogger config-set --openai-key YOUR_API_KEY

# Start the daemon
lifelogger start

# Check status
lifelogger status

# View activity summary
lifelogger summary

# Stop the daemon
lifelogger stop
```

## Usage

### Commands

| Command | Description |
|---------|-------------|
| `lifelogger init` | Initialize configuration and data directories |
| `lifelogger start` | Start the background daemon |
| `lifelogger start -f` | Run in foreground (for debugging) |
| `lifelogger stop` | Stop the daemon |
| `lifelogger status` | Show daemon status and statistics |
| `lifelogger summary` | Show current activity summary |
| `lifelogger events` | Show recent events |
| `lifelogger chunks` | Show chunk summaries |
| `lifelogger config-show` | Display current configuration |
| `lifelogger config-set` | Update configuration |

### Configuration

Configuration is stored in `~/.lifelogger/config.json`. You can modify it via CLI:

```bash
# Enable/disable capture types
lifelogger config-set --keypress/--no-keypress
lifelogger config-set --mouseclick/--no-mouseclick
lifelogger config-set --screenshot-on-click/--no-screenshot-on-click

# Configure cron screenshots
lifelogger config-set --cron-screenshot/--no-cron-screenshot
lifelogger config-set --cron-schedule "*/5 * * * *"

# Configure summarization
lifelogger config-set --summarizer/--no-summarizer
lifelogger config-set --model gpt-4o-mini
lifelogger config-set --openai-key YOUR_KEY
```

Environment variables are also supported:
- `LIFELOGGER_OPENAI_API_KEY`
- `LIFELOGGER_CAPTURE_ENABLE_KEYPRESS`
- `LIFELOGGER_CAPTURE_ENABLE_MOUSECLICK`
- etc.

## Platform Notes

### macOS
Requires accessibility permissions for keyboard/mouse capture. Grant permissions in System Preferences > Privacy & Security > Accessibility.

### Linux
May require running as root or adding user to the `input` group for keyboard/mouse capture.

### Windows
Should work out of the box. Some antivirus software may flag keyboard monitoring.

## Development

```bash
# Clone the repo
git clone https://github.com/JacobFV/lifelogger.git
cd lifelogger

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy lifelogger

# Linting
ruff check lifelogger
```

## License

MIT
