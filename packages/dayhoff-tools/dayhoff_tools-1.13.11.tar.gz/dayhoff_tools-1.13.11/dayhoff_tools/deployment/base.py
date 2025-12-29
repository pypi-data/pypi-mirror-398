"""Base functionality for container deployment across cloud providers.

This module provides the core functionality for building and running containers,
which can then be used locally or deployed to various cloud providers.
"""

import datetime
import hashlib
import os
import subprocess
from typing import List

import torch
import typer
import yaml
from dayhoff_tools.deployment.deploy_aws import push_image_to_ecr, submit_aws_batch_job
from dayhoff_tools.deployment.deploy_gcp import submit_gcp_batch_job
from dayhoff_tools.deployment.deploy_utils import (
    get_container_env_vars,
    move_to_repo_root,
)


def _generate_image_tag(versioning: str) -> str:
    """Generate a Docker image tag based on versioning strategy.

    The tag is generated based on the specified versioning strategy:
    - For 'latest': Simply returns 'latest'
    - For 'unique': Generates a tag combining timestamp and content hash
                   Format: YYYYMMDD_HHMMSS_<8_char_hash>
                   The hash is computed from all Python and shell files in src/
                   to detect code changes.

    Args:
        versioning: Either 'unique' or 'latest'

    Returns:
        Generated tag string
    """
    if versioning == "latest":
        return "latest"

    # Generate unique tag based on timestamp and content hash
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create hash of relevant files to detect code changes
    hasher = hashlib.sha256()
    for root, _, files in os.walk("src"):
        for file in sorted(files):  # Sort for reproducibility
            if file.endswith((".py", ".sh")):  # Add other relevant extensions
                filepath = os.path.join(root, file)
                with open(filepath, "rb") as f:
                    hasher.update(f.read())

    content_hash = hasher.hexdigest()[:8]  # First 8 chars are sufficient
    return f"{timestamp}_{content_hash}"


def _build_image_uri(config: dict) -> str:
    """Build the full image URI from config.

    The URI is constructed in one of two ways:
    1. If image_uri is provided in config:
       - For 'unique' versioning: Use the provided URI as is
       - For 'latest' versioning: Ensure the URI ends with :latest
    2. If image_uri is empty or not provided:
       - Use the registry_uri and repository from cloud-specific config
       - Combine with base_name and generated tag

    Args:
        config: Dictionary containing docker configuration

    Returns:
        Complete image URI

    Raises:
        ValueError: If cloud is not specified or invalid
        ValueError: If registry_uri or repository is missing for the selected cloud
    """
    docker_config = config["docker"]

    # Handle provided image URI
    if docker_config.get("image_uri"):
        uri = docker_config["image_uri"]
        if docker_config["image_versioning"] == "latest" and not uri.endswith(
            ":latest"
        ):
            uri = uri.split(":")[0] + ":latest"
        return uri

    # Get cloud provider from config
    cloud = config.get("cloud")
    if not cloud:
        raise ValueError("cloud must be specified when image_uri is not provided")
    if cloud not in ["aws", "gcp"]:
        raise ValueError(f"Invalid cloud provider: {cloud}. Must be one of: aws, gcp")

    # Get cloud-specific configuration
    cloud_config = config.get(cloud, {})
    registry_uri = cloud_config.get("registry_uri")
    if not registry_uri:
        raise ValueError(
            f"{cloud}.registry_uri must be specified when image_uri is not provided"
        )

    repository = cloud_config.get("repository")
    if not repository:
        raise ValueError(
            f"{cloud}.repository must be specified when image_uri is not provided"
        )

    # Ensure registry_uri doesn't end with slash
    registry_uri = registry_uri.rstrip("/")

    base_name = docker_config["base_name"]
    tag = _generate_image_tag(docker_config["image_versioning"])

    # For AWS ECR, the base_name becomes part of the tag
    if cloud == "aws":
        return f"{registry_uri}/{repository}:{base_name}-{tag}"

    # For GCP, include base_name in path
    return f"{registry_uri}/{repository}/{base_name}:{tag}"


