"""Engine and Studio management commands for DHT CLI."""

from typing import Optional

import typer

# Initialize Typer apps
engine_app = typer.Typer(help="Manage compute engines for development.")
studio_app = typer.Typer(help="Manage persistent development studios.")

# Use lazy loading pattern similar to main.py swarm commands
# Import functions only when commands are actually called


# Engine commands
@engine_app.command("launch")
def launch_engine_cmd(
    name: str = typer.Argument(help="Name for the new engine"),
    engine_type: str = typer.Option(
        "cpu",
        "--type",
        "-t",
        help="Engine type: cpu, cpumax, t4, a10g, a100, 4_t4, 8_t4, 4_a10g, 8_a10g",
    ),
    user: str = typer.Option(None, "--user", "-u", help="Override username"),
    boot_disk_size: int = typer.Option(
        None,
        "--size",
        "-s",
        help="Boot disk size in GB (default: 50GB, min: 20GB, max: 1000GB)",
    ),
    availability_zone: str = typer.Option(
        None,
        "--az",
        help="Prefer a specific Availability Zone (e.g., us-east-1b). If omitted the service will try all public subnets.",
    ),
):
    """Launch a new engine instance."""
    from .engine_core import launch_engine

    return launch_engine(name, engine_type, user, boot_disk_size, availability_zone)


@engine_app.command("list")
def list_engines_cmd(
    user: str = typer.Option(None, "--user", "-u", help="Filter by user"),
    running_only: bool = typer.Option(
        False, "--running", help="Show only running engines"
    ),
    stopped_only: bool = typer.Option(
        False, "--stopped", help="Show only stopped engines"
    ),
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed status (slower)"
    ),
):
    """List engines (shows all engines by default)."""
    from .engine_core import list_engines

    return list_engines(user, running_only, stopped_only, detailed)


@engine_app.command("status")
def engine_status_cmd(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
    detailed: bool = typer.Option(
        False, "--detailed", "-d", help="Show detailed status (slower)"
    ),
    show_log: bool = typer.Option(
        False, "--show-log", help="Show bootstrap log (requires --detailed)"
    ),
):
    """Show engine status and information."""
    from .engine_core import engine_status

    return engine_status(name_or_id, detailed, show_log)


@engine_app.command("start")
def start_engine_cmd(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
):
    """Start a stopped engine."""
    from .engine_lifecycle import start_engine

    return start_engine(name_or_id)


@engine_app.command("stop")
def stop_engine_cmd(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force stop and detach all studios"
    ),
):
    """Stop an engine."""
    from .engine_lifecycle import stop_engine

    return stop_engine(name_or_id, force)


@engine_app.command("terminate")
def terminate_engine_cmd(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
):
    """Permanently terminate an engine."""
    from .engine_lifecycle import terminate_engine

    return terminate_engine(name_or_id)


@engine_app.command("ssh")
def ssh_engine_cmd(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
    admin: bool = typer.Option(
        False, "--admin", help="Connect as ec2-user instead of the engine owner user"
    ),
    idle_timeout: int = typer.Option(
        600,
        "--idle-timeout",
        help="Idle timeout (seconds) for the SSM port-forward (0 = disable)",
    ),
):
    """Connect to an engine via SSH."""
    from .engine_management import ssh_engine

    return ssh_engine(name_or_id, admin, idle_timeout)


@engine_app.command("config-ssh")
def config_ssh_cmd(
    clean: bool = typer.Option(False, "--clean", help="Remove all managed entries"),
    all_engines: bool = typer.Option(
        False, "--all", "-a", help="Include all engines from all users"
    ),
    admin: bool = typer.Option(
        False,
        "--admin",
        help="Generate entries that use ec2-user instead of per-engine owner user",
    ),
):
    """Update SSH config with available engines."""
    from .engine_management import config_ssh

    return config_ssh(clean, all_engines, admin)


@engine_app.command("resize")
def resize_engine_cmd(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
    size: int = typer.Option(..., "--size", "-s", help="New size in GB"),
    online: bool = typer.Option(
        False,
        "--online",
        help="Resize while running (requires manual filesystem expansion)",
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force resize and detach all studios"
    ),
):
    """Resize an engine's boot disk."""
    from .engine_management import resize_engine

    return resize_engine(name_or_id, size, online, force)


