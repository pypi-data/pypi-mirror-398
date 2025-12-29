"""CLI commands common to all repos."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import toml
import typer

# Import cloud helper lazily inside functions to avoid heavy deps at module load


def test_github_actions_locally():
    """Run the script test_pytest_in_github_actions_container.sh.sh."""
    script_path = ".devcontainer/scripts/test_pytest_in_github_actions_container.sh"

    try:
        subprocess.check_call(["bash", script_path])
        print("Script ran successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running the script: {e}")


def delete_local_branch(branch_name: str, folder_path: str):
    """Delete a local Git branch after fetching with pruning.

    Args:
        branch_name: Name of the branch to delete
        folder_path: Path to the git repository folder
    """
    try:
        # Store current working directory
        original_dir = os.getcwd()

        # Change to the specified directory
        os.chdir(folder_path)
        print(f"Changed to directory: {folder_path}")

        # Delete the specified branch
        delete_branch_cmd = ["git", "branch", "-D", branch_name]
        subprocess.run(delete_branch_cmd, check=True)
        print(f"Deleted branch: {branch_name}")

        # Fetch changes from the remote repository and prune obsolete branches
        fetch_prune_cmd = ["git", "fetch", "-p"]
        subprocess.run(fetch_prune_cmd, check=True)
        print("Fetched changes and pruned obsolete branches")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running Git commands: {e}")
    finally:
        # Always return to the original directory
        os.chdir(original_dir)


def get_current_version_from_toml(file_path="pyproject.toml"):
    """Reads the version from a pyproject.toml file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
        version_match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if version_match:
            return version_match.group(1)
        else:
            raise ValueError(f"Could not find version string in {file_path}")
    except FileNotFoundError:
        raise FileNotFoundError(f"{file_path} not found.")
    except Exception as e:
        raise e


