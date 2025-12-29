"""Shared utilities, constants, and helper functions for engine and studio commands."""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import boto3
import requests
import typer
from botocore.exceptions import ClientError, NoCredentialsError
from rich.console import Console
from rich.prompt import Confirm, IntPrompt

console = Console()

# Cost information
HOURLY_COSTS = {
    "cpu": 0.50,  # r6i.2xlarge
    "cpumax": 2.02,  # r7i.8xlarge
    "t4": 0.75,  # g4dn.2xlarge
    "a10g": 1.50,  # g5.2xlarge
    "a100": 21.96,  # p4d.24xlarge
    "4_t4": 3.91,  # g4dn.12xlarge
    "8_t4": 7.83,  # g4dn.metal
    "4_a10g": 6.24,  # g5.12xlarge
    "8_a10g": 16.29,  # g5.48xlarge
}

# SSH config management
SSH_MANAGED_COMMENT = "# Managed by dh engine"


# --------------------------------------------------------------------------------
# Bootstrap stage helpers
# --------------------------------------------------------------------------------


def _colour_stage(stage: str) -> str:
    """Return colourised stage name for table output."""
    if not stage:
        return "[dim]-[/dim]"
    low = stage.lower()
    if low.startswith("error"):
        return f"[red]{stage}[/red]"
    if low == "finished":
        return f"[green]{stage}[/green]"
    return f"[yellow]{stage}[/yellow]"


def _fetch_init_stages(instance_ids: List[str]) -> Dict[str, str]:
    """Fetch DayhoffInitStage tag for many instances in one call."""
    if not instance_ids:
        return {}
    ec2 = boto3.client("ec2", region_name="us-east-1")
    stages: Dict[str, str] = {}
    try:
        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate(InstanceIds=instance_ids):
            for res in page["Reservations"]:
                for inst in res["Instances"]:
                    iid = inst["InstanceId"]
                    tag_val = next(
                        (
                            t["Value"]
                            for t in inst.get("Tags", [])
                            if t["Key"] == "DayhoffInitStage"
                        ),
                        None,
                    )
                    if tag_val:
                        stages[iid] = tag_val
    except Exception:
        pass  # best-effort
    return stages


def check_aws_sso() -> str:
    """Check AWS SSO status and return username."""
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        # Parse username from assumed role ARN
        # Format: arn:aws:sts::123456789012:assumed-role/AWSReservedSSO_DeveloperAccess_xxxx/username
        arn = identity["Arn"]
        if "assumed-role" in arn:
            username = arn.split("/")[-1]
            return username
        else:
            # Fallback for other auth methods
            return identity["UserId"].split(":")[-1]
    except (NoCredentialsError, ClientError):
        console.print("[red]❌ Not logged in to AWS SSO[/red]")
        console.print("Please run: [cyan]aws sso login[/cyan]")
        if Confirm.ask("Would you like to login now?"):
            try:
                result = subprocess.run(
                    ["aws", "sso", "login"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if result.returncode == 0:
                    console.print("[green]✓ Successfully logged in![/green]")
                    return check_aws_sso()
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Login failed: {e}[/red]")
        raise typer.Exit(1)


def get_api_url() -> str:
    """Get Studio Manager API URL from SSM Parameter Store."""
    ssm = boto3.client("ssm", region_name="us-east-1")
    try:
        response = ssm.get_parameter(Name="/dev/studio-manager/api-url")
        return response["Parameter"]["Value"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "ParameterNotFound":
            console.print(
                "[red]❌ API URL parameter not found in SSM Parameter Store[/red]"
            )
            console.print(
                "Please ensure the Studio Manager infrastructure is deployed."
            )
        else:
            console.print(f"[red]❌ Error retrieving API URL: {e}[/red]")
        raise typer.Exit(1)


def make_api_request(
    method: str,
    endpoint: str,
    json_data: Optional[Dict] = None,
    params: Optional[Dict] = None,
) -> requests.Response:
    """Make an API request with error handling."""
    api_url = get_api_url()
    url = f"{api_url}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=json_data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        return response
    except requests.exceptions.RequestException as e:
        console.print(f"[red]❌ API request failed: {e}[/red]")
        raise typer.Exit(1)


def format_duration(duration: timedelta) -> str:
    """Format a duration as a human-readable string."""
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def get_disk_usage_via_ssm(instance_id: str) -> Optional[str]:
    """Get disk usage for an engine via SSM.

    Returns:
        String like "17/50 GB" or None if failed
    """
    try:
        ssm = boto3.client("ssm", region_name="us-east-1")

        # Run df command to get disk usage
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    # Get root filesystem usage in GB
                    'df -BG / | tail -1 | awk \'{gsub(/G/, "", $2); gsub(/G/, "", $3); print $3 "/" $2 " GB"}\''
                ],
                "executionTimeout": ["10"],
            },
        )

        command_id = response["Command"]["CommandId"]

        # Wait for command to complete (with timeout)
        for _ in range(5):  # 5 second timeout
            time.sleep(1)
            result = ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id,
            )
            if result["Status"] in ["Success", "Failed"]:
                break

        if result["Status"] == "Success":
            output = result["StandardOutputContent"].strip()
            return output if output else None

        return None

    except Exception as e:
        # logger.debug(f"Failed to get disk usage for {instance_id}: {e}") # Original code had this line commented out
        return None


