"""Platform-specific permission handling for Lifelogger."""

import platform
import subprocess
import sys

PLATFORM = platform.system()


def check_accessibility_permissions() -> bool:
    """Check if accessibility permissions are granted (macOS only).

    Returns:
        True if permissions are granted or not on macOS, False otherwise.
    """
    if PLATFORM != "Darwin":
        return True

    try:
        # Use AppleScript to check accessibility permissions
        result = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to get name of first process',
            ],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def check_screen_recording_permissions() -> bool:
    """Check if screen recording permissions are granted (macOS only).

    Returns:
        True if permissions are granted or not on macOS, False otherwise.
    """
    if PLATFORM != "Darwin":
        return True

    try:
        # Try to take a screenshot - this will fail without permissions
        import mss
        with mss.mss() as sct:
            # Just try to grab, don't save
            sct.grab(sct.monitors[0])
        return True
    except Exception:
        return False


def request_accessibility_permissions() -> None:
    """Open System Preferences to accessibility settings (macOS only)."""
    if PLATFORM != "Darwin":
        return

    subprocess.run(
        [
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
        ],
        check=False,
    )


def request_screen_recording_permissions() -> None:
    """Open System Preferences to screen recording settings (macOS only)."""
    if PLATFORM != "Darwin":
        return

    subprocess.run(
        [
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
        ],
        check=False,
    )


def get_terminal_app_name() -> str:
    """Get the name of the current terminal application."""
    if PLATFORM != "Darwin":
        return "Terminal"

    # Try to detect the terminal app
    term_program = subprocess.run(
        ["echo", "$TERM_PROGRAM"],
        capture_output=True,
        text=True,
        shell=True,
    )

    term = term_program.stdout.strip()
    if "iTerm" in term:
        return "iTerm"
    elif "Apple_Terminal" in term:
        return "Terminal"
    else:
        return "your terminal app"


def print_permission_instructions() -> None:
    """Print instructions for granting permissions."""
    if PLATFORM == "Darwin":
        terminal = get_terminal_app_name()
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                    macOS Permissions Required                     ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Lifelogger needs the following permissions to function:          ║
║                                                                   ║
║  1. ACCESSIBILITY (for keyboard/mouse capture)                    ║
║     System Settings > Privacy & Security > Accessibility          ║
║     → Enable for: {terminal:50s}║
║                                                                   ║
║  2. SCREEN RECORDING (for screenshots)                            ║
║     System Settings > Privacy & Security > Screen Recording       ║
║     → Enable for: {terminal:50s}║
║                                                                   ║
║  After granting permissions, you may need to restart your         ║
║  terminal application.                                            ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
""".format(terminal=terminal))

    elif PLATFORM == "Linux":
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                     Linux Permissions Info                        ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Keyboard/mouse capture may require:                              ║
║                                                                   ║
║  Option 1: Run as root (not recommended)                          ║
║    sudo lifelogger start                                          ║
║                                                                   ║
║  Option 2: Add user to 'input' group (recommended)                ║
║    sudo usermod -aG input $USER                                   ║
║    # Then log out and back in                                     ║
║                                                                   ║
║  Option 3: Set up udev rules for input devices                    ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
""")


def check_all_permissions(verbose: bool = True) -> dict[str, bool]:
    """Check all required permissions.

    Args:
        verbose: Print status messages.

    Returns:
        Dictionary with permission status.
    """
    results = {
        "accessibility": check_accessibility_permissions(),
        "screen_recording": check_screen_recording_permissions(),
    }

    if verbose:
        print("Permission Status:")
        print(f"  Accessibility (keyboard/mouse): {'✓ Granted' if results['accessibility'] else '✗ Not granted'}")
        print(f"  Screen Recording (screenshots):  {'✓ Granted' if results['screen_recording'] else '✗ Not granted'}")
        print()

    return results