def build_and_upload_wheel(bump_part: str = "patch"):
    """Build a Python wheel and upload to PyPI using UV.

    Automatically increments the version number in pyproject.toml before building
    based on the bump_part argument ('major', 'minor', 'patch').

    Expects PyPI authentication to be configured via the environment variable:
    - UV_PUBLISH_TOKEN

    Args:
        bump_part (str): The part of the version to bump. Defaults to 'patch'.
    """
    if bump_part not in ["major", "minor", "patch"]:
        print(
            f"Error: Invalid bump_part '{bump_part}'. Must be 'major', 'minor', or 'patch'."
        )
        return

    # ANSI color codes
    BLUE = "\033[94m"
    RESET = "\033[0m"

    # --- Authentication Setup ---
    token = os.environ.get("UV_PUBLISH_TOKEN")

    if not token:
        print("Error: PyPI authentication not configured.")
        print(
            "Please set the UV_PUBLISH_TOKEN environment variable with your PyPI API token."
        )
        return

    # Build the command with token authentication
    # IMPORTANT: Mask token for printing
    publish_cmd_safe_print = ["uv", "publish", "--token", "*****"]
    publish_cmd = ["uv", "publish", "--token", token]
    print("Using UV_PUBLISH_TOKEN for authentication.")

    # Find the primary manifest (prefer AWS, then Mac, then Workstation)
    pyproject_path = None
    for candidate in [
        "pyproject.aws.toml",
        "pyproject.mac.toml",
        "pyproject.workstation.toml",
    ]:
        if Path(candidate).exists():
            pyproject_path = candidate
            break

    if not pyproject_path:
        print(
            "Error: No platform-specific manifest found (pyproject.aws.toml, pyproject.mac.toml, or pyproject.workstation.toml)"
        )
        return

    print(f"Using manifest: {pyproject_path}")
    current_version = None  # Initialize in case the first try block fails

    try:
        # --- Clean dist directory ---
        dist_dir = Path("dist")
        if dist_dir.exists():
            print(f"Removing existing build directory: {dist_dir}")
            shutil.rmtree(dist_dir)
        # --- End Clean dist directory ---

        # --- Version Bumping Logic ---
        current_version = get_current_version_from_toml(pyproject_path)
        print(f"Current version: {current_version}")

        try:
            major, minor, patch = map(int, current_version.split("."))
        except ValueError:
            print(
                f"Error: Could not parse version '{current_version}'. Expected format X.Y.Z"
            )
            return

        if bump_part == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_part == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        new_version = f"{major}.{minor}.{patch}"
        print(f"Bumping {bump_part} version to: {new_version}")

        # Read pyproject.toml
        with open(pyproject_path, "r") as f:
            content = f.read()

        # Replace the version string
        pattern = re.compile(
            f'^version\s*=\s*"{re.escape(current_version)}"', re.MULTILINE
        )
        new_content, num_replacements = pattern.subn(
            f'version = "{new_version}"', content
        )

        if num_replacements == 0:
            print(
                f"Error: Could not find 'version = \"{current_version}\"' in {pyproject_path}"
            )
            return  # Exit before build/publish if version wasn't updated
        if num_replacements > 1:
            print(
                f"Warning: Found multiple version lines for '{current_version}'. Only the first was updated."
            )

        # Write the updated content back
        with open(pyproject_path, "w") as f:
            f.write(new_content)
        print(f"Updated {pyproject_path} with version {new_version}")

        # Mirror version in all other platform manifests (best-effort)
        other_manifests = []
        for candidate in [
            "pyproject.aws.toml",
            "pyproject.mac.toml",
            "pyproject.workstation.toml",
        ]:
            if Path(candidate).exists() and candidate != pyproject_path:
                other_manifests.append(Path(candidate))

        for manifest_path in other_manifests:
            try:
                content = manifest_path.read_text()
                pattern = re.compile(
                    f'^version\s*=\s*"{re.escape(current_version)}"', re.MULTILINE
                )
                new_content, replacements = pattern.subn(
                    f'version = "{new_version}"', content
                )
                if replacements > 0:
                    manifest_path.write_text(new_content)
                    print(f"Updated {manifest_path} with version {new_version}")
            except Exception as e:
                print(f"Warning: Could not update {manifest_path}: {e}")
        # --- End Version Bumping Logic ---

        # Build wheel and sdist
        # UV expects pyproject.toml, so temporarily copy the platform manifest
        backup_created = False
        temp_pyproject_created = False
        if pyproject_path != "pyproject.toml":
            if Path("pyproject.toml").exists():
                Path("pyproject.toml").rename("pyproject.toml.build.bak")
                backup_created = True
            Path(pyproject_path).read_text()
            with open("pyproject.toml", "w") as f:
                f.write(Path(pyproject_path).read_text())
            temp_pyproject_created = True

        try:
            build_cmd = ["uv", "build"]
            # Print command in blue
            print(f"Running command: {BLUE}{' '.join(build_cmd)}{RESET}")
            subprocess.run(build_cmd, check=True)

            # Upload using uv publish with explicit arguments
            # Print masked command in blue
            print(f"Running command: {BLUE}{' '.join(publish_cmd_safe_print)}{RESET}")
            subprocess.run(
                publish_cmd,  # Use the actual command with token
                check=True,
            )

            print(f"Successfully built and uploaded version {new_version} to PyPI")

            # Re-install DHT in current venv when building from DHT itself
            # (Keep temp pyproject.toml until after this step)
            try:
                proj_name = None
                try:
                    proj_toml = toml.load(pyproject_path)
                    proj_name = (
                        proj_toml.get("project", {}).get("name")
                        if isinstance(proj_toml, dict)
                        else None
                    )
                except Exception:
                    pass
                if proj_name == "dayhoff-tools":
                    print("Re-installing dayhoff-tools into the active environment…")
                    reinstall_cmd = ["uv", "pip", "install", "-e", ".[full]"]
                    print(f"Running command: {BLUE}{' '.join(reinstall_cmd)}{RESET}")
                    subprocess.run(reinstall_cmd, check=True)
                    print("dayhoff-tools reinstalled in the current environment.")
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to reinstall dayhoff-tools locally: {e}")

        finally:
            # Restore original state (always clean up, even if errors occurred)
            if temp_pyproject_created:
                if Path("pyproject.toml").exists():
                    Path("pyproject.toml").unlink()
                if backup_created and Path("pyproject.toml.build.bak").exists():
                    Path("pyproject.toml.build.bak").rename("pyproject.toml")

    except FileNotFoundError:
        print(f"Error: {pyproject_path} not found.")
        # No version change happened, so no rollback needed
    except subprocess.CalledProcessError as e:
        print(f"Error during build/upload: {e}")
        # Attempt to roll back version change only if it was bumped successfully
        if current_version and new_version:
            try:
                print(
                    f"Attempting to revert version in {pyproject_path} back to {current_version}..."
                )
                with open(pyproject_path, "r") as f:
                    content_revert = f.read()
                # Use new_version in pattern for reverting
                pattern_revert = re.compile(
                    f'^version\s*=\s*"{re.escape(new_version)}"', re.MULTILINE
                )
                reverted_content, num_revert = pattern_revert.subn(
                    f'version = "{current_version}"', content_revert
                )
                if num_revert > 0:
                    with open(pyproject_path, "w") as f:
                        f.write(reverted_content)
                    print(f"Successfully reverted version in {pyproject_path}.")
                else:
                    print(
                        f"Warning: Could not find version {new_version} to revert in {pyproject_path}."
                    )

                # Also revert other platform manifests
                for candidate in [
                    "pyproject.aws.toml",
                    "pyproject.mac.toml",
                    "pyproject.workstation.toml",
                ]:
                    if Path(candidate).exists() and candidate != pyproject_path:
                        try:
                            content_revert = Path(candidate).read_text()
                            reverted, num = pattern_revert.subn(
                                f'version = "{current_version}"', content_revert
                            )
                            if num > 0:
                                Path(candidate).write_text(reverted)
                                print(f"Successfully reverted version in {candidate}.")
                        except Exception as e2:
                            print(
                                f"Warning: Failed to revert version change in {candidate}: {e2}"
                            )
            except Exception as revert_e:
                print(
                    f"Warning: Failed to revert version change in {pyproject_path}: {revert_e}"
                )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Also attempt rollback here if version was bumped
        if current_version and "new_version" in locals() and new_version:
            try:
                print(
                    f"Attempting to revert version in {pyproject_path} back to {current_version} due to unexpected error..."
                )
                # (Same revert logic as above)
                with open(pyproject_path, "r") as f:
                    content_revert = f.read()
                pattern_revert = re.compile(
                    f'^version\s*=\s*"{re.escape(new_version)}"', re.MULTILINE
                )
                reverted_content, num_revert = pattern_revert.subn(
                    f'version = "{current_version}"', content_revert
                )
                if num_revert > 0:
                    with open(pyproject_path, "w") as f:
                        f.write(reverted_content)
                    print(f"Successfully reverted version in {pyproject_path}.")
                else:
                    print(
                        f"Warning: Could not find version {new_version} to revert in {pyproject_path}."
                    )
                # Also revert other platform manifests
                for candidate in [
                    "pyproject.aws.toml",
                    "pyproject.mac.toml",
                    "pyproject.workstation.toml",
                ]:
                    if Path(candidate).exists() and candidate != pyproject_path:
                        try:
                            content_revert = Path(candidate).read_text()
                            reverted, num = pattern_revert.subn(
                                f'version = "{current_version}"', content_revert
                            )
                            if num > 0:
                                Path(candidate).write_text(reverted)
                                print(f"Successfully reverted version in {candidate}.")
                        except Exception as e2:
                            print(
                                f"Warning: Failed to revert version change in {candidate}: {e2}"
                            )
            except Exception as revert_e:
                print(
                    f"Warning: Failed to revert version change in {pyproject_path}: {revert_e}"
                )


