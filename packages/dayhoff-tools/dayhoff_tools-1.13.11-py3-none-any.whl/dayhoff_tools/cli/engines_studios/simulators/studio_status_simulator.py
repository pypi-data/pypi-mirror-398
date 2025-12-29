#!/usr/bin/env python3
"""Simulator for studio status output - iterate on design locally without AWS.

This lets you quickly see how the studio status command output looks for different
studio states and configurations.

Usage:
    python dayhoff_tools/cli/engines_studios/simulators/studio_status_simulator.py                    # Show all scenarios
    python dayhoff_tools/cli/engines_studios/simulators/studio_status_simulator.py --scenario attached # Show specific scenario
    python dayhoff_tools/cli/engines_studios/simulators/studio_status_simulator.py --env prod         # Override environment
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Import standalone utilities
simulator_dir = Path(__file__).parent
sys.path.insert(0, str(simulator_dir))
from simulator_utils import format_time_ago


def colorize(text: str, color_code: str) -> str:
    """Apply ANSI color code to text."""
    return f"\033[{color_code}m{text}\033[0m"


def format_studio_status(studio_data: dict, env: str = "dev") -> None:
    """Format and print studio status output matching the actual CLI."""

    # Reordered output: User, Status, Attached to, Account, Size, Created, Studio ID
    print(f"User: {studio_data['user']}")
    # Status in blue
    print(f"Status: {colorize(studio_data['status'], '34')}")
    # Attached to in blue (if present)
    if studio_data.get("attached_to"):
        print(f"Attached to: {colorize(studio_data['attached_to'], '34')}")
    print(f"Account: {env}")
    print(f"Size: {studio_data['size_gb']}GB")
    if studio_data.get("created_at"):
        print(f"Created: {format_time_ago(studio_data['created_at'])}")
    print(f"Studio ID: {studio_data['studio_id']}")


def generate_scenarios() -> dict:
    """Generate various test scenarios for studio status output."""

    scenarios = {}

    # Scenario 1: Available studio (not attached)
    scenarios["available"] = {
        "name": "Available Studio - Not Attached",
        "studio_data": {
            "user": "alice",
            "size_gb": 100,
            "status": "available",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            "studio_id": "vol-0123456789abcdef0",
        },
        "env": "dev",
    }

    # Scenario 2: Studio attached to engine
    scenarios["attached"] = {
        "name": "Studio Attached to Engine",
        "studio_data": {
            "user": "bob",
            "size_gb": 150,
            "status": "attached",
            "created_at": (
                datetime.now(timezone.utc) - timedelta(days=21, hours=3)
            ).isoformat(),
            "studio_id": "vol-1234567890abcdef1",
            "attached_to": "bob-main (i-1234567890abcdef1)",
        },
        "env": "sand",
    }

    # Scenario 3: Large studio in production
    scenarios["large"] = {
        "name": "Large Production Studio",
        "studio_data": {
            "user": "charlie",
            "size_gb": 500,
            "status": "available",
            "created_at": (
                datetime.now(timezone.utc) - timedelta(days=120)
            ).isoformat(),
            "studio_id": "vol-2345678901abcdef2",
        },
        "env": "prod",
    }

    # Scenario 4: Recently created studio
    scenarios["new"] = {
        "name": "Newly Created Studio",
        "studio_data": {
            "user": "diana",
            "size_gb": 50,
            "status": "available",
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "studio_id": "vol-3456789012abcdef3",
        },
        "env": "dev",
    }

    # Scenario 5: Studio being modified
    scenarios["modifying"] = {
        "name": "Studio Being Modified",
        "studio_data": {
            "user": "eve",
            "size_gb": 200,
            "status": "modifying",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
            "studio_id": "vol-4567890123abcdef4",
        },
        "env": "sand",
    }

    return scenarios


def main():
    parser = argparse.ArgumentParser(
        description="Simulate studio status output for design iteration"
    )
    parser.add_argument(
        "--scenario",
        choices=["available", "attached", "large", "new", "modifying", "all"],
        default="all",
        help="Which scenario to display (default: all)",
    )
    parser.add_argument(
        "--env",
        choices=["dev", "sand", "prod"],
        help="Override environment for display",
    )

    args = parser.parse_args()

    scenarios = generate_scenarios()

    if args.scenario == "all":
        # Show all scenarios
        for scenario_key, scenario_data in scenarios.items():
            print("\n" + "=" * 80)
            print(f"SCENARIO: {scenario_data['name']}")
            print("=" * 80 + "\n")

            env = args.env if args.env else scenario_data["env"]
            format_studio_status(scenario_data["studio_data"], env)
            print()  # Extra newline between scenarios
    else:
        # Show specific scenario
        scenario_data = scenarios[args.scenario]
        print(f"\nSCENARIO: {scenario_data['name']}\n")

        env = args.env if args.env else scenario_data["env"]
        format_studio_status(scenario_data["studio_data"], env)


if __name__ == "__main__":
    main()