def get_studio_disk_usage_via_ssm(instance_id: str, username: str) -> Optional[str]:
    """Get disk usage for a studio via SSM.

    Returns:
        String like "333/500 GB" or None if failed
    """
    try:
        ssm = boto3.client("ssm", region_name="us-east-1")

        # Run df command to get studio disk usage
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    # Get studio filesystem usage in GB
                    f'df -BG /studios/{username} 2>/dev/null | tail -1 | awk \'{{gsub(/G/, "", $2); gsub(/G/, "", $3); print $3 "/" $2 " GB"}}\''
                ],
                "executionTimeout": ["10"],
            },
        )

        command_id = response["Command"]["CommandId"]

        # Wait for command to complete (with timeout)
        for _ in range(5):  # 5 second timeout
            time.sleep(1)
            result = ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id,
            )
            if result["Status"] in ["Success", "Failed"]:
                break

        if result["Status"] == "Success":
            output = result["StandardOutputContent"].strip()
            return output if output else None

        return None

    except Exception:
        return None


def parse_launch_time(launch_time_str: str) -> datetime:
    """Parse launch time from API response."""
    # Try different datetime formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",  # ISO format with timezone
        "%Y-%m-%dT%H:%M:%S+00:00",  # Explicit UTC offset
        "%Y-%m-%d %H:%M:%S",
    ]

    # First try parsing with fromisoformat for better timezone handling
    try:
        # Handle the ISO format properly
        return datetime.fromisoformat(launch_time_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        pass

    # Fallback to manual format parsing
    for fmt in formats:
        try:
            parsed = datetime.strptime(launch_time_str, fmt)
            # If no timezone info, assume UTC
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            continue

    # Fallback: assume it's recent
    return datetime.now(timezone.utc)


def format_status(state: str, ready: Optional[bool]) -> str:
    """Format engine status with ready indicator."""
    if state.lower() == "running":
        if ready is True:
            return "[green]Running ✓[/green]"
        elif ready is False:
            return "[yellow]Running ⚠ (Bootstrapping...)[/yellow]"
        else:
            return "[green]Running[/green]"
    elif state.lower() == "stopped":
        return "[dim]Stopped[/dim]"
    elif state.lower() == "stopping":
        return "[yellow]Stopping...[/yellow]"
    elif state.lower() == "pending":
        return "[yellow]Starting...[/yellow]"
    else:
        return state


def resolve_engine(name_or_id: str, engines: List[Dict]) -> Dict:
    """Resolve engine by name or ID with interactive selection."""
    # Exact ID match
    exact_id = [e for e in engines if e["instance_id"] == name_or_id]
    if exact_id:
        return exact_id[0]

    # Exact name match
    exact_name = [e for e in engines if e["name"] == name_or_id]
    if len(exact_name) == 1:
        return exact_name[0]

    # Prefix matches
    matches = [
        e
        for e in engines
        if e["name"].startswith(name_or_id) or e["instance_id"].startswith(name_or_id)
    ]

    if len(matches) == 0:
        console.print(f"[red]❌ No engine found matching '{name_or_id}'[/red]")
        raise typer.Exit(1)
    elif len(matches) == 1:
        return matches[0]
    else:
        # Interactive selection
        console.print(f"Multiple engines match '{name_or_id}':")
        for i, engine in enumerate(matches, 1):
            cost = HOURLY_COSTS.get(engine["engine_type"], 0)
            console.print(
                f"  {i}. [cyan]{engine['name']}[/cyan] ({engine['instance_id']}) "
                f"- {engine['engine_type']} - {engine['state']} - ${cost:.2f}/hr"
            )

        while True:
            try:
                choice = IntPrompt.ask(
                    "Select engine",
                    default=1,
                    choices=[str(i) for i in range(1, len(matches) + 1)],
                )
                return matches[choice - 1]
            except (ValueError, IndexError):
                console.print("[red]Invalid selection, please try again[/red]")


def get_ssh_public_key() -> str:
    """Get the user's SSH public key.

    Discovery order (container-friendly):
    1) DHT_SSH_PUBLIC_KEY env var (direct key content)
    2) DHT_SSH_PUBLIC_KEY_PATH env var (path to a .pub file)
    3) ssh-agent via `ssh-add -L` (requires SSH_AUTH_SOCK)
    4) Conventional files: ~/.ssh/id_ed25519.pub, ~/.ssh/id_rsa.pub

    Raises:
        FileNotFoundError: If no public key can be discovered.
    """
    # 1) Direct env var content
    env_key = os.environ.get("DHT_SSH_PUBLIC_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    # 2) Env var path
    env_path = os.environ.get("DHT_SSH_PUBLIC_KEY_PATH")
    if env_path:
        p = Path(env_path).expanduser()
        if p.is_file():
            try:
                return p.read_text().strip()
            except Exception:
                pass

    # 3) Agent lookup (ssh-add -L)
    try:
        if shutil.which("ssh-add") is not None:
            proc = subprocess.run(["ssh-add", "-L"], capture_output=True, text=True)
            if proc.returncode == 0 and proc.stdout:
                keys = [
                    line.strip() for line in proc.stdout.splitlines() if line.strip()
                ]
                # Prefer ed25519, then rsa
                for pref in ("ssh-ed25519", "ssh-rsa", "ecdsa-sha2-nistp256"):
                    for k in keys:
                        if k.startswith(pref + " "):
                            return k
                # Fallback to first key if types not matched
                if keys:
                    return keys[0]
    except Exception:
        pass

    # 4) Conventional files
    home = Path.home()
    key_paths = [home / ".ssh" / "id_ed25519.pub", home / ".ssh" / "id_rsa.pub"]
    for key_path in key_paths:
        if key_path.is_file():
            try:
                return key_path.read_text().strip()
            except Exception:
                continue

    raise FileNotFoundError(
        "No SSH public key found. Please create one with 'ssh-keygen' first."
    )


def check_session_manager_plugin():
    """Check if AWS Session Manager Plugin is available and warn if not."""
    if shutil.which("session-manager-plugin") is None:
        console.print(
            "[bold red]⚠️  AWS Session Manager Plugin not found![/bold red]\n"
            "SSH connections to engines require the Session Manager Plugin.\n"
            "Please install it following the setup guide:\n"
            "[link]https://github.com/dayhofflabs/nutshell/blob/main/REFERENCE/setup_guides/new-laptop.md[/link]"
        )
        return False
    return True


def update_ssh_config_entry(
    engine_name: str, instance_id: str, ssh_user: str, idle_timeout: int = 600
):
    """Add or update a single SSH config entry for the given SSH user.

    Args:
        engine_name:  Host alias to write into ~/.ssh/config
        instance_id:  EC2 instance-id (used by the proxy command)
        ssh_user:     Username to place into the SSH stanza
        idle_timeout: Idle timeout **in seconds** to pass to the SSM port-forward. 600 = 10 min.
    """
    config_path = Path.home() / ".ssh" / "config"
    config_path.parent.mkdir(mode=0o700, exist_ok=True)

    # Touch the file if it doesn't exist
    if not config_path.exists():
        config_path.touch(mode=0o600)

    # Read existing config
    content = config_path.read_text()
    lines = content.splitlines() if content else []

    # Remove any existing entry for this engine
    new_lines = []
    skip_until_next_host = False
    for line in lines:
        # Check if this is our managed host
        if (
            line.strip().startswith(f"Host {engine_name}")
            and SSH_MANAGED_COMMENT in line
        ):
            skip_until_next_host = True
        elif line.strip().startswith("Host ") and skip_until_next_host:
            skip_until_next_host = False
            # This is a different host entry, keep it
            new_lines.append(line)
        elif not skip_until_next_host:
            new_lines.append(line)

    # Add the new entry
    if new_lines and new_lines[-1].strip():  # Add blank line if needed
        new_lines.append("")

    new_lines.extend(
        [
            f"Host {engine_name} {SSH_MANAGED_COMMENT}",
            f"    HostName {instance_id}",
            f"    User {ssh_user}",
            f"    ProxyCommand sh -c \"AWS_SSM_IDLE_TIMEOUT={idle_timeout} aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'\"",
        ]
    )

    # Write back
    config_path.write_text("\n".join(new_lines))
    config_path.chmod(0o600)


def get_user_studio(username: str) -> Optional[Dict]:
    """Get the current user's studio."""
    response = make_api_request("GET", "/studios")
    if response.status_code != 200:
        return None

    studios = response.json().get("studios", [])
    user_studios = [s for s in studios if s["user"] == username]

    return user_studios[0] if user_studios else None
