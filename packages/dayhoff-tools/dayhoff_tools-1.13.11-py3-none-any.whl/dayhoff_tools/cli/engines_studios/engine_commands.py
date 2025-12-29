"""Engine CLI commands for engines_studios system."""

import os
import subprocess
from typing import Optional

import click

from .api_client import StudioManagerClient
from .auth import check_aws_auth, detect_aws_environment, get_aws_username
from .progress import format_idle_state, format_time_ago, wait_with_progress


def _update_ssh_config_silent(client: StudioManagerClient, env: str) -> bool:
    """Update SSH config silently. Returns True if successful."""
    ssh_config_path = os.path.expanduser("~/.ssh/config")

    try:
        # Read existing config
        if os.path.exists(ssh_config_path):
            with open(ssh_config_path, "r") as f:
                lines = f.readlines()
        else:
            lines = []

        # Remove managed entries
        managed_start = "# BEGIN DAYHOFF ENGINES\n"
        managed_end = "# END DAYHOFF ENGINES\n"

        new_lines = []
        skip = False
        for line in lines:
            if line == managed_start:
                skip = True
            elif line == managed_end:
                skip = False
                continue
            elif not skip:
                new_lines.append(line)

        # Get engines
        result = client.list_engines()
        engines = result.get("engines", [])

        if not engines:
            return False

        # Generate new entries
        config_entries = [managed_start]

        try:
            current_user = get_aws_username()
        except RuntimeError:
            # Not authenticated - can't determine user, skip filtering
            current_user = None

        for engine in engines:
            user = engine.get("user", "unknown")

            # Skip engines owned by other users (unless user is unknown or we can't determine current user)
            if current_user and user != "unknown" and user != current_user:
                continue

            instance_id = engine.get("instance_id")
            name = engine.get("name", instance_id)
            state = engine.get("state", "unknown")

            # Only add running engines
            if state != "running":
                continue

            # Map environment to AWS profile
            profile = f"{env}-devaccess"

            config_entries.append(f"\nHost {name}\n")
            config_entries.append(f"    HostName {instance_id}\n")
            config_entries.append(f"    User {user}\n")
            config_entries.append(f"    ForwardAgent yes\n")
            config_entries.append(
                f"    ProxyCommand aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p' --profile {profile}\n"
            )

        config_entries.append(managed_end)

        # Write back
        new_lines.extend(config_entries)

        with open(ssh_config_path, "w") as f:
            f.writelines(new_lines)

        return True

    except Exception:
        return False


@click.group()
def engine_cli():
    """Manage engines."""
    pass


# ============================================================================
# Lifecycle Management
# ============================================================================


