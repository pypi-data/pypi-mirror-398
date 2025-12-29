#!/usr/bin/env python3
"""Simulator for studio list output - iterate on design locally without AWS.

This lets you quickly see how the list command output looks with different
studio states and configurations.

Usage:
    python dayhoff_tools/cli/engines_studios/simulators/studio_list_simulator.py                # Show all scenarios
    python dayhoff_tools/cli/engines_studios/simulators/studio_list_simulator.py --scenario few # Show specific scenario
    python dayhoff_tools/cli/engines_studios/simulators/studio_list_simulator.py --env prod     # Simulate different environment
"""

import argparse
import sys
from typing import Any


def colorize(text: str, color_code: str) -> str:
    """Apply ANSI color code to text."""
    return f"\033[{color_code}m{text}\033[0m"


def format_list_output(
    studios: list[dict[str, Any]], engines_map: dict[str, str], env: str = "dev"
) -> None:
    """Format and print studio list output matching the actual CLI."""

    # Header with blue account name
    print(f"\nStudios for AWS Account {colorize(env, '34')}")

    if not studios:
        print("No studios found\n")
        return

    # Calculate dynamic width for User column (longest user + 2 for padding)
    max_user_len = max(
        (len(studio.get("user", "unknown")) for studio in studios), default=4
    )
    user_width = max(max_user_len + 2, len("User") + 2)

    # Calculate dynamic width for Attached To column
    max_attached_len = 0
    for studio in studios:
        if studio.get("attached_to"):
            instance_id = studio["attached_to"]
            engine_name = engines_map.get(instance_id, "unknown")
            max_attached_len = max(max_attached_len, len(engine_name))
    attached_width = max(
        max_attached_len + 2, len("Attached To") + 2, 3
    )  # At least 3 for "-"

    # Fixed widths for other columns
    status_width = 12
    size_width = 10
    id_width = 25

    # Table top border
    print(
        "╭"
        + "─" * (user_width + 1)
        + "┬"
        + "─" * (status_width + 1)
        + "┬"
        + "─" * (attached_width + 1)
        + "┬"
        + "─" * (size_width + 1)
        + "┬"
        + "─" * (id_width + 1)
        + "╮"
    )

    # Table header
    print(
        f"│ {'User':<{user_width}}│ {'Status':<{status_width}}│ {'Attached To':<{attached_width}}│ {'Size':<{size_width}}│ {'Studio ID':<{id_width}}│"
    )

    # Header separator
    print(
        "├"
        + "─" * (user_width + 1)
        + "┼"
        + "─" * (status_width + 1)
        + "┼"
        + "─" * (attached_width + 1)
        + "┼"
        + "─" * (size_width + 1)
        + "┼"
        + "─" * (id_width + 1)
        + "┤"
    )

    # Table rows
    for studio in studios:
        user = studio.get("user", "unknown")
        status = studio.get("status", "unknown")
        size = f"{studio.get('size_gb', 0)}GB"
        studio_id = studio.get("studio_id", "unknown")
        attached_to = studio.get("attached_to")

        # Truncate if needed
        if len(user) > user_width - 1:
            user = user[: user_width - 1]

        # Color the user (blue)
        user_display = colorize(f"{user:<{user_width}}", "34")

        # Format status - display "in-use" as "attached" in purple
        if status == "in-use":
            display_status = "attached"
            status_display = colorize(
                f"{display_status:<{status_width}}", "35"
            )  # Purple
        elif status == "available":
            status_display = colorize(f"{status:<{status_width}}", "32")  # Green
        elif status in ["attaching", "detaching"]:
            status_display = colorize(f"{status:<{status_width}}", "33")  # Yellow
        elif status == "attached":
            status_display = colorize(f"{status:<{status_width}}", "35")  # Purple
        elif status == "error":
            status_display = colorize(f"{status:<{status_width}}", "31")  # Red
        else:
            status_display = f"{status:<{status_width}}"  # No color for other states

        # Format Attached To column
        if attached_to:
            instance_id = attached_to
            engine_name = engines_map.get(instance_id, "unknown")
            # Engine name in white (no color)
            attached_display = f"{engine_name:<{attached_width}}"
        else:
            attached_display = f"{'-':<{attached_width}}"

        # Color the studio ID (grey)
        studio_id_display = colorize(f"{studio_id:<{id_width}}", "90")

        print(
            f"│ {user_display}│ {status_display}│ {attached_display}│ {size:<{size_width}}│ {studio_id_display}│"
        )

    # Table bottom border
    print(
        "╰"
        + "─" * (user_width + 1)
        + "┴"
        + "─" * (status_width + 1)
        + "┴"
        + "─" * (attached_width + 1)
        + "┴"
        + "─" * (size_width + 1)
        + "┴"
        + "─" * (id_width + 1)
        + "╯"
    )

    print(f"Total: {len(studios)}\n")