def build_job_image(config: dict) -> str:
    """Build a Docker image based on configuration.

    This function handles the complete image building process:
    1. Ensures we're in the repo root
    2. Cleans Docker config to avoid credential helper conflicts
    3. Constructs the image URI based on config
    4. Builds the image using docker build

    Args:
        config: Dictionary containing the configuration loaded from YAML.
               The docker.image_versioning field can be either:
               - "unique": Generate a unique tag based on timestamp and content hash
               - "latest": Use the :latest tag for reusability

               If docker.image_uri is provided:
               - For "unique" versioning: Use the provided URI as is
               - For "latest" versioning: Ensure the URI ends with :latest

    Returns:
        str: The complete image URI with appropriate tag
    """
    move_to_repo_root()

    # Clean Docker config to avoid VS Code dev container credential helper conflicts
    from dayhoff_tools.deployment.deploy_utils import clean_docker_config

    clean_docker_config()

    # Get image URI
    image_uri = _build_image_uri(config)
    docker_config = config["docker"]

    print("\nBuilding Docker image: ", image_uri)
    print(f"Using Dockerfile: {docker_config['dockerfile']}")
    print(f"Using shared memory: {docker_config['shared_memory']}")
    platform = docker_config.get("platform", "linux/amd64")
    print(f"Building for platform: {platform}\n")

    # Build the image
    build_image_command = [
        "docker",
        "build",
        f"--shm-size={docker_config['shared_memory']}",
        "-f",
        docker_config["dockerfile"],
        "-t",
        image_uri,
    ]

    # Add platform specification if provided, default to linux/amd64 for cloud deployments
    platform = docker_config.get("platform", "linux/amd64")
    build_image_command.extend(["--platform", platform])

    # Add build context
    build_image_command.append(".")  # Use the root of the repo as image context
    subprocess.run(build_image_command, check=True)

    # Get and print image size
    image_info = subprocess.check_output(
        ["docker", "images", "--format", "{{.Size}}", image_uri], encoding="utf-8"
    ).strip()
    print(f"\nBuilt image size: {image_info}")

    return image_uri


def _build_docker_run_command(
    config: dict,
    image_uri: str,
    container_name: str,
    env_vars: dict,
    mode: str,
) -> List[str]:
    """Build the docker run command with all necessary options.

    This function constructs the complete docker run command, including:
    - Mode-specific options (--rm, -d, -it)
    - GPU support if available
    - Container name
    - Environment variables
    - Entrypoint and command
    - Privileged mode if specified
    - Volume mounts if specified

    Args:
        config: Configuration dictionary
        image_uri: URI of the image to run
        container_name: Name for the container
        env_vars: Environment variables to pass to container
        mode: Deployment mode (local, shell, batch)

    Returns:
        List of command parts ready for subprocess.run

    Raises:
        ValueError: If placeholder strings are found in volume paths during local mode.
    """
    command = [
        "docker",
        "run",
        f"--shm-size={config['docker']['shared_memory']}",
    ]

    # Add mode-specific options
    if mode == "local":
        command += ["--rm", "-d"]  # Remove container after exit, run detached
    elif mode == "shell":
        command += ["--rm", "-it"]  # Remove container after exit, interactive TTY

    # Add privileged mode if specified
    if config["docker"].get("privileged", False):
        print("Container will run in privileged mode")
        command += ["--privileged"]

    # Add volume mounts if specified
    if "volumes" in config["docker"]:
        # Check for placeholder strings in local mode before adding volumes
        if mode == "local":
            for volume in config["docker"]["volumes"]:
                if "<YOUR_USERNAME>" in volume or "<YOUR_REPO_NAME>" in volume:
                    raise ValueError(
                        f"Placeholder string found in volume path: '{volume}'. "
                        "Please replace <YOUR_USERNAME> and <YOUR_REPO_NAME> in your "
                        "local YAML configuration file's 'volumes' section."
                    )
        # Add validated volumes to the command
        for volume in config["docker"]["volumes"]:
            print(f"Adding volume mount: {volume}")
            command += ["-v", volume]

    # Add GPU support if available
    if torch.cuda.is_available():
        print("Container has access to GPU")
        command += ["--gpus", "all"]
    else:
        print("Container has access to CPU only, no GPU")

    # Add container name
    command += ["--name", container_name]

    # Add environment variables
    for key, value in env_vars.items():
        command += ["-e", f"{key}={value}"]

    # Add image and command
    if mode == "local":
        # For detached mode, use bash -c to execute the command
        entrypoint = config["docker"].get(
            "container_entrypoint", ["python", "swarm/main.py"]
        )
        if isinstance(entrypoint, str):
            entrypoint = [entrypoint]
        cmd_str = " ".join(entrypoint)
        command += ["--entrypoint", "/bin/bash", image_uri, "-c", cmd_str]
    else:
        # For shell mode, just use bash as entrypoint
        command += ["--entrypoint", "/bin/bash", image_uri]

    return command


