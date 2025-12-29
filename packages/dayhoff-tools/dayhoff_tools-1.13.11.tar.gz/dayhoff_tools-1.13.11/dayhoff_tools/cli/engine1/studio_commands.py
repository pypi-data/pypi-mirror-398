"""Studio management commands: create, attach, detach, delete, list, reset, resize."""

import time
from datetime import timedelta
from typing import Dict, Optional

import boto3
import typer
from botocore.exceptions import ClientError
from rich import box
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from .shared import (
    check_aws_sso,
    check_session_manager_plugin,
    console,
    format_duration,
    get_ssh_public_key,
    get_studio_disk_usage_via_ssm,
    get_user_studio,
    make_api_request,
    resolve_engine,
    update_ssh_config_entry,
)


def create_studio(
    size_gb: int = typer.Option(50, "--size", "-s", help="Studio size in GB"),
):
    """Create a new studio for the current user."""
    username = check_aws_sso()

    # Check if user already has a studio
    existing = get_user_studio(username)
    if existing:
        console.print(
            f"[yellow]You already have a studio: {existing['studio_id']}[/yellow]"
        )
        return

    console.print(f"Creating {size_gb}GB studio for user [cyan]{username}[/cyan]...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Creating studio volume...", total=None)

        response = make_api_request(
            "POST",
            "/studios",
            json_data={"user": username, "size_gb": size_gb},
        )

    if response.status_code == 201:
        data = response.json()
        console.print(f"[green]✓ Studio created successfully![/green]")
        console.print(f"Studio ID: [cyan]{data['studio_id']}[/cyan]")
        console.print(f"Size: {data['size_gb']}GB")
        console.print(f"\nNext step: [cyan]dh studio attach <engine-name>[/cyan]")
    else:
        error = response.json().get("error", "Unknown error")
        console.print(f"[red]❌ Failed to create studio: {error}[/red]")


def studio_status(
    user: Optional[str] = typer.Option(
        None, "--user", "-u", help="Check status for a different user (admin only)"
    ),
):
    """Show status of your studio."""
    username = check_aws_sso()

    # Use specified user if provided, otherwise use current user
    target_user = user if user else username

    # Add warning when checking another user's studio
    if target_user != username:
        console.print(
            f"[yellow]⚠️  Checking studio status for user: {target_user}[/yellow]"
        )

    studio = get_user_studio(target_user)
    if not studio:
        if target_user == username:
            console.print("[yellow]You don't have a studio yet.[/yellow]")
            console.print("Create one with: [cyan]dh studio create[/cyan]")
        else:
            console.print(f"[yellow]User {target_user} doesn't have a studio.[/yellow]")
        return

    # Create status panel
    # Format status with colors
    status = studio["status"]
    if status == "in-use":
        status_display = "[bright_blue]attached[/bright_blue]"
    elif status in ["attaching", "detaching"]:
        status_display = f"[yellow]{status}[/yellow]"
    else:
        status_display = f"[green]{status}[/green]"

    status_lines = [
        f"[bold]Studio ID:[/bold]    {studio['studio_id']}",
        f"[bold]User:[/bold]         {studio['user']}",
        f"[bold]Status:[/bold]       {status_display}",
        f"[bold]Size:[/bold]         {studio['size_gb']}GB",
        f"[bold]Created:[/bold]      {studio['creation_date']}",
    ]

    if studio.get("attached_vm_id"):
        status_lines.append(f"[bold]Attached to:[/bold]  {studio['attached_vm_id']}")

        # Try to get engine details
        response = make_api_request("GET", "/engines")
        if response.status_code == 200:
            engines = response.json().get("engines", [])
            attached_engine = next(
                (e for e in engines if e["instance_id"] == studio["attached_vm_id"]),
                None,
            )
            if attached_engine:
                status_lines.append(
                    f"[bold]Engine Name:[/bold]  {attached_engine['name']}"
                )

    panel = Panel(
        "\n".join(status_lines),
        title="Studio Details",
        border_style="blue",
    )
    console.print(panel)


