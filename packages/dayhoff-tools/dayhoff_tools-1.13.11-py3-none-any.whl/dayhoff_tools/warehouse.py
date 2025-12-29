import os
import subprocess
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path
from zoneinfo import ZoneInfo

# Import cloud helper lazily inside functions to avoid heavy deps at module load


def _find_project_root() -> Path | None:
    """
    Find the project root by searching upwards from the current directory for
    a `.git` directory or a `pyproject.toml` file.

    Returns:
        The path to the project root, or None if not found.
    """
    current_dir = Path.cwd().resolve()
    while current_dir != current_dir.parent:
        if (current_dir / ".git").is_dir() or (
            current_dir / "pyproject.toml"
        ).is_file():
            return current_dir
        current_dir = current_dir.parent
    # Check the final directory in the hierarchy (e.g., '/')
    if (current_dir / ".git").is_dir() or (current_dir / "pyproject.toml").is_file():
        return current_dir
    return None


def _warn_if_gcp_default_sa(force_prompt: bool = False) -> None:
    """Warn the user when the active gcloud principal is the default VM service
    account.  See detailed docstring later in file (duplicate for early
    availability)."""

    from dayhoff_tools.cli import cloud_commands as _cc

    try:
        impersonation = _cc._get_current_gcp_impersonation()
        user = _cc._get_current_gcp_user()
        active = impersonation if impersonation != "None" else user
        short = _cc._get_short_name(active)

        # Determine if user creds are valid
        auth_valid = _cc._is_gcp_user_authenticated()
    except Exception:
        # If any helper errors out, don't block execution
        return

    problem_type = None  # "default_sa" | "stale"
    if short == "default VM service account":
        problem_type = "default_sa"
    elif not auth_valid:
        problem_type = "stale"

    if problem_type is None:
        return  # Everything looks good

    YELLOW = getattr(_cc, "YELLOW", "\033[0;33m")
    BLUE = getattr(_cc, "BLUE", "\033[0;36m")
    RED = getattr(_cc, "RED", "\033[0;31m")
    NC = getattr(_cc, "NC", "\033[0m")

    if problem_type == "default_sa":
        msg_body = (
            f"You are currently authenticated as the *default VM service account*.\n"
            f"   This will block gsutil/DVC access to private buckets (e.g. warehouse)."
        )
    else:  # stale creds
        msg_body = (
            f"Your GCP credentials appear to be *expired/stale*.\n"
            f"   Re-authenticate to refresh the access token."
        )

    print(
        f"{YELLOW}⚠  {msg_body}{NC}\n"
        f"{YELLOW}   Run {BLUE}dh gcp login{YELLOW} or {BLUE}dh gcp use-devcon{YELLOW} before retrying.{NC}",
        file=sys.stderr,
    )

    if force_prompt and sys.stdin.isatty() and sys.stdout.isatty():
        import questionary

        if not questionary.confirm("Proceed anyway?", default=False).ask():
            print(f"{RED}Aborted due to unsafe GCP credentials.{NC}", file=sys.stderr)
            raise SystemExit(1)


