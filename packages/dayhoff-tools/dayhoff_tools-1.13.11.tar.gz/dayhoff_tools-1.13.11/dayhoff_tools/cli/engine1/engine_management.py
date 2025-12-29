"""Engine management commands: SSH, configuration, resizing, and AMI creation."""

import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import boto3
import typer
from botocore.exceptions import ClientError
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm

from .shared import (
    SSH_MANAGED_COMMENT,
    check_aws_sso,
    check_session_manager_plugin,
    console,
    make_api_request,
    resolve_engine,
    update_ssh_config_entry,
)


def ssh_engine(
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
    """Connect to an engine via SSH.

    By default the CLI connects using the engine's owner username (the same one stored in the `User` tag).
    Pass `--admin` to connect with the underlying [`ec2-user`] account for break-glass or debugging.
    """
    username = check_aws_sso()

    # Check for Session Manager Plugin
    if not check_session_manager_plugin():
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

    # Choose SSH user
    ssh_user = "ec2-user" if admin else username

    # Update SSH config
    console.print(
        f"Updating SSH config for [cyan]{engine['name']}[/cyan] (user: {ssh_user})..."
    )
    update_ssh_config_entry(
        engine["name"], engine["instance_id"], ssh_user, idle_timeout
    )

    # Connect
    console.print(f"[green]✓ Connecting to {engine['name']}...[/green]")
    subprocess.run(["ssh", engine["name"]])


def config_ssh(
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
    username = check_aws_sso()

    # Only check for Session Manager Plugin if we're not just cleaning
    if not clean and not check_session_manager_plugin():
        raise typer.Exit(1)

    if clean:
        console.print("Removing all managed SSH entries...")
    else:
        if all_engines:
            console.print("Updating SSH config with all running engines...")
        else:
            console.print(
                f"Updating SSH config with running engines for [cyan]{username}[/cyan] and [cyan]shared[/cyan]..."
            )

    # Get all engines
    response = make_api_request("GET", "/engines")
    if response.status_code != 200:
        console.print("[red]❌ Failed to fetch engines[/red]")
        raise typer.Exit(1)

    engines = response.json().get("engines", [])
    running_engines = [e for e in engines if e["state"].lower() == "running"]

    # Filter engines based on options
    if not all_engines:
        # Show only current user's engines and shared engines
        running_engines = [
            e for e in running_engines if e["user"] == username or e["user"] == "shared"
        ]

    # Read existing config
    config_path = Path.home() / ".ssh" / "config"
    config_path.parent.mkdir(mode=0o700, exist_ok=True)

    if config_path.exists():
        content = config_path.read_text()
        lines = content.splitlines()
    else:
        content = ""
        lines = []

    # Remove old managed entries
    new_lines = []
    skip_until_next_host = False
    for line in lines:
        if SSH_MANAGED_COMMENT in line:
            skip_until_next_host = True
        elif line.strip().startswith("Host ") and skip_until_next_host:
            skip_until_next_host = False
            # Check if this is a managed host
            if SSH_MANAGED_COMMENT not in line:
                new_lines.append(line)
        elif not skip_until_next_host:
            new_lines.append(line)

    # Add new entries if not cleaning
    if not clean:
        for engine in running_engines:
            # Determine ssh user based on --admin flag
            ssh_user = "ec2-user" if admin else username
            new_lines.extend(
                [
                    "",
                    f"Host {engine['name']} {SSH_MANAGED_COMMENT}",
                    f"    HostName {engine['instance_id']}",
                    f"    User {ssh_user}",
                    f"    ProxyCommand sh -c \"AWS_SSM_IDLE_TIMEOUT=600 aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'\"",
                ]
            )

    # Write back
    config_path.write_text("\n".join(new_lines))
    config_path.chmod(0o600)

    if clean:
        console.print("[green]✓ Removed all managed SSH entries[/green]")
    else:
        console.print(
            f"[green]✓ Updated SSH config with {len(running_engines)} engines[/green]"
        )
        for engine in running_engines:
            user_display = (
                f"[dim]({engine['user']})[/dim]" if engine["user"] != username else ""
            )
            console.print(
                f"  • {engine['name']} → {engine['instance_id']} {user_display}"
            )


def resize_engine(
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
    check_aws_sso()

    # Get all engines to resolve name
    response = make_api_request("GET", "/engines")
    if response.status_code != 200:
        console.print("[red]❌ Failed to fetch engines[/red]")
        raise typer.Exit(1)

    engines = response.json().get("engines", [])
    engine = resolve_engine(name_or_id, engines)

    # Get current volume info to validate size
    ec2 = boto3.client("ec2", region_name="us-east-1")

    try:
        # Get instance details to find root volume
        instance_info = ec2.describe_instances(InstanceIds=[engine["instance_id"]])
        instance = instance_info["Reservations"][0]["Instances"][0]

        # Find root volume
        root_device = instance.get("RootDeviceName", "/dev/xvda")
        root_volume_id = None

        for bdm in instance.get("BlockDeviceMappings", []):
            if bdm["DeviceName"] == root_device:
                root_volume_id = bdm["Ebs"]["VolumeId"]
                break

        if not root_volume_id:
            console.print("[red]❌ Could not find root volume[/red]")
            raise typer.Exit(1)

        # Get current volume size
        volumes = ec2.describe_volumes(VolumeIds=[root_volume_id])
        current_size = volumes["Volumes"][0]["Size"]

        if size <= current_size:
            console.print(
                f"[red]❌ New size ({size}GB) must be larger than current size ({current_size}GB)[/red]"
            )
            raise typer.Exit(1)

        console.print(
            f"[yellow]Resizing engine boot disk from {current_size}GB to {size}GB[/yellow]"
        )

        # Check if we need to stop the instance
        if not online and engine["state"].lower() == "running":
            console.print("Stopping engine for offline resize...")
            stop_response = make_api_request(
                "POST",
                f"/engines/{engine['instance_id']}/stop",
                json_data={"detach_studios": False},
            )
            if stop_response.status_code != 200:
                console.print("[red]❌ Failed to stop engine[/red]")
                raise typer.Exit(1)

            # Wait for instance to stop
            console.print("Waiting for engine to stop...")
            waiter = ec2.get_waiter("instance_stopped")
            waiter.wait(InstanceIds=[engine["instance_id"]])
            console.print("[green]✓ Engine stopped[/green]")

        # Call the resize API
        console.print("Resizing volume...")
        resize_response = make_api_request(
            "POST",
            f"/engines/{engine['instance_id']}/resize",
            json_data={"size": size, "detach_studios": force},
        )

        if resize_response.status_code == 409 and not force:
            # Engine has attached studios
            data = resize_response.json()
            attached_studios = data.get("attached_studios", [])

            console.print("\n[yellow]⚠️  This engine has attached studios:[/yellow]")
            for studio in attached_studios:
                console.print(f"  • {studio['user']} ({studio['studio_id']})")

            if Confirm.ask("\nDetach all studios and resize the engine?"):
                resize_response = make_api_request(
                    "POST",
                    f"/engines/{engine['instance_id']}/resize",
                    json_data={"size": size, "detach_studios": True},
                )
            else:
                console.print("Resize cancelled.")
                return

        if resize_response.status_code != 200:
            error = resize_response.json().get("error", "Unknown error")
            console.print(f"[red]❌ Failed to resize engine: {error}[/red]")
            raise typer.Exit(1)

        # Check if studios were detached
        data = resize_response.json()
        detached_studios = data.get("detached_studios", 0)
        if detached_studios > 0:
            console.print(
                f"[green]✓ Detached {detached_studios} studio(s) before resize[/green]"
            )

        # Wait for modification to complete
        console.print("Waiting for volume modification to complete...")
        while True:
            mod_state = ec2.describe_volumes_modifications(VolumeIds=[root_volume_id])
            if not mod_state["VolumesModifications"]:
                break  # Modification complete

            modification = mod_state["VolumesModifications"][0]
            state = modification["ModificationState"]
            progress = modification.get("Progress", 0)

            # Show progress updates only for the resize phase
            if state == "modifying":
                console.print(f"[yellow]Progress: {progress}%[/yellow]")

            # Exit as soon as optimization starts (resize is complete)
            if state == "optimizing":
                console.print("[green]✓ Volume resized successfully[/green]")
                console.print(
                    "[dim]AWS is optimizing the volume in the background (no action needed).[/dim]"
                )
                break

            if state == "completed":
                console.print("[green]✓ Volume resized successfully[/green]")
                break
            elif state == "failed":
                console.print("[red]❌ Volume modification failed[/red]")
                raise typer.Exit(1)

            time.sleep(2)  # Check more frequently for better UX

        # If offline resize, start the instance back up
        if not online and engine["state"].lower() == "running":
            console.print("Starting engine back up...")
            start_response = make_api_request(
                "POST", f"/engines/{engine['instance_id']}/start"
            )
            if start_response.status_code != 200:
                console.print(
                    "[yellow]⚠️  Failed to restart engine automatically[/yellow]"
                )
                console.print(
                    f"Please start it manually: [cyan]dh engine start {engine['name']}[/cyan]"
                )
            else:
                console.print("[green]✓ Engine started[/green]")
                console.print("The filesystem will be automatically expanded on boot.")

        elif online and engine["state"].lower() == "running":
            console.print(
                "\n[yellow]⚠️  Online resize complete. You must now expand the filesystem:[/yellow]"
            )
            console.print(f"1. SSH into the engine: [cyan]ssh {engine['name']}[/cyan]")
            console.print("2. Find the root device: [cyan]lsblk[/cyan]")
            console.print(
                "3. Expand the partition: [cyan]sudo growpart /dev/nvme0n1 1[/cyan] (adjust device name as needed)"
            )
            console.print("4. Expand the filesystem: [cyan]sudo xfs_growfs /[/cyan]")

    except ClientError as e:
        console.print(f"[red]❌ Failed to resize engine: {e}[/red]")
        raise typer.Exit(1)


def create_ami(
    name_or_id: str = typer.Argument(
        help="Engine name or instance ID to create AMI from"
    ),
):
    """Create a 'Golden AMI' from a running engine.

    This process is for creating a pre-warmed, standardized machine image
    that can be used to launch new engines more quickly.

    IMPORTANT:
    - The engine MUST have all studios detached before running this command.
    - This process will make the source engine unusable. You should
      plan to TERMINATE the engine after the AMI is created.
    """
    check_aws_sso()

    # Get all engines to resolve name and check status
    # We pass check_ready=True to get attached studio info
    response = make_api_request("GET", "/engines", params={"check_ready": "true"})
    if response.status_code != 200:
        console.print("[red]❌ Failed to fetch engines[/red]")
        raise typer.Exit(1)

    engines = response.json().get("engines", [])
    engine = resolve_engine(name_or_id, engines)

    # --- Pre-flight checks ---

    # 1. Check if engine is running
    if engine["state"].lower() != "running":
        console.print(f"[red]❌ Engine '{engine['name']}' is not running.[/red]")
        console.print("Please start it before creating an AMI.")
        raise typer.Exit(1)

    # 2. Check for attached studios from the detailed API response
    attached_studios = engine.get("studios", [])
    if attached_studios:
        console.print(
            f"[bold red]❌ Engine '{engine['name']}' has studios attached.[/bold red]"
        )
        console.print("Please detach all studios before creating an AMI:")
        for studio in attached_studios:
            console.print(f"  - {studio['user']} ({studio['studio_id']})")
        console.print("\nTo detach, run [bold]dh studio detach[/bold]")
        raise typer.Exit(1)

    # Construct AMI name and description
    ami_name = (
        f"prewarmed-engine-{engine['engine_type']}-{datetime.now().strftime('%Y%m%d')}"
    )
    description = (
        f"Amazon Linux 2023 with NVIDIA drivers, Docker, and pre-pulled "
        f"dev container image for {engine['engine_type']} engines"
    )

    console.print(f"Creating AMI from engine [cyan]{engine['name']}[/cyan]...")
    console.print(f"[bold]AMI Name:[/] {ami_name}")
    console.print(f"[bold]Description:[/] {description}")

    console.print(
        "\n[bold yellow]⚠️  Important:[/bold yellow]\n"
        "1. This process will run cleanup scripts on the engine.\n"
        "2. The source engine should be [bold]terminated[/bold] after the AMI is created.\n"
    )

    if not Confirm.ask("Continue with AMI creation?"):
        raise typer.Exit()

    # Create AMI using EC2 client directly, as the backend logic is too complex
    ec2 = boto3.client("ec2", region_name="us-east-1")
    ssm = boto3.client("ssm", region_name="us-east-1")

    try:
        # Clean up instance state before snapshotting
        console.print("Cleaning up instance for AMI creation...")
        cleanup_commands = [
            "sudo rm -f /opt/dayhoff/first_boot_complete.sentinel",
            "history -c",
            "sudo rm -rf /tmp/* /var/log/messages /var/log/cloud-init.log",
            "sudo rm -rf /var/lib/amazon/ssm/* /etc/amazon/ssm/*",
            "sleep 2 && sudo systemctl stop amazon-ssm-agent &",  # Stop agent last
        ]

        cleanup_response = ssm.send_command(
            InstanceIds=[engine["instance_id"]],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": cleanup_commands, "executionTimeout": ["120"]},
        )

        # Acknowledge that the SSM command might be in progress as the agent shuts down
        console.print(
            "[dim]ℹ️  Cleanup command sent (status may show 'InProgress' as SSM agent stops)[/dim]"
        )

        # Create the AMI
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(
                "Creating AMI (this will take several minutes)...", total=None
            )

            response = ec2.create_image(
                InstanceId=engine["instance_id"],
                Name=ami_name,
                Description=description,
                NoReboot=False,
                TagSpecifications=[
                    {
                        "ResourceType": "image",
                        "Tags": [
                            {"Key": "Environment", "Value": "dev"},
                            {"Key": "Type", "Value": "golden-ami"},
                            {"Key": "EngineType", "Value": engine["engine_type"]},
                            {"Key": "Name", "Value": ami_name},
                        ],
                    }
                ],
            )

            ami_id = response["ImageId"]
            progress.update(
                task,
                completed=True,
                description=f"[green]✓ AMI creation initiated![/green]",
            )

        console.print(f"  [bold]AMI ID:[/] {ami_id}")
        console.print("\nThe AMI creation process will continue in the background.")
        console.print("You can monitor progress in the EC2 Console under 'AMIs'.")
        console.print(
            "\nOnce complete, update the AMI ID in [bold]terraform/environments/dev/variables.tf[/bold] "
            "and run [bold]terraform apply[/bold]."
        )
        console.print(
            f"\nRemember to [bold red]terminate the source engine '{engine['name']}'[/bold red] to save costs."
        )

    except ClientError as e:
        console.print(f"[red]❌ Failed to create AMI: {e}[/red]")
        raise typer.Exit(1)