@engine_cli.command("launch")
@click.argument("name")
@click.option(
    "--type",
    "engine_type",
    required=True,
    type=click.Choice(
        ["cpu", "cpumax", "t4", "a10g", "a100", "4_t4", "8_t4", "4_a10g", "8_a10g"]
    ),
)
@click.option("--size", "boot_disk_size", type=int, help="Boot disk size in GB")
@click.option(
    "--user",
    default=None,
    help="User to launch engine for (defaults to current user, use for testing/admin)",
)
@click.option(
    "--no-wait", is_flag=True, help="Return immediately without waiting for readiness"
)
@click.option(
    "--skip-ssh-config", is_flag=True, help="Don't automatically update SSH config"
)
@click.option(
    "--yes", "-y", is_flag=True, help="Skip confirmation for non-dev environments"
)
@click.option(
    "--env",
    default=None,
    help="Environment (dev, sand, prod) - auto-detected if not specified",
)
def launch_engine(
    name: str,
    engine_type: str,
    boot_disk_size: Optional[int],
    yes: bool,
    user: Optional[str],
    no_wait: bool,
    skip_ssh_config: bool,
    env: Optional[str],
):
    """Launch a new engine for the current user (or specified user with --user flag)."""

    # Check AWS auth first to provide clear error messages
    check_aws_auth()

    # Auto-detect environment if not specified
    if env is None:
        env = detect_aws_environment()
        click.echo(f"🔍 Detected environment: {env}")

        # Require confirmation for non-dev environments
        if env != "dev" and not yes:
            if not click.confirm(
                f"⚠️  You are about to launch in {env.upper()}. Continue?"
            ):
                click.echo("Cancelled")
                raise click.Abort()

    client = StudioManagerClient(environment=env)

    # Get user (from flag or current AWS user)
    if user is None:
        try:
            user = get_aws_username()
        except RuntimeError as e:
            click.echo(f"✗ {e}", err=True)
            raise click.Abort()

    click.echo(f"🚀 Launching {engine_type} engine '{name}' for {user}...")

    try:
        # Launch the engine
        engine = client.launch_engine(
            name=name, user=user, engine_type=engine_type, boot_disk_size=boot_disk_size
        )

        engine_id = engine["instance_id"]
        click.echo(f"✓ EC2 instance launched: {engine_id}")

        if no_wait:
            click.echo(f"\nEngine is initializing. Check status with:")
            click.echo(f"  dh engine status {name}")
            return

        # Wait for readiness with progress updates
        click.echo(f"\n⏳ Waiting for engine to be ready (typically 2-3 minutes)...\n")

        try:
            _final_status = wait_with_progress(
                status_func=lambda: client.get_engine_readiness(engine_id),
                is_complete_func=lambda s: s.get("ready", False),
                label="Progress",
                timeout_seconds=600,
            )

            click.echo(f"\n✓ Engine ready!")

            # Update SSH config unless skipped
            if not skip_ssh_config:
                if _update_ssh_config_silent(client, env):
                    click.echo("✓ SSH config updated")

            click.echo(f"\nConnect with:")
            click.echo(f"  dh studio attach {name}")
            click.echo(f"  ssh {name}")

        except TimeoutError:
            click.echo(f"\n⚠ Engine is still initializing. Check status with:")
            click.echo(f"  dh engine status {name}")

    except Exception as e:
        error_msg = str(e)

        # Check for quota/limit errors
        if "VcpuLimitExceeded" in error_msg or "vCPU limit" in error_msg:
            click.echo(f"✗ Failed to launch engine: vCPU quota exceeded", err=True)
            click.echo("", err=True)
            click.echo(
                f"The {env} AWS account has insufficient vCPU quota for {engine_type} instances.",
                err=True,
            )
            click.echo("", err=True)
            click.echo("Solutions:", err=True)
            click.echo(
                "  1. Use a different instance type (e.g., --type cpu)", err=True
            )
            click.echo("  2. Request a quota increase:", err=True)
            click.echo("     • AWS Console → Service Quotas → Amazon EC2", err=True)
            click.echo("     • Find quota for the instance family", err=True)
            click.echo(
                "     • Request increase (typically approved within 24h)", err=True
            )
            click.echo("", err=True)
            click.echo(
                "For testing infrastructure, use CPU instances instead of GPU.",
                err=True,
            )
            raise click.Abort()

        # Check for insufficient capacity errors
        if "InsufficientInstanceCapacity" in error_msg:
            click.echo(
                f"✗ Failed to launch engine: insufficient EC2 capacity", err=True
            )
            click.echo("", err=True)
            click.echo(
                f"AWS does not have available {engine_type} capacity in your region/AZ.",
                err=True,
            )
            click.echo("", err=True)
            click.echo("Solutions:", err=True)
            click.echo(
                "  1. Try again in a few minutes (capacity fluctuates)", err=True
            )
            click.echo("  2. Use a different instance type", err=True)
            click.echo("  3. Contact AWS support for capacity reservations", err=True)
            raise click.Abort()

        # Check for instance limit errors
        if (
            "InstanceLimitExceeded" in error_msg
            or "instance limit" in error_msg.lower()
        ):
            click.echo(f"✗ Failed to launch engine: instance limit exceeded", err=True)
            click.echo("", err=True)
            click.echo(
                f"You have reached the maximum number of running instances in {env}.",
                err=True,
            )
            click.echo("", err=True)
            click.echo("Solutions:", err=True)
            click.echo(
                "  1. Terminate unused engines: dh engine2 list --env {env}", err=True
            )
            click.echo("  2. Request a limit increase via AWS Service Quotas", err=True)
            raise click.Abort()

        # Generic error
        click.echo(f"✗ Failed to launch engine: {e}", err=True)
        raise click.Abort()


