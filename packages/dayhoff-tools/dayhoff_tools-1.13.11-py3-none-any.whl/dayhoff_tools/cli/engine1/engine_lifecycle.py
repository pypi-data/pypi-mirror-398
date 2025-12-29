"""Engine lifecycle commands: start, stop, and terminate."""

from datetime import datetime, timezone

import typer
from rich.prompt import Confirm

from .shared import (
    HOURLY_COSTS,
    check_aws_sso,
    console,
    format_duration,
    make_api_request,
    parse_launch_time,
    resolve_engine,
)


def start_engine(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
):
    """Start a stopped engine."""
    check_aws_sso()

    # Get all engines to resolve name
    response = make_api_request("GET", "/engines")
    if response.status_code != 200:
        console.print("[red]❌ Failed to fetch engines[/red]")
        raise typer.Exit(1)

    engines = response.json().get("engines", [])
    engine = resolve_engine(name_or_id, engines)

    console.print(f"Starting engine [cyan]{engine['name']}[/cyan]...")

    response = make_api_request("POST", f"/engines/{engine['instance_id']}/start")

    if response.status_code == 200:
        data = response.json()
        console.print(f"[green]✓ Engine started successfully![/green]")
        console.print(f"New public IP: {data.get('public_ip', 'Pending...')}")
    else:
        error = response.json().get("error", "Unknown error")
        console.print(f"[red]❌ Failed to start engine: {error}[/red]")


def stop_engine(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force stop and detach all studios"
    ),
):
    """Stop an engine."""
    check_aws_sso()

    # Get all engines to resolve name
    response = make_api_request("GET", "/engines")
    if response.status_code != 200:
        console.print("[red]❌ Failed to fetch engines[/red]")
        raise typer.Exit(1)

    engines = response.json().get("engines", [])
    engine = resolve_engine(name_or_id, engines)

    console.print(f"Stopping engine [cyan]{engine['name']}[/cyan]...")

    # First attempt without detaching
    response = make_api_request(
        "POST",
        f"/engines/{engine['instance_id']}/stop",
        json_data={"detach_studios": force},
    )

    if response.status_code == 409 and not force:
        # Engine has attached studios
        data = response.json()
        attached_studios = data.get("attached_studios", [])

        console.print("\n[yellow]⚠️  This engine has attached studios:[/yellow]")
        for studio in attached_studios:
            console.print(f"  • {studio['user']} ({studio['studio_id']})")

        if Confirm.ask("\nDetach all studios and stop the engine?"):
            response = make_api_request(
                "POST",
                f"/engines/{engine['instance_id']}/stop",
                json_data={"detach_studios": True},
            )
        else:
            console.print("Stop cancelled.")
            return

    if response.status_code == 200:
        console.print(f"[green]✓ Engine stopped successfully![/green]")
    else:
        error = response.json().get("error", "Unknown error")
        console.print(f"[red]❌ Failed to stop engine: {error}[/red]")


def terminate_engine(
    name_or_id: str = typer.Argument(help="Engine name or instance ID"),
):
    """Permanently terminate an engine."""
    check_aws_sso()

    # Get all engines to resolve name
    response = make_api_request("GET", "/engines")
    if response.status_code != 200:
        console.print("[red]❌ Failed to fetch engines[/red]")
        raise typer.Exit(1)

    engines = response.json().get("engines", [])
    engine = resolve_engine(name_or_id, engines)

    # Calculate cost
    launch_time = parse_launch_time(engine["launch_time"])
    uptime = datetime.now(timezone.utc) - launch_time
    hourly_cost = HOURLY_COSTS.get(engine["engine_type"], 0)
    total_cost = hourly_cost * (uptime.total_seconds() / 3600)

    console.print(
        f"\n[yellow]⚠️  This will permanently terminate engine '{engine['name']}'[/yellow]"
    )
    console.print(f"Total cost for this session: ${total_cost:.2f}")

    if not Confirm.ask("\nAre you sure you want to terminate this engine?"):
        console.print("Termination cancelled.")
        return

    response = make_api_request("DELETE", f"/engines/{engine['instance_id']}")

    if response.status_code == 200:
        console.print(f"[green]✓ Engine terminated successfully![/green]")
    else:
        error = response.json().get("error", "Unknown error")
        console.print(f"[red]❌ Failed to terminate engine: {error}[/red]")