def run_container(config: dict, image_uri: str, mode: str) -> None:
    """Run a container based on deployment mode.

    This function handles the complete container lifecycle:
    1. Generates a unique container name
    2. Collects all necessary environment variables
    3. Builds and executes the docker run command
    4. Handles container logs for detached mode

    The container name is generated using:
    - Username (from LOCAL_USER or USER env var)
    - Timestamp (YYYYMMDD_HHMMSS format)

    Args:
        config: Dictionary containing the configuration loaded from YAML
        image_uri: URI of the Docker image to run
        mode: Deployment mode (local, shell, batch)

    Raises:
        ValueError: If deployment mode is invalid
        subprocess.CalledProcessError: If container fails to start or run
    """
    if mode not in ["local", "shell"]:
        raise ValueError(
            f"Invalid deployment mode: {mode}. Must be one of: local, shell"
        )

    # Generate unique container name
    username = os.getenv("LOCAL_USER") or os.getenv("USER", "unknown_user")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    container_name = f"{username}_job_{timestamp}"

    # Get environment variables
    env_vars = get_container_env_vars(config)

    # Build and run the container
    command = _build_docker_run_command(
        config, image_uri, container_name, env_vars, mode
    )

    # Handle container execution based on mode
    print(f"Running container in {mode} mode: {container_name}")

    if mode == "shell":
        # Simple case: Run interactively with TTY, command will block until container exits
        subprocess.run(command, check=True)
    elif mode == "local":
        # Complex case: Run in background and handle logs
        try:
            # Start the container in detached mode
            subprocess.run(command, check=True)

            # Once container is started, immediately follow its logs
            # This helps users see what's happening without having to run 'docker logs' manually
            print("\nDetached container logs:")
            log_command = ["docker", "logs", "-f", container_name]
            subprocess.run(log_command, check=True)
        except subprocess.CalledProcessError as e:
            # If anything goes wrong (either during startup or while running),
            # try to get any available logs to help with debugging
            print("\nContainer failed. Attempting to retrieve logs:")
            try:
                # Don't use -f here as the container has likely already stopped
                subprocess.run(["docker", "logs", container_name], check=True)
            except subprocess.CalledProcessError:
                # If we can't get logs, container probably failed to start
                print(
                    "No logs available. Container didn't start or failed immediately."
                )
                print("Try running it in shell mode to get more information.")
            raise e  # Re-raise the original error


