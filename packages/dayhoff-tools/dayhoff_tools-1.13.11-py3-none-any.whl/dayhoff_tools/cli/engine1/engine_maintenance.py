"""Engine maintenance commands: coffee, idle timeout, debug, and repair."""

import re
import subprocess
import time
from typing import Optional

import boto3
import typer
from botocore.exceptions import ClientError
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

from .shared import check_aws_sso, console, make_api_request, resolve_engine


def coffee(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
    duration: str = typer.Argument("4h", help="Duration (e.g., 2h, 30m, 2h30m)"),
    cancel: bool = typer.Option(
        False, "--cancel", help="Cancel existing coffee lock instead of extending"
    ),
):
    """Pour ☕ for an engine: keeps it awake for the given duration (or cancel)."""
    username = check_aws_sso()

    # Parse duration
    import re

    if not cancel:
        match = re.match(r"(?:(\d+)h)?(?:(\d+)m)?", duration)
        if not match or (not match.group(1) and not match.group(2)):
            console.print(f"[red]❌ Invalid duration format: {duration}[/red]")
            console.print("Use format like: 4h, 30m, 2h30m")
            raise typer.Exit(1)

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds_total = (hours * 60 + minutes) * 60
        if seconds_total == 0:
            console.print("[red]❌ Duration must be greater than zero[/red]")
            raise typer.Exit(1)

    # Get all engines to resolve name
    response = make_api_request("GET", "/engines")
    if response.status_code != 200:
        console.print("[red]❌ Failed to fetch engines[/red]")
        raise typer.Exit(1)

    engines = response.json().get("engines", [])
    engine = resolve_engine(name_or_id, engines)

    if engine["state"].lower() != "running":
        console.print(f"[red]❌ Engine is not running (state: {engine['state']})[/red]")
        raise typer.Exit(1)

    if cancel:
        console.print(f"Cancelling coffee for [cyan]{engine['name']}[/cyan]…")
    else:
        console.print(
            f"Pouring coffee for [cyan]{engine['name']}[/cyan] for {duration}…"
        )

    # Use SSM to run the engine coffee command
    ssm = boto3.client("ssm", region_name="us-east-1")
    try:
        response = ssm.send_command(
            InstanceIds=[engine["instance_id"]],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    (
                        "/usr/local/bin/engine-coffee --cancel"
                        if cancel
                        else f"/usr/local/bin/engine-coffee {seconds_total}"
                    )
                ],
                "executionTimeout": ["60"],
            },
        )

        command_id = response["Command"]["CommandId"]

        # Wait for command to complete
        for _ in range(10):
            time.sleep(1)
            result = ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=engine["instance_id"],
            )
            if result["Status"] in ["Success", "Failed"]:
                break

        if result["Status"] == "Success":
            if cancel:
                console.print(
                    "[green]✓ Coffee cancelled – auto-shutdown re-enabled[/green]"
                )
            else:
                console.print(f"[green]✓ Coffee poured for {duration}[/green]")
            console.print(
                "\n[dim]Note: Detached Docker containers (except dev containers) will also keep the engine awake.[/dim]"
            )
            console.print(
                "[dim]Use coffee for nohup operations or other background tasks.[/dim]"
            )
        else:
            console.print(
                f"[red]❌ Failed to manage coffee: {result.get('StatusDetails', 'Unknown error')}[/red]"
            )

    except ClientError as e:
        console.print(f"[red]❌ Failed to manage coffee: {e}[/red]")