# --- Dependency Management Commands ---


def sync_with_toml(
    install_project: bool = typer.Option(
        False,
        "--install-project",
        "-p",
        help="Install the local project package itself (with 'full' extras) into the environment.",
    ),
):
    """Sync environment with platform-specific TOML manifest (install/update dependencies).

    Behavior by platform:
    - Workstation (STUDIO_PLATFORM=workstation) with pyproject.workstation.toml:
      * Uses pip with constraints.txt to preserve NGC PyTorch
      * Parses dependencies directly from pyproject.workstation.toml
      * Installs into .venv_workstation with --system-site-packages
    - Mac (STUDIO_PLATFORM=mac) with pyproject.mac.toml:
      * Ensure `.mac_uv_project/pyproject.toml` is a copy of `pyproject.mac.toml`
      * Run `uv lock` and `uv sync` in `.mac_uv_project` targeting active venv with `--active`
      * If `install_project` is true, install the project from repo root into the active env (editable, [full])
    - AWS (default) with pyproject.aws.toml:
      * Uses UV in temp directory `.aws_uv_project` similar to Mac
      * Run `uv lock` and `uv sync` targeting active venv
    """
    # ANSI color codes
    BLUE = "\033[94m"
    RESET = "\033[0m"

    try:
        platform = os.environ.get("STUDIO_PLATFORM", "aws")

        # Workstation platform: use pip with constraints
        if platform == "workstation" and Path("pyproject.workstation.toml").exists():
            print(
                "Installing dependencies for workstation platform (using pip + constraints)..."
            )

            # Check for constraints.txt
            if not Path("constraints.txt").exists():
                print(
                    "Error: constraints.txt not found. Run direnv to generate it first."
                )
                sys.exit(1)

            # Parse and install dependencies from pyproject.workstation.toml
            import re

            with open("pyproject.workstation.toml", "r") as f:
                content = f.read()

            # Extract dependencies list using line-by-line parsing to handle [] in package names
            lines = content.split("\n")
            in_deps = False
            deps_lines = []

            for line in lines:
                if re.match(r"\s*dependencies\s*=\s*\[", line):
                    in_deps = True
                    continue
                if in_deps:
                    if re.match(r"^\s*\]\s*$", line):
                        break
                    deps_lines.append(line)

            deps = []
            for line in deps_lines:
                line = line.strip()
                if line.startswith('"') or line.startswith("'"):
                    dep = re.sub(r'["\']', "", line)
                    dep = re.sub(r",?\s*#.*$", "", dep)
                    dep = dep.strip().rstrip(",")
                    if dep:
                        deps.append(dep)

            if deps:
                pip_cmd = (
                    [sys.executable, "-m", "pip", "install"]
                    + deps
                    + ["-c", "constraints.txt"]
                )
                print(
                    f"Running command: {BLUE}{' '.join(pip_cmd[:5])} ... -c constraints.txt{RESET}"
                )
                subprocess.run(pip_cmd, check=True)

            # Install dev dependencies using line-by-line parsing
            in_dev_groups = False
            in_dev_list = False
            dev_lines = []

            for line in lines:
                if re.match(r"\s*\[dependency-groups\]", line):
                    in_dev_groups = True
                    continue
                if in_dev_groups and re.match(r"\s*dev\s*=\s*\[", line):
                    in_dev_list = True
                    continue
                if in_dev_list:
                    if re.match(r"^\s*\]\s*$", line):
                        break
                    dev_lines.append(line)

            dev_deps = []
            for line in dev_lines:
                line = line.strip()
                if line.startswith('"') or line.startswith("'"):
                    dep = re.sub(r'["\']', "", line)
                    dep = re.sub(r",?\s*#.*$", "", dep)
                    dep = dep.strip().rstrip(",")
                    if dep:
                        dev_deps.append(dep)

            if dev_deps:
                print("Installing dev dependencies...")
                pip_cmd = (
                    [sys.executable, "-m", "pip", "install"]
                    + dev_deps
                    + ["-c", "constraints.txt"]
                )
                print(
                    f"Running command: {BLUE}{' '.join(pip_cmd[:5])} ... -c constraints.txt{RESET}"
                )
                subprocess.run(pip_cmd, check=True)

            # Install project if requested
            if install_project:
                repo_name = Path.cwd().name
                if repo_name == "dayhoff-tools":
                    pip_cmd = [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "-e",
                        ".[full]",
                        "-c",
                        "constraints.txt",
                    ]
                else:
                    pip_cmd = [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "-e",
                        ".",
                        "-c",
                        "constraints.txt",
                    ]
                print(f"Running command: {BLUE}{' '.join(pip_cmd)}{RESET}")
                subprocess.run(pip_cmd, check=True)

            print("✅ Dependencies installed successfully (workstation)")
            return

        # Mac platform: use UV with pyproject.mac.toml
        is_mac = platform == "mac"
        mac_manifest = Path("pyproject.mac.toml")
        if is_mac and mac_manifest.exists():
            # Mac devcontainer flow
            mac_uv_dir = Path(".mac_uv_project")
            mac_uv_dir.mkdir(parents=True, exist_ok=True)
            mac_pyproject = mac_uv_dir / "pyproject.toml"
            mac_pyproject.write_text(mac_manifest.read_text())

            # Copy README.md if it exists (required by some build backends)
            if Path("README.md").exists():
                (mac_uv_dir / "README.md").write_text(Path("README.md").read_text())

            # Ensure lock matches manifest (in mac temp dir)
            print("Ensuring lock file matches pyproject.mac.toml (Mac devcon)…")
            lock_cmd = ["uv", "lock"]
            print(f"Running command: {BLUE}{' '.join(lock_cmd)}{RESET}")
            subprocess.run(
                lock_cmd, check=True, capture_output=True, cwd=str(mac_uv_dir)
            )

            # Sync into the active environment
            if install_project:
                print(
                    "Syncing dependencies into ACTIVE env (project installed separately)…"
                )
                sync_cmd = [
                    "uv",
                    "sync",
                    "--all-groups",
                    "--no-install-project",
                    "--active",
                ]
                print(f"Running command: {BLUE}{' '.join(sync_cmd)}{RESET}")
                subprocess.run(sync_cmd, check=True, cwd=str(mac_uv_dir))

                # Install project from repo root (where source code actually is)
                # Temporarily create pyproject.toml at repo root for UV
                print("Installing project with 'full' extras from repo root…")
                temp_pyproject = False
                backup_created = False
                try:
                    if not Path("pyproject.toml").exists():
                        # Create temp pyproject.toml from platform manifest
                        Path("pyproject.toml").write_text(mac_manifest.read_text())
                        temp_pyproject = True
                    elif Path("pyproject.toml").is_symlink():
                        # Backup existing symlink
                        Path("pyproject.toml").rename("pyproject.toml.sync.bak")
                        Path("pyproject.toml").write_text(mac_manifest.read_text())
                        backup_created = True

                    pip_install_cmd = ["uv", "pip", "install", "-e", ".[full]"]
                    print(f"Running command: {BLUE}{' '.join(pip_install_cmd)}{RESET}")
                    subprocess.run(pip_install_cmd, check=True)
                    print("Project installed with 'full' extras successfully.")
                finally:
                    # Clean up temp pyproject.toml
                    if temp_pyproject and Path("pyproject.toml").exists():
                        Path("pyproject.toml").unlink()
                    if backup_created and Path("pyproject.toml.sync.bak").exists():
                        Path("pyproject.toml.sync.bak").rename("pyproject.toml")
            else:
                print("Syncing dependencies into ACTIVE env (project not installed)…")
                sync_cmd = [
                    "uv",
                    "sync",
                    "--all-groups",
                    "--no-install-project",
                    "--active",
                ]
                print(f"Running command: {BLUE}{' '.join(sync_cmd)}{RESET}")
                subprocess.run(sync_cmd, check=True, cwd=str(mac_uv_dir))
                print("Dependencies synced successfully (project not installed).")
        else:
            # AWS platform (or fallback): use UV with pyproject.aws.toml
            aws_manifest = Path("pyproject.aws.toml")
            if aws_manifest.exists():
                # AWS devcontainer flow (similar to Mac)
                aws_uv_dir = Path(".aws_uv_project")
                aws_uv_dir.mkdir(parents=True, exist_ok=True)
                aws_pyproject = aws_uv_dir / "pyproject.toml"
                aws_pyproject.write_text(aws_manifest.read_text())

                # Copy README.md if it exists (required by some build backends)
                if Path("README.md").exists():
                    (aws_uv_dir / "README.md").write_text(Path("README.md").read_text())

                # Ensure lock matches manifest (in aws temp dir)
                print("Ensuring lock file matches pyproject.aws.toml (AWS devcon)…")
                lock_cmd = ["uv", "lock"]
                print(f"Running command: {BLUE}{' '.join(lock_cmd)}{RESET}")
                subprocess.run(
                    lock_cmd, check=True, capture_output=True, cwd=str(aws_uv_dir)
                )

                # Sync into the active environment
                if install_project:
                    print(
                        "Syncing dependencies into ACTIVE env (project installed separately)…"
                    )
                    sync_cmd = [
                        "uv",
                        "sync",
                        "--all-groups",
                        "--no-install-project",
                        "--active",
                    ]
                    print(f"Running command: {BLUE}{' '.join(sync_cmd)}{RESET}")
                    subprocess.run(sync_cmd, check=True, cwd=str(aws_uv_dir))

                    # Install project from repo root (where source code actually is)
                    # Temporarily create pyproject.toml at repo root for UV
                    print("Installing project with 'full' extras from repo root…")
                    temp_pyproject = False
                    backup_created = False
                    try:
                        if not Path("pyproject.toml").exists():
                            # Create temp pyproject.toml from platform manifest
                            Path("pyproject.toml").write_text(aws_manifest.read_text())
                            temp_pyproject = True
                        elif Path("pyproject.toml").is_symlink():
                            # Backup existing symlink
                            Path("pyproject.toml").rename("pyproject.toml.sync.bak")
                            Path("pyproject.toml").write_text(aws_manifest.read_text())
                            backup_created = True

                        pip_install_cmd = ["uv", "pip", "install", "-e", ".[full]"]
                        print(
                            f"Running command: {BLUE}{' '.join(pip_install_cmd)}{RESET}"
                        )
                        subprocess.run(pip_install_cmd, check=True)
                        print("Project installed with 'full' extras successfully.")
                    finally:
                        # Clean up temp pyproject.toml
                        if temp_pyproject and Path("pyproject.toml").exists():
                            Path("pyproject.toml").unlink()
                        if backup_created and Path("pyproject.toml.sync.bak").exists():
                            Path("pyproject.toml.sync.bak").rename("pyproject.toml")
                else:
                    print(
                        "Syncing dependencies into ACTIVE env (project not installed)…"
                    )
                    sync_cmd = [
                        "uv",
                        "sync",
                        "--all-groups",
                        "--no-install-project",
                        "--active",
                    ]
                    print(f"Running command: {BLUE}{' '.join(sync_cmd)}{RESET}")
                    subprocess.run(sync_cmd, check=True, cwd=str(aws_uv_dir))
                    print("Dependencies synced successfully (project not installed).")
            else:
                print(
                    "Error: No platform-specific manifest found (pyproject.aws.toml, pyproject.mac.toml, or pyproject.workstation.toml)"
                )
                sys.exit(1)

    except subprocess.CalledProcessError as e:
        stderr_output = e.stderr.decode() if e.stderr else "No stderr output."
        print(f"Error occurred during dependency installation/sync: {e}")
        print(f"Stderr: {stderr_output}")
        if "NoSolution" in stderr_output:
            print(
                "\nHint: Could not find a compatible set of dependencies. Check constraints in pyproject.toml."
            )
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'uv' command not found. Is uv installed and in PATH?")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