def human_readable_size(size_bytes):
    """Convert size in bytes to a human-readable format"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_yaml_with_meta_spacing(yaml_str: str) -> str:
    """
    Format YAML content with blank lines between top-level sections and meta subsections.
    Avoids adding duplicate blank lines.
    """
    lines = yaml_str.split("\n")
    formatted_lines = []
    in_meta = False
    meta_depth = 0
    last_line_blank = True  # Start true to avoid adding blank line at the beginning

    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line == "meta:":
            in_meta = True
            meta_depth = 0
            if not last_line_blank:
                formatted_lines.append("")  # Add a blank line before 'meta:' if needed
            formatted_lines.append(line)
            if (
                i + 1 < len(lines) and lines[i + 1].strip()
            ):  # Check if next line is not blank
                formatted_lines.append(
                    ""
                )  # Add a blank line after 'meta:' only if needed
            last_line_blank = True
        elif in_meta:
            if stripped_line and not line.startswith("  "):
                in_meta = False
                if not last_line_blank:
                    formatted_lines.append(
                        ""
                    )  # Add a blank line before leaving 'meta' if needed
                formatted_lines.append(line)
                last_line_blank = False
            else:
                current_depth = len(line) - len(line.lstrip())
                if current_depth == 2 and meta_depth >= 2 and not last_line_blank:
                    formatted_lines.append(
                        ""
                    )  # Add a blank line before new top-level category in meta if needed
                formatted_lines.append(line)
                meta_depth = current_depth
                last_line_blank = not stripped_line
        else:
            if stripped_line and not line.startswith(" ") and not last_line_blank:
                formatted_lines.append(
                    ""
                )  # Add a blank line before top-level keys if needed
            formatted_lines.append(line)
            last_line_blank = not stripped_line

    return "\n".join(formatted_lines).rstrip() + "\n"


def update_dvc_files(directory):
    """Traverse directory and update .dvc files with human-readable size, preserving existing formatting"""
    from ruamel.yaml import YAML

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".dvc"):
                file_path = Path(root) / file
                with open(file_path, "r") as f:
                    dvc_content = yaml.load(f)

                if "outs" in dvc_content and dvc_content["outs"]:
                    size_bytes = dvc_content["outs"][0].get("size", 0)
                    human_size = human_readable_size(size_bytes)

                    if "meta" not in dvc_content:
                        dvc_content["meta"] = {}

                    # Create a new ordered dict with 'size' as the first item
                    new_meta = {"size": human_size}
                    new_meta.update(dvc_content["meta"])
                    dvc_content["meta"] = new_meta

                # Convert the updated content to a string and format it
                string_stream = StringIO()
                yaml.dump(dvc_content, string_stream)
                formatted_content = format_yaml_with_meta_spacing(
                    string_stream.getvalue()
                )

                with open(file_path, "w") as f:
                    f.write(formatted_content)

                print(f"Updated {file_path}")


def import_from_warehouse(
    warehouse_path: str,
    output_folder: str = "same_as_warehouse",
    branch: str = "main",
    logger=None,
) -> str:
    """Import a file from warehouse, or update if it exists already.

    Args:
        warehouse_path (str): The relative path to a .dvc file in the
                warehouse submodule of the current repo.
                eg, 'warehouse/data/toy/2seqs.fasta.dvc'
        output_folder (str): A folder where the file will be imported.
                eg, 'data/raw/'. Defaults to the same folder as the
                original location in warehouse.
        branch (str): The branch of warehouse to import from.

    Returns: The path to the imported/updated file.
    """
    assert warehouse_path.startswith(
        "warehouse"
    ), "expected the relative path to start with 'warehouse'"
    assert warehouse_path.endswith(
        ".dvc"
    ), "expected the relative path to end with '.dvc'"

    if branch != "main":
        if logger:
            logger.warning("You should usually import data from main.")
        else:
            print("WARNING: You should usually import data from main.\n")

    # Remove extra slashes
    if output_folder.endswith("/"):
        output_folder = output_folder[:-1]

    # The core path is the same within warehouse and in the
    # local data folder where the file will be imported by default
    core_path = warehouse_path[len("warehouse/") : -len(".dvc")]
    filename = core_path.split("/")[-1]

    command = [
        "dvc",
        "import",
        "https://github.com/dayhofflabs/warehouse",
        core_path,
    ]

    if output_folder == "same_as_warehouse":
        final_path = core_path
        final_folder = "/".join(final_path.split("/")[:-1])
    else:
        final_folder = output_folder
        final_path = final_folder + "/" + filename

    os.makedirs(final_folder, exist_ok=True)
    command += ["--out", final_path, "--rev", branch]

    if os.path.exists(final_path):
        # Update existing file.  This re-writes if it doesn't match origin,
        # and also updates the .dvc file.
        if logger:
            logger.info(
                "File already exists. Will `dvc update` instead of `dvc import`."
            )
        else:
            print(f"File already exists. Will `dvc update` instead of `dvc import`.")
        subprocess.run(
            ["dvc", "update", final_path + ".dvc", "--rev", branch], check=True
        )
    else:
        if logger:
            logger.info(f"Importing from warehouse: {final_path}")
        else:
            print(f"Importing from warehouse: {final_path}")
        subprocess.run(command, check=True)

    # Copy meta section from warehouse_path to final_path.dvc
    from ruamel.yaml import YAML

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    # Read the original warehouse .dvc file
    with open(warehouse_path, "r") as f:
        warehouse_content = yaml.load(f)

    # Read the newly created/updated .dvc file
    final_dvc_path = final_path + ".dvc"
    with open(final_dvc_path, "r") as f:
        final_dvc_content = yaml.load(f)

    # Copy the meta section if it exists in the warehouse file
    if "meta" in warehouse_content:
        final_dvc_content["meta"] = warehouse_content["meta"]

    # Convert the updated content to a string and format it
    string_stream = StringIO()
    yaml.dump(final_dvc_content, string_stream)
    formatted_content = format_yaml_with_meta_spacing(string_stream.getvalue())

    # Write the formatted content back to the file
    with open(final_dvc_path, "w") as f:
        f.write(formatted_content)

    if logger:
        logger.info(f"Updated {final_dvc_path} with meta section from {warehouse_path}")
    else:
        print(f"Updated {final_dvc_path} with meta section from {warehouse_path}")

    return final_path


def add_to_warehouse(
    warehouse_path: str,
    ancestor_dvc_paths: list[str],
) -> str:
    """Upload a file to warehouse, using `dvc add`, and edit its .dvc file
    to add information about ancestors.
    Args:
        warehouse_path (str): The relative path (in warehouse) where the new
                                data file should go.
        ancestor_dvc_paths (list[str]): A list of all the paths to the frozen
                        .dvc files that were produced when importing the
                        ancestors to this file.
    Returns: The path to the new .dvc file.
    Raises:
        ValueError: If the function is executed outside of the repo's root directory.
        ValueError: If an ancestor .dvc file is not frozen.
    """

    print(f"Uploading to Warehouse: {warehouse_path}")
    assert warehouse_path.startswith(
        "warehouse/"
    ), "expected the relative path to start with 'warehouse/'"
    warehouse_path = warehouse_path.replace("warehouse/", "")

    # Process each ancestor .dvc file
    ancestors = []
    from ruamel.yaml import YAML

    yaml_loader = YAML()
    yaml_loader.preserve_quotes = True
    yaml_loader.indent(mapping=2, sequence=4, offset=2)
    for path in ancestor_dvc_paths:
        assert path.endswith(".dvc"), "ERROR: Not a .dvc file"
        with open(path, "r") as file:
            ancestor_content = yaml_loader.load(file)

            # Check if the .dvc file is frozen
            if (
                "frozen" not in ancestor_content
                or ancestor_content["frozen"] is not True
            ):
                raise ValueError(
                    f"Error: Not a frozen .dvc file generated by 'dvc import': {path}"
                )

            ancestor_info = {
                "name": os.path.basename(ancestor_content["outs"][0]["path"]),
                "file_md5_hash": ancestor_content["outs"][0]["md5"],
                "repo_url": ancestor_content["deps"][0]["repo"]["url"],
                "repo_path": ancestor_content["deps"][0]["path"],
                "commit_hash": ancestor_content["deps"][0]["repo"]["rev_lock"],
            }

            # Add the optional "git_branch" field if available
            if "rev" in ancestor_content["deps"][0]["repo"]:
                ancestor_info["git_branch"] = ancestor_content["deps"][0]["repo"]["rev"]

            ancestors.append(ancestor_info)

    # Change the working directory to the warehouse folder
    os.chdir("warehouse")

    # Add and push the data file
    subprocess.run(["dvc", "add", warehouse_path], check=True)

    # Read the generated .dvc file
    dvc_file_path = f"{warehouse_path}.dvc"
    with open(dvc_file_path, "r") as file:
        dvc_content = yaml_loader.load(file)

    # Add the ancestors' information
    dvc_content["ancestors"] = ancestors

    # Get the human-readable size
    size_bytes = dvc_content["outs"][0]["size"]
    human_size = human_readable_size(size_bytes)

    # Write this, plus more metadata, back to the .dvc file
    today = datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%d")

    # Use ruamel.yaml's ScalarString for block-style literal formatting
    from ruamel.yaml.scalarstring import LiteralScalarString

    description = LiteralScalarString("MISSING_METADATA\nMISSING_METADATA")

    yaml_content = {
        "outs": dvc_content["outs"],
        "meta": {
            "size": human_size,
            "date_created": today,
            "author": "MISSING_METADATA",
            "description": description,
            "transformation_source_code": [
                "MISSING_METADATA",
            ],
            "ancestors": dvc_content["ancestors"],
        },
    }

    # Convert the updated content to a string and format it
    string_stream = StringIO()
    yaml_loader.dump(yaml_content, string_stream)
    formatted_content = format_yaml_with_meta_spacing(string_stream.getvalue())

    # Write the formatted content back to the file
    with open(dvc_file_path, "w") as file:
        file.write(formatted_content)

    # Point the user to the updated .dvc file
    print(f"\033[92m\n\nMade .dvc file: {dvc_file_path}\033[0m")
    print(
        f"\033[92mRemember to manually fill out the missing metadata fields.\n\033[0m"
    )

    subprocess.run(["dvc", "push"], check=True)
    os.chdir("..")

    return "warehouse/" + dvc_file_path


def get_from_warehouse(
    warehouse_path: str,
    output_folder: str = "same_as_warehouse",
    branch: str = "main",
    logger=None,
) -> str:
    """`dvc get` a file from warehouse.

    Args:
        warehouse_path (str): The relative path to a .dvc file in the
                warehouse submodule of the current repo.
                eg, 'warehouse/data/toy/2seqs.fasta.dvc'
        output_folder (str): A folder where the file will be imported.
                eg, 'data/raw/'. Defaults to the same folder as the
                original location in warehouse.
        branch (str): The branch of warehouse to import from.

    Returns: The path to the imported/updated file.
    Raises:
        ValueError: If the function is executed outside of the repo's root directory.
    """

    assert warehouse_path.startswith(
        "warehouse"
    ), "expected the relative path to start with 'warehouse'"
    assert warehouse_path.endswith(
        ".dvc"
    ), "expected the relative path to end with '.dvc'"

    if branch != "main":
        if logger:
            logger.warning("You should usually import data from main.")
        else:
            print("WARNING: You should usually import data from main.\n")

    # Remove extra slashes
    if output_folder.endswith("/"):
        output_folder = output_folder[:-1]

    # The core path is the same within warehouse and in the
    # local data folder where the file will be imported by default
    core_path = warehouse_path[len("warehouse/") : -len(".dvc")]
    filename = core_path.split("/")[-1]

    command = [
        "dvc",
        "get",
        "https://github.com/dayhofflabs/warehouse",
        core_path,
    ]

    if output_folder == "same_as_warehouse":
        final_path = core_path
        final_folder = "/".join(final_path.split("/")[:-1])
    else:
        final_folder = output_folder
        final_path = final_folder + "/" + filename

    os.makedirs(final_folder, exist_ok=True)
    command += ["--out", final_path, "--rev", branch]

    if os.path.exists(final_path):
        # Update existing file.  This re-writes if it doesn't match origin,
        # and also updates the .dvc file.
        if logger:
            logger.info("File already exists. Will exit without changing.")
        else:
            print(f"File already exists. Will exit without changing.")
    else:
        if logger:
            logger.info(f"Getting from warehouse: {final_path}")
        else:
            print(f"Getting from warehouse: {final_path}")
        subprocess.run(command, check=True)

    return final_path


def get_ancestry(filepath: str) -> None:
    """Take a .dvc file created from import, and generate an ancestry entry
    that can be manually copied into other .dvc files."""
    with open(filepath, "r") as file:
        assert filepath.endswith(".dvc"), "ERROR: Not a .dvc file"
        import yaml

        ancestor_content = yaml.safe_load(file)

        error_msg = "Unexpected file structure. Are you sure this is a .dvc file generated from `dvc import`?"
        assert "deps" in ancestor_content, error_msg

        error_msg = "Please only reference data imported from main branches."
        assert "rev" not in ancestor_content["deps"][0]["repo"], error_msg

        ancestor_info = {
            "name": os.path.basename(ancestor_content["outs"][0]["path"]),
            "file_md5_hash": ancestor_content["outs"][0]["md5"],
            "size": ancestor_content["outs"][0]["size"],
            "repo_url": ancestor_content["deps"][0]["repo"]["url"],
            "repo_path": ancestor_content["deps"][0]["path"],
            "commit_hash": ancestor_content["deps"][0]["repo"]["rev_lock"],
        }
        print()
        yaml.safe_dump(
            [ancestor_info], sys.stdout, default_flow_style=False, sort_keys=False
        )


def import_from_warehouse_typer() -> None:
    """Import a file from warehouse.

    Emits an early warning if the active GCP credentials are the *default VM
    service account* because this will prevent DVC/gsutil from accessing the
    warehouse bucket.  The user can abort the command when running
    interactively.
    """

    # Early-exit guard for wrong GCP credentials
    _warn_if_gcp_default_sa(force_prompt=True)

    # Import only when the function is called
    import questionary

    # Ensure execution from root directory
    project_root = _find_project_root()
    cwd = Path.cwd()
    if not project_root or project_root != cwd:
        error_msg = (
            "This command must be run from the project's root directory, which is"
            " expected to contain a `.git` folder or a `pyproject.toml` file.\n"
            f"Current directory: {cwd}"
        )
        if project_root:
            error_msg += f"\nDetected project root: {project_root}"
        raise Exception(error_msg)

    # Use questionary for prompts instead of typer
    warehouse_path = questionary.text("Warehouse path:").ask()

    # Provide multiple-choice options for output folder
    output_folder_choice = questionary.select(
        "Output folder:",
        choices=["data/imports", "same_as_warehouse", "Custom path..."],
    ).ask()

    # If custom path is selected, ask for the path
    if output_folder_choice == "Custom path...":
        output_folder = questionary.text("Enter custom output folder:").ask()
    else:
        output_folder = output_folder_choice

    branch = questionary.text("Branch (default: main):", default="main").ask()

    final_path = import_from_warehouse(
        warehouse_path=warehouse_path,
        output_folder=output_folder,
        branch=branch,
    )


def get_from_warehouse_typer() -> None:
    """Get a file from warehouse using `dvc get`.

    Emits an early warning if the active GCP credentials are the *default VM
    service account* because this will prevent DVC/gsutil from accessing the
    warehouse bucket.  The user can abort the command when running
    interactively.
    """

    # Early-exit guard for wrong GCP credentials
    _warn_if_gcp_default_sa(force_prompt=True)

    # Import only when the function is called
    import questionary

    # Ensure execution from root directory
    project_root = _find_project_root()
    cwd = Path.cwd()
    if not project_root or project_root != cwd:
        error_msg = (
            "This command must be run from the project's root directory, which is"
            " expected to contain a `.git` folder or a `pyproject.toml` file.\n"
            f"Current directory: {cwd}"
        )
        if project_root:
            error_msg += f"\nDetected project root: {project_root}"
        raise Exception(error_msg)

    # Use questionary for prompts instead of typer
    warehouse_path = questionary.text("Warehouse path:").ask()

    # Provide multiple-choice options for output folder
    output_folder_choice = questionary.select(
        "Output folder:",
        choices=["data/imports", "same_as_warehouse", "Custom path..."],
    ).ask()

    # If custom path is selected, ask for the path
    if output_folder_choice == "Custom path...":
        output_folder = questionary.text("Enter custom output folder:").ask()
    else:
        output_folder = output_folder_choice

    branch = questionary.text("Branch (default: main):", default="main").ask()

    final_path = get_from_warehouse(
        warehouse_path=warehouse_path,
        output_folder=output_folder,
        branch=branch,
    )


def add_to_warehouse_typer() -> None:
    """Add a new data file to warehouse and enrich its generated .dvc file.

    As with *dh wimport*, this command fails when the user is logged in with
    the default VM service account.  A guard therefore warns the user first
    and allows them to abort interactively.
    """

    # Early-exit guard for wrong GCP credentials
    _warn_if_gcp_default_sa(force_prompt=True)

    # Import only when the function is called
    import questionary

    # Ensure execution from root directory
    project_root = _find_project_root()
    cwd = Path.cwd()
    if not project_root or project_root != cwd:
        error_msg = (
            "This command must be run from the project's root directory, which is"
            " expected to contain a `.git` folder or a `pyproject.toml` file.\n"
            f"Current directory: {cwd}"
        )
        if project_root:
            error_msg += f"\nDetected project root: {project_root}"
        raise Exception(error_msg)

    # Prompt for the data file path
    warehouse_path = questionary.text("Data file to be registered:").ask()

    # Prompt for the ancestor .dvc file paths
    ancestor_dvc_paths = []
    print("\nEnter the path of all ancestor .dvc files (or hit Enter to finish).")
    print("These files must be generated by `dvc import` or `dh wimport`.")
    while True:
        ancestor_path = questionary.text("Ancestor path: ").ask()
        if ancestor_path:
            ancestor_dvc_paths.append(ancestor_path)
        else:
            print()
            break

    dvc_path = add_to_warehouse(
        warehouse_path=warehouse_path,
        ancestor_dvc_paths=ancestor_dvc_paths,
    )