def idle_timeout_cmd(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
    set: Optional[str] = typer.Option(
        None, "--set", "-s", help="New timeout (e.g., 2h30m, 45m)"
    ),
    slack: Optional[str] = typer.Option(
        None, "--slack", help="Set Slack notifications: none, default, all"
    ),
):
    """Show or set engine idle-detector settings."""
    check_aws_sso()

    # Resolve engine
    response = make_api_request("GET", "/engines")
    if response.status_code != 200:
        console.print("[red]❌ Failed to fetch engines[/red]")
        raise typer.Exit(1)

    engines = response.json().get("engines", [])
    engine = resolve_engine(name_or_id, engines)

    ssm = boto3.client("ssm", region_name="us-east-1")

    # Handle slack notifications change
    if slack:
        slack = slack.lower()
        if slack not in ["none", "default", "all"]:
            console.print("[red]❌ Invalid slack option. Use: none, default, all[/red]")
            raise typer.Exit(1)

        console.print(f"Setting Slack notifications to [bold]{slack}[/bold]...")

        if slack == "none":
            settings = {
                "SLACK_NOTIFY_WARNINGS": "false",
                "SLACK_NOTIFY_IDLE_START": "false",
                "SLACK_NOTIFY_IDLE_END": "false",
                "SLACK_NOTIFY_SHUTDOWN": "false",
            }
        elif slack == "default":
            settings = {
                "SLACK_NOTIFY_WARNINGS": "true",
                "SLACK_NOTIFY_IDLE_START": "false",
                "SLACK_NOTIFY_IDLE_END": "false",
                "SLACK_NOTIFY_SHUTDOWN": "true",
            }
        else:  # all
            settings = {
                "SLACK_NOTIFY_WARNINGS": "true",
                "SLACK_NOTIFY_IDLE_START": "true",
                "SLACK_NOTIFY_IDLE_END": "true",
                "SLACK_NOTIFY_SHUTDOWN": "true",
            }

        commands = []
        for key, value in settings.items():
            # Use a robust sed command that adds the line if it doesn't exist
            commands.append(
                f"grep -q '^{key}=' /etc/engine.env && sudo sed -i 's|^{key}=.*|{key}={value}|' /etc/engine.env || echo '{key}={value}' | sudo tee -a /etc/engine.env > /dev/null"
            )

        # Instead of restarting service, send SIGHUP to reload config
        commands.append(
            "sudo pkill -HUP -f engine-idle-detector.py || sudo systemctl restart engine-idle-detector.service"
        )

        resp = ssm.send_command(
            InstanceIds=[engine["instance_id"]],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": commands, "executionTimeout": ["60"]},
        )
        cid = resp["Command"]["CommandId"]
        time.sleep(2)  # Give it a moment to process
        console.print(f"[green]✓ Slack notifications updated to '{slack}'[/green]")
        console.print("[dim]Note: Settings updated without resetting idle timer[/dim]")

    # Handle setting new timeout value
    if set is not None:
        m = re.match(r"^(?:(\d+)h)?(?:(\d+)m)?$", set)
        if not m:
            console.print(
                "[red]❌ Invalid duration format. Use e.g. 2h, 45m, 1h30m[/red]"
            )
            raise typer.Exit(1)
        hours = int(m.group(1) or 0)
        minutes = int(m.group(2) or 0)
        seconds = hours * 3600 + minutes * 60
        if seconds == 0:
            console.print("[red]❌ Duration must be greater than zero[/red]")
            raise typer.Exit(1)

        console.print(f"Setting idle timeout to {set} ({seconds} seconds)…")

        cmd = (
            "sudo sed -i '/^IDLE_TIMEOUT_SECONDS=/d' /etc/engine.env && "
            f"echo 'IDLE_TIMEOUT_SECONDS={seconds}' | sudo tee -a /etc/engine.env >/dev/null && "
            "sudo systemctl restart engine-idle-detector.service"
        )

        resp = ssm.send_command(
            InstanceIds=[engine["instance_id"]],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [cmd], "executionTimeout": ["60"]},
        )
        cid = resp["Command"]["CommandId"]
        time.sleep(2)
        console.print(f"[green]✓ Idle timeout updated to {set}[/green]")

    # If no action was specified, show current timeout
    if set is None and slack is None:
        # Show current timeout setting
        resp = ssm.send_command(
            InstanceIds=[engine["instance_id"]],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    "grep -E '^IDLE_TIMEOUT_SECONDS=' /etc/engine.env || echo 'IDLE_TIMEOUT_SECONDS=1800'"
                ],
                "executionTimeout": ["10"],
            },
        )
        cid = resp["Command"]["CommandId"]
        time.sleep(1)
        inv = ssm.get_command_invocation(
            CommandId=cid, InstanceId=engine["instance_id"]
        )
        if inv["Status"] == "Success":
            line = inv["StandardOutputContent"].strip()
            secs = int(line.split("=")[1]) if "=" in line else 1800
            console.print(f"Current idle timeout: {secs//60}m ({secs} seconds)")
        else:
            console.print("[red]❌ Could not retrieve idle timeout[/red]")
        return


def debug_engine(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
):
    """Debug engine bootstrap status and files."""
    check_aws_sso()

    # Resolve engine
    response = make_api_request("GET", "/engines")
    if response.status_code != 200:
        console.print("[red]❌ Failed to fetch engines[/red]")
        raise typer.Exit(1)

    engines = response.json().get("engines", [])
    engine = resolve_engine(name_or_id, engines)

    console.print(f"[bold]Debug info for {engine['name']}:[/bold]\n")

    ssm = boto3.client("ssm", region_name="us-east-1")

    # Check multiple files and systemd status
    checks = [
        (
            "Stage file",
            "cat /opt/dayhoff/state/engine-init.stage 2>/dev/null || cat /var/run/engine-init.stage 2>/dev/null || echo 'MISSING'",
        ),
        (
            "Health file",
            "cat /opt/dayhoff/state/engine-health.json 2>/dev/null || cat /var/run/engine-health.json 2>/dev/null || echo 'MISSING'",
        ),
        (
            "Sentinel file",
            "ls -la /opt/dayhoff/first_boot_complete.sentinel 2>/dev/null || echo 'MISSING'",
        ),
        (
            "Setup service",
            "systemctl status setup-aws-vm.service --no-pager || echo 'Service not found'",
        ),
        (
            "Bootstrap log tail",
            "tail -20 /var/log/engine-setup.log 2>/dev/null || echo 'No log'",
        ),
        ("Environment file", "cat /etc/engine.env 2>/dev/null || echo 'MISSING'"),
    ]

    for name, cmd in checks:
        try:
            resp = ssm.send_command(
                InstanceIds=[engine["instance_id"]],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [cmd], "executionTimeout": ["10"]},
            )
            cid = resp["Command"]["CommandId"]
            time.sleep(1)
            inv = ssm.get_command_invocation(
                CommandId=cid, InstanceId=engine["instance_id"]
            )

            if inv["Status"] == "Success":
                output = inv["StandardOutputContent"].strip()
                console.print(f"[cyan]{name}:[/cyan]")
                console.print(f"[dim]{output}[/dim]\n")
            else:
                console.print(f"[cyan]{name}:[/cyan] [red]FAILED[/red]\n")

        except Exception as e:
            console.print(f"[cyan]{name}:[/cyan] [red]ERROR: {e}[/red]\n")