@engine_app.command("gami")
def create_ami_cmd(
    name_or_id: str = typer.Argument(
        help="Engine name or instance ID to create AMI from"
    ),
):
    """Create a 'Golden AMI' from a running engine."""
    from .engine_management import create_ami

    return create_ami(name_or_id)


@engine_app.command("coffee")
def coffee_cmd(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
    duration: str = typer.Argument("4h", help="Duration (e.g., 2h, 30m, 2h30m)"),
    cancel: bool = typer.Option(
        False, "--cancel", help="Cancel existing coffee lock instead of extending"
    ),
):
    """Pour ☕ for an engine: keeps it awake for the given duration (or cancel)."""
    from .engine_maintenance import coffee

    return coffee(name_or_id, duration, cancel)


@engine_app.command("idle")
def idle_timeout_cmd_wrapper(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
    set: Optional[str] = typer.Option(
        None, "--set", "-s", help="New timeout (e.g., 2h30m, 45m)"
    ),
    slack: Optional[str] = typer.Option(
        None, "--slack", help="Set Slack notifications: none, default, all"
    ),
):
    """Show or set engine idle-detector settings."""
    from .engine_maintenance import idle_timeout_cmd

    return idle_timeout_cmd(name_or_id=name_or_id, set=set, slack=slack)


@engine_app.command("debug")
def debug_engine_cmd(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
):
    """Debug engine bootstrap status and files."""
    from .engine_maintenance import debug_engine

    return debug_engine(name_or_id)


@engine_app.command("repair")
def repair_engine_cmd(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
):
    """Repair an engine that's stuck in a bad state (e.g., after GAMI creation)."""
    from .engine_maintenance import repair_engine

    return repair_engine(name_or_id)


# Studio commands
@studio_app.command("create")
def create_studio_cmd(
    size_gb: int = typer.Option(50, "--size", "-s", help="Studio size in GB"),
):
    """Create a new studio for the current user."""
    from .studio_commands import create_studio

    return create_studio(size_gb)


@studio_app.command("status")
def studio_status_cmd(
    user: str = typer.Option(
        None, "--user", "-u", help="Check status for a different user (admin only)"
    ),
):
    """Show status of your studio."""
    from .studio_commands import studio_status

    return studio_status(user)


@studio_app.command("attach")
def attach_studio_cmd(
    engine_name_or_id: str = typer.Argument(help="Engine name or instance ID"),
    user: str = typer.Option(
        None, "--user", "-u", help="Attach a different user's studio (admin only)"
    ),
):
    """Attach your studio to an engine."""
    from .studio_commands import attach_studio

    return attach_studio(engine_name_or_id, user)


@studio_app.command("detach")
def detach_studio_cmd(
    user: str = typer.Option(
        None, "--user", "-u", help="Detach a different user's studio (admin only)"
    ),
):
    """Detach your studio from its current engine."""
    from .studio_commands import detach_studio

    return detach_studio(user)


@studio_app.command("delete")
def delete_studio_cmd(
    user: str = typer.Option(
        None, "--user", "-u", help="Delete a different user's studio (admin only)"
    ),
):
    """Delete your studio permanently."""
    from .studio_commands import delete_studio

    return delete_studio(user)


@studio_app.command("list")
def list_studios_cmd(
    all_users: bool = typer.Option(
        False, "--all", "-a", help="Show all users' studios"
    ),
):
    """List studios."""
    from .studio_commands import list_studios

    return list_studios(all_users)


@studio_app.command("reset")
def reset_studio_cmd(
    user: str = typer.Option(
        None, "--user", "-u", help="Reset a different user's studio"
    ),
):
    """Reset a stuck studio (admin operation)."""
    from .studio_commands import reset_studio

    return reset_studio(user)


@studio_app.command("resize")
def resize_studio_cmd(
    size: int = typer.Option(..., "--size", "-s", help="New size in GB"),
    user: str = typer.Option(
        None, "--user", "-u", help="Resize a different user's studio (admin only)"
    ),
):
    """Resize your studio volume (requires detachment)."""
    from .studio_commands import resize_studio

    return resize_studio(size, user)