def deploy(
    mode: str = typer.Argument(help="Deployment mode. Options: local, shell, batch"),
    config_path: str = typer.Argument(help="Path to the YAML configuration file"),
) -> None:
    """Deploy a job based on configuration from a YAML file.

    This is the main entry point for all deployments. It handles:
    1. Validating the deployment mode
    2. Loading and validating the configuration
    3. Building or using an existing image
    4. Running the container locally or delegating to cloud-specific batch deployment

    Args:
        mode: Deployment mode to use. Options: local, shell, batch
        config_path: Path to the YAML configuration file

    Raises:
        ValueError: If deployment mode is invalid
        ValueError: If cloud field is not specified or invalid for batch mode
    """
    # Validate mode
    valid_modes = ["local", "shell", "batch"]
    if mode not in valid_modes:
        raise ValueError(
            f"Invalid mode: {mode}. Must be one of: {', '.join(valid_modes)}"
        )

    # Load YAML configuration
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # For batch mode, check cloud provider and credentials early
    if mode == "batch":
        cloud = config.get("cloud")
        if not cloud:
            raise ValueError(
                "cloud field must be specified in configuration for batch mode"
            )
        if cloud not in ["aws", "gcp"]:
            raise ValueError(f"Invalid cloud: {cloud}. Must be one of: aws, gcp")

        # Check AWS credentials early if using AWS
        if cloud == "aws":
            print("\nVerifying AWS credentials...")
            from dayhoff_tools.deployment.deploy_aws import get_boto_session

            # This will validate credentials and throw an appropriate error if they're invalid
            get_boto_session(config)
            print("AWS credentials verified.")

        # Check GCP credentials early if using GCP
        elif cloud == "gcp":
            print("\nVerifying GCP credentials...")
            from dayhoff_tools.cli.cloud_commands import (
                _is_adc_authenticated,
                _is_gcp_user_authenticated,
            )

            user_creds_valid = _is_gcp_user_authenticated()
            adc_creds_valid = _is_adc_authenticated()

            if not user_creds_valid:
                print(
                    "\n⚠️  Warning: Your GCP user credentials appear to be stale/expired."
                )
                print(
                    "   This may cause authentication issues when deploying to GCP Batch."
                )
                print("   Consider running 'dh gcp login' to refresh your credentials.")

            if not adc_creds_valid:
                print(
                    "\n⚠️  Warning: Your Application Default Credentials (ADC) appear to be stale/expired."
                )
                print(
                    "   This may cause authentication issues with API client libraries."
                )
                print(
                    "   Consider running 'dh gcp use-user-adc' or 'dh gcp use-devcon-adc' to refresh your ADC."
                )

            if user_creds_valid and adc_creds_valid:
                print("GCP credentials verified.")
            else:
                # Ask for confirmation before proceeding with possibly invalid credentials
                proceed = (
                    input("\nProceed with potentially invalid credentials? (y/n): ")
                    .lower()
                    .strip()
                )
                if proceed != "y":
                    print("Deployment aborted.")
                    return

    # Track if we built a new image
    had_image_uri = bool(config["docker"]["image_uri"])

    # Build or use existing image
    image_uri = build_job_image(config)

    if mode in ["local", "shell"]:
        run_container(config, image_uri, mode)
        return

    # Handle batch mode
    cloud = config.get("cloud")
    # We already validated cloud above, so no need to check again

    # Push image if we built it
    if not had_image_uri:
        if cloud == "aws":
            push_image_to_ecr(image_uri, config)
        else:  # cloud == "gcp"
            print("\nPushing image to Artifact Registry")
            registry = config["gcp"]["registry_uri"].split("/")[
                0
            ]  # e.g. "us-central1-docker.pkg.dev"
            print(f"Configuring Docker authentication for {registry}")
            subprocess.run(
                ["gcloud", "auth", "configure-docker", registry, "--quiet"],
                check=True,
            )
            subprocess.run(["docker", "push", image_uri], check=True)
            print(f"Pushed image to Artifact Registry: {image_uri}")

    # Submit batch job
    if cloud == "aws":
        job_id, job_name = submit_aws_batch_job(image_uri, config)
        print(f"\nSubmitted AWS Batch job '{job_name}' with ID: {job_id}")
    else:  # cloud == "gcp"
        submit_gcp_batch_job(config, image_uri)
        print(f"\nSubmitted GCP Batch job: {config['gcp']['job_name']}")
