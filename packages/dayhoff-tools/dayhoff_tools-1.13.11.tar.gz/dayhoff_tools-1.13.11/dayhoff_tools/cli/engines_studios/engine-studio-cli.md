# Engine & Studio CLI Commands (v2)

Comprehensive CLI for managing ephemeral compute engines and persistent studio volumes with **real-time progress tracking and enhanced observability**.

## Overview

This is the **new implementation** of the engines/studios CLI, currently accessed via `dh engine2` and `dh studio2` during the migration period.

### Key Improvements Over v1
- ✅ **Real-time progress tracking** for launch and attach operations
- ✅ **Detailed idle detector visibility** with sensor-level information
- ✅ **Click-based architecture** for better composability
- ✅ **Comprehensive error messages** with actionable guidance
- ✅ **Environment flag support** across all commands

### Command Migration

**Current (during transition):**
- `dh engine` / `dh studio` → Legacy Typer-based commands (v1)
- `dh engine2` / `dh studio2` → New Click-based commands with progress (v2)

**After production deployment:**
- `dh engine2` will become `dh engine`
- `dh studio2` will become `dh studio`
- v1 commands will be deprecated

### System Components
- **Engines**: Ephemeral EC2 instances for compute (CPU, GPU types)
- **Studios**: Persistent EBS volumes that attach/detach from engines
- **Auto-shutdown**: Modular idle detection prevents runaway costs
- **Progress APIs**: Real-time status updates during async operations

## Global Options

All commands support:
- `--env <dev|sand|prod>` - Target environment (default: dev)
- `--help` - Show command help

## Engine Commands

### Lifecycle Management

#### `dh engine2 launch`

Launch a new engine and wait for it to be ready with real-time progress tracking.

**Usage:**
```bash
dh engine2 launch <name> --type <type> [options]
```

**Arguments:**
- `name` - Unique name for the engine (used for SSH, identification)

**Options:**
- `--type <type>` - **Required.** Engine type:
  - `cpu` - r6i.2xlarge (8 vCPU, 64GB RAM)
  - `cpumax` - r7i.8xlarge (32 vCPU, 256GB RAM)
  - `t4` - g4dn.2xlarge (T4 GPU, 16GB VRAM)
  - `a10g` - g5.2xlarge (A10G GPU, 24GB VRAM)
  - `a100` - p4d.24xlarge (8x A100, 40GB VRAM each)
  - `4_t4`, `8_t4` - Multi-GPU T4 instances
  - `4_a10g`, `8_a10g` - Multi-GPU A10G instances
- `--size <GB>` - Boot disk size in GB (optional)
- `--user <username>` - User to launch engine for (defaults to current user, use for testing/admin)
- `--no-wait` - Return immediately without waiting for readiness
- `-y, --yes` - Skip confirmation for non-dev environments
- `--env <env>` - Target environment (default: dev)

**Examples:**
```bash
# Launch CPU engine for development
dh engine2 launch dev-work --type cpu

# Launch GPU engine with custom disk size
dh engine2 launch training-job --type a10g --size 200

# Launch without waiting (check status later)
dh engine2 launch batch-worker --type cpumax --no-wait

# Launch engine for test user (testing/admin)
dh engine2 launch e2e-engine --type cpu --user testuser1
```

**Output with progress tracking:**
```
🚀 Launching cpu engine 'my-engine'...
✓ EC2 instance launched: i-1234567890abcdef0

⏳ Waiting for engine to be ready (typically 2-3 minutes)...

Progress ████████████░░░░░░░░░░ 60%
  [5s] Instance Running
  [8s] Downloading Scripts
  [15s] Installing Packages
  [22s] Mounting Primordial Drive
  [45s] Configuring Idle Detector
  [52s] Finalizing

✓ Engine ready!

Connect with:
  dh engine2 config-ssh  # Add to SSH config
  ssh my-engine          # Then use native SSH
```

**Bootstrap stages (9 total):**
1. Instance running
2. Downloading scripts
3. Installing packages
4. Mounting Primordial Drive
5. Installing GPU drivers (if applicable)
6. Creating environment
7. Configuring idle detector
8. Configuring SSH (passwordless access for IDE connections)
9. Ready

**Bootstrap time:**
- CPU: 1-2 minutes
- GPU (first boot): 3-5 minutes (driver installation + reboot)
- GPU (from GAMI): 1-2 minutes

---

#### `dh engine2 start`