def _get_all_platform_manifests():
    """Get list of all platform manifests that exist."""
    manifest_files = []
    for fname in [
        "pyproject.aws.toml",
        "pyproject.mac.toml",
        "pyproject.workstation.toml",
    ]:
        if Path(fname).exists():
            manifest_files.append(Path(fname))
    return manifest_files


def _resolve_package_version(package_name: str) -> str | None:
    """Resolve a package version by running uv lock and parsing the lock file.

    Args:
        package_name: Name of the package to resolve

    Returns:
        Resolved version string, or None if resolution failed
    """
    import os

    try:
        # Determine which manifest to use (prefer Mac, then AWS)
        platform = os.environ.get("STUDIO_PLATFORM", "aws")
        manifest_path = None
        uv_dir = None

        if platform == "mac" and Path("pyproject.mac.toml").exists():
            manifest_path = Path("pyproject.mac.toml")
            uv_dir = Path(".mac_uv_project")
        elif Path("pyproject.aws.toml").exists():
            manifest_path = Path("pyproject.aws.toml")
            uv_dir = Path(".aws_uv_project")
        elif Path("pyproject.mac.toml").exists():
            # Fallback to Mac if AWS doesn't exist
            manifest_path = Path("pyproject.mac.toml")
            uv_dir = Path(".mac_uv_project")
        else:
            return None

        # Create temp directory and copy manifest
        uv_dir.mkdir(parents=True, exist_ok=True)
        (uv_dir / "pyproject.toml").write_text(manifest_path.read_text())

        # Copy README if it exists
        if Path("README.md").exists():
            (uv_dir / "README.md").write_text(Path("README.md").read_text())

        # Run uv lock (suppress output)
        subprocess.run(["uv", "lock"], cwd=str(uv_dir), check=True, capture_output=True)

        # Parse lock file
        lock_file = uv_dir / "uv.lock"
        if not lock_file.exists():
            return None

        lock_data = toml.load(lock_file)
        for package in lock_data.get("package", []):
            if package.get("name") == package_name:
                return package.get("version")

        return None

    except Exception as e:
        print(f"Warning: Failed to resolve version: {e}")
        return None