@engine_cli.command("start")
@click.argument("name_or_id")
@click.option(
    "--no-wait", is_flag=True, help="Return immediately without waiting for readiness"
)
@click.option(
    "--skip-ssh-config", is_flag=True, help="Don't automatically update SSH config"
)
@click.option(
    "--yes", "-y", is_flag=True, help="Skip confirmation for non-dev environments"
)
@click.option(
    "--env",
    default=None,
    help="Environment (dev, sand, prod) - auto-detected if not specified",
)
def start_engine(
    name_or_id: str, no_wait: bool, skip_ssh_config: bool, yes: bool, env: Optional[str]
):
    """Start a stopped engine."""

    # Check AWS auth first to provide clear error messages
    check_aws_auth()

    # Auto-detect environment if not specified
    if env is None:
        env = detect_aws_environment()
        click.echo(f"🔍 Detected environment: {env}")

        # Require confirmation for non-dev environments
        if env != "dev" and not yes:
            if not click.confirm(
                f"⚠️  You are about to operate in {env.upper()}. Continue?"
            ):
                click.echo("Cancelled")
                raise click.Abort()

    client = StudioManagerClient(environment=env)

    try:
        # Find engine
        engine = client.get_engine_by_name(name_or_id)
        if not engine:
            engine = {"instance_id": name_or_id, "name": name_or_id}

        engine_id = engine["instance_id"]
        engine_name = engine.get("name", engine_id)

        result = client.start_engine(engine_id)

        if "error" in result:
            click.echo(f"✗ Error: {result['error']}", err=True)
            raise click.Abort()

        click.echo(f"✓ Engine '{engine_name}' is starting")

        if no_wait:
            click.echo(f"\nCheck status with:")
            click.echo(f"  dh engine status {engine_name}")
            return

        # Wait for engine to be running and fully ready (including status checks)
        click.echo(f"\n⏳ Waiting for engine to be ready...\n")

        try:

            def check_engine_running():
                """Check if engine is running, status checks passed, and SSM is accessible."""
                # Check EC2 state and status checks
                instance_status = client.check_instance_status(engine_id)
                if "error" in instance_status:
                    return {"ready": False, "progress_percent": 0}

                state = instance_status.get("state", "unknown")
                status_checks_passed = instance_status.get("reachable", False)

                # Check SSM accessibility via idle state
                engine_status = client.get_engine_status(engine_id)
                ssm_working = (
                    not ("error" in engine_status)
                    and engine_status.get("idle_state") is not None
                )

                # Progress based on state and checks
                if state == "pending":
                    progress = 30
                elif state == "running" and not status_checks_passed:
                    # Running but status checks still initializing
                    progress = 60
                elif state == "running" and status_checks_passed and not ssm_working:
                    # Status checks passed but SSM not yet responding
                    progress = 85
                elif state == "running" and status_checks_passed and ssm_working:
                    # Fully ready
                    progress = 100
                else:
                    progress = 10

                # Ready when running AND status checks pass AND SSM works
                ready = state == "running" and status_checks_passed and ssm_working

                return {"ready": ready, "progress_percent": progress}

            _final_status = wait_with_progress(
                status_func=check_engine_running,
                is_complete_func=lambda s: s.get("ready", False),
                label="Starting",
                timeout_seconds=300,
                show_stages=False,
            )

            click.echo(f"\n✓ Engine ready!")

            # Update SSH config unless skipped
            if not skip_ssh_config:
                if _update_ssh_config_silent(client, env):
                    click.echo("✓ SSH config updated")

            click.echo(f"\nConnect with:")
            click.echo(f"  dh studio attach {engine_name}")
            click.echo(f"  ssh {engine_name}")

        except TimeoutError:
            click.echo(f"\n⚠ Engine is still starting. Check status with:")
            click.echo(f"  dh engine status {engine_name}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@engine_cli.command("stop")
@click.argument("name_or_id")
@click.option(
    "--yes", "-y", is_flag=True, help="Skip confirmation for non-dev environments"
)
@click.option(
    "--env",
    default=None,
    help="Environment (dev, sand, prod) - auto-detected if not specified",
)
def stop_engine(name_or_id: str, yes: bool, env: Optional[str]):
    """Stop a running engine."""

    # Check AWS auth first to provide clear error messages
    check_aws_auth()

    # Auto-detect environment if not specified
    if env is None:
        env = detect_aws_environment()
        click.echo(f"🔍 Detected environment: {env}")

        # Require confirmation for non-dev environments
        if env != "dev" and not yes:
            if not click.confirm(
                f"⚠️  You are about to operate in {env.upper()}. Continue?"
            ):
                click.echo("Cancelled")
                raise click.Abort()

    client = StudioManagerClient(environment=env)

    try:
        # Find engine
        engine = client.get_engine_by_name(name_or_id)
        if not engine:
            engine = {"instance_id": name_or_id, "name": name_or_id}

        engine_id = engine["instance_id"]
        engine_name = engine.get("name", engine_id)

        click.echo(f"Stopping engine '{engine_name}'...")

        result = client.stop_engine(engine_id)

        if "error" in result:
            click.echo(f"✗ Error: {result['error']}", err=True)
            raise click.Abort()

        click.echo(f"✓ Engine '{engine_name}' is stopping")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@engine_cli.command("terminate")
@click.argument("name_or_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.option(
    "--env",
    default=None,
    help="Environment (dev, sand, prod) - auto-detected if not specified",
)
def terminate_engine(name_or_id: str, yes: bool, env: Optional[str]):
    """Terminate an engine."""

    # Check AWS auth first to provide clear error messages
    check_aws_auth()

    # Auto-detect environment if not specified
    if env is None:
        env = detect_aws_environment()
        click.echo(f"🔍 Detected environment: {env}")

        # Require confirmation for non-dev environments
        if env != "dev" and not yes:
            if not click.confirm(
                f"⚠️  You are about to operate in {env.upper()}. Continue?"
            ):
                click.echo("Cancelled")
                raise click.Abort()

    client = StudioManagerClient(environment=env)

    try:
        # Find engine
        engine = client.get_engine_by_name(name_or_id)
        if not engine:
            engine = {"instance_id": name_or_id, "name": name_or_id}

        engine_id = engine["instance_id"]
        engine_name = engine.get("name", engine_id)

        # Confirm
        if not yes:
            if not click.confirm(f"Terminate engine '{engine_name}' ({engine_id})?"):
                click.echo("Cancelled")
                return

        # Terminate
        result = client.terminate_engine(engine_id)

        if "error" in result:
            click.echo(f"✗ Error: {result['error']}", err=True)
            raise click.Abort()

        click.echo(f"✓ Engine '{engine_name}' is terminating")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# Status and Information
# ============================================================================


@engine_cli.command("status")
@click.argument("name_or_id")
@click.option(
    "--env",
    default=None,
    help="Environment (dev, sand, prod) - auto-detected if not specified",
)
def engine_status(name_or_id: str, env: Optional[str]):
    """Show engine status including idle detector state."""

    # Check AWS auth first to provide clear error messages
    check_aws_auth()

    # Auto-detect environment if not specified
    if env is None:
        env = detect_aws_environment()

    client = StudioManagerClient(environment=env)

    try:
        # Try to find by name first
        engine = client.get_engine_by_name(name_or_id)
        if not engine:
            # Assume it's an instance ID
            engine = {"instance_id": name_or_id, "name": name_or_id}

        engine_id = engine["instance_id"]

        # Get full status
        status_data = client.get_engine_status(engine_id)

        if "error" in status_data:
            click.echo(f"✗ Error: {status_data['error']}", err=True)
            raise click.Abort()

        # Display basic info - reordered per user request
        engine_name = status_data.get("name", engine_id)
        click.echo(
            f"Name: \033[34m{engine_name}\033[0m"
        )  # Blue engine name (renamed from "Engine")

        # Show state with color coding
        engine_state = status_data.get("state", "unknown")
        state_lower = engine_state.lower()
        if state_lower == "running":
            click.echo(f"State: \033[32m{engine_state}\033[0m")  # Green for running
        elif state_lower in ["stopped", "terminated"]:
            click.echo(
                f"State: \033[31m{engine_state}\033[0m"
            )  # Red for stopped/terminated
        elif state_lower in ["stopping", "starting", "pending"]:
            click.echo(
                f"State: \033[33m{engine_state}\033[0m"
            )  # Yellow for transitional states
        else:
            click.echo(f"State: {engine_state}")  # No color for unknown states

        # Show account (environment)
        click.echo(f"Account: {env}")

        if status_data.get("launch_time"):
            click.echo(f"Launched: {format_time_ago(status_data['launch_time'])}")

        click.echo(f"Type: {status_data.get('instance_type', 'unknown')}")
        click.echo(f"Instance ID: {engine_id}")

        if status_data.get("public_ip"):
            click.echo(f"Public IP: {status_data['public_ip']}")

        # Check if engine is stopped - don't show idle state or activity sensors
        if engine_state.lower() in ["stopped", "stopping", "terminated", "terminating"]:
            return

        # Show readiness if not ready
        if status_data.get("readiness"):
            readiness = status_data["readiness"]
            if not readiness.get("ready"):
                click.echo(
                    f"\n⏳ Initialization: {readiness.get('progress_percent', 0)}%"
                )
                click.echo(
                    f"Current Stage: {readiness.get('current_stage', 'unknown')}"
                )
                if readiness.get("estimated_time_remaining_seconds"):
                    remaining = readiness["estimated_time_remaining_seconds"]
                    click.echo(f"Estimated Time Remaining: {remaining}s")

        # Show idle state (only for running engines) - always detailed per user request
        attached_studios = status_data.get("attached_studios", [])
        if status_data.get("idle_state"):
            click.echo(
                f"\n{format_idle_state(status_data['idle_state'], detailed=True, attached_studios=attached_studios)}"
            )
        else:
            # If no idle state yet, still show attached studios
            if attached_studios:
                studio_names = ", ".join(
                    [
                        f"\033[35m{s.get('user', 'unknown')}\033[0m"
                        for s in attached_studios
                    ]
                )
                click.echo(f"\nAttached Studios: {studio_names}")
            else:
                click.echo(f"\nAttached Studios: None")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@engine_cli.command("list")
@click.option(
    "--env",
    default=None,
    help="Environment (dev, sand, prod) - auto-detected if not specified",
)
def list_engines(env: Optional[str]):
    """List all engines."""

    # Check AWS auth first to provide clear error messages
    check_aws_auth()

    # Auto-detect environment if not specified
    if env is None:
        env = detect_aws_environment()

    client = StudioManagerClient(environment=env)

    try:
        result = client.list_engines()
        engines = result.get("engines", [])

        # Show account header with blue account name
        click.echo(f"\nEngines for AWS Account \033[34m{env}\033[0m")

        if not engines:
            click.echo("No engines found\n")
            return

        # Calculate dynamic width for Name column (longest name + 2 for padding)
        max_name_len = max(
            (len(engine.get("name", "unknown")) for engine in engines), default=4
        )
        name_width = max(max_name_len + 2, len("Name") + 2)

        # Fixed widths for other columns
        state_width = 12
        user_width = 12
        type_width = 12
        id_width = 20

        # Table top border
        click.echo(
            "╭"
            + "─" * (name_width + 1)
            + "┬"
            + "─" * (state_width + 1)
            + "┬"
            + "─" * (user_width + 1)
            + "┬"
            + "─" * (type_width + 1)
            + "┬"
            + "─" * (id_width + 1)
            + "╮"
        )

        # Table header
        click.echo(
            f"│ {'Name':<{name_width}}│ {'State':<{state_width}}│ {'User':<{user_width}}│ {'Type':<{type_width}}│ {'Instance ID':<{id_width}}│"
        )

        # Header separator
        click.echo(
            "├"
            + "─" * (name_width + 1)
            + "┼"
            + "─" * (state_width + 1)
            + "┼"
            + "─" * (user_width + 1)
            + "┼"
            + "─" * (type_width + 1)
            + "┼"
            + "─" * (id_width + 1)
            + "┤"
        )

        # Table rows
        for engine in engines:
            name = engine.get("name", "unknown")
            state = engine.get("state", "unknown")
            user = engine.get("user", "unknown")
            engine_type = engine.get("engine_type", "unknown")
            instance_id = engine.get("instance_id", "unknown")

            # Truncate if needed
            if len(name) > name_width - 1:
                name = name[: name_width - 1]
            if len(user) > user_width - 1:
                user = user[: user_width - 1]
            if len(engine_type) > type_width - 1:
                engine_type = engine_type[: type_width - 1]

            # Color the name (blue)
            name_display = f"\033[34m{name:<{name_width}}\033[0m"

            # Color the state
            if state == "running":
                state_display = f"\033[32m{state:<{state_width}}\033[0m"  # Green
            elif state in ["starting", "stopping", "pending"]:
                state_display = f"\033[33m{state:<{state_width}}\033[0m"  # Yellow
            elif state == "stopped":
                state_display = f"\033[90m{state:<{state_width}}\033[0m"  # Grey (dim)
            else:
                state_display = f"{state:<{state_width}}"  # No color for other states

            # Color the instance ID (grey)
            instance_id_display = f"\033[90m{instance_id:<{id_width}}\033[0m"

            click.echo(
                f"│ {name_display}│ {state_display}│ {user:<{user_width}}│ {engine_type:<{type_width}}│ {instance_id_display}│"
            )

        # Table bottom border
        click.echo(
            "╰"
            + "─" * (name_width + 1)
            + "┴"
            + "─" * (state_width + 1)
            + "┴"
            + "─" * (user_width + 1)
            + "┴"
            + "─" * (type_width + 1)
            + "┴"
            + "─" * (id_width + 1)
            + "╯"
        )

        click.echo(f"Total: {len(engines)}\n")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# Access (SSH Config Management)
# ============================================================================


@engine_cli.command("config-ssh")
@click.option("--clean", is_flag=True, help="Remove all managed entries")
@click.option("--all", is_flag=True, help="Include engines from all users")
@click.option(
    "--admin",
    is_flag=True,
    help="Generate entries using ec2-user instead of owner",
)
@click.option(
    "--env",
    default=None,
    help="Environment (dev, sand, prod) - auto-detected if not specified",
)
def config_ssh(clean: bool, all: bool, admin: bool, env: Optional[str]):
    """Update SSH config with available engines."""

    # Auto-detect environment if not specified (and not just cleaning)
    if env is None and not clean:
        check_aws_auth()
        env = detect_aws_environment()
    elif env is None:
        env = "dev"  # Default for clean operation

    client = StudioManagerClient(environment=env)
    ssh_config_path = os.path.expanduser("~/.ssh/config")

    try:
        # Read existing config
        if os.path.exists(ssh_config_path):
            with open(ssh_config_path, "r") as f:
                lines = f.readlines()
        else:
            lines = []

        # Remove managed entries
        managed_start = "# BEGIN DAYHOFF ENGINES\n"
        managed_end = "# END DAYHOFF ENGINES\n"

        new_lines = []
        skip = False
        for line in lines:
            if line == managed_start:
                skip = True
            elif line == managed_end:
                skip = False
                continue
            elif not skip:
                new_lines.append(line)

        if clean:
            # Write back without managed section
            with open(ssh_config_path, "w") as f:
                f.writelines(new_lines)
            click.echo("✓ Removed managed engine entries from SSH config")
            return

        # Get engines
        result = client.list_engines()
        engines = result.get("engines", [])

        if not engines:
            click.echo("No engines found")
            return

        # Generate new entries
        config_entries = [managed_start]

        try:
            current_user = get_aws_username()
        except RuntimeError:
            # Not authenticated - can't determine user
            current_user = None

        for engine in engines:
            user = engine.get("user", "unknown")

            # Skip if not all and not owned by current user (unless user is unknown or we can't determine current user)
            if not all and current_user and user != "unknown" and user != current_user:
                continue

            instance_id = engine.get("instance_id")
            name = engine.get("name", instance_id)
            state = engine.get("state", "unknown")

            # Only add running engines
            if state != "running":
                continue

            username = "ec2-user" if admin else user

            # Map environment to AWS profile
            profile_map = {
                "dev": "dev-devaccess",
                "sand": "sand-devaccess",
                "prod": "prod-devaccess",
            }
            aws_profile = profile_map.get(env, f"{env}-devaccess")

            config_entries.append(f"\nHost {name}\n")
            config_entries.append(f"    HostName {instance_id}\n")
            config_entries.append(f"    User {username}\n")
            config_entries.append(f"    ForwardAgent yes\n")
            config_entries.append(
                f"    ProxyCommand aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p' --profile {aws_profile}\n"
            )

        config_entries.append(managed_end)

        # Write back
        new_lines.extend(config_entries)

        with open(ssh_config_path, "w") as f:
            f.writelines(new_lines)

        click.echo(f"✓ Updated SSH config with {len(engines)} engine(s)")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# Idle Detection Control
# ============================================================================


@engine_cli.command("coffee")
@click.argument("name_or_id")
@click.argument("duration", required=False)
@click.option("--cancel", is_flag=True, help="Cancel existing coffee lock")
@click.option(
    "--env",
    default=None,
    help="Environment (dev, sand, prod) - auto-detected if not specified",
)
def coffee(name_or_id: str, duration: Optional[str], cancel: bool, env: Optional[str]):
    """Keep engine awake for specified duration (e.g., '4h', '2h30m')."""

    # Check AWS auth and auto-detect environment if not specified
    check_aws_auth()

    if env is None:
        env = detect_aws_environment()

    client = StudioManagerClient(environment=env)

    try:
        # Find engine
        engine = client.get_engine_by_name(name_or_id)
        if not engine:
            engine = {"instance_id": name_or_id, "name": name_or_id}

        engine_id = engine["instance_id"]
        engine_name = engine.get("name", engine_id)

        if cancel:
            result = client.cancel_coffee(engine_id)
            if "error" in result:
                click.echo(f"✗ Error: {result['error']}", err=True)
                raise click.Abort()
            click.echo(f"✓ Coffee lock cancelled for '{engine_name}'")
        else:
            if not duration:
                click.echo("✗ Error: duration required (e.g., '4h', '2h30m')", err=True)
                raise click.Abort()

            result = client.set_coffee(engine_id, duration)
            if "error" in result:
                click.echo(f"✗ Error: {result['error']}", err=True)
                raise click.Abort()
            click.echo(f"✓ Coffee lock set for '{engine_name}': {duration}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@engine_cli.command("idle")
@click.argument("name_or_id")
@click.option("--set", "set_timeout", help="Set new timeout (e.g., '2h30m', '45m')")
@click.option(
    "--slack",
    type=click.Choice(["none", "default", "all"]),
    help="Set Slack notifications",
)
@click.option(
    "--env",
    default=None,
    help="Environment (dev, sand, prod) - auto-detected if not specified",
)
def idle_timeout_cmd(
    name_or_id: str,
    set_timeout: Optional[str],
    slack: Optional[str],
    env: Optional[str],
):
    """Show or configure idle detector settings."""

    # Check AWS auth and auto-detect environment if not specified
    check_aws_auth()

    if env is None:
        env = detect_aws_environment()

    client = StudioManagerClient(environment=env)

    try:
        # Find engine
        engine = client.get_engine_by_name(name_or_id)
        if not engine:
            engine = {"instance_id": name_or_id, "name": name_or_id}

        engine_id = engine["instance_id"]
        engine_name = engine.get("name", engine_id)

        # Get current settings
        status = client.get_engine_status(engine_id)

        if "error" in status:
            click.echo(f"✗ Error: {status['error']}", err=True)
            raise click.Abort()

        # Update if requested
        if set_timeout or slack:
            result = client.update_idle_settings(
                engine_id, timeout=set_timeout, slack=slack
            )
            if "error" in result:
                click.echo(f"✗ Error: {result['error']}", err=True)
                raise click.Abort()
            click.echo(f"✓ Idle settings updated for '{engine_name}'")

        # Show current settings
        idle_state = status.get("idle_state", {})
        timeout_seconds = int(idle_state.get("timeout_seconds", 1800))
        timeout_minutes = timeout_seconds // 60

        click.echo(f"\nIdle Settings for '{engine_name}':")
        click.echo(f"  Timeout: {timeout_minutes} minutes")
        click.echo(
            f"  Current State: {'IDLE' if idle_state.get('is_idle') else 'ACTIVE'}"
        )

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


# ============================================================================
# Maintenance
# ============================================================================


@engine_cli.command("resize")
@click.argument("name_or_id")
@click.option("--size", "-s", required=True, type=int, help="New size in GB")
@click.option(
    "--online",
    is_flag=True,
    help="Resize while running (requires manual filesystem expansion)",
)
@click.option("--force", "-f", is_flag=True, help="Force resize")
@click.option(
    "--env",
    default=None,
    help="Environment (dev, sand, prod) - auto-detected if not specified",
)
def resize_engine(
    name_or_id: str, size: int, online: bool, force: bool, env: Optional[str]
):
    """Resize an engine's boot disk."""

    # Check AWS auth and auto-detect environment if not specified
    check_aws_auth()

    if env is None:
        env = detect_aws_environment()

    client = StudioManagerClient(environment=env)

    try:
        # Find engine
        engine = client.get_engine_by_name(name_or_id)
        if not engine:
            engine = {"instance_id": name_or_id, "name": name_or_id}

        engine_id = engine["instance_id"]
        engine_name = engine.get("name", engine_id)

        if not force:
            if not click.confirm(f"Resize boot disk of '{engine_name}' to {size}GB?"):
                click.echo("Cancelled")
                return

        result = client.resize_engine(engine_id, size, online)

        if "error" in result:
            click.echo(f"✗ Error: {result['error']}", err=True)
            raise click.Abort()

        click.echo(f"✓ Boot disk resize initiated for '{engine_name}'")
        if online:
            click.echo("  Note: Manual filesystem expansion required")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@engine_cli.command("debug")
@click.argument("name_or_id")
@click.option(
    "--env",
    default=None,
    help="Environment (dev, sand, prod) - auto-detected if not specified",
)
def debug_engine(name_or_id: str, env: Optional[str]):
    """Debug engine bootstrap status and files."""

    # Check AWS auth and auto-detect environment if not specified
    check_aws_auth()

    if env is None:
        env = detect_aws_environment()

    client = StudioManagerClient(environment=env)

    try:
        # Find engine
        engine = client.get_engine_by_name(name_or_id)
        if not engine:
            engine = {"instance_id": name_or_id, "name": name_or_id}

        engine_id = engine["instance_id"]

        # Get readiness status
        readiness = client.get_engine_readiness(engine_id)

        click.echo(f"Engine: {engine_id}")
        click.echo(f"Ready: {readiness.get('ready', False)}")
        click.echo(f"Current Stage: {readiness.get('current_stage', 'unknown')}")
        click.echo(f"\nBootstrap Stages:")

        stages = readiness.get("stages", [])
        for i, stage in enumerate(stages, 1):
            status = stage.get("status", "unknown")
            name = stage.get("name", "unknown")
            duration = (
                stage.get("duration_ms", 0) / 1000 if stage.get("duration_ms") else None
            )

            icon = (
                "✓"
                if status == "completed"
                else "⏳" if status == "in_progress" else "✗"
            )
            duration_str = f" ({duration:.1f}s)" if duration else ""

            click.echo(f"  {icon} {i}. {name}{duration_str}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()