Start a stopped engine.

**Usage:**
```bash
dh engine2 start <name-or-id> [options]
```

**Arguments:**
- `name-or-id` - Engine name or EC2 instance ID

**Options:**
- `--no-wait` - Return immediately without waiting for readiness
- `--skip-ssh-config` - Don't automatically update SSH config
- `-y, --yes` - Skip confirmation for non-dev environments
- `--env <env>` - Target environment

**Examples:**
```bash
dh engine2 start my-engine
dh engine2 start i-1234567890abcdef0
```

**Output:**
```
Starting engine 'my-engine'...
✓ Engine 'my-engine' is starting
```

**Note:** Starting an engine does not re-run bootstrap. The engine resumes from its previous state.

---

#### `dh engine2 stop`

Stop a running engine (keeps EBS boot disk).

**Usage:**
```bash
dh engine2 stop <name-or-id> [options]
```

**Arguments:**
- `name-or-id` - Engine name or EC2 instance ID

**Options:**
- `-y, --yes` - Skip confirmation for non-dev environments
- `--env <env>` - Target environment

**Examples:**
```bash
dh engine2 stop my-engine
```

**Output:**
```
Stopping engine 'my-engine'...
✓ Engine 'my-engine' is stopping
```

**Note:** Stopped engines still incur EBS storage costs (~$0.08/GB-month for boot disk). Studios must be detached before stopping.

---

#### `dh engine2 terminate`

Permanently terminate an engine (deletes EBS boot disk).

**Usage:**
```bash
dh engine2 terminate <name-or-id> [options]
```

**Arguments:**
- `name-or-id` - Engine name or EC2 instance ID

**Options:**
- `-y, --yes` - Skip confirmation prompt
- `--env <env>` - Target environment

**Examples:**
```bash
# With confirmation
dh engine2 terminate my-engine

# Skip confirmation
dh engine2 terminate my-engine -y
```

**Output:**
```
Terminate engine 'my-engine' (i-1234567890abcdef0)? [y/N]: y
✓ Engine 'my-engine' is terminating
```

**Warning:** This permanently deletes the engine's boot disk. Any data not in studios or Primordial Drive will be lost.

---

### Status and Information

#### `dh engine2 status`

Show comprehensive engine status including idle detector state with real-time sensor data.

**Usage:**
```bash
dh engine2 status <name-or-id> [options]
```

**Arguments:**
- `name-or-id` - Engine name or EC2 instance ID

**Options:**
- `--detailed` - Show detailed sensor information with confidence levels
- `--env <env>` - Target environment

**Examples:**
```bash
# Basic status
dh engine2 status my-engine

# Detailed status with sensor breakdown
dh engine2 status my-engine --detailed
```

**Output (basic):**
```
Engine: my-engine
Instance ID: i-1234567890abcdef0
Type: cpu
State: running
Public IP: 54.123.45.67
Launched: 2 hours ago

Idle Status: 🟢 ACTIVE
Reason: ssh: 1 active SSH session(s)
```

**Output (detailed):**
```
Engine: my-engine
Instance ID: i-1234567890abcdef0
Type: cpu
State: running

Idle Status: 🟢 ACTIVE
Reason: ssh: 1 active SSH session(s)

============================================================
Activity Sensors:
============================================================

✓ SSH (HIGH confidence)
  1 active SSH session(s)
  sessions:
    - alice pts/0 2025-11-10 14:30 old 12345

✗ IDE (MEDIUM confidence)
  No IDE connections found

✗ DOCKER (MEDIUM confidence)
  No workload containers
  ignored:
    - devcontainer-1 (dev-container)

✗ COFFEE (HIGH confidence)
  No coffee lock
```

**Idle detector sensors:**
- **SSH** (HIGH confidence) - Detects active SSH sessions via `who -u`
- **IDE** (MEDIUM confidence) - Detects VS Code/Cursor remote connections
- **Docker** (MEDIUM confidence) - Detects non-dev workload containers
- **Coffee** (HIGH confidence) - Explicit user keep-alive lock

---

#### `dh engine2 list`

List all engines in the environment.

**Usage:**
```bash
dh engine2 list [--env <env>]
```

**Examples:**
```bash
# List engines in dev
dh engine2 list

# List engines in sand
dh engine2 list --env sand
```

