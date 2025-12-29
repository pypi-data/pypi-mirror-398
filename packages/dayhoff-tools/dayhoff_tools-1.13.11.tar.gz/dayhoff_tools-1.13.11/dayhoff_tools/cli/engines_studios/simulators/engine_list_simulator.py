#!/usr/bin/env python3
"""Simulator for engine list output - iterate on design locally without AWS.

This lets you quickly see how the list command output looks with different
engine states and configurations.

Usage:
    python dayhoff_tools/cli/engines_studios/simulators/engine_list_simulator.py                # Show all scenarios
    python dayhoff_tools/cli/engines_studios/simulators/engine_list_simulator.py --scenario few # Show specific scenario
    python dayhoff_tools/cli/engines_studios/simulators/engine_list_simulator.py --env prod     # Simulate different environment
"""

import argparse
import sys
from typing import Any


def colorize(text: str, color_code: str) -> str:
    """Apply ANSI color code to text."""
    return f"\033[{color_code}m{text}\033[0m"


def format_list_output(engines: list[dict[str, Any]], env: str = "dev") -> None:
    """Format and print engine list output matching the actual CLI."""

    # Header with blue account name
    print(f"\nEngines for AWS Account {colorize(env, '34')}")

    if not engines:
        print("No engines found\n")
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
    print(
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
    print(
        f"│ {'Name':<{name_width}}│ {'State':<{state_width}}│ {'User':<{user_width}}│ {'Type':<{type_width}}│ {'Instance ID':<{id_width}}│"
    )

    # Header separator
    print(
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
        name_display = colorize(f"{name:<{name_width}}", "34")

        # Color the state
        if state == "running":
            state_display = colorize(f"{state:<{state_width}}", "32")  # Green
        elif state in ["starting", "stopping", "pending"]:
            state_display = colorize(f"{state:<{state_width}}", "33")  # Yellow
        elif state == "stopped":
            state_display = colorize(f"{state:<{state_width}}", "90")  # Grey (dim)
        else:
            state_display = f"{state:<{state_width}}"  # No color for other states

        # Color the instance ID (grey)
        instance_id_display = colorize(f"{instance_id:<{id_width}}", "90")

        print(
            f"│ {name_display}│ {state_display}│ {user:<{user_width}}│ {engine_type:<{type_width}}│ {instance_id_display}│"
        )

    # Table bottom border
    print(
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

    print(f"Total: {len(engines)}\n")


def generate_scenarios() -> dict[str, dict[str, Any]]:
    """Generate various test scenarios for list output."""

    scenarios = {}

    # Scenario 1: Single running engine
    scenarios["single"] = {
        "name": "Single Running Engine",
        "engines": [
            {
                "name": "alice-gpu",
                "state": "running",
                "user": "alice",
                "engine_type": "gpu",
                "instance_id": "i-0123456789abcdef0",
            }
        ],
        "env": "dev",
    }

    # Scenario 2: Few engines with various states
    scenarios["few"] = {
        "name": "Few Engines - Mixed States",
        "engines": [
            {
                "name": "alice-gpu",
                "state": "running",
                "user": "alice",
                "engine_type": "gpu",
                "instance_id": "i-0123456789abcdef0",
            },
            {
                "name": "bob-cpu",
                "state": "stopped",
                "user": "bob",
                "engine_type": "cpu",
                "instance_id": "i-1234567890abcdef1",
            },
            {
                "name": "charlie",
                "state": "starting",
                "user": "charlie",
                "engine_type": "cpu",
                "instance_id": "i-2345678901abcdef2",
            },
        ],
        "env": "sand",
    }

    # Scenario 3: Many engines (production-like)
    scenarios["many"] = {
        "name": "Many Engines - Production",
        "engines": [
            {
                "name": "alice-main",
                "state": "running",
                "user": "alice",
                "engine_type": "gpu",
                "instance_id": "i-0123456789abcdef0",
            },
            {
                "name": "bob-exp1",
                "state": "running",
                "user": "bob",
                "engine_type": "cpu",
                "instance_id": "i-1234567890abcdef1",
            },
            {
                "name": "bob-exp2",
                "state": "stopped",
                "user": "bob",
                "engine_type": "cpu",
                "instance_id": "i-2345678901abcdef2",
            },
            {
                "name": "charlie-gpu",
                "state": "running",
                "user": "charlie",
                "engine_type": "gpu",
                "instance_id": "i-3456789012abcdef3",
            },
            {
                "name": "diana-dev",
                "state": "running",
                "user": "diana",
                "engine_type": "cpu",
                "instance_id": "i-4567890123abcdef4",
            },
            {
                "name": "eve-test",
                "state": "stopping",
                "user": "eve",
                "engine_type": "cpu",
                "instance_id": "i-5678901234abcdef5",
            },
            {
                "name": "frank-prod",
                "state": "running",
                "user": "frank",
                "engine_type": "gpu",
                "instance_id": "i-6789012345abcdef6",
            },
        ],
        "env": "prod",
    }

    # Scenario 4: Empty list
    scenarios["empty"] = {
        "name": "No Engines",
        "engines": [],
        "env": "dev",
    }

    # Scenario 5: All transitional states
    scenarios["transitions"] = {
        "name": "Transitional States",
        "engines": [
            {
                "name": "engine1",
                "state": "starting",
                "user": "alice",
                "engine_type": "cpu",
                "instance_id": "i-0123456789abcdef0",
            },
            {
                "name": "engine2",
                "state": "stopping",
                "user": "bob",
                "engine_type": "cpu",
                "instance_id": "i-1234567890abcdef1",
            },
            {
                "name": "engine3",
                "state": "pending",
                "user": "charlie",
                "engine_type": "gpu",
                "instance_id": "i-2345678901abcdef2",
            },
        ],
        "env": "sand",
    }

    return scenarios


def main():
    parser = argparse.ArgumentParser(
        description="Simulate engine list output for design iteration"
    )
    parser.add_argument(
        "--scenario",
        choices=["single", "few", "many", "empty", "transitions", "all"],
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
            format_list_output(scenario_data["engines"], env)
            print()  # Extra newline between scenarios
    else:
        # Show specific scenario
        scenario_data = scenarios[args.scenario]
        print(f"\nSCENARIO: {scenario_data['name']}\n")

        env = args.env if args.env else scenario_data["env"]
        format_list_output(scenario_data["engines"], env)


if __name__ == "__main__":
    main()
