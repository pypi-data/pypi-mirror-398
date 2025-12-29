"""CLI commands for cloud provider authentication and management.

This module provides commands for authenticating with GCP and AWS from within
development containers. It handles both immediate shell environment configuration
via the --export flag (deprecated for GCP) and persistent configuration via
shell RC files (AWS only) or gcloud config settings (GCP).

The implementation focuses on:
1. Unifying cloud authentication with the `dh` CLI tool
2. Maintaining persistence across shell sessions via RC file modifications (AWS)
   or gcloud config (GCP).
3. Providing similar capabilities to the shell scripts it replaces
4. For GCP, leveraging `gcloud config` and Application Default Credentials (ADC)
   updates for a streamlined, keyless, no-`eval` workflow.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import questionary
import typer

# --- Configuration ---
GCP_DEVCON_SA = "devcon@enzyme-discovery.iam.gserviceaccount.com"
GCP_PROJECT_ID = "enzyme-discovery"
AWS_DEFAULT_PROFILE = "dev-devaccess"
AWS_CONFIG_FILE = Path.home() / ".aws" / "config"
SHELL_RC_FILES = [
    Path.home() / ".bashrc",
    Path.home() / ".bash_profile",
    Path.home() / ".profile",
]

# --- Color constants for formatted output ---
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;36m"
NC = "\033[0m"  # No Color


# --- Common Helper Functions ---
def _find_executable(name: str) -> str:
    """Find the full path to an executable in PATH."""
    path = shutil.which(name)
    if not path:
        raise FileNotFoundError(
            f"{name} command not found. Please ensure it's installed."
        )
    return path


def _run_command(
    cmd_list: List[str],
    capture: bool = False,
    check: bool = True,
    suppress_output: bool = False,
) -> Tuple[int, str, str]:
    """Run a command and return its result.

    Args:
        cmd_list: List of command arguments
        capture: Whether to capture output
        check: Whether to raise on non-zero exit code
        suppress_output: Whether to hide output even if not captured

    Returns:
        Tuple of (return_code, stdout_str, stderr_str)
    """
    stdout_opt = (
        subprocess.PIPE if capture else subprocess.DEVNULL if suppress_output else None
    )
    stderr_opt = (
        subprocess.PIPE if capture else subprocess.DEVNULL if suppress_output else None
    )

    try:
        result = subprocess.run(
            cmd_list, stdout=stdout_opt, stderr=stderr_opt, check=check, text=True
        )
        return (
            result.returncode,
            result.stdout if capture else "",
            result.stderr if capture else "",
        )
    except subprocess.CalledProcessError as e:
        if capture:
            return (e.returncode, e.stdout or "", e.stderr or "")
        return (e.returncode, "", "")


def _modify_rc_files(variable: str, value: Optional[str]) -> None:
    """Add or remove an export line from RC files.

    Args:
        variable: Environment variable name
        value: Value to set, or None to remove
    """
    for rc_file in SHELL_RC_FILES:
        if not rc_file.exists():
            continue

        try:
            # Read existing content
            with open(rc_file, "r") as f:
                lines = f.readlines()

            # Filter out existing exports for this variable
            pattern = re.compile(f"^export {variable}=")
            new_lines = [line for line in lines if not pattern.match(line.strip())]

            # Add new export if value is provided
            if value is not None:
                new_lines.append(f"export {variable}={value}\n")

            # Write back to file
            with open(rc_file, "w") as f:
                f.writelines(new_lines)

        except (IOError, PermissionError) as e:
            print(f"Warning: Could not update {rc_file}: {e}", file=sys.stderr)


def _get_env_var(variable: str) -> Optional[str]:
    """Safely get an environment variable."""
    return os.environ.get(variable)


# --- GCP Functions ---

# New approach: Use gcloud config settings instead of environment variables
# for impersonation and project settings. This avoids modifying RC files
# and the need for `eval "$(dh gcp use-... --export)"`.
# ADC is updated during the initial `dh gcp login` for the user.
# Subsequent ADC updates for impersonation or user mode must be done manually
# if required by libraries, as the underlying gcloud commands can force interaction.


def _get_short_name(account: str) -> str:
    """Extracts a short name ('dma', 'devcon') from a GCP account email.

    Args:
        account: The full account string (e.g., 'dma@dayhofflabs.com',
                 'devcon@...', 'None', 'Not authenticated').

    Returns:
        The short name or the original string if not a recognized email pattern.
    """
    if account == GCP_DEVCON_SA:
        return "devcon"
    if "@" in account:
        # Attempt to get the part before @, common for user accounts
        user_part = account.split("@")[0]
        # You might want more specific logic here if user formats vary
        # For now, assume simple user name like 'dma'
        return user_part
    # Handle special strings like 'None', 'Not authenticated', etc.
    return account


def _gcloud_set_config(key: str, value: str) -> Tuple[int, str, str]:
    """Set a gcloud configuration value using `gcloud config set`.

    Args:
        key: The configuration key (e.g., 'project', 'auth/impersonate_service_account').
        value: The value to set for the key.

    Returns:
        Tuple of (return_code, stdout_str, stderr_str) from _run_command.
    """
    gcloud_path = _find_executable("gcloud")
    cmd = [gcloud_path, "config", "set", key, value, "--quiet"]
    return _run_command(cmd, capture=True, check=False, suppress_output=True)


def _gcloud_unset_config(key: str) -> Tuple[int, str, str]:
    """Unset a gcloud configuration value using `gcloud config unset`.

    Args:
        key: The configuration key to unset.

    Returns:
        Tuple of (return_code, stdout_str, stderr_str) from _run_command.
    """
    gcloud_path = _find_executable("gcloud")
    cmd = [gcloud_path, "config", "unset", key, "--quiet"]
    return _run_command(cmd, capture=True, check=False, suppress_output=True)


def _get_adc_status() -> str:
    """Check the status and type of Application Default Credentials (ADC).

    Attempts to determine the effective credential source, including the
    default GCE metadata server fallback if no explicit config is found.

    Returns:
        A short string describing the ADC principal ('dma', 'devcon',
        'default VM service account', 'Other/External', 'Not configured', etc.).
    """
    adc_file = (
        Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    )

    # Check environment variable first (highest precedence after explicit file)
    if _get_env_var("GOOGLE_APPLICATION_CREDENTIALS"):
        # We don't know *what* key it points to without reading/parsing it.
        return "Keyfile (GOOGLE_APPLICATION_CREDENTIALS)"

    # Check explicit ADC JSON file
    if adc_file.is_file():
        try:
            with open(adc_file, "r") as f:
                adc_data = json.load(f)
            cred_type = adc_data.get("type")

            if cred_type == "authorized_user":
                return "dma"  # Assuming 'dma' is the likely user
            elif cred_type == "impersonated_service_account":
                sa_url = adc_data.get("service_account_impersonation_url", "")
                sa_match = re.search(r"serviceAccounts/([^:]+)", sa_url)
                if sa_match and sa_match.group(1) == GCP_DEVCON_SA:
                    return "devcon"
                elif sa_match:
                    return f"Other SA ({_get_short_name(sa_match.group(1))})"
                else:
                    return "devcon (?)"  # Likely devcon but failed parse
            elif cred_type == "external_account":
                return "Other/External"
            elif cred_type == "service_account":
                # This type in the file usually means it was created pointing
                # to a specific key file, but not via the env var.
                # Hard to know details without parsing more.
                return "Keyfile (from ADC json)"
            else:
                return f"Unknown ({cred_type})"

        except json.JSONDecodeError:
            return "Invalid format"
        except (IOError, PermissionError, Exception) as e:
            print(f"Warning: Could not read ADC file {adc_file}: {e}", file=sys.stderr)
            return "Error reading"

    # If no env var and no JSON file, check for GCE default SA fallback
    # We infer this by checking the *CLI*'s current user status
    cli_user = _get_current_gcp_user()  # Reuse existing helper
    if cli_user == "default VM service account":
        return "default VM service account"  # ADC likely uses this via metadata

    # If none of the above, ADC is likely unconfigured for this environment
    return "Not configured"


def _is_adc_authenticated() -> bool:
    """Check if Application Default Credentials (ADC) are valid.

    Returns:
        True if `gcloud auth application-default print-access-token --quiet` succeeds,
        False otherwise.
    """
    try:
        gcloud_path = _find_executable("gcloud")
        returncode, _, _ = _run_command(
            [
                gcloud_path,
                "auth",
                "application-default",
                "print-access-token",
                "--quiet",
            ],
            capture=True,
            check=False,
            suppress_output=True,
        )
        return returncode == 0
    except FileNotFoundError:
        return False


def _is_gcp_user_authenticated() -> bool:
    """Check if the current gcloud user authentication is valid and non-interactive.

    Returns:
        True if `gcloud auth print-access-token --quiet` succeeds (exit code 0),
        False otherwise (indicating potential need for interactive login).
    """
    try:
        gcloud_path = _find_executable("gcloud")
        # Attempt to get a token silently. If this fails, login is likely expired or needs interaction.
        returncode, _, _ = _run_command(
            [gcloud_path, "auth", "print-access-token", "--quiet"],
            capture=True,  # We don't need the token, just the exit code
            check=False,  # Don't raise on failure
            suppress_output=True,  # Hide any potential output/errors from this check
        )
        return returncode == 0
    except FileNotFoundError:
        # If gcloud isn't found, they are definitely not authenticated.
        return False


def _get_current_gcp_user() -> str:
    """Get the currently authenticated GCP user or indicate default VM SA."""
    gcloud_path = _find_executable("gcloud")
    cmd = [
        gcloud_path,
        "auth",
        "list",
        "--filter=status:ACTIVE",
        "--format=value(account)",
    ]
    _, stdout, _ = _run_command(cmd, capture=True, check=False)

    account = stdout.strip()
    if account:
        if "compute@developer.gserviceaccount.com" in account:
            # Return a more user-friendly string for the default VM SA case
            return "default VM service account"
        return account
    return "Not authenticated"


def _get_current_gcp_impersonation() -> str:
    """Get the current impersonated service account from gcloud config."""
    gcloud_path = _find_executable("gcloud")
    cmd = [
        gcloud_path,
        "config",
        "get-value",
        "auth/impersonate_service_account",
        "--quiet",
    ]
    returncode, stdout, _ = _run_command(cmd, capture=True, check=False)
    sa = stdout.strip() if returncode == 0 else ""
    return sa if sa else "None"


def _run_gcloud_login() -> None:
    """Run the gcloud auth login command, updating ADC using device flow.

    Always uses --update-adc to ensure libraries using ADC work immediately for the user.
    Uses --no-launch-browser for headless environments.
    """
    gcloud_path = _find_executable("gcloud")
    print(f"{BLUE}Authenticating with Google Cloud (will update ADC)...{NC}")

    # Directly use device flow as remote browser consistently failed
    cmd = [gcloud_path, "auth", "login", "--update-adc", "--no-launch-browser"]

    print(f"{YELLOW}Initiating device flow login... Follow the instructions below.{NC}")
    # Remove capture=True, rely on direct output and return code
    returncode, _, _ = _run_command(
        cmd,
        capture=False,  # Changed from True
        check=False,
        suppress_output=False,
    )

    if returncode != 0:
        # stderr is not captured, provide a generic error
        print(
            f"{RED}Login command failed (return code: {returncode}). Please check gcloud output above.{NC}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"{GREEN}User authentication complete. ADC updated for user account.{NC}")


def _test_gcp_credentials(user: str, impersonation_sa: str) -> None:
    """Test GCP credentials. Prints output on failure (to stderr) and success (to stdout)."""
    gcloud_path = _find_executable("gcloud")
    user_short = _get_short_name(user)
    impersonation_short = _get_short_name(impersonation_sa)

    if user != "Not authenticated" and "Not authenticated" not in user:
        cmd = [
            gcloud_path,
            "compute",
            "zones",
            "list",
            "--limit=1",
            f"--project={GCP_PROJECT_ID}",
        ]

        if impersonation_sa != "None":
            # Test 1: Access as the user directly (temporarily disable impersonation)
            print(f"  Testing direct access as user ({user_short})...")
            orig_sa = impersonation_sa
            unset_rc, _, unset_err = _gcloud_unset_config(
                "auth/impersonate_service_account"
            )
            if unset_rc != 0:
                print(
                    f"    {RED}✗ Test Error: Failed to temporarily disable impersonation: {unset_err}{NC}",
                    file=sys.stderr,
                )
                # Even if unsetting fails, attempt to restore and continue with impersonation test
            else:
                user_returncode, _, _ = _run_command(
                    cmd, suppress_output=True, check=False
                )
                if user_returncode != 0:
                    print(
                        f"    {RED}✗ User Test Failure: Cannot access resources directly as user '{user_short}'. Check roles/project.{NC}",
                        file=sys.stderr,
                    )
                else:
                    print(
                        f"    {GREEN}✓ User Test ({user_short}): Direct access OK{NC}"
                    )

            # Restore impersonation setting
            set_rc, _, set_err = _gcloud_set_config(
                "auth/impersonate_service_account", orig_sa
            )
            if set_rc != 0:
                print(
                    f"    {RED}✗ Test Error: Failed to restore impersonation config for {impersonation_short}: {set_err}{NC}",
                    file=sys.stderr,
                )
                # If restoring fails, it's a significant issue for the next test

            # Test 2: Access while impersonating the SA
            print(f"  Testing access while impersonating SA ({impersonation_short})...")
            impersonation_returncode, _, _ = _run_command(
                cmd, suppress_output=True, check=False
            )
            if impersonation_returncode != 0:
                print(
                    f"    {RED}✗ Impersonation Test Failure: Cannot access resources impersonating '{impersonation_short}'. Check permissions/config.{NC}",
                    file=sys.stderr,
                )
            else:
                print(
                    f"    {GREEN}✓ Impersonation Test ({impersonation_short}): Access OK{NC}"
                )

        else:
            # Test user account directly (no impersonation config)
            print(f"  Testing direct access as user ({user_short})...")
            returncode, _, _ = _run_command(cmd, suppress_output=True, check=False)
            if returncode != 0:
                print(
                    f"    {RED}✗ User Test Failure: Cannot access resources directly as user '{user_short}'. Check roles/project.{NC}",
                    file=sys.stderr,
                )
            else:
                print(f"    {GREEN}✓ User Test ({user_short}): Direct access OK{NC}")
    else:
        print(
            f"  {YELLOW}User not authenticated, skipping credential access tests.{NC}"
        )


# --- AWS Functions ---
def _unset_aws_static_creds() -> None:
    """Unset static AWS credential environment variables."""
    _modify_rc_files("AWS_ACCESS_KEY_ID", None)
    _modify_rc_files("AWS_SECRET_ACCESS_KEY", None)
    _modify_rc_files("AWS_SESSION_TOKEN", None)


def _set_aws_profile(profile: str) -> None:
    """Set and persist AWS profile in environment and RC files."""
    _modify_rc_files("AWS_PROFILE", profile)
    _unset_aws_static_creds()


def _get_current_aws_profile() -> str:
    """Get the current AWS profile."""
    # Check environment variable first
    profile = _get_env_var("AWS_PROFILE")
    if profile:
        return profile

    # Try using aws command to check
    aws_path = _find_executable("aws")
    try:
        cmd = [aws_path, "configure", "list", "--no-cli-pager"]
        _, stdout, _ = _run_command(cmd, capture=True, check=False)

        # Extract profile from output (format: "profile    : <value>    : <type>    : <location>")
        # Match the line starting with "profile" and capture the value after the first colon
        profile_match = re.search(r"^profile\s+:\s+(\S+)", stdout, re.MULTILINE)
        if profile_match:
            profile_value = profile_match.group(1)
            # Check if the profile is actually set (not "<not" or "not")
            if profile_value not in ("<not", "not"):
                return profile_value
    except:
        pass

    # Default if nothing else works
    return AWS_DEFAULT_PROFILE


def _is_aws_profile_authenticated(profile: str) -> bool:
    """Check if an AWS profile has valid credentials."""
    aws_path = _find_executable("aws")
    cmd = [
        aws_path,
        "sts",
        "get-caller-identity",
        "--profile",
        profile,
        "--no-cli-pager",
    ]
    returncode, _, _ = _run_command(cmd, suppress_output=True, check=False)
    return returncode == 0


def _run_aws_sso_login(profile: str) -> None:
    """Run the AWS SSO login command for a specific profile."""
    aws_path = _find_executable("aws")
    print(f"{BLUE}Running 'aws sso login --profile {profile}'...{NC}")
    _run_command([aws_path, "sso", "login", "--profile", profile])
    print(f"{GREEN}Authentication complete.{NC}")


def _get_available_aws_profiles() -> List[str]:
    """Get list of available AWS profiles from config file."""
    profiles = []

    if not AWS_CONFIG_FILE.exists():
        return profiles

    try:
        with open(AWS_CONFIG_FILE, "r") as f:
            lines = f.readlines()

        for line in lines:
            # Match [profile name] or [name] if default profile
            match = re.match(r"^\[(?:profile\s+)?([^\]]+)\]", line.strip())
            if match:
                profiles.append(match.group(1))
    except:
        pass

    return profiles


# --- Typer Applications ---
gcp_app = typer.Typer(
    help="Manage GCP authentication using gcloud config and ADC. (RC file/env var methods are deprecated)."
)
aws_app = typer.Typer(help="Manage AWS SSO authentication using RC files.")


# --- GCP Commands ---
@gcp_app.command("status")
def gcp_status():
    """Show active GCP credentials for CLI and Libraries/ADC, including staleness."""
    cli_user = _get_current_gcp_user()
    cli_impersonation = _get_current_gcp_impersonation()
    adc_principal_raw = _get_adc_status()  # Raw status string, potentially complex

    user_auth_valid = _is_gcp_user_authenticated()
    adc_auth_valid = _is_adc_authenticated()

    # Determine active principal for CLI
    if cli_impersonation != "None":
        cli_active_short = _get_short_name(cli_impersonation)
        cli_is_impersonating = True
    else:
        cli_active_short = _get_short_name(cli_user)
        cli_is_impersonating = False

    adc_active_short = _get_short_name(adc_principal_raw)

    print(f"{BLUE}--- GCP CLI Credentials ---{NC}")
    print(f"  Effective Principal: {GREEN}{cli_active_short}{NC}")
    print(f"  User Account ({_get_short_name(cli_user)}):")
    if user_auth_valid:
        print(f"    └─ Authentication: {GREEN}VALID{NC}")
    else:
        print(
            f"    └─ Authentication: {RED}STALE/EXPIRED{NC} (Hint: run 'dh gcp login')"
        )

    if cli_is_impersonating:
        print(
            f"  Impersonation ({_get_short_name(cli_impersonation)}): {GREEN}Active{NC}"
        )
        print(f"    └─ Access Test: (see results below)")
    else:
        print(f"  Impersonation: {YELLOW}Not Active{NC}")

    print(f"\n{BLUE}--- GCP Library/ADC Credentials ---{NC}")
    print(f"  Effective Principal: {GREEN}{adc_active_short}{NC}")
    if adc_principal_raw in ["Not configured", "Error reading", "Invalid format"]:
        print(f"    └─ Status: {RED}{adc_principal_raw}{NC}")
    elif adc_auth_valid:
        print(f"    └─ Authentication: {GREEN}VALID{NC}")
    else:
        print(
            f"    └─ Authentication: {RED}STALE/EXPIRED{NC} (Hint: run 'dh gcp use-...-adc' or 'gcloud auth application-default login ...')"
        )

    print(f"\n{BLUE}--- GCP Access Tests (for CLI configuration) ---{NC}")
    # Run tests silently, they will print to stderr only on failure
    _test_gcp_credentials(cli_user, cli_impersonation)


@gcp_app.command("login")
def gcp_login():
    """Authenticate user & configure CLI to impersonate devcon SA."""
    # Step 1: Authenticate the user (updates ADC for user)
    _run_gcloud_login()  # Uses device flow

    # Step 2: Configure gcloud CLI for devcon SA impersonation
    print(f"\n{BLUE}Configuring gcloud CLI to impersonate {GCP_DEVCON_SA}...{NC}")
    set_sa_rc, _, set_sa_err = _gcloud_set_config(
        "auth/impersonate_service_account", GCP_DEVCON_SA
    )
    if set_sa_rc != 0:
        print(
            f"{RED}Error setting impersonation config: {set_sa_err}{NC}",
            file=sys.stderr,
        )
        print(f"{YELLOW}Warning: CLI impersonation failed to configure.{NC}")
        # Attempt to show status anyway before exiting command
        print("\n{BLUE}Current status:{NC}")
        gcp_status()
        return

    set_proj_rc, _, set_proj_err = _gcloud_set_config("project", GCP_PROJECT_ID)
    if set_proj_rc != 0:
        print(f"{RED}Error setting project config: {set_proj_err}{NC}", file=sys.stderr)
        # Continue, but warn user

    # Step 3: Print configuration options
    print(f"\n{GREEN}Login successful. CLI configured for devcon impersonation.{NC}")
    print(f"{BLUE}--- Common Configuration Commands ---\n{NC}")

    cmd_width = 25  # Adjusted width for dh commands

    print(f"  {BLUE}Set CLI to use User:{NC}")
    print(f"    {YELLOW}{f'dh gcp use-user':<{cmd_width}}{NC}")

    print(f"  {BLUE}Set CLI to use Devcon SA:{NC}")
    print(
        f"    {YELLOW}{f'dh gcp use-devcon':<{cmd_width}}{NC} {GREEN}(Current default after login){NC}"
    )

    print(f"  {BLUE}Set Libraries/Tools (ADC) to use User:{NC}")
    print(f"    {YELLOW}{f'dh gcp use-user-adc':<{cmd_width}}{NC}")

    print(f"  {BLUE}Set Libraries/Tools (ADC) to use Devcon SA:{NC}")
    print(f"    {YELLOW}{f'dh gcp use-devcon-adc':<{cmd_width}}{NC}")

    # Step 4: Show current status automatically
    print(f"\n{BLUE}--- Current Status ---{NC}")
    gcp_status()


@gcp_app.command("use-devcon")
def gcp_use_devcon(
    export: bool = typer.Option(
        False,
        "--export",
        "-x",
        help="Deprecated. Has no effect. Settings are applied directly via gcloud config.",
        hidden=True,
    ),
):
    """Configure gcloud CLI to impersonate the devcon SA.

    This command updates gcloud configuration settings directly.
    It DOES NOT modify shell RC files or require `eval`.
    It DOES NOT automatically update Application Default Credentials (ADC) for impersonation.

    Ensures the primary user login is valid first.
    """
    if export:
        print(
            f"{YELLOW}Warning: --export/-x is deprecated and has no effect. "
            f"GCP settings are now managed via gcloud config.{NC}",
            file=sys.stderr,
        )

    if not _is_gcp_user_authenticated():
        print(
            f"{RED}Error: GCP user authentication is invalid or requires interactive login.{NC}",
            file=sys.stderr,
        )
        print(
            f"{YELLOW}Please run 'dh gcp login' interactively first, then try this command again.{NC}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"{BLUE}Configuring gcloud CLI to impersonate {GCP_DEVCON_SA}...{NC}")

    # Set gcloud CLI impersonation via config
    set_sa_rc, _, set_sa_err = _gcloud_set_config(
        "auth/impersonate_service_account", GCP_DEVCON_SA
    )
    if set_sa_rc != 0:
        print(
            f"{RED}Error setting impersonation config: {set_sa_err}{NC}",
            file=sys.stderr,
        )
        sys.exit(1)

    set_proj_rc, _, set_proj_err = _gcloud_set_config("project", GCP_PROJECT_ID)
    if set_proj_rc != 0:
        print(f"{RED}Error setting project config: {set_proj_err}{NC}", file=sys.stderr)
        # Continue, but warn user

    # Check for lingering legacy environment variable
    if _get_env_var("CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT"):
        print(
            f"{YELLOW}Warning: Legacy env var CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT is set.{NC}",
            file=sys.stderr,
        )
        print(
            f"{YELLOW}         This may override gcloud config. Consider running:{NC}",
            file=sys.stderr,
        )
        print(
            f"{YELLOW}         unset CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT{NC}",
            file=sys.stderr,
        )

    print(f"\n{GREEN}GCP CLI configured to use devcon SA ({GCP_DEVCON_SA}).{NC}")
    print(f"Project set to: {GCP_PROJECT_ID}")
    print(
        f"{YELLOW}NOTE: If libraries/tools (e.g., for DVC, Terraform) need to use impersonation, update Application Default Credentials (ADC) manually:{NC}"
    )
    print(
        f"{YELLOW}        gcloud auth application-default login --impersonate-service-account={GCP_DEVCON_SA}{NC}"
    )
    print(f"Run 'dh gcp status' to verify CLI configuration.")


@gcp_app.command("use-user")
def gcp_use_user(
    export: bool = typer.Option(
        False,
        "--export",
        "-x",
        help="Deprecated. Has no effect. Settings are applied directly via gcloud config.",
        hidden=True,
    ),
):
    """Configure gcloud CLI to use the personal user account via gcloud config.

    This command updates gcloud configuration settings directly.
    It DOES NOT modify shell RC files or require `eval`.
    It DOES NOT automatically update Application Default Credentials (ADC).

    Ensures the primary user login is valid first.
    """
    if export:
        print(
            f"{YELLOW}Warning: --export/-x is deprecated and has no effect. "
            f"GCP settings are now managed via gcloud config.{NC}",
            file=sys.stderr,
        )

    if not _is_gcp_user_authenticated():
        print(
            f"{RED}Error: GCP user authentication is invalid or requires interactive login.{NC}",
            file=sys.stderr,
        )
        print(
            f"{YELLOW}Please run 'dh gcp login' interactively first, then try this command again.{NC}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"{BLUE}Configuring gcloud CLI to use personal user account...{NC}")

    # Unset gcloud CLI impersonation via config
    unset_sa_rc, _, unset_sa_err = _gcloud_unset_config(
        "auth/impersonate_service_account"
    )
    if unset_sa_rc != 0:
        print(
            f"{RED}Error unsetting impersonation config: {unset_sa_err}{NC}",
            file=sys.stderr,
        )
        # Continue, but warn user

    set_proj_rc, _, set_proj_err = _gcloud_set_config("project", GCP_PROJECT_ID)
    if set_proj_rc != 0:
        print(f"{RED}Error setting project config: {set_proj_err}{NC}", file=sys.stderr)
        # Continue, but warn user

    # Check for lingering legacy environment variable
    if _get_env_var("CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT"):
        print(
            f"{YELLOW}Warning: Legacy env var CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT is set.{NC}",
            file=sys.stderr,
        )
        print(
            f"{YELLOW}         This may interfere with using your personal account. Consider running:{NC}",
            file=sys.stderr,
        )
        print(
            f"{YELLOW}         unset CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT{NC}",
            file=sys.stderr,
        )

    print(f"\n{GREEN}GCP CLI configured to use personal account.{NC}")
    print(f"Project set to: {GCP_PROJECT_ID}")
    print(
        f"{YELLOW}NOTE: If libraries/tools (e.g., for DVC, Terraform) need to use impersonation, update Application Default Credentials (ADC) manually:{NC}"
    )
    print(f"{YELLOW}        gcloud auth application-default login{NC}")
    print(f"Run 'dh gcp status' to verify CLI configuration.")


# === NEW ADC Commands ===


@gcp_app.command("use-user-adc")
def gcp_use_user_adc():
    """Configure Libraries/Tools (ADC) to use your PERSONAL account."""
    if not _is_gcp_user_authenticated():
        print(
            f"{RED}Error: GCP user authentication is invalid or requires interactive login.{NC}",
            file=sys.stderr,
        )
        print(
            f"{YELLOW}Please run 'dh gcp login' interactively first.{NC}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"{BLUE}Attempting to configure ADC for your personal user account...{NC}")
    print(
        f"{YELLOW}This may require you to complete a browser authentication flow.{NC}"
    )

    gcloud_path = _find_executable("gcloud")
    cmd = [gcloud_path, "auth", "application-default", "login"]

    # Allow interaction, don't capture output
    returncode, _, _ = _run_command(
        cmd, capture=False, check=False, suppress_output=False
    )

    if returncode == 0:
        print(f"\n{GREEN}Successfully configured ADC for personal user account.{NC}")
        print(f"{BLUE}--- Current Status ---{NC}")
        gcp_status()  # Show status after successful change
    else:
        print(
            f"{RED}Failed to configure ADC (Return code: {returncode}). Check messages above.{NC}",
            file=sys.stderr,
        )
        sys.exit(1)


@gcp_app.command("use-devcon-adc")
def gcp_use_devcon_adc():
    """Configure Libraries/Tools (ADC) to use the DEVCON service account."""
    if not _is_gcp_user_authenticated():
        print(
            f"{RED}Error: GCP user authentication is invalid or requires interactive login.{NC}",
            file=sys.stderr,
        )
        print(
            f"{YELLOW}Please run 'dh gcp login' interactively first.{NC}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"{BLUE}Attempting to configure ADC for devcon SA ({GCP_DEVCON_SA})...{NC}")
    print(
        f"{YELLOW}This may require you to complete a browser authentication flow.{NC}"
    )

    gcloud_path = _find_executable("gcloud")
    cmd = [
        gcloud_path,
        "auth",
        "application-default",
        "login",
        f"--impersonate-service-account={GCP_DEVCON_SA}",
    ]

    # Allow interaction, don't capture output
    returncode, _, _ = _run_command(
        cmd, capture=False, check=False, suppress_output=False
    )

    if returncode == 0:
        print(
            f"\n{GREEN}Successfully configured ADC for devcon SA ({GCP_DEVCON_SA}).{NC}"
        )
        print(f"{BLUE}--- Current Status ---{NC}")
        gcp_status()  # Show status after successful change
    else:
        print(
            f"{RED}Failed to configure ADC (Return code: {returncode}). Check messages above.{NC}",
            file=sys.stderr,
        )
        sys.exit(1)


@gcp_app.command("logout")
def gcp_logout():
    """Clear all GCP credentials for testing or role switching purposes.

    This removes the active user's gcloud login, disables impersonation,
    and invalidates Application Default Credentials (ADC).
    """
    print(f"{BLUE}Clearing all GCP credentials...{NC}")

    try:
        gcloud_path = _find_executable("gcloud")
        errors = []

        # 1. Revoke user-level credentials
        print(f"{BLUE}Revoking active gcloud credentials...{NC}")
        revoke_cmd = [gcloud_path, "auth", "revoke", "--all", "--quiet"]
        revoke_code, _, revoke_err = _run_command(revoke_cmd, capture=True, check=False)
        if revoke_code != 0 and revoke_err:
            errors.append(f"Failed to revoke credentials: {revoke_err}")

        # 2. Unset impersonation config
        print(f"{BLUE}Disabling service account impersonation...{NC}")
        unset_code, _, unset_err = _gcloud_unset_config(
            "auth/impersonate_service_account"
        )
        if unset_code != 0 and unset_err:
            errors.append(f"Failed to unset impersonation: {unset_err}")

        # 3. Revoke ADC
        print(f"{BLUE}Revoking Application Default Credentials (ADC)...{NC}")
        adc_cmd = [gcloud_path, "auth", "application-default", "revoke", "--quiet"]
        adc_code, _, adc_err = _run_command(adc_cmd, capture=True, check=False)

        # 4. Additionally remove ADC file if it exists (belt-and-suspenders approach)
        adc_file = (
            Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
        )
        if adc_file.exists():
            try:
                adc_file.unlink()
                print(f"{BLUE}Removed ADC file: {adc_file}{NC}")
            except Exception as e:
                errors.append(f"Failed to delete ADC file: {e}")

        if errors:
            print(f"{YELLOW}Logged out with some warnings:{NC}")
            for err in errors:
                print(f"{YELLOW}  - {err}{NC}")
        else:
            print(f"{GREEN}Successfully logged out from GCP.{NC}")

        # Always show how to log back in
        print(f"\n{BLUE}To log back in:{NC}")
        print(f"  {YELLOW}dh gcp login{NC}")

        # Show current (now-cleared) status
        print(f"\n{BLUE}Current status:{NC}")
        gcp_status()

    except Exception as e:
        print(f"{RED}Error during logout: {e}{NC}", file=sys.stderr)
        print(f"{YELLOW}You may need to manually run:{NC}")
        print(f"  {YELLOW}gcloud auth revoke --all{NC}")
        print(f"  {YELLOW}gcloud auth application-default revoke{NC}")


# === End NEW ADC Commands ===


# --- AWS Commands ---
@aws_app.command("status")
def aws_status(
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Check specific profile instead of current."
    )
):
    """Show current AWS authentication status."""
    target_profile = profile or _get_current_aws_profile()
    print(f"{BLUE}AWS profile:{NC} {GREEN}{target_profile}{NC}")

    if _is_aws_profile_authenticated(target_profile):
        print(f"Credential status: {GREEN}valid{NC}")
        # Get detailed identity information
        aws_path = _find_executable("aws")
        _run_command(
            [
                aws_path,
                "sts",
                "get-caller-identity",
                "--profile",
                target_profile,
                "--no-cli-pager",
            ]
        )
    else:
        print(f"Credential status: {RED}not authenticated{NC}")
        print(f"\nTo authenticate, run:")
        print(f"  {YELLOW}dh aws login{NC}")


@aws_app.command("login")
def aws_login(
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Login to specific profile instead of current."
    )
):
    """Login to AWS SSO with the specified or current profile."""
    target_profile = profile or _get_current_aws_profile()
    _run_aws_sso_login(target_profile)
    print(f"\nTo activate profile {target_profile} in your current shell, run:")
    print(f'  {YELLOW}eval "$(dh aws use-profile {target_profile} --export)"{NC}')


@aws_app.command("use-profile")
def aws_use_profile(
    profile: str = typer.Argument(..., help="AWS profile name to activate."),
    export: bool = typer.Option(
        False, "--export", "-x", help="Print export commands for the current shell."
    ),
    auto_login: bool = typer.Option(
        False, "--auto-login", "-a", help="Run 'aws sso login' if needed."
    ),
):
    """Switch to a specific AWS profile."""
    # Modify RC files to persist across sessions
    _set_aws_profile(profile)

    if auto_login and not _is_aws_profile_authenticated(profile):
        print(
            f"{YELLOW}Profile '{profile}' not authenticated. Running 'aws sso login'...{NC}",
            file=sys.stderr,
        )
        _run_aws_sso_login(profile)

    if export:
        # Print export commands for the current shell to stdout
        print(f"export AWS_PROFILE='{profile}'")
        print("unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN")

        # Print confirmation to stderr so it doesn't affect eval
        print(
            f"{GREEN}AWS profile '{profile}' exported successfully.{NC}",
            file=sys.stderr,
        )
    else:
        # Just print confirmation
        print(f"{GREEN}AWS profile set to '{profile}' and persisted to RC files.{NC}")
        print(
            f"Changes will take effect in new shell sessions. To apply in current shell, run:"
        )
        print(f'  {YELLOW}eval "$(dh aws use-profile {profile} --export)"{NC}')


@aws_app.command("interactive")
def aws_interactive():
    """Launch interactive AWS profile management menu."""
    current_profile = _get_current_aws_profile()

    print(f"{BLUE}AWS SSO helper – current profile: {GREEN}{current_profile}{NC}")

    while True:
        choice = questionary.select(
            "Choose an option:",
            choices=[
                f"Authenticate current profile ({current_profile})",
                "Switch profile",
                "Show status",
                "Exit",
            ],
        ).ask()

        if choice == f"Authenticate current profile ({current_profile})":
            _run_aws_sso_login(current_profile)
            print(f"{GREEN}Authentication complete.{NC}")
            print(f"To activate in your current shell, run:")
            print(
                f'  {YELLOW}eval "$(dh aws use-profile {current_profile} --export)"{NC}'
            )

        elif choice == "Switch profile":
            available_profiles = _get_available_aws_profiles()

            if not available_profiles:
                print(f"{RED}No AWS profiles found. Check your ~/.aws/config file.{NC}")
                continue

            for i, prof in enumerate(available_profiles, 1):
                print(f"{i}) {prof}")

            # Get profile selection by number or name
            sel = questionary.text("Select profile number or name:").ask()

            if sel.isdigit() and 1 <= int(sel) <= len(available_profiles):
                new_profile = available_profiles[int(sel) - 1]
            elif sel in available_profiles:
                new_profile = sel
            else:
                print(f"{RED}Invalid selection{NC}")
                continue

            _set_aws_profile(new_profile)
            print(f"{GREEN}Switched to profile {new_profile}{NC}")
            print(f"To activate in your current shell, run:")
            print(f'  {YELLOW}eval "$(dh aws use-profile {new_profile} --export)"{NC}')

            # Ask if they want to authenticate now
            if questionary.confirm(
                "Authenticate this profile now?", default=False
            ).ask():
                _run_aws_sso_login(new_profile)
                print(f"{GREEN}Authentication complete.{NC}")
                print(f"To activate in your current shell, run:")
                print(
                    f'  {YELLOW}eval "$(dh aws use-profile {new_profile} --export)"{NC}'
                )

        elif choice == "Show status":
            # Fix: Explicitly pass None for the profile parameter
            aws_status(profile=None)

        elif choice == "Exit":
            print(f"To activate profile {current_profile} in your current shell, run:")
            print(
                f'  {YELLOW}eval "$(dh aws use-profile {current_profile} --export)"{NC}'
            )
            break

        print()  # Add newline between iterations