def generate_scenarios() -> dict[str, dict[str, Any]]:
    """Generate various test scenarios for studio list output."""

    scenarios = {}

    # Create a consistent engines map for all scenarios
    engines_map = {
        "i-0123456789abcdef0": "alice-gpu",
        "i-1234567890abcdef1": "bob-cpu",
        "i-2345678901abcdef2": "charlie-work",
        "i-3456789012abcdef3": "diana-dev",
    }

    # Scenario 1: Single available studio
    scenarios["single"] = {
        "name": "Single Available Studio",
        "studios": [
            {
                "user": "alice",
                "status": "available",
                "size_gb": 100,
                "studio_id": "vol-0abc123def456789a",
                "attached_to": None,
            }
        ],
        "engines_map": engines_map,
        "env": "dev",
    }

    # Scenario 2: Few studios with various states
    scenarios["few"] = {
        "name": "Few Studios - Mixed States",
        "studios": [
            {
                "user": "alice",
                "status": "in-use",  # Will be displayed as "attached" in purple
                "size_gb": 100,
                "studio_id": "vol-0abc123def456789a",
                "attached_to": "i-0123456789abcdef0",
            },
            {
                "user": "bob",
                "status": "available",
                "size_gb": 200,
                "studio_id": "vol-0abc123def456789b",
                "attached_to": None,
            },
            {
                "user": "charlie",
                "status": "attaching",
                "size_gb": 150,
                "studio_id": "vol-0abc123def456789c",
                "attached_to": "i-2345678901abcdef2",
            },
        ],
        "engines_map": engines_map,
        "env": "sand",
    }

    # Scenario 3: Many studios (production-like)
    scenarios["many"] = {
        "name": "Many Studios - Production",
        "studios": [
            {
                "user": "alice",
                "status": "attached",
                "size_gb": 100,
                "studio_id": "vol-0abc123def456789a",
                "attached_to": "i-0123456789abcdef0",
            },
            {
                "user": "bob",
                "status": "attached",
                "size_gb": 200,
                "studio_id": "vol-0abc123def456789b",
                "attached_to": "i-1234567890abcdef1",
            },
            {
                "user": "charlie",
                "status": "available",
                "size_gb": 150,
                "studio_id": "vol-0abc123def456789c",
                "attached_to": None,
            },
            {
                "user": "diana",
                "status": "attached",
                "size_gb": 250,
                "studio_id": "vol-0abc123def456789d",
                "attached_to": "i-3456789012abcdef3",
            },
            {
                "user": "eve",
                "status": "available",
                "size_gb": 100,
                "studio_id": "vol-0abc123def456789e",
                "attached_to": None,
            },
            {
                "user": "frank",
                "status": "detaching",
                "size_gb": 300,
                "studio_id": "vol-0abc123def456789f",
                "attached_to": None,
            },
        ],
        "engines_map": engines_map,
        "env": "prod",
    }

    # Scenario 4: Empty list
    scenarios["empty"] = {
        "name": "No Studios",
        "studios": [],
        "engines_map": engines_map,
        "env": "dev",
    }

    # Scenario 5: All transitional states
    scenarios["transitions"] = {
        "name": "Transitional States",
        "studios": [
            {
                "user": "alice",
                "status": "attaching",
                "size_gb": 100,
                "studio_id": "vol-0abc123def456789a",
                "attached_to": "i-0123456789abcdef0",
            },
            {
                "user": "bob",
                "status": "detaching",
                "size_gb": 200,
                "studio_id": "vol-0abc123def456789b",
                "attached_to": None,
            },
            {
                "user": "charlie",
                "status": "error",
                "size_gb": 150,
                "studio_id": "vol-0abc123def456789c",
                "attached_to": None,
            },
        ],
        "engines_map": engines_map,
        "env": "sand",
    }

    # Scenario 6: Long names
    scenarios["long_names"] = {
        "name": "Long User Names",
        "studios": [
            {
                "user": "alice-with-very-long-username",
                "status": "attached",
                "size_gb": 100,
                "studio_id": "vol-0abc123def456789a",
                "attached_to": "i-0123456789abcdef0",
            },
            {
                "user": "bob",
                "status": "available",
                "size_gb": 200,
                "studio_id": "vol-0abc123def456789b",
                "attached_to": None,
            },
        ],
        "engines_map": engines_map,
        "env": "dev",
    }

    return scenarios


def main():
    parser = argparse.ArgumentParser(
        description="Simulate studio list output for design iteration"
    )
    parser.add_argument(
        "--scenario",
        choices=["single", "few", "many", "empty", "transitions", "long_names", "all"],
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
        for _, scenario_data in scenarios.items():
            print("\n" + "=" * 80)
            print(f"SCENARIO: {scenario_data['name']}")
            print("=" * 80 + "\n")

            env = args.env if args.env else scenario_data["env"]
            format_list_output(
                scenario_data["studios"], scenario_data["engines_map"], env
            )
            print()  # Extra newline between scenarios
    else:
        # Show specific scenario
        scenario_data = scenarios[args.scenario]
        print(f"\nSCENARIO: {scenario_data['name']}\n")

        env = args.env if args.env else scenario_data["env"]
        format_list_output(scenario_data["studios"], scenario_data["engines_map"], env)


if __name__ == "__main__":
    main()