def _update_all_manifests_for_dayhoff_tools(new_version: str):
    """Update dayhoff-tools constraint in all platform manifests."""
    import re

    manifest_files = _get_all_platform_manifests()

    if not manifest_files:
        print("Warning: No platform manifests found to update.")
        return

    package_name = "dayhoff-tools"
    package_name_esc = re.escape(package_name)

    # Regex to match the dependency line, with optional extras and version spec
    pattern = re.compile(
        rf"^(\s*['\"]){package_name_esc}(\[[^]]+\])?(?:[><=~^][^'\"]*)?(['\"].*)$",
        re.MULTILINE,
    )

    new_constraint_text = f">={new_version}"

    def _repl(match: re.Match):
        prefix = match.group(1)
        extras = match.group(2) or ""
        suffix = match.group(3)
        return f"{prefix}{package_name}{extras}{new_constraint_text}{suffix}"

    # Update all manifest files
    for manifest_file in manifest_files:
        try:
            print(f"Updating {manifest_file} version constraint...")
            content = manifest_file.read_text()
            new_content, num_replacements = pattern.subn(_repl, content)
            if num_replacements > 0:
                manifest_file.write_text(new_content)
                print(
                    f"Updated dayhoff-tools constraint in {manifest_file} to '{new_constraint_text}'"
                )
            else:
                print(
                    f"Warning: Could not find dayhoff-tools dependency line in {manifest_file}"
                )
        except Exception as e:
            print(f"Error updating {manifest_file}: {e}")


