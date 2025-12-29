# CLI Output Simulators

This directory contains simulators for iterating on CLI output design without needing AWS access. They're useful for:

- Rapid UI iteration during development
- Visualizing edge cases and different states
- Testing output formatting without live infrastructure
- Documentation and examples

## Available Simulators

### 1. Engine List Simulator

Simulates `dh engine2 list` output with different configurations.

**Usage:**
```bash
# Show all scenarios
python dayhoff_tools/cli/engines_studios/simulators/engine_list_simulator.py

# Show specific scenario
python dayhoff_tools/cli/engines_studios/simulators/engine_list_simulator.py --scenario few

# Override environment
python dayhoff_tools/cli/engines_studios/simulators/engine_list_simulator.py --scenario many --env prod
```

**Scenarios:**
- `single` - Single running engine
- `few` - Few engines with mixed states (running, stopped, starting)
- `many` - Many engines (production-like)
- `empty` - No engines
- `transitions` - All transitional states (starting, stopping, pending)
- `all` - Show all scenarios

### 2. Engine Status Simulator

Simulates `dh engine2 status` output for different engine states.

**Usage:**
```bash
# Show all scenarios
python dayhoff_tools/cli/engines_studios/simulators/engine_status_simulator.py

# Show specific scenario
python dayhoff_tools/cli/engines_studios/simulators/engine_status_simulator.py --scenario running_active

# Override environment
python dayhoff_tools/cli/engines_studios/simulators/engine_status_simulator.py --scenario stopped --env sand
```

**Scenarios:**
- `running_idle` - Running engine with all sensors idle
- `running_active` - Running engine with SSH, IDE, and coffee active
- `stopped` - Stopped engine (no idle detection)
- `starting` - Engine in starting state
- `stopping` - Engine in stopping state
- `running_docker` - Running engine with Docker containers
- `all` - Show all scenarios

### 3. Studio Status Simulator

Simulates `dh studio2 status` output for different studio states.

**Usage:**
```bash
# Show all scenarios
python dayhoff_tools/cli/engines_studios/simulators/studio_status_simulator.py

# Show specific scenario
python dayhoff_tools/cli/engines_studios/simulators/studio_status_simulator.py --scenario attached

# Override environment
python dayhoff_tools/cli/engines_studios/simulators/studio_status_simulator.py --scenario large --env prod
```

**Scenarios:**
- `available` - Available studio (not attached)
- `attached` - Studio attached to an engine
- `large` - Large production studio
- `new` - Newly created studio
- `modifying` - Studio being modified
- `all` - Show all scenarios

### 4. Idle Status Simulator

Simulates detailed idle detection output with various sensor configurations.

**Usage:**
```bash
# Show all scenarios
python dayhoff_tools/cli/engines_studios/simulators/idle_status_simulator.py

# Show specific scenario
python dayhoff_tools/cli/engines_studios/simulators/idle_status_simulator.py --scenario coffee_lock

# Use more emojis
python dayhoff_tools/cli/engines_studios/simulators/idle_status_simulator.py --colorful
```

**Scenarios:**
- `idle` - Completely idle engine (all sensors inactive)
- `active_ssh_docker` - Active SSH sessions and Docker containers
- `active_ide` - Active IDE connection (Cursor)
- `coffee_lock` - Coffee lock active (prevents shutdown)
- `near_timeout` - Engine near idle timeout
- `initializing` - Engine just started (initializing state)
- `stopped` - Stopped engine (no idle detection)
- `all` - Show all scenarios

## Implementation Notes

### Standalone Design

The simulators are completely standalone and don't require:
- AWS credentials
- Network access
- Installed Python packages (beyond stdlib)

They use `simulator_utils.py` which contains formatting functions copied from the main codebase but with no external dependencies.

### Synchronization

When modifying formatting in the actual CLI code (`engine_commands.py`, `studio_commands.py`, `progress.py`), update the corresponding simulators to match:

1. **Output changes** → Update simulator `format_*_output()` functions
2. **New scenarios** → Add scenarios to `generate_scenarios()`
3. **New formatters** → Copy to `simulator_utils.py` (without dependencies)

### Color Codes

The simulators use ANSI escape codes for colors:
- `\033[32m` - Green (running states, active)
- `\033[31m` - Red (stopped/terminated)
- `\033[33m` - Yellow (transitional states, warnings)
- `\033[34m` - Blue (names, environments)
- `\033[35m` - Purple (studios)
- `\033[0m` - Reset

## Development Workflow

When designing new CLI output:

1. **Add scenarios** to the appropriate simulator
2. **Iterate quickly** by running the simulator
3. **Review output** for readability and information density
4. **Implement** in actual CLI code
5. **Update simulator** to match final implementation

This is much faster than deploying infrastructure changes and running real CLI commands for every tweak.