def _is_studio_attached(target_studio_id: str, target_vm_id: str) -> bool:
    """Return True when the given studio already shows as attached to the VM.

    Using this extra check lets us stop the outer retry loop as soon as the
    asynchronous attach operation actually finishes, even in the unlikely
    event that the operation-tracking DynamoDB record is not yet updated.
    """
    # First try the per-studio endpoint – fastest.
    resp = make_api_request("GET", f"/studios/{target_studio_id}")
    if resp.status_code == 200:
        data = resp.json()
        if (
            data.get("status") == "in-use"
            and data.get("attached_vm_id") == target_vm_id
        ):
            return True
    # Fallback: list + filter (covers edge-cases where the direct endpoint
    # is slower to update IAM/APIGW mapping than the list endpoint).
    list_resp = make_api_request("GET", "/studios")
    if list_resp.status_code == 200:
        for stu in list_resp.json().get("studios", []):
            if (
                stu.get("studio_id") == target_studio_id
                and stu.get("status") == "in-use"
                and stu.get("attached_vm_id") == target_vm_id
            ):
                return True
    return False


def attach_studio(
    engine_name_or_id: str = typer.Argument(help="Engine name or instance ID"),
    user: Optional[str] = typer.Option(
        None, "--user", "-u", help="Attach a different user's studio (admin only)"
    ),
):
    """Attach your studio to an engine."""
    username = check_aws_sso()

    # Check for Session Manager Plugin since we'll update SSH config
    if not check_session_manager_plugin():
        raise typer.Exit(1)

    # Use specified user if provided, otherwise use current user
    target_user = user if user else username

    # Add confirmation when attaching another user's studio
    if target_user != username:
        console.print(f"[yellow]⚠️  Managing studio for user: {target_user}[/yellow]")
        if not Confirm.ask(f"Are you sure you want to attach {target_user}'s studio?"):
            console.print("Operation cancelled.")
            return

    # Get user's studio
    studio = get_user_studio(target_user)
    if not studio:
        if target_user == username:
            console.print("[yellow]You don't have a studio yet.[/yellow]")
            if Confirm.ask("Would you like to create one now?"):
                size = IntPrompt.ask("Studio size (GB)", default=50)
                response = make_api_request(
                    "POST",
                    "/studios",
                    json_data={"user": username, "size_gb": size},
                )
                if response.status_code != 201:
                    console.print("[red]❌ Failed to create studio[/red]")
                    raise typer.Exit(1)
                studio = response.json()
                studio["studio_id"] = studio["studio_id"]  # Normalize key
            else:
                raise typer.Exit(0)
        else:
            console.print(f"[red]❌ User {target_user} doesn't have a studio.[/red]")
            raise typer.Exit(1)

    # Check if already attached
    if studio.get("status") == "in-use":
        console.print(
            f"[yellow]Studio is already attached to {studio.get('attached_vm_id')}[/yellow]"
        )
        if not Confirm.ask("Detach and reattach to new engine?"):
            return
        # Detach first
        response = make_api_request("POST", f"/studios/{studio['studio_id']}/detach")
        if response.status_code != 200:
            console.print("[red]❌ Failed to detach studio[/red]")
            raise typer.Exit(1)

    # Get all engines to resolve name
    response = make_api_request("GET", "/engines")
    if response.status_code != 200:
        console.print("[red]❌ Failed to fetch engines[/red]")
        raise typer.Exit(1)

    engines = response.json().get("engines", [])
    engine = resolve_engine(engine_name_or_id, engines)

    # Flag to track if we started the engine in this command (affects retry length)
    engine_started_now: bool = False

    if engine["state"].lower() != "running":
        console.print(f"[yellow]⚠️  Engine is {engine['state']}[/yellow]")
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
            # Mark that we booted the engine so attach loop gets extended retries
            engine_started_now = True
            # No further waiting here – attachment attempts below handle retry logic while the
            # engine finishes booting.
        else:
            raise typer.Exit(1)

    # Retrieve SSH public key (required for authorised_keys provisioning)
    try:
        public_key = get_ssh_public_key()
    except FileNotFoundError as e:
        console.print(f"[red]❌ {e}[/red]")
        raise typer.Exit(1)

    console.print(f"Attaching studio to engine [cyan]{engine['name']}[/cyan]...")

    # Determine retry strategy based on whether we just started the engine
    if engine_started_now:
        max_attempts = 40  # About 7 minutes total with exponential backoff
        base_delay = 8
        max_delay = 20
    else:
        max_attempts = 15  # About 2 minutes total with exponential backoff
        base_delay = 5
        max_delay = 10

    # Unified retry loop with exponential backoff
    with Progress(
        SpinnerColumn(),
        TimeElapsedColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as prog:
        desc = (
            "Attaching studio (engine is still booting)…"
            if engine_started_now
            else "Attaching studio…"
        )
        task = prog.add_task(desc, total=None)

        consecutive_not_ready = 0
        last_error = None

        for attempt in range(max_attempts):
            # Check if the attach already completed
            if _is_studio_attached(studio["studio_id"], engine["instance_id"]):
                success = True
                break

            success, error_msg = _attempt_studio_attach(
                studio, engine, target_user, public_key
            )

            if success:
                break  # success!

            if error_msg:
                # Fatal error – bubble up immediately
                console.print(f"[red]❌ Failed to attach studio: {error_msg}[/red]")

                # Suggest repair command if engine seems broken
                if "not ready" in error_msg.lower() and attempt > 5:
                    console.print(
                        f"\n[yellow]Engine may be in a bad state. Try:[/yellow]"
                    )
                    console.print(f"[dim]  dh engine repair {engine['name']}[/dim]")
                return

            # Track consecutive "not ready" responses
            consecutive_not_ready += 1
            last_error = "Engine not ready"

            # Update progress display
            if attempt % 3 == 0:
                prog.update(
                    task,
                    description=f"{desc} attempt {attempt+1}/{max_attempts}",
                )

            # If engine seems stuck after many attempts, show a hint
            if consecutive_not_ready > 10 and attempt == 10:
                console.print(
                    "[yellow]Engine is taking longer than expected to become ready.[/yellow]"
                )
                console.print(
                    "[dim]This can happen after GAMI creation or if the engine is still bootstrapping.[/dim]"
                )

            # Exponential backoff with jitter
            delay = min(base_delay * (1.5 ** min(attempt, 5)), max_delay)
            delay += time.time() % 2  # Add 0-2 seconds of jitter
            time.sleep(delay)

        else:
            # All attempts exhausted
            console.print(
                f"[yellow]Engine is not becoming ready after {max_attempts} attempts.[/yellow]"
            )
            if last_error:
                console.print(f"[dim]Last issue: {last_error}[/dim]")
            console.print("\n[yellow]You can try:[/yellow]")
            console.print(
                f"  1. Wait a minute and retry: [cyan]dh studio attach {engine['name']}[/cyan]"
            )
            console.print(
                f"  2. Check engine status: [cyan]dh engine status {engine['name']}[/cyan]"
            )
            console.print(
                f"  3. Repair the engine: [cyan]dh engine repair {engine['name']}[/cyan]"
            )
            return

    # Successful attach path
    console.print(f"[green]✓ Studio attached successfully![/green]")

    # Update SSH config - use target_user for the connection
    update_ssh_config_entry(engine["name"], engine["instance_id"], target_user)
    console.print(f"[green]✓ SSH config updated[/green]")
    console.print(f"\nConnect with: [cyan]ssh {engine['name']}[/cyan]")
    console.print(f"Files are at: [cyan]/studios/{target_user}[/cyan]")


def _attempt_studio_attach(studio, engine, target_user, public_key):
    response = make_api_request(
        "POST",
        f"/studios/{studio['studio_id']}/attach",
        json_data={
            "vm_id": engine["instance_id"],
            "user": target_user,
            "public_key": public_key,
        },
    )

    # Fast-path success
    if response.status_code == 200:
        return True, None

    # Asynchronous path – API returned 202 Accepted and operation tracking ID
    if response.status_code == 202:
        # The operation status polling is broken in the Lambda, so we just
        # wait and check if the studio is actually attached
        time.sleep(5)  # Give the async operation a moment to start

        # Check periodically if the studio is attached
        for check in range(20):  # Check for up to 60 seconds
            if _is_studio_attached(studio["studio_id"], engine["instance_id"]):
                return True, None
            time.sleep(3)

        # If we get here, attachment didn't complete in reasonable time
        return False, None  # Return None to trigger retry

    # --- determine if we should retry ---
    recoverable = False
    error_text = response.json().get("error", "Unknown error")
    err_msg = error_text.lower()

    # Check for "Studio is not available (status: in-use)" which means it's already attached
    if (
        response.status_code == 400
        and "not available" in err_msg
        and "in-use" in err_msg
    ):
        # Studio is already attached somewhere - check if it's to THIS engine
        if _is_studio_attached(studio["studio_id"], engine["instance_id"]):
            return True, None  # It's attached to our target engine - success!
        else:
            return False, error_text  # It's attached elsewhere - fatal error

    if response.status_code in (409, 503):
        recoverable = True
    else:
        RECOVERABLE_PATTERNS = [
            "not ready",
            "still starting",
            "initializing",
            "failed to mount",
            "device busy",
            "pending",  # VM state pending
        ]
        FATAL_PATTERNS = [
            "permission",
        ]
        if any(p in err_msg for p in FATAL_PATTERNS):
            recoverable = False
        elif any(p in err_msg for p in RECOVERABLE_PATTERNS):
            recoverable = True

    if not recoverable:
        # fatal – abort immediately
        return False, error_text

    # recoverable – signal caller to retry without treating as error
    return False, None


# Note: _poll_operation was removed because the Lambda's operation tracking is broken.
# We now use _is_studio_attached() to check if the studio is actually attached instead.


def detach_studio(
    user: Optional[str] = typer.Option(
        None, "--user", "-u", help="Detach a different user's studio (admin only)"
    ),
):
    """Detach your studio from its current engine."""
    username = check_aws_sso()

    # Use specified user if provided, otherwise use current user
    target_user = user if user else username

    # Add confirmation when detaching another user's studio
    if target_user != username:
        console.print(f"[yellow]⚠️  Managing studio for user: {target_user}[/yellow]")
        if not Confirm.ask(f"Are you sure you want to detach {target_user}'s studio?"):
            console.print("Operation cancelled.")
            return

    studio = get_user_studio(target_user)
    if not studio:
        if target_user == username:
            console.print("[yellow]You don't have a studio.[/yellow]")
        else:
            console.print(f"[yellow]User {target_user} doesn't have a studio.[/yellow]")
        return

    if studio.get("status") != "in-use":
        if target_user == username:
            console.print("[yellow]Your studio is not attached to any engine.[/yellow]")
        else:
            console.print(
                f"[yellow]{target_user}'s studio is not attached to any engine.[/yellow]"
            )
        return

    console.print(f"Detaching studio from {studio.get('attached_vm_id')}...")

    response = make_api_request("POST", f"/studios/{studio['studio_id']}/detach")

    if response.status_code == 200:
        console.print(f"[green]✓ Studio detached successfully![/green]")
    else:
        error = response.json().get("error", "Unknown error")
        console.print(f"[red]❌ Failed to detach studio: {error}[/red]")


def delete_studio(
    user: Optional[str] = typer.Option(
        None, "--user", "-u", help="Delete a different user's studio (admin only)"
    ),
):
    """Delete your studio permanently."""
    username = check_aws_sso()

    # Use specified user if provided, otherwise use current user
    target_user = user if user else username

    # Extra warning when deleting another user's studio
    if target_user != username:
        console.print(
            f"[red]⚠️  ADMIN ACTION: Deleting studio for user: {target_user}[/red]"
        )

    studio = get_user_studio(target_user)
    if not studio:
        if target_user == username:
            console.print("[yellow]You don't have a studio to delete.[/yellow]")
        else:
            console.print(
                f"[yellow]User {target_user} doesn't have a studio to delete.[/yellow]"
            )
        return

    console.print(
        "[red]⚠️  WARNING: This will permanently delete the studio and all data![/red]"
    )
    console.print(f"Studio ID: {studio['studio_id']}")
    console.print(f"User: {target_user}")
    console.print(f"Size: {studio['size_gb']}GB")

    # Multiple confirmations
    if not Confirm.ask(
        f"\nAre you sure you want to delete {target_user}'s studio?"
        if target_user != username
        else "\nAre you sure you want to delete your studio?"
    ):
        console.print("Deletion cancelled.")
        return

    if not Confirm.ask("[red]This action cannot be undone. Continue?[/red]"):
        console.print("Deletion cancelled.")
        return

    typed_confirm = Prompt.ask('Type "DELETE" to confirm permanent deletion')
    if typed_confirm != "DELETE":
        console.print("Deletion cancelled.")
        return

    response = make_api_request("DELETE", f"/studios/{studio['studio_id']}")

    if response.status_code == 200:
        console.print(f"[green]✓ Studio deleted successfully![/green]")
    else:
        error = response.json().get("error", "Unknown error")
        console.print(f"[red]❌ Failed to delete studio: {error}[/red]")


def list_studios(
    all_users: bool = typer.Option(
        False, "--all", "-a", help="Show all users' studios"
    ),
):
    """List studios."""
    username = check_aws_sso()

    response = make_api_request("GET", "/studios")

    if response.status_code == 200:
        studios = response.json().get("studios", [])

        if not studios:
            console.print("No studios found.")
            return

        # Get all engines to map instance IDs to names
        engines_response = make_api_request("GET", "/engines")
        engines = {}
        if engines_response.status_code == 200:
            for engine in engines_response.json().get("engines", []):
                engines[engine["instance_id"]] = engine["name"]

        # Create table
        table = Table(title="Studios", box=box.ROUNDED)
        table.add_column("Studio ID", style="cyan")
        table.add_column("User")
        table.add_column("Status")
        table.add_column("Size", justify="right")
        table.add_column("Disk Usage", justify="right")
        table.add_column("Attached To")

        for studio in studios:
            # Change status display
            if studio["status"] == "in-use":
                status_display = "[bright_blue]attached[/bright_blue]"
            elif studio["status"] in ["attaching", "detaching"]:
                status_display = "[yellow]" + studio["status"] + "[/yellow]"
            else:
                status_display = "[green]available[/green]"

            # Format attached engine info
            attached_to = "-"
            disk_usage = "?/?"
            if studio.get("attached_vm_id"):
                vm_id = studio["attached_vm_id"]
                engine_name = engines.get(vm_id, "unknown")
                attached_to = f"{engine_name} ({vm_id})"

                # Try to get disk usage if attached
                if studio["status"] == "in-use":
                    usage = get_studio_disk_usage_via_ssm(vm_id, studio["user"])
                    if usage:
                        disk_usage = usage

            table.add_row(
                studio["studio_id"],
                studio["user"],
                status_display,
                f"{studio['size_gb']}GB",
                disk_usage,
                attached_to,
            )

        console.print(table)
    else:
        error = response.json().get("error", "Unknown error")
        console.print(f"[red]❌ Failed to list studios: {error}[/red]")


def reset_studio(
    user: Optional[str] = typer.Option(
        None, "--user", "-u", help="Reset a different user's studio"
    ),
):
    """Reset a stuck studio (admin operation)."""
    username = check_aws_sso()

    # Use specified user if provided, otherwise use current user
    target_user = user if user else username

    # Add warning when resetting another user's studio
    if target_user != username:
        console.print(f"[yellow]⚠️  Resetting studio for user: {target_user}[/yellow]")

    studio = get_user_studio(target_user)
    if not studio:
        if target_user == username:
            console.print("[yellow]You don't have a studio.[/yellow]")
        else:
            console.print(f"[yellow]User {target_user} doesn't have a studio.[/yellow]")
        return

    console.print(f"[yellow]⚠️  This will force-reset the studio state[/yellow]")
    console.print(f"Current status: {studio['status']}")
    if studio.get("attached_vm_id"):
        console.print(f"Listed as attached to: {studio['attached_vm_id']}")

    if not Confirm.ask("\nReset studio state?"):
        console.print("Reset cancelled.")
        return

    # Direct DynamoDB update
    console.print("Resetting studio state...")

    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("dev-studios")

    try:
        # Check if volume is actually attached
        ec2 = boto3.client("ec2", region_name="us-east-1")
        volumes = ec2.describe_volumes(VolumeIds=[studio["studio_id"]])

        if volumes["Volumes"]:
            volume = volumes["Volumes"][0]
            attachments = volume.get("Attachments", [])
            if attachments:
                console.print(
                    f"[red]Volume is still attached to {attachments[0]['InstanceId']}![/red]"
                )
                if Confirm.ask("Force-detach the volume?"):
                    ec2.detach_volume(
                        VolumeId=studio["studio_id"],
                        InstanceId=attachments[0]["InstanceId"],
                        Force=True,
                    )
                    console.print("Waiting for volume to detach...")
                    waiter = ec2.get_waiter("volume_available")
                    waiter.wait(VolumeIds=[studio["studio_id"]])

        # Reset in DynamoDB – align attribute names with Studio Manager backend
        table.update_item(
            Key={"StudioID": studio["studio_id"]},
            UpdateExpression="SET #st = :status, AttachedVMID = :vm_id, AttachedDevice = :device",
            ExpressionAttributeNames={"#st": "Status"},
            ExpressionAttributeValues={
                ":status": "available",
                ":vm_id": None,
                ":device": None,
            },
        )

        console.print(f"[green]✓ Studio reset to available state![/green]")

    except ClientError as e:
        console.print(f"[red]❌ Failed to reset studio: {e}[/red]")


def resize_studio(
    size: int = typer.Option(..., "--size", "-s", help="New size in GB"),
    user: Optional[str] = typer.Option(
        None, "--user", "-u", help="Resize a different user's studio (admin only)"
    ),
):
    """Resize your studio volume (requires detachment)."""
    username = check_aws_sso()

    # Use specified user if provided, otherwise use current user
    target_user = user if user else username

    # Add warning when resizing another user's studio
    if target_user != username:
        console.print(f"[yellow]⚠️  Resizing studio for user: {target_user}[/yellow]")

    studio = get_user_studio(target_user)
    if not studio:
        if target_user == username:
            console.print("[yellow]You don't have a studio yet.[/yellow]")
        else:
            console.print(f"[yellow]User {target_user} doesn't have a studio.[/yellow]")
        return

    current_size = studio["size_gb"]

    if size <= current_size:
        console.print(
            f"[red]❌ New size ({size}GB) must be larger than current size ({current_size}GB)[/red]"
        )
        raise typer.Exit(1)

    # Check if studio is attached
    if studio["status"] == "in-use":
        console.print("[yellow]⚠️  Studio must be detached before resizing[/yellow]")
        console.print(f"Currently attached to: {studio.get('attached_vm_id')}")

        if not Confirm.ask("\nDetach studio and proceed with resize?"):
            console.print("Resize cancelled.")
            return

        # Detach the studio
        console.print("Detaching studio...")
        response = make_api_request("POST", f"/studios/{studio['studio_id']}/detach")
        if response.status_code != 200:
            console.print("[red]❌ Failed to detach studio[/red]")
            raise typer.Exit(1)

        console.print("[green]✓ Studio detached[/green]")

        # Wait a moment for detachment to complete
        time.sleep(5)

    console.print(f"[yellow]Resizing studio from {current_size}GB to {size}GB[/yellow]")

    # Call the resize API
    resize_response = make_api_request(
        "POST", f"/studios/{studio['studio_id']}/resize", json_data={"size": size}
    )

    if resize_response.status_code != 200:
        error = resize_response.json().get("error", "Unknown error")
        console.print(f"[red]❌ Failed to resize studio: {error}[/red]")
        raise typer.Exit(1)

    # Wait for volume modification to complete
    ec2 = boto3.client("ec2", region_name="us-east-1")
    console.print("Resizing volume...")

    # Track progress
    last_progress = 0

    while True:
        try:
            mod_state = ec2.describe_volumes_modifications(
                VolumeIds=[studio["studio_id"]]
            )
            if not mod_state["VolumesModifications"]:
                break  # Modification complete

            modification = mod_state["VolumesModifications"][0]
            state = modification["ModificationState"]
            progress = modification.get("Progress", 0)

            # Show progress updates only for the resize phase
            if state == "modifying" and progress > last_progress:
                console.print(f"[yellow]Progress: {progress}%[/yellow]")
                last_progress = progress

            # Exit as soon as optimization starts (resize is complete)
            if state == "optimizing":
                console.print(
                    f"[green]✓ Studio resized successfully to {size}GB![/green]"
                )
                console.print(
                    "[dim]AWS is optimizing the volume in the background (no action needed).[/dim]"
                )
                break

            if state == "completed":
                console.print(
                    f"[green]✓ Studio resized successfully to {size}GB![/green]"
                )
                break
            elif state == "failed":
                console.print("[red]❌ Volume modification failed[/red]")
                raise typer.Exit(1)

            time.sleep(2)  # Check more frequently for better UX

        except ClientError:
            # Modification might be complete
            console.print(f"[green]✓ Studio resized successfully to {size}GB![/green]")
            break

    console.print(
        "\n[dim]The filesystem will be automatically expanded when you next attach the studio.[/dim]"
    )
    console.print(f"To attach: [cyan]dh studio attach <engine-name>[/cyan]")