def add_dependency(
    package: str,
    dev: bool = typer.Option(
        False, "--dev", "-d", help="Add to dev dependencies instead of main."
    ),
):
    """Add a dependency to all platform-specific manifests.

    Args:
        package: Package specification (e.g., "numpy>=1.24.0" or "pandas")
        dev: If True, add to [dependency-groups] dev instead of [project] dependencies
    """
    import re

    # ANSI color codes
    BLUE = "\033[94m"
    RESET = "\033[0m"

    manifest_files = _get_all_platform_manifests()

    if not manifest_files:
        print(
            "Error: No platform-specific manifests found (pyproject.aws.toml, pyproject.mac.toml, or pyproject.workstation.toml)"
        )
        sys.exit(1)

    # Determine section to add to
    section_name = "dev dependencies" if dev else "main dependencies"
    print(f"Adding '{package}' to {section_name} in all platform manifests...")

    # Parse package name to check for duplicates and version specs
    package_name = re.split(r"[<>=~!\[]", package)[0].strip()
    has_version_spec = any(c in package for c in ["<", ">", "=", "~", "!"])

    added_count = 0

    for manifest_file in manifest_files:
        try:
            content = manifest_file.read_text()

            # Check if package already exists
            existing_check = re.search(
                rf'^(\s*["\']){re.escape(package_name)}[<>=~!\[]',
                content,
                re.MULTILINE,
            )
            if existing_check:
                print(
                    f"⚠️  Package '{package_name}' already exists in {manifest_file}, skipping"
                )
                continue

            if dev:
                # Add to [dependency-groups] dev section
                # Use line-by-line parsing to handle [] in dependency names like dayhoff-tools[full]
                lines = content.split("\n")
                in_dev_groups = False
                in_dev_list = False
                dev_start_idx = None
                dev_end_idx = None

                for idx, line in enumerate(lines):
                    if re.match(r"\s*\[dependency-groups\]", line):
                        in_dev_groups = True
                        continue
                    if in_dev_groups and re.match(r"\s*dev\s*=\s*\[", line):
                        in_dev_list = True
                        dev_start_idx = idx
                        continue
                    if in_dev_list and re.match(r"^\s*\]\s*$", line):
                        dev_end_idx = idx
                        break

                if dev_start_idx is None or dev_end_idx is None:
                    print(
                        f"Warning: Could not find [dependency-groups] dev section in {manifest_file}"
                    )
                    continue

                # Insert new dependency before the closing ]
                new_dep = f'    "{package}",'
                lines.insert(dev_end_idx, new_dep)
                new_content = "\n".join(lines)
            else:
                # Add to [project] dependencies section
                # Use line-by-line parsing to handle [] in dependency names like dayhoff-tools[full]
                lines = content.split("\n")
                in_deps = False
                deps_start_idx = None
                deps_end_idx = None

                for idx, line in enumerate(lines):
                    if re.match(r"\s*dependencies\s*=\s*\[", line):
                        in_deps = True
                        deps_start_idx = idx
                        continue
                    if in_deps and re.match(r"^\s*\]\s*$", line):
                        deps_end_idx = idx
                        break

                if deps_start_idx is None or deps_end_idx is None:
                    print(
                        f"Warning: Could not find dependencies section in {manifest_file}"
                    )
                    continue

                # Insert new dependency before the closing ]
                new_dep = f'    "{package}",'
                lines.insert(deps_end_idx, new_dep)
                new_content = "\n".join(lines)

            manifest_file.write_text(new_content)
            print(f"✅ Added '{package}' to {manifest_file}")
            added_count += 1

        except Exception as e:
            print(f"Error updating {manifest_file}: {e}")

    # If nothing was added, exit early
    if added_count == 0:
        print(f"\n⚠️  Package '{package_name}' already exists in all manifests")
        return

    print(f"\n✅ Added '{package}' to {added_count} platform manifest(s)")

    # If no version specified, resolve and add version constraint
    if not has_version_spec:
        print(f"\n🔍 Resolving version for '{package_name}'...")
        resolved_version = _resolve_package_version(package_name)

        if resolved_version:
            print(f"📌 Resolved to version {resolved_version}")
            print(
                f"Updating manifests with version constraint '>={resolved_version}'..."
            )

            # Update all manifests to add version constraint
            for manifest_file in manifest_files:
                try:
                    content = manifest_file.read_text()
                    # Replace unversioned package with versioned one
                    pattern = re.compile(
                        rf'^(\s*["\']){re.escape(package_name)}(["\'],?)(.*)$',
                        re.MULTILINE,
                    )

                    def replace_with_version(match):
                        prefix = match.group(1)
                        suffix = match.group(2)
                        rest = match.group(3)
                        return (
                            f"{prefix}{package_name}>={resolved_version}{suffix}{rest}"
                        )

                    new_content = pattern.sub(replace_with_version, content)
                    manifest_file.write_text(new_content)
                    print(f"✅ Updated {manifest_file} with version constraint")
                except Exception as e:
                    print(f"Warning: Could not update version in {manifest_file}: {e}")

            print(
                f"\n✅ Added '{package_name}>={resolved_version}' to {added_count} platform manifest(s)"
            )
        else:
            print(
                f"⚠️  Could not resolve version for '{package_name}', left unversioned"
            )

    print(
        f"\nRun {BLUE}dh tomlsync{RESET} to install the new dependency in your environment."
    )