def repair_engine(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
):
    """Repair an engine that's stuck in a bad state (e.g., after GAMI creation)."""
    check_aws_sso()

    # Get all engines to resolve name
    response = make_api_request("GET", "/engines")
    if response.status_code != 200:
        console.print("[red]❌ Failed to fetch engines[/red]")
        raise typer.Exit(1)

    engines = response.json().get("engines", [])
    engine = resolve_engine(name_or_id, engines)

    if engine["state"].lower() != "running":
        console.print(
            f"[yellow]⚠️  Engine is {engine['state']}. Must be running to repair.[/yellow]"
        )
        if engine["state"].lower() == "stopped" and Confirm.ask(
            "Start the engine first?"
        ):
            response = make_api_request(
                "POST", f"/engines/{engine['instance_id']}/start"
            )
            if response.status_code != 200:
                console.print("[red]❌ Failed to start engine[/red]")
                raise typer.Exit(1)
            console.print("[green]✓ Engine started[/green]")
            console.print("Waiting for engine to become ready...")
            time.sleep(30)  # Give it time to boot
        else:
            raise typer.Exit(1)

    console.print(f"[bold]Repairing engine [cyan]{engine['name']}[/cyan][/bold]")
    console.print(
        "[dim]This will restore bootstrap state and ensure all services are running[/dim]\n"
    )

    ssm = boto3.client("ssm", region_name="us-east-1")

    # Repair commands
    repair_commands = [
        # Create necessary directories
        "sudo mkdir -p /opt/dayhoff /opt/dayhoff/state /opt/dayhoff/scripts",
        # Download scripts from S3 if missing
        "source /etc/engine.env && sudo aws s3 sync s3://${VM_SCRIPTS_BUCKET}/ /opt/dayhoff/scripts/ --exclude '*' --include '*.sh' --quiet",
        "sudo chmod +x /opt/dayhoff/scripts/*.sh 2>/dev/null || true",
        # Restore bootstrap state
        "sudo touch /opt/dayhoff/first_boot_complete.sentinel",
        "echo 'finished' | sudo tee /opt/dayhoff/state/engine-init.stage > /dev/null",
        # Ensure SSM agent is running
        "sudo systemctl restart amazon-ssm-agent 2>/dev/null || true",
        # Restart idle detector (service only)
        "sudo systemctl restart engine-idle-detector.service 2>/dev/null || true",
        # Report status
        "echo '=== Repair Complete ===' && echo 'Sentinel: ' && ls -la /opt/dayhoff/first_boot_complete.sentinel",
        "echo 'Stage: ' && cat /opt/dayhoff/state/engine-init.stage",
        "echo 'Scripts: ' && ls /opt/dayhoff/scripts/*.sh 2>/dev/null | wc -l",
    ]

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Repairing engine...", total=None)

            response = ssm.send_command(
                InstanceIds=[engine["instance_id"]],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": repair_commands,
                    "executionTimeout": ["60"],
                },
            )

            command_id = response["Command"]["CommandId"]

            # Wait for command
            for _ in range(60):
                time.sleep(1)
                result = ssm.get_command_invocation(
                    CommandId=command_id,
                    InstanceId=engine["instance_id"],
                )
                if result["Status"] in ["Success", "Failed"]:
                    break

        if result["Status"] == "Success":
            output = result["StandardOutputContent"]
            console.print("[green]✓ Engine repaired successfully![/green]\n")

            # Show repair results
            if "=== Repair Complete ===" in output:
                repair_section = output.split("=== Repair Complete ===")[1].strip()
                console.print("[bold]Repair Results:[/bold]")
                console.print(repair_section)

            console.print(
                "\n[dim]You should now be able to attach studios to this engine.[/dim]"
            )
        else:
            console.print(
                f"[red]❌ Repair failed: {result.get('StandardErrorContent', 'Unknown error')}[/red]"
            )
            console.print(
                "\n[yellow]Try running 'dh engine debug' for more information.[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]❌ Failed to repair engine: {e}[/red]")
