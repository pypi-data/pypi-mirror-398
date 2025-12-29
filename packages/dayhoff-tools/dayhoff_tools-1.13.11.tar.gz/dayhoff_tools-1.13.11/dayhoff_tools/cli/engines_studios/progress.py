"""Progress display utilities for async operations."""

import time
from typing import Any, Callable, Dict, Optional

import click


def wait_with_progress(
    status_func: Callable[[], Dict[str, Any]],
    is_complete_func: Callable[[Dict[str, Any]], bool],
    label: str = "Progress",
    timeout_seconds: int = 300,
    poll_interval: float = 2.0,
    show_stages: bool = True,
) -> Dict[str, Any]:
    """Wait for an async operation with progress display.

    Args:
        status_func: Function that returns current status dict
        is_complete_func: Function that checks if operation is complete
        label: Label for progress bar
        timeout_seconds: Maximum time to wait
        poll_interval: Seconds between status checks
        show_stages: Whether to show stage/step updates

    Returns:
        Final status dict

    Raises:
        TimeoutError: If operation exceeds timeout
    """

    stages_shown = set()
    start_time = time.time()

    with click.progressbar(length=100, label=label) as bar:
        while True:
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                raise TimeoutError(f"Operation exceeded {timeout_seconds}s timeout")

            # Get current status
            try:
                status = status_func()
            except Exception as e:
                click.echo(f"\nError fetching status: {e}", err=True)
                time.sleep(poll_interval)
                continue

            # Update progress bar
            progress = status.get("progress_percent", 0)
            if progress > bar.pos:
                bar.update(progress - bar.pos)

            # Show stage/step updates
            if show_stages:
                current_stage = status.get("current_stage") or status.get(
                    "current_step"
                )
                if current_stage and current_stage not in stages_shown:
                    stages_shown.add(current_stage)
                    elapsed = int(time.time() - start_time)
                    display_name = current_stage.replace("_", " ").title()
                    click.echo(f"  [{elapsed}s] {display_name}")

            # Check completion
            if is_complete_func(status):
                bar.update(100 - bar.pos)
                return status

            # Check for failure
            status_value = status.get("status", "").lower()
            if status_value == "failed" or status_value == "error":
                error = status.get("error", "Unknown error")
                raise Exception(f"Operation failed: {error}")

            time.sleep(poll_interval)


def format_sensor_status(sensor_data: Dict[str, Any]) -> str:
    """Format sensor status for display.

    Args:
        sensor_data: Sensor data dict

    Returns:
        Formatted string
    """
    active = sensor_data.get("active", False)
    reason = sensor_data.get("reason", "No reason provided")

    if active:
        return f"🟢\n  {reason}"
    else:
        return "⚪"


def format_idle_state(
    idle_state: Dict[str, Any],
    detailed: bool = False,
    attached_studios: Optional[list] = None,
) -> str:
    """Format idle state for display.

    Args:
        idle_state: Idle state dict
        detailed: Whether to show detailed sensor information
        attached_studios: Optional list of attached studio dicts

    Returns:
        Formatted string
    """
    is_idle = idle_state.get("is_idle", False)

    lines = []

    # Status line
    icon = "🟡 IDLE" if is_idle else "🟢 ACTIVE"
    lines.append(f"Idle Status: {icon}")

    # Timing information
    if idle_state.get("idle_seconds"):
        timeout = idle_state.get("timeout_seconds", 1800)
        elapsed = idle_state["idle_seconds"]
        remaining = max(0, timeout - elapsed)
        lines.append(f"Idle Time: {elapsed}s / {timeout}s")
        if remaining > 0:
            minutes = remaining // 60
            # Yellow text using ANSI escape codes
            lines.append(f"\033[33mWill shutdown in: {remaining}s ({minutes}m)\033[0m")

    # Attached studios (show before sensors)
    if attached_studios:
        # Purple text for studio names
        studio_names = ", ".join(
            [
                f"\033[35m{s.get('user', s.get('studio_id', 'unknown'))}\033[0m"
                for s in attached_studios
            ]
        )
        lines.append(f"\nAttached Studios: {studio_names}")
    else:
        # Normal text for "None"
        lines.append(f"\nAttached Studios: None")

    # Detailed sensor information with colorful emojis
    if detailed and idle_state.get("sensors"):
        lines.append(f"\n{'═'*60}")
        lines.append("🔍 Activity Sensors:")
        lines.append(f"{'═'*60}")

        # Sensor emoji mapping
        sensor_emojis = {
            "coffee": "☕",
            "ssh": "🐚",
            "ide": "💻",
            "docker": "🐳",
        }

        for sensor_name, sensor_data in idle_state["sensors"].items():
            emoji = sensor_emojis.get(sensor_name.lower(), "📊")
            active = sensor_data.get("active", False)

            # Special formatting for coffee sensor
            if sensor_name.lower() == "coffee" and active:
                # Extract minutes from details for cleaner display
                details = sensor_data.get("details", {})
                remaining_seconds = int(details.get("remaining_seconds", 0))
                remaining_minutes = remaining_seconds // 60
                lines.append(f"\n{emoji} {sensor_name.upper()} 🟢")
                lines.append(f"  Caffeinated for another {remaining_minutes}m")
            else:
                status_icon = format_sensor_status(sensor_data)
                # Format: emoji NAME status_icon (on same line for inactive, split for active)
                if active:
                    lines.append(
                        f"\n{emoji} {sensor_name.upper()} {status_icon.split(chr(10))[0]}"
                    )
                    # Add reason on next line
                    reason_line = (
                        status_icon.split("\n")[1] if "\n" in status_icon else ""
                    )
                    if reason_line:
                        lines.append(reason_line)
                else:
                    lines.append(f"\n{emoji} {sensor_name.upper()} {status_icon}")

            # Show details if available (skip for active coffee sensor with special formatting)
            if sensor_name.lower() == "coffee" and active:
                continue  # Already showed coffee details in special format above

            details = sensor_data.get("details", {})
            if details:
                for key, value in details.items():
                    # Skip internal bookkeeping fields and redundant info
                    if key in [
                        "unique_flavor_count",
                        "unique_pid_count",
                        "expires_at",
                        "flavors",
                        "remaining_seconds",  # Redundant with time shown in reason
                        "pid_count",  # Redundant with connections list
                        "connections",  # Redundant, connections shown in sessions/containers
                    ]:
                        continue

                    if isinstance(value, list):
                        if value:  # Only show non-empty lists
                            # Show workload containers with clear header
                            if key == "containers":
                                # Show actual workload container names that are keeping engine active
                                for item in value[:5]:
                                    lines.append(f"    • {item}")
                            elif key in ["connections", "sessions"]:
                                # Just show the items with bullets, no header
                                for item in value[:5]:
                                    lines.append(f"    • {item}")
                            elif key == "ignored":
                                # Ignored list at same indentation level, with header
                                lines.append(f"  {key}:")
                                for item in value[:5]:
                                    lines.append(f"    • {item}")
                            else:
                                # Other lists get shown with bullets only
                                for item in value[:5]:
                                    lines.append(f"    • {item}")
                    elif not isinstance(value, (dict, list)):
                        lines.append(f"  ℹ️  {key}: {value}")

    return "\n".join(lines)


def format_time_ago(timestamp: str) -> str:
    """Format timestamp as time ago.

    Args:
        timestamp: ISO format timestamp

    Returns:
        Human readable time ago string
    """
    from datetime import datetime

    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        delta = now - dt

        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"
    except:
        return timestamp