def remove_dependency(
    package: str,
    dev: bool = typer.Option(
        False, "--dev", "-d", help="Remove from dev dependencies instead of main."
    ),
):
    """Remove a dependency from all platform-specific manifests.

    Args:
        package: Package name (e.g., "numpy" or "pandas")
        dev: If True, remove from [dependency-groups] dev instead of [project] dependencies
    """
    import re

    # ANSI color codes
    BLUE = "\033[94m"
    RESET = "\033[0m"

    manifest_files = _get_all_platform_manifests()

    if not manifest_files:
        print(
            "Error: No platform-specific manifests found (pyproject.aws.toml, pyproject.mac.toml, or pyproject.workstation.toml)"
        )
        sys.exit(1)

    section_name = "dev dependencies" if dev else "main dependencies"
    print(f"Removing '{package}' from {section_name} in all platform manifests...")

    # Escape package name for regex
    package_esc = re.escape(package)

    removed_count = 0
    for manifest_file in manifest_files:
        try:
            content = manifest_file.read_text()

            # Pattern to match the dependency line (with optional version spec)
            # Matches:  "package...",  or  "package...",\n (including the newline)
            pattern = re.compile(
                rf'^\s*["\']({package_esc}[<>=~!\[].+?|{package_esc})["\'],?\s*(?:#.*)?$\n?',
                re.MULTILINE,
            )

            new_content, num_removed = pattern.subn("", content)

            if num_removed > 0:
                # Clean up any consecutive blank lines (more than one)
                new_content = re.sub(r"\n\n\n+", "\n\n", new_content)
                # Also clean up trailing whitespace on lines
                new_content = re.sub(r"[ \t]+$", "", new_content, flags=re.MULTILINE)
                manifest_file.write_text(new_content)
                print(f"✅ Removed '{package}' from {manifest_file}")
                removed_count += 1
            else:
                print(f"⚠️  Package '{package}' not found in {manifest_file}")

        except Exception as e:
            print(f"Error updating {manifest_file}: {e}")

    if removed_count > 0:
        print(f"\n✅ Removed '{package}' from {removed_count} platform manifest(s)")
        print(
            f"\nRun {BLUE}dh tomlsync{RESET} to uninstall the dependency from your environment."
        )
    else:
        print(f"\n⚠️  Package '{package}' was not found in any manifests")


