#!/bin/bash
# Demo script to showcase all CLI output simulators

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                  CLI Output Simulators Demo                                ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "These simulators let you iterate on CLI design without AWS access."
echo ""

read -p "Press Enter to start the demo..."

# Engine List Simulator
echo ""
echo "┌────────────────────────────────────────────────────────────────────────────┐"
echo "│ 1. ENGINE LIST - Few engines in different states                          │"
echo "└────────────────────────────────────────────────────────────────────────────┘"
echo ""
python engine_list_simulator.py --scenario few
read -p "Press Enter to continue..."

# Engine Status - Running with activity
echo ""
echo "┌────────────────────────────────────────────────────────────────────────────┐"
echo "│ 2. ENGINE STATUS - Running engine with SSH, IDE, and Coffee active        │"
echo "└────────────────────────────────────────────────────────────────────────────┘"
echo ""
python engine_status_simulator.py --scenario running_active
read -p "Press Enter to continue..."

# Engine Status - Stopped
echo ""
echo "┌────────────────────────────────────────────────────────────────────────────┐"
echo "│ 3. ENGINE STATUS - Stopped engine (no idle detection)                     │"
echo "└────────────────────────────────────────────────────────────────────────────┘"
echo ""
python engine_status_simulator.py --scenario stopped
read -p "Press Enter to continue..."

# Studio Status - Attached
echo ""
echo "┌────────────────────────────────────────────────────────────────────────────┐"
echo "│ 4. STUDIO STATUS - Studio attached to engine                              │"
echo "└────────────────────────────────────────────────────────────────────────────┘"
echo ""
python studio_status_simulator.py --scenario attached
read -p "Press Enter to continue..."

# Idle Status - Coffee lock
echo ""
echo "┌────────────────────────────────────────────────────────────────────────────┐"
echo "│ 5. IDLE STATUS - Engine with coffee lock active                           │"
echo "└────────────────────────────────────────────────────────────────────────────┘"
echo ""
python idle_status_simulator.py --scenario coffee_lock
read -p "Press Enter to continue..."

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                           Demo Complete!                                   ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Try running simulators with different scenarios:"
echo "  • python engine_list_simulator.py --scenario many"
echo "  • python engine_status_simulator.py --scenario running_docker"
echo "  • python studio_status_simulator.py --scenario all"
echo "  • python idle_status_simulator.py --scenario all"
echo ""
echo "See README.md for full documentation."