**Output:**
```

Engines for AWS Account dev
╭──────────────┬─────────────┬─────────────┬─────────────┬─────────────────────╮
│ Name         │ State       │ User        │ Type        │ Instance ID         │
├──────────────┼─────────────┼─────────────┼─────────────┼─────────────────────┤
│ alice-work   │ running     │ alice       │ cpu         │ i-0123456789abcdef0 │
│ bob-training │ running     │ bob         │ a10g        │ i-0fedcba987654321  │
│ batch-worker │ stopped     │ charlie     │ cpumax      │ i-0abc123def456789  │
╰──────────────┴─────────────┴─────────────┴─────────────┴─────────────────────╯
Total: 3

```

**Formatting:**
- Full table borders with Unicode box-drawing characters
- Engine names are displayed in blue
- State is color-coded: green for "running", yellow for "starting/stopping", grey for "stopped"
- Instance IDs are displayed in grey
- Name column width adjusts dynamically to fit the longest engine name

---

### Access

#### `dh engine2 config-ssh`

Update `~/.ssh/config` with entries for all running engines.

**Usage:**
```bash
dh engine2 config-ssh [options]
```

**Options:**
- `--clean` - Remove all managed entries (doesn't add new ones)
- `--all` - Include engines from all users (default: only your engines)
- `--admin` - Use `ec2-user` instead of owner username
- `--env <env>` - Target environment

**Examples:**
```bash
# Add your running engines
dh engine2 config-ssh

# Add all engines (all users)
dh engine2 config-ssh --all

# Remove managed entries
dh engine2 config-ssh --clean

# Add engines as admin user
dh engine2 config-ssh --admin
```

**Output:**
```
✓ Updated SSH config with 3 engine(s)
```

**Managed section in ~/.ssh/config:**
```
# BEGIN DAYHOFF ENGINES

Host my-engine
    HostName i-1234567890abcdef0
    User alice
    ProxyCommand aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p' --profile dev-devaccess

# END DAYHOFF ENGINES
```

**Note**: The `--profile` flag is automatically added based on `--env`:
- `--env dev` → `--profile dev-devaccess`
- `--env sand` → `--profile sand-devaccess`
- `--env prod` → `--profile prod-devaccess`

This ensures GUI applications like VS Code and Cursor can connect without inheriting shell environment variables.

**Usage after config - Standard SSH:**
```bash
# Interactive SSH
ssh my-engine

# Execute remote commands
ssh my-engine "ls /studios"

# File transfer
scp local-file my-engine:/studios/alice/
rsync -avz project/ my-engine:/studios/alice/project/

# Port forwarding
ssh -L 8080:localhost:8080 my-engine

# VS Code Remote SSH
code --remote ssh-remote+my-engine /studios/alice/project

# VS Code Remote - Tunnels
code tunnel --name my-engine
```

**All standard SSH features work:**
- Command execution: `ssh <engine> "<command>"`
- File transfer: `scp`, `rsync`, `sftp`
- Port forwarding: `-L`, `-R`, `-D` flags
- IDE remote development: VS Code, Cursor, PyCharm
- SSH agent forwarding: `-A` flag
- Config file options: ControlMaster, compression, etc.

**Recommended workflow:**
1. Run `dh engine2 config-ssh` once after launching engines
2. Use native `ssh <engine-name>` for all access
3. Rerun `config-ssh` if you launch new engines

---

### Idle Detection Control

#### `dh engine2 coffee`

Set or cancel a "coffee lock" to prevent idle shutdown.

**Usage:**
```bash
dh engine2 coffee <name-or-id> <duration> [options]
dh engine2 coffee <name-or-id> --cancel [options]
```

**Arguments:**
- `name-or-id` - Engine name or EC2 instance ID
- `duration` - How long to keep alive (e.g., `4h`, `2h30m`, `45m`)

**Options:**
- `--cancel` - Cancel existing coffee lock
- `--env <env>` - Target environment

**Examples:**
```bash
# Keep alive for 4 hours
dh engine2 coffee my-engine 4h

# Keep alive for 2.5 hours
dh engine2 coffee my-engine 2h30m

# Cancel coffee lock
dh engine2 coffee my-engine --cancel
```

**Output:**
```
✓ Coffee lock set for 'my-engine': 4h
```

**Use cases:**
- Long-running training jobs without active SSH
- Batch processing where idle detector might trigger
- Overnight jobs that don't show activity

**Note:** Coffee lock is HIGH confidence - overrides all other sensors.

---

#### `dh engine2 idle`

Show or configure idle timeout settings.

**Usage:**
```bash
dh engine2 idle <name-or-id> [options]
```

**Arguments:**
- `name-or-id` - Engine name or EC2 instance ID

**Options:**
- `--set <duration>` - Set new timeout (e.g., `2h`, `45m`)
- `--slack <none|default|all>` - Configure Slack notifications
- `--env <env>` - Target environment

**Examples:**
```bash
# Show current settings
dh engine2 idle my-engine

# Set 2-hour timeout
dh engine2 idle my-engine --set 2h

# Configure Slack notifications
dh engine2 idle my-engine --slack all
```

**Output:**
```
Idle Settings for 'my-engine':
  Timeout: 30 minutes
  Current State: ACTIVE
```

**Default timeout:** 30 minutes (1800 seconds)

---

### Maintenance

#### `dh engine2 resize`

Resize an engine's boot disk.

**Usage:**
```bash
dh engine2 resize <name-or-id> --size <GB> [options]
```

**Arguments:**
- `name-or-id` - Engine name or EC2 instance ID

**Options:**
- `-s, --size <GB>` - **Required.** New size in GB
- `--online` - Resize while running (requires manual filesystem expansion)
- `-f, --force` - Skip confirmation
- `--env <env>` - Target environment

**Examples:**
```bash
# Offline resize (requires stop/start)
dh engine2 resize my-engine --size 200 --force

# Online resize (advanced)
dh engine2 resize my-engine --size 200 --online --force
```

**Output (offline resize):**
```
✓ Boot disk resize initiated for 'my-engine'
  Engine will be stopped and restarted
  Filesystem will be automatically expanded
```

**Output (online resize):**
```
✓ Boot disk resize initiated for 'my-engine'

⚠ Manual filesystem expansion required:
  ssh my-engine
  sudo growpart /dev/nvme0n1 1
  sudo xfs_growfs /
  df -h  # Verify new size
```

**Note:** Online resize keeps the engine running but requires manual steps. Offline resize (default) stops/starts the engine but handles filesystem expansion automatically.

---

#### `dh engine2 debug`

Debug engine bootstrap status and show detailed stage information.

**Usage:**
```bash
dh engine2 debug <name-or-id> [--env <env>]
```

**Arguments:**
- `name-or-id` - Engine name or EC2 instance ID

**Examples:**
```bash
dh engine2 debug my-engine
```

**Output:**
```
Engine: i-1234567890abcdef0
Ready: False
Current Stage: installing_packages

Bootstrap Stages:
  ✓ 1. instance_running (30.0s)
  ✓ 2. downloading_scripts (8.0s)
  ⏳ 3. installing_packages
```

**Use case:** Troubleshooting stuck or failed bootstrap. Shows exactly which stage failed and timing information.

---

## Studio Commands

### Lifecycle Management

#### `dh studio2 create`

Create a new studio for the current user (or specified user with `--user` flag).

**Usage:**
```bash
dh studio2 create [options]
```

**Options:**
- `--size <GB>` - Studio size in GB (default: 100)
- `--user <username>` - User to create studio for (defaults to current user, use for testing/admin)
- `--env <env>` - Target environment

**Examples:**
```bash
# Create 100GB studio (default)
dh studio2 create

# Create 200GB studio
dh studio2 create --size 200

# Create studio for test user (testing/admin)
dh studio2 create --user testuser1 --size 50
```

**Output:**
```
Creating 100GB studio for alice...
✓ Studio created: vol-0123456789abcdef0

Attach to an engine with:
  dh studio2 attach <engine-name>
```

**Limits:**
- One studio per user per environment
- Studio is encrypted with AWS-managed keys
- Billed at ~$0.08/GB-month for EBS storage

---

#### `dh studio2 delete`

Delete your studio (or another user's studio with `--user` flag).

**Usage:**
```bash
dh studio2 delete [options]
```

**Options:**
- `-y, --yes` - Skip confirmation
- `--user <username>` - User whose studio to delete (defaults to current user, use for testing/admin)
- `--env <env>` - Target environment

**Examples:**
```bash
# With confirmation
dh studio2 delete

# Skip confirmation
dh studio2 delete -y

# Delete another user's studio (testing/admin)
dh studio2 delete --user testuser1 -y
```

**Warning prompt:**
```
⚠ WARNING: This will permanently delete all data in vol-0123456789abcdef0
Are you sure? [y/N]:
```

**Output:**
```
✓ Studio vol-0123456789abcdef0 deleted
```

**Requirements:**
- Studio must be detached (`dh studio2 detach` first)
- All data in the studio will be permanently lost

---

### Status and Information

#### `dh studio2 status`

Show information about your studio.

**Usage:**
```bash
dh studio2 status [--env <env>]
```

**Examples:**
```bash
dh studio2 status
```

**Output (available):**
```
Studio ID: vol-0123456789abcdef0
User: alice
Size: 100GB
Status: available
Created: 5 days ago
```

**Output (attached):**
```
Studio ID: vol-0123456789abcdef0
User: alice
Size: 100GB
Status: attached
Created: 5 days ago
Attached to: i-0fedcba987654321
```

**Statuses:**
- `available` - Ready to attach
- `attached` - Attached to an engine
- `attaching` - Attachment in progress
- `detaching` - Detachment in progress
- `error` - Stuck state (use `dh studio2 reset`)

---

#### `dh studio2 list`

List all studios in the environment.

**Usage:**
```bash
dh studio2 list [--env <env>]
```

**Examples:**
```bash
dh studio2 list
```

**Output:**
```

Studios for AWS Account dev
╭────────┬──────────────┬──────────────┬───────────┬───────────────────────────╮
│ User   │ Status       │ Attached To  │ Size      │ Studio ID                 │
├────────┼──────────────┼──────────────┼───────────┼───────────────────────────┤
│ alice  │ attached     │ alice-work   │ 100GB     │ vol-0123456789abcdef0     │
│ bob    │ available    │ -            │ 200GB     │ vol-0fedcba987654321      │
│ carol  │ attaching    │ carol-gpu    │ 150GB     │ vol-0abc123def456789      │
╰────────┴──────────────┴──────────────┴───────────┴───────────────────────────╯
Total: 3

```

**Formatting:**
- Full table borders with Unicode box-drawing characters
- User names are displayed in blue
- Status is color-coded: purple for "attached", green for "available", yellow for "attaching/detaching", red for "error"
- "Attached To" shows engine name, or "-" if not attached
- Studio IDs are displayed in grey
- User column width adjusts dynamically to fit the longest username
- Attached To column width adjusts dynamically to fit the longest engine name
- Columns are ordered: User, Status, Attached To, Size, Studio ID

---

### Attachment

#### `dh studio2 attach`

Attach your studio to an engine with real-time progress tracking through all 6 attachment stages.

**Usage:**
```bash
dh studio2 attach <engine-name-or-id> [--env <env>]
```

**Arguments:**
- `engine-name-or-id` - Engine name or EC2 instance ID

**Examples:**
```bash
dh studio2 attach my-engine
```

**Output with progress tracking:**
```
📎 Attaching studio to my-engine...

⏳ Attachment in progress...

Progress ████████████████████ 100%
  Validate Engine
  Find Device Slot
  Attach Volume
  Resolve Device
  Mount Filesystem
  Update State

✓ Studio attached successfully!

Your files are now available at:
  /studios/alice/

Connect with:
  ssh my-engine
```

**6-step attachment process:**
1. **Validate Engine** - Ensure engine is ready (~250ms)
2. **Find Device Slot** - Locate available `/dev/sd[f-p]` (~150ms)
3. **Attach Volume** - AWS EBS attachment (~8-10s)
4. **Resolve Device** - Map to NVMe device path via `/dev/disk/by-id/` (~2s)
5. **Mount Filesystem** - Execute mount script via SSM RunCommand (~5s)
6. **Update State** - Mark studio as `attached` in DynamoDB (~200ms)

**Total time:** ~15-20 seconds

**Requirements:**
- Studio must be in `available` status
- Engine must be in `ready` state
- Engine can have max 10 studios attached (device slots)

**Error handling:**
If attachment fails, shows detailed error with failed step:
```
✗ Attachment failed: Mount filesystem timeout

Failed at step: mount_filesystem
Error: SSM command timeout after 30s
```

---

#### `dh studio2 detach`

Detach your studio from its engine.

**Usage:**
```bash
dh studio2 detach [--env <env>]
```

**Examples:**
```bash
dh studio2 detach
```

**Output:**
```
Detaching studio vol-0123456789abcdef0...
✓ Studio detached
```

**Process:**
1. Clean unmount with `sync`
2. AWS EBS detachment
3. Update studio status to `available`

**Use cases:**
- Moving studio to a different engine
- Shutting down engine but preserving studio data
- Preparing for studio deletion or resize

---

### Maintenance

#### `dh studio2 resize`

Resize your studio volume (requires detachment).

**Usage:**
```bash
dh studio2 resize --size <GB> [options]
```

**Options:**
- `-s, --size <GB>` - **Required.** New size in GB
- `-y, --yes` - Skip confirmation
- `--user <username>` - User whose studio to resize (defaults to current user, use for testing/admin)
- `--env <env>` - Target environment

**Examples:**
```bash
# With confirmation
dh studio2 resize --size 200

# Skip confirmation
dh studio2 resize --size 200 -y

# Resize test user's studio (testing/admin)
dh studio2 resize --size 200 -y --user testuser1
```

**Output:**
```
Resize studio from 100GB to 200GB? [y/N]: y
✓ Studio resize initiated: 100GB → 200GB
```

**Requirements:**
- Studio must be detached
- New size must be larger than current size (no shrinking)
- Filesystem automatically expands on next attach

**Note:** You're billed for the new size immediately (~$0.08/GB-month).

---

#### `dh studio2 reset`

Reset a stuck studio to `available` status (admin operation).

**Usage:**
```bash
dh studio2 reset [options]
```

**Options:**
- `-y, --yes` - Skip confirmation
- `--user <username>` - User whose studio to reset (defaults to current user, use for testing/admin)
- `--env <env>` - Target environment

**Examples:**
```bash
# Reset your own studio (with confirmation)
dh studio2 reset

# Skip confirmation
dh studio2 reset -y

# Reset test user's studio (testing/admin)
dh studio2 reset -y --user testuser1
```

**Output:**
```
Studio: vol-0123456789abcdef0
Current Status: attaching

Reset studio status to 'available'? [y/N]: y
✓ Studio reset to 'available' status
  Note: Manual cleanup may be required on engines
```

**Use cases:**
- Studio stuck in `attaching` or `detaching`
- Attachment operation failed and didn't revert
- DynamoDB state out of sync with actual state

**Warning:** This only resets the DynamoDB state. If the volume is actually attached, you'll need to manually detach via AWS console or unmount on the engine.

---

## Common Workflows

### Daily Development

```bash
# Launch engine
dh engine2 launch dev-work --type cpu

# Add to SSH config
dh engine2 config-ssh

# Create studio (first time only)
dh studio2 create --size 100

# Attach studio
dh studio2 attach dev-work

# Connect with native SSH
ssh dev-work

# When done, detach and terminate
dh studio2 detach
dh engine2 terminate dev-work -y
```

### GPU Training with Coffee Lock

```bash
# Launch GPU engine
dh engine2 launch training --type a10g

# Add to SSH config
dh engine2 config-ssh

# Set coffee lock for long job
dh engine2 coffee training 8h

# Attach and start work
dh studio2 attach training
ssh training

# Job runs without idle shutdown
# When done:
dh engine2 coffee training --cancel
dh studio2 detach
dh engine2 terminate training -y
```

### Multi-Engine Development

```bash
# Launch multiple engines
dh engine2 launch frontend --type cpu
dh engine2 launch backend --type cpu
dh engine2 launch ml --type t4

# Update SSH config for easy access
dh engine2 config-ssh

# Now use direct SSH
ssh frontend
ssh backend
ssh ml
```

### Monitoring Idle Detection

```bash
# Check basic idle status
dh engine2 status my-engine

# Check detailed sensor information
dh engine2 status my-engine --detailed

# Shows all 4 sensors with confidence levels:
# - SSH (HIGH)
# - IDE (MEDIUM)
# - Docker (MEDIUM)
# - Coffee (HIGH)
```

---

## Error Handling

### Common Errors

**"You already have a studio"**
```bash
✗ You already have a studio: vol-0123456789abcdef0
   Use 'dh studio2 delete' to remove it first
```
Solution: Delete existing studio or use existing one.

**"Studio must be detached before deletion"**
```bash
✗ Studio must be detached before deletion
  Run: dh studio2 detach
```
Solution: Detach studio first.

**"Studio is not available"**
```bash
✗ Studio is not available (status: attaching)
```
Solution: Wait for current operation to complete or use `dh studio2 reset`.

**"Could not fetch API URL"**
```bash
✗ Could not fetch API URL from /dev/studio-manager/api-url
```
Solution: Ensure you're authenticated to AWS and the environment is deployed.

**"Attachment failed"**
Shows detailed error with failed step:
```bash
✗ Attachment failed: Mount filesystem timeout

Failed at step: mount_filesystem
Error: SSM command timeout after 30s
```
Solution: Check engine is ready and SSM agent is running. Retry the attachment.

---

## Progress Tracking Features

The v2 implementation includes real-time progress tracking for long-running operations:

### Launch Progress
- Shows progress through 8 bootstrap stages
- Real-time percentage completion
- Stage timing information
- Estimated time remaining

### Attachment Progress
- Shows progress through 6 attachment steps
- Visual progress bar
- Step-by-step updates
- Detailed error reporting if failure occurs

### Status Visibility
- Real-time idle detector sensor states
- Confidence levels for each sensor
- Detailed activity information with `--detailed` flag
- Clear indication of what's keeping engine awake

---

## Idle Detection Architecture

The v2 implementation uses a modular sensor-based idle detector with confidence levels:

### 4 Independent Sensors

1. **SSH Sensor** (HIGH confidence)
   - Uses `who -u` to detect active sessions
   - Filters out system users
   - HIGH confidence: presence/absence is definitive

2. **IDE Sensor** (MEDIUM confidence)
   - Detects VS Code/Cursor remote connections
   - Uses `ss -tanpo` to inspect TCP connections
   - 3 retries to avoid false positives
   - MEDIUM confidence: connections can be transient

3. **Docker Sensor** (MEDIUM confidence)
   - Detects non-dev workload containers
   - Filters out dev containers, system images, transient patterns
   - MEDIUM confidence: heuristic-based filtering

4. **Coffee Lock Sensor** (HIGH confidence)
   - Explicit user keep-alive via `/var/run/engine-coffee`
   - Timestamp-based expiration
   - HIGH confidence: user intent is clear

### Decision Logic

Conservative fail-safe approach:
```
if any_sensor_has_high_confidence_activity:
    return ACTIVE
elif any_sensor_has_error (LOW confidence):
    return ACTIVE  # Fail safe - don't shut down on errors
elif any_sensor_has_medium_confidence_activity:
    return ACTIVE
else:
    return IDLE
```

**Philosophy:** Better to waste a bit of compute than lose user work.

### Visibility

Use `dh engine2 status --detailed` to see:
- Current state (ACTIVE/IDLE)
- Reason for current state
- All 4 sensor states with confidence levels
- Detailed activity information for each sensor

---

## Storage Tiers

| Storage | Path | Speed | Use Case |
|---------|------|-------|----------|
| Studios | `/studios/{user}/` | Fast (<1ms) | Personal code, configs, experiments |
| Primordial | `/primordial/` | Medium (1-3ms) | Shared datasets, batch I/O |
| S3 | `s3://` | Slow (~100ms) | Archives, raw data, final models |

**Primordial Drive** (shared EFS):
- Automatically mounted at `/primordial/` during bootstrap
- Intelligent-Tiering: $0.30/GB-month → $0.016/GB-month after 30 days
- Available on all engines and batch jobs
- Use for datasets shared across users

---

## Technical Implementation

### API Backend
- **18 REST endpoints** via API Gateway + Lambda
- **3 DynamoDB tables** for state management
- **Optimistic locking** prevents race conditions
- **Progress tracking** for all async operations stored in DynamoDB

### Security
- **IAM Identity Center (SSO)** for authentication
- **SSM Session Manager** for SSH (no bastion hosts)
- **Encrypted EBS volumes** for studios
- **Least-privilege IAM roles** for engines

### Monitoring
- **CloudWatch metrics** for operations
- **Slack notifications** (configurable per engine)
- **Progress APIs** for real-time status
- **Detailed logging** for debugging

---

## Migration Timeline

**Current Status:**
- v2 implementation complete and tested
- All commands available via `engine2`/`studio2`
- v1 commands remain available via `engine`/`studio`

**Production Deployment:**
1. Deploy v2 to prod environment
2. Team testing period (1-2 weeks)
3. Promote `engine2` → `engine`, `studio2` → `studio`
4. Deprecate v1 commands
5. Remove v1 code after stabilization

**Why v2?**
- Real-time progress eliminates "is it stuck?" questions
- Detailed idle detector visibility prevents false shutdowns
- Better error messages reduce debugging time
- Click architecture enables better tooling integration
