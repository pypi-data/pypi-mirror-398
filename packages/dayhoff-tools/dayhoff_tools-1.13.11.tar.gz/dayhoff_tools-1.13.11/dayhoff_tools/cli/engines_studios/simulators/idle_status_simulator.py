#!/usr/bin/env python3
"""Simulator for engine status output - iterate on design locally without AWS.

This lets you quickly see how the status command output looks under different
engine states and sensor combinations.

Usage:
    python dayhoff_tools/cli/engines_studios/idle_status_simulator.py                    # Show all scenarios
    python dayhoff_tools/cli/engines_studios/idle_status_simulator.py --scenario idle    # Show specific scenario
    python dayhoff_tools/cli/engines_studios/idle_status_simulator.py --colorful         # Use more emojis
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone

# Import standalone utilities
from pathlib import Path

simulator_dir = Path(__file__).parent
sys.path.insert(0, str(simulator_dir))
from simulator_utils import format_idle_state, format_time_ago


def generate_scenarios():
    """Generate various test scenarios for status output."""

    scenarios = {}

    # Scenario 1: Completely idle engine
    scenarios["idle"] = {
        "name": "Completely Idle Engine",
        "status_data": {
            "name": "alice-work",
            "instance_id": "i-0123456789abcdef0",
            "instance_type": "t3a.xlarge",
            "state": "running",
            "public_ip": "54.123.45.67",
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(hours=2)
            ).isoformat(),
            "idle_state": {
                "is_idle": True,
                "reason": "All sensors report idle",
                "idle_seconds": 450,
                "timeout_seconds": 1800,
                "sensors": {
                    "coffee": {
                        "active": False,
                        "confidence": "HIGH",
                        "reason": "No coffee lock",
                        "details": {},
                    },
                    "ssh": {
                        "active": False,
                        "confidence": "HIGH",
                        "reason": "No active SSH sessions",
                        "details": {},
                    },
                    "ide": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "reason": "No IDE connections detected (after 3 checks)",
                        "details": {},
                    },
                    "docker": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "reason": "No workload containers",
                        "details": {"ignored": []},  # Empty list - should not display
                    },
                },
            },
            "attached_studios": [],
        },
    }

    # Scenario 2: Active with SSH and Docker
    scenarios["active_ssh_docker"] = {
        "name": "Active: SSH + Docker Workloads",
        "status_data": {
            "name": "bob-training",
            "instance_id": "i-0fedcba987654321",
            "instance_type": "g5.4xlarge",
            "state": "running",
            "public_ip": "34.234.56.78",
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(minutes=45)
            ).isoformat(),
            "idle_state": {
                "is_idle": False,
                "reason": "ssh: 2 SSH session(s), docker: 3 workload container(s)",
                "idle_seconds": 0,
                "timeout_seconds": 1800,
                "sensors": {
                    "coffee": {
                        "active": False,
                        "confidence": "HIGH",
                        "reason": "No coffee lock",
                        "details": {},
                    },
                    "ssh": {
                        "active": True,
                        "confidence": "HIGH",
                        "reason": "2 SSH session(s)",
                        "details": {
                            "sessions": [
                                "bob pts/0 2025-11-13 14:30 old 12345",
                                "alice pts/1 2025-11-13 15:00 old 67890",
                            ]
                        },
                    },
                    "ide": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "reason": "No IDE connections detected",
                        "details": {},
                    },
                    "docker": {
                        "active": True,
                        "confidence": "MEDIUM",
                        "reason": "3 workload container(s)",
                        "details": {
                            "containers": [
                                "training-job-1",
                                "tensorboard",
                                "jupyter-lab",
                            ],
                            "ignored": [
                                "ecs-agent (AWS system container)",
                                "devcontainer (dev-container)",
                            ],
                        },
                    },
                },
            },
            "attached_studios": [{"user": "bob", "studio_id": "vol-0123456789abcdef0"}],
        },
    }

    # Scenario 3: Active with IDE only
    scenarios["active_ide"] = {
        "name": "Active: IDE Connection Only",
        "status_data": {
            "name": "charlie-dev",
            "instance_id": "i-0abc123def456789",
            "instance_type": "t3a.xlarge",
            "state": "running",
            "public_ip": "52.12.34.56",
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(hours=5)
            ).isoformat(),
            "idle_state": {
                "is_idle": False,
                "reason": "ide: 2 IDE(s):",
                "idle_seconds": 0,
                "timeout_seconds": 1800,
                "sensors": {
                    "coffee": {
                        "active": False,
                        "confidence": "HIGH",
                        "reason": "No coffee lock",
                        "details": {},
                    },
                    "ssh": {
                        "active": False,
                        "confidence": "HIGH",
                        "reason": "No SSH sessions",
                        "details": {},
                    },
                    "ide": {
                        "active": True,
                        "confidence": "MEDIUM",
                        "reason": "2 IDE(s):",
                        "details": {
                            "unique_flavor_count": 2,
                            "unique_pid_count": 3,
                            "flavors": ["cursor", "vscode"],
                            "connections": [
                                "PID 12345: node",
                                "PID 12346: code-server",
                                "PID 12347: cursor-server",
                            ],
                        },
                    },
                    "docker": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "reason": "No workload containers",
                        "details": {"ignored": ["ecs-agent (AWS system container)"]},
                    },
                },
            },
            "attached_studios": [
                {"user": "charlie", "studio_id": "vol-09876543210fedcba"}
            ],
        },
    }

    # Scenario 4: Coffee lock active (near timeout)
    scenarios["coffee_lock"] = {
        "name": "Active: Coffee Lock (Near Timeout)",
        "status_data": {
            "name": "diana-batch",
            "instance_id": "i-0def789abc123456",
            "instance_type": "c5.9xlarge",
            "state": "running",
            "public_ip": "18.234.56.78",
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(hours=8)
            ).isoformat(),
            "idle_state": {
                "is_idle": False,
                "reason": "coffee: Coffee lock active (15m remaining)",
                "idle_seconds": 0,
                "timeout_seconds": 1800,
                "sensors": {
                    "coffee": {
                        "active": True,
                        "confidence": "HIGH",
                        "reason": "Coffee lock active (15m remaining)",
                        "details": {
                            "expires_at": (datetime.now().timestamp() + 900)  # 15 min
                        },
                    },
                    "ssh": {
                        "active": False,
                        "confidence": "HIGH",
                        "reason": "No SSH sessions",
                        "details": {},
                    },
                    "ide": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "reason": "No IDE connections detected",
                        "details": {},
                    },
                    "docker": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "reason": "No workload containers",
                        "details": {},
                    },
                },
            },
            "attached_studios": [],
        },
    }

    # Scenario 5: Almost timed out
    scenarios["near_timeout"] = {
        "name": "Nearly Timed Out (28 min idle)",
        "status_data": {
            "name": "eve-forgotten",
            "instance_id": "i-0eeeeeeeeeeeeeeee",
            "instance_type": "t3a.xlarge",
            "state": "running",
            "public_ip": "54.234.56.89",
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(hours=3)
            ).isoformat(),
            "idle_state": {
                "is_idle": True,
                "reason": "All sensors report idle",
                "idle_seconds": 1680,  # 28 minutes
                "timeout_seconds": 1800,  # 30 minutes
                "sensors": {
                    "coffee": {
                        "active": False,
                        "confidence": "HIGH",
                        "reason": "No coffee lock",
                        "details": {},
                    },
                    "ssh": {
                        "active": False,
                        "confidence": "HIGH",
                        "reason": "No SSH sessions",
                        "details": {},
                    },
                    "ide": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "reason": "No IDE connections detected",
                        "details": {},
                    },
                    "docker": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "reason": "No workload containers",
                        "details": {},
                    },
                },
            },
            "attached_studios": [{"user": "eve", "studio_id": "vol-0eeeeeeeeeeeeeeee"}],
        },
    }

    # Scenario 6: Initializing (not ready yet)
    scenarios["initializing"] = {
        "name": "Engine Initializing (Not Ready)",
        "status_data": {
            "name": "frank-new",
            "instance_id": "i-0fffffffffffffff",
            "instance_type": "g5.xlarge",
            "state": "running",
            "public_ip": "3.123.45.67",
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(minutes=2)
            ).isoformat(),
            "readiness": {
                "ready": False,
                "status": "configuring",
                "current_stage": "installing_packages",
                "progress_percent": 50,
                "estimated_time_remaining_seconds": 90,
            },
            "idle_state": None,  # Not available yet
            "attached_studios": [],
        },
    }

    # Scenario 7: Stopped engine
    scenarios["stopped"] = {
        "name": "Stopped Engine",
        "status_data": {
            "name": "george-stopped",
            "instance_id": "i-0aaaaaaaaaaaaaaaa",
            "instance_type": "t3a.xlarge",
            "state": "stopped",
            "public_ip": None,
            "launch_time": (
                datetime.now(timezone.utc) - timedelta(hours=4)
            ).isoformat(),
            "idle_state": {
                "is_idle": True,
                "reason": "All sensors report idle",
                "idle_seconds": 1800,
                "timeout_seconds": 1800,
                "sensors": {
                    "coffee": {
                        "active": False,
                        "confidence": "HIGH",
                        "reason": "No coffee lock",
                        "details": {},
                    },
                    "ssh": {
                        "active": False,
                        "confidence": "HIGH",
                        "reason": "No SSH sessions",
                        "details": {},
                    },
                    "ide": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "reason": "No IDE connections",
                        "details": {},
                    },
                    "docker": {
                        "active": False,
                        "confidence": "MEDIUM",
                        "reason": "No workload containers",
                        "details": {},
                    },
                },
            },
            "attached_studios": [],
        },
    }

    return scenarios


def display_scenario(name, scenario_data, detailed=True):
    """Display a single scenario in formatted output."""
    status = scenario_data["status_data"]

    print(f"\n{'='*80}")
    print(f" SCENARIO: {scenario_data['name']}")
    print(f"{'='*80}\n")

    # Basic info
    print(f"Engine: \033[34m{status['name']}\033[0m")  # Blue engine name
    print(f"Instance ID: {status['instance_id']}")
    print(f"Type: {status['instance_type']}")

    # Show state in red if stopped, normal otherwise
    engine_state = status["state"]
    if engine_state.lower() in ["stopped", "stopping", "terminated", "terminating"]:
        print(f"State: \033[31m{engine_state}\033[0m")  # Red for stopped
    else:
        print(f"State: {engine_state}")

    if status.get("public_ip"):
        print(f"Public IP: {status['public_ip']}")

    if status.get("launch_time"):
        print(f"Launched: {format_time_ago(status['launch_time'])}")

    # Check if engine is stopped - don't show idle state or activity sensors
    if engine_state.lower() in ["stopped", "stopping", "terminated", "terminating"]:
        print()  # Extra newline for readability
        return

    # Show readiness if not ready
    if status.get("readiness") and not status["readiness"].get("ready"):
        readiness = status["readiness"]
        print(f"\n⏳ Initialization: {readiness.get('progress_percent', 0)}%")
        print(f"Current Stage: {readiness.get('current_stage', 'unknown')}")
        if readiness.get("estimated_time_remaining_seconds"):
            remaining = readiness["estimated_time_remaining_seconds"]
            print(f"Estimated Time Remaining: {remaining}s")

    # Show idle state (only for running engines)
    if status.get("idle_state"):
        attached_studios = status.get("attached_studios", [])
        print(
            f"\n{format_idle_state(status['idle_state'], detailed=detailed, attached_studios=attached_studios)}"
        )

    print()  # Extra newline for readability


def main():
    parser = argparse.ArgumentParser(
        description="Simulator for engine status output design iteration"
    )
    parser.add_argument(
        "--scenario",
        help="Show specific scenario (idle, active_ssh_docker, active_ide, coffee_lock, near_timeout, initializing, stopped)",
        type=str,
    )
    parser.add_argument(
        "--simple", action="store_true", help="Show simple (non-detailed) output"
    )
    parser.add_argument(
        "--colorful",
        action="store_true",
        help="Use more emojis and colors (future: implement enhanced formatting)",
    )

    args = parser.parse_args()

    scenarios = generate_scenarios()

    if args.scenario:
        if args.scenario not in scenarios:
            print(f"❌ Unknown scenario: {args.scenario}")
            print(f"Available scenarios: {', '.join(scenarios.keys())}")
            return 1

        display_scenario(
            args.scenario, scenarios[args.scenario], detailed=not args.simple
        )
    else:
        # Show all scenarios
        print("\n" + "=" * 80)
        print(" ENGINE STATUS OUTPUT SIMULATOR")
        print("=" * 80)
        print("\nShowing all scenarios. Use --scenario <name> to see just one.")
        print("Use --simple to see non-detailed output.")
        print()

        for name, scenario_data in scenarios.items():
            display_scenario(name, scenario_data, detailed=not args.simple)

    if args.colorful:
        print("\n💡 TIP: --colorful flag noted! Implement enhanced formatting by:")
        print("   1. Edit format_idle_state() in progress.py")
        print("   2. Re-run this simulator to see changes")
        print("   3. No AWS calls needed - iterate quickly!\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