def update_dependencies(
    update_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Update all dependencies instead of just dayhoff-tools.",
    ),
):
    """Update dependencies to newer versions (platform-aware).

    - Default Action (no flags): Updates only 'dayhoff-tools' package to latest,
      updates ALL manifest files with the version constraint, and syncs.
    - Flags:
      --all/-a: Updates all dependencies and syncs.

    Cross-platform behavior:
    - Workstation: Uses pip to upgrade packages, regenerates constraints.txt
    - Mac/AWS: Uses UV with platform-specific manifests (.mac_uv_project or .aws_uv_project)
    - Always updates ALL platform manifests (pyproject.aws.toml, pyproject.mac.toml,
      pyproject.workstation.toml) to ensure version consistency
    """
    # ANSI color codes
    BLUE = "\033[94m"
    RESET = "\033[0m"

    platform = os.environ.get("STUDIO_PLATFORM", "aws")

    # Workstation platform: use pip upgrade
    if platform == "workstation" and Path("pyproject.workstation.toml").exists():
        print("Updating dependencies for workstation platform (using pip)...")

        if update_all:
            print("Error: --all flag not supported on workstation platform yet.")
            print("Use 'pip install --upgrade <package>' manually for now.")
            sys.exit(1)

        # Update dayhoff-tools only (default behavior)
        print("Upgrading dayhoff-tools to latest version...")
        upgrade_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "dayhoff-tools[full]",
        ]
        print(f"Running command: {BLUE}{' '.join(upgrade_cmd)}{RESET}")
        subprocess.run(upgrade_cmd, check=True)

        # Get new version
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "dayhoff-tools"],
            capture_output=True,
            text=True,
            check=True,
        )
        version_line = [
            l for l in result.stdout.split("\n") if l.startswith("Version:")
        ]
        if version_line:
            new_version = version_line[0].split(":", 1)[1].strip()
            print(f"Updated to dayhoff-tools {new_version}")

            # Update all platform manifests with new constraint
            _update_all_manifests_for_dayhoff_tools(new_version)

        print("✅ Dependencies updated successfully (workstation)")
        return

    # Mac/AWS platforms: use UV
    mac_manifest = Path("pyproject.mac.toml")
    aws_manifest = Path("pyproject.aws.toml")
    mac_uv_dir = Path(".mac_uv_project")
    aws_uv_dir = Path(".aws_uv_project")
    lock_file_path = Path("uv.lock")

    # Determine action based on flags
    lock_cmd = ["uv", "lock"]
    action_description = ""
    run_pyproject_update = False

    if update_all:
        lock_cmd.append("--upgrade")
        action_description = (
            "Updating lock file for all dependencies to latest versions..."
        )
    else:  # Default behavior: update dayhoff-tools
        lock_cmd.extend(["--upgrade-package", "dayhoff-tools"])
        action_description = (
            "Updating dayhoff-tools lock and pyproject.toml (default behavior)..."
        )
        run_pyproject_update = (
            True  # Only update pyproject if we are doing the dayhoff update
        )

    try:
        # Choose working directory for uv operations based on platform
        uv_cwd = None
        manifest_path_for_constraint = None

        if platform == "mac" and mac_manifest.exists():
            mac_uv_dir.mkdir(parents=True, exist_ok=True)
            (mac_uv_dir / "pyproject.toml").write_text(mac_manifest.read_text())
            # Copy README.md if it exists (required by some build backends)
            if Path("README.md").exists():
                (mac_uv_dir / "README.md").write_text(Path("README.md").read_text())
            uv_cwd = str(mac_uv_dir)
            lock_file_path = mac_uv_dir / "uv.lock"
            manifest_path_for_constraint = mac_manifest
        elif aws_manifest.exists():
            # AWS platform (default)
            aws_uv_dir.mkdir(parents=True, exist_ok=True)
            (aws_uv_dir / "pyproject.toml").write_text(aws_manifest.read_text())
            # Copy README.md if it exists (required by some build backends)
            if Path("README.md").exists():
                (aws_uv_dir / "README.md").write_text(Path("README.md").read_text())
            uv_cwd = str(aws_uv_dir)
            lock_file_path = aws_uv_dir / "uv.lock"
            manifest_path_for_constraint = aws_manifest
        else:
            print(
                "Error: No platform-specific manifest found (pyproject.aws.toml or pyproject.mac.toml)"
            )
            sys.exit(1)

        # Step 1: Run the update lock command
        print(action_description)
        print(f"Running command: {BLUE}{' '.join(lock_cmd)}{RESET}")
        subprocess.run(lock_cmd, check=True, capture_output=True, cwd=uv_cwd)

        # Step 2: Update both manifest files if doing the dayhoff update (default)
        if run_pyproject_update:
            print(f"Reading {lock_file_path} to find new dayhoff-tools version...")
            if not lock_file_path.exists():
                print(f"Error: {lock_file_path} not found after lock command.")
                return
            locked_version = None
            try:
                lock_data = toml.load(lock_file_path)
                for package in lock_data.get("package", []):
                    if package.get("name") == "dayhoff-tools":
                        locked_version = package.get("version")
                        break
            except toml.TomlDecodeError as e:
                print(f"Error parsing {lock_file_path}: {e}")
                return
            except Exception as e:
                print(f"Error reading lock file: {e}")
                return

            if not locked_version:
                print(
                    f"Error: Could not find dayhoff-tools version in {lock_file_path}."
                )
                return

            print(f"Found dayhoff-tools version {locked_version} in lock file.")

            # Update all platform manifest files to ensure consistency
            _update_all_manifests_for_dayhoff_tools(locked_version)

        # Step 3: Sync environment
        print("Syncing environment with updated lock file...")
        # Always use --no-install-project for updates
        sync_cmd = ["uv", "sync", "--all-groups", "--no-install-project", "--active"]
        print(f"Running command: {BLUE}{' '.join(sync_cmd)}{RESET}")
        subprocess.run(sync_cmd, check=True, cwd=uv_cwd)

        # Final status message
        if update_all:
            print("All dependencies updated and environment synced successfully.")
        else:  # Default case (dayhoff update)
            print(
                "dayhoff-tools updated, manifest files modified, and environment synced successfully."
            )

    except subprocess.CalledProcessError as e:
        stderr_output = e.stderr.decode() if e.stderr else "No stderr output."
        print(f"Error occurred during dependency update/sync: {e}")
        print(f"Stderr: {stderr_output}")
        if "NoSolution" in stderr_output:
            print(
                "\nHint: Could not find a compatible set of dependencies. Check constraints in pyproject.toml."
            )
        elif "unrecognized arguments: --upgrade" in stderr_output:
            print(
                "\nHint: Your version of 'uv' might be too old to support '--upgrade'. Try updating uv."
            )
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'uv' command not found. Is uv installed and in PATH?")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
