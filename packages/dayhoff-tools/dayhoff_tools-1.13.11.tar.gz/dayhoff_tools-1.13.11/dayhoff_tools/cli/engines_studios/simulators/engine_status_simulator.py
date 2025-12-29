#!/usr/bin/env python3
"""Simulator for engine status output - iterate on design locally without AWS.

This lets you quickly see how the status command output looks for different
engine states and configurations.

Usage:
    python dayhoff_tools/cli/engines_studios/simulators/engine_status_simulator.py                    # Show all scenarios
    python dayhoff_tools/cli/engines_studios/simulators/engine_status_simulator.py --scenario running # Show specific scenario
    python dayhoff_tools/cli/engines_studios/simulators/engine_status_simulator.py --env sand         # Override environment
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Import standalone utilities
simulator_dir = Path(__file__).parent
sys.path.insert(0, str(simulator_dir))
from simulator_utils import format_idle_state, format_time_ago


def colorize(text: str, color_code: str) -> str:
    """Apply ANSI color code to text."""
    return f"\033[{color_code}m{text}\033[0m"


def format_status_output(status_data: dict, env: str = "dev") -> None:
    """Format and print engine status output matching the actual CLI."""

    # Display basic info - matching engine_commands.py order
    engine_name = status_data.get("name", status_data.get("instance_id", "unknown"))
    print(f"Name: {colorize(engine_name, '34')}")  # Blue

    # Show state with color coding
    engine_state = status_data.get("state", "unknown")
    state_lower = engine_state.lower()
    if state_lower == "running":
        print(f"State: {colorize(engine_state, '32')}")  # Green
    elif state_lower in ["stopped", "terminated"]:
        print(f"State: {colorize(engine_state, '31')}")  # Red
    elif state_lower in ["stopping", "starting", "pending"]:
        print(f"State: {colorize(engine_state, '33')}")  # Yellow
    else:
        print(f"State: {engine_state}")

    # Show account
    print(f"Account: {env}")

    if status_data.get("launch_time"):
        print(f"Launched: {format_time_ago(status_data['launch_time'])}")

    print(f"Type: {status_data.get('instance_type', 'unknown')}")
    print(f"Instance ID: {status_data.get('instance_id', 'unknown')}")

    if status_data.get("public_ip"):
        print(f"Public IP: {status_data['public_ip']}")

    # Only show idle state and sensors for running engines
    if state_lower != "running":
        if state_lower in ["stopped", "terminated"]:
            print(
                f"\n⚠️  Engine is {engine_state.lower()} - idle detection not available"
            )
        return

    # Display idle state
    idle_state = status_data.get("idle_state", {})
    if idle_state:
        idle_display = format_idle_state(idle_state)
        print(idle_display)

    # Display attached studios
    print(f"\nAttached Studios: {status_data.get('attached_studios', 'None')}")


def generate_scenarios() -> dict:
    """Generate various test scenarios for status output."""

    scenarios = {}

    # Scenario 1: Running engine with idle state
    scenarios["running_idle"] = {
        "name": "Running Engine - Idle",
        "status_data": {
            "name": "alice-gpu",
            "instance_id": "i-0123456789abcdef0",
            "instance_type": "g4dn.xlarge",
            "state": "running",
            "public_ip": "54.123.45.67",
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(hours=3)
            ).isoformat(),
            "idle_state": {
                "is_idle": True,
                "reason": "All sensors report idle",
                "idle_seconds": 450,
                "timeout_seconds": "1800",
                "sensors": {
                    "coffee": {
                        "active": False,
                        "confidence": "HIGH",
                        "details": {},
                    },
                    "ssh": {
                        "active": False,
                        "confidence": "HIGH",
                        "details": {},
                    },
                    "ide": {
                        "active": False,
                        "confidence": "HIGH",
                        "details": {},
                    },
                    "docker": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "details": {},
                    },
                },
            },
            "attached_studios": "None",
        },
        "env": "dev",
    }

    # Scenario 2: Running engine with active SSH
    scenarios["running_active"] = {
        "name": "Running Engine - Active (SSH + IDE + Coffee)",
        "status_data": {
            "name": "bob-cpu",
            "instance_id": "i-1234567890abcdef1",
            "instance_type": "t3a.xlarge",
            "state": "running",
            "public_ip": "54.234.56.78",
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(minutes=45)
            ).isoformat(),
            "idle_state": {
                "is_idle": False,
                "reason": "Active connections detected",
                "idle_seconds": 0,
                "timeout_seconds": "1800",
                "sensors": {
                    "coffee": {
                        "active": True,
                        "confidence": "HIGH",
                        "details": {
                            "remaining_seconds": "13200",  # 220 minutes
                            "timeout_seconds": "14400",
                        },
                    },
                    "ssh": {
                        "active": True,
                        "confidence": "HIGH",
                        "details": {
                            "session_count": 2,
                            "sessions": [
                                {
                                    "user": "bob",
                                    "tty": "pts/0",
                                    "from": "127.0.0.1",
                                    "login": "2025-11-18 09:30",
                                    "idle": "00:05",
                                    "pid": "12345",
                                },
                                {
                                    "user": "bob",
                                    "tty": "pts/1",
                                    "from": "127.0.0.1",
                                    "login": "2025-11-18 09:45",
                                    "idle": "00:02",
                                    "pid": "12567",
                                },
                            ],
                        },
                    },
                    "ide": {
                        "active": True,
                        "confidence": "HIGH",
                        "details": {
                            "connection_count": 1,
                            "ide_type": "Cursor",
                            "connections": [
                                {
                                    "local": "127.0.0.1:32777",
                                    "remote": "127.0.0.1:33616",
                                    "process": "cursor-ba90f2f8",
                                    "pid": "24967",
                                }
                            ],
                        },
                    },
                    "docker": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "details": {},
                    },
                },
            },
            "attached_studios": "vol-047e03b0647fa9d87",
        },
        "env": "sand",
    }

    # Scenario 3: Stopped engine
    scenarios["stopped"] = {
        "name": "Stopped Engine",
        "status_data": {
            "name": "charlie-test",
            "instance_id": "i-2345678901abcdef2",
            "instance_type": "t3a.medium",
            "state": "stopped",
            "launch_time": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "attached_studios": "None",
        },
        "env": "dev",
    }

    # Scenario 4: Starting engine
    scenarios["starting"] = {
        "name": "Starting Engine",
        "status_data": {
            "name": "diana-gpu",
            "instance_id": "i-3456789012abcdef3",
            "instance_type": "g5.xlarge",
            "state": "starting",
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(minutes=2)
            ).isoformat(),
            "attached_studios": "None",
        },
        "env": "prod",
    }

    # Scenario 5: Stopping engine
    scenarios["stopping"] = {
        "name": "Stopping Engine",
        "status_data": {
            "name": "eve-dev",
            "instance_id": "i-4567890123abcdef4",
            "instance_type": "t3a.large",
            "state": "stopping",
            "public_ip": "54.123.45.89",
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(hours=8)
            ).isoformat(),
            "attached_studios": "None",
        },
        "env": "sand",
    }

    # Scenario 6: Running with Docker activity
    scenarios["running_docker"] = {
        "name": "Running Engine - Docker Active",
        "status_data": {
            "name": "frank-ml",
            "instance_id": "i-5678901234abcdef5",
            "instance_type": "g4dn.2xlarge",
            "state": "running",
            "public_ip": "54.234.67.90",
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(hours=12)
            ).isoformat(),
            "idle_state": {
                "is_idle": False,
                "reason": "Docker containers running",
                "idle_seconds": 0,
                "timeout_seconds": "1800",
                "sensors": {
                    "coffee": {
                        "active": False,
                        "confidence": "HIGH",
                        "details": {},
                    },
                    "ssh": {
                        "active": False,
                        "confidence": "HIGH",
                        "details": {},
                    },
                    "ide": {
                        "active": False,
                        "confidence": "HIGH",
                        "details": {},
                    },
                    "docker": {
                        "active": True,
                        "confidence": "HIGH",
                        "details": {
                            "container_count": 3,
                            "containers": [
                                {
                                    "name": "training-job-1",
                                    "status": "running",
                                    "uptime": "3 hours",
                                },
                                {
                                    "name": "redis-cache",
                                    "status": "running",
                                    "uptime": "12 hours",
                                },
                                {
                                    "name": "monitoring",
                                    "status": "running",
                                    "uptime": "12 hours",
                                },
                            ],
                        },
                    },
                },
            },
            "attached_studios": "vol-01234567890abcdef",
        },
        "env": "prod",
    }

    return scenarios


def main():
    parser = argparse.ArgumentParser(
        description="Simulate engine status output for design iteration"
    )
    parser.add_argument(
        "--scenario",
        choices=[
            "running_idle",
            "running_active",
            "stopped",
            "starting",
            "stopping",
            "running_docker",
            "all",
        ],
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
            format_status_output(scenario_data["status_data"], env)
            print()  # Extra newline between scenarios
    else:
        # Show specific scenario
        scenario_data = scenarios[args.scenario]
        print(f"\nSCENARIO: {scenario_data['name']}\n")

        env = args.env if args.env else scenario_data["env"]
        format_status_output(scenario_data["status_data"], env)


if __name__ == "__main__":
    main()
