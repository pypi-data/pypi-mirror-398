"""Utility functions and classes for deployment and system monitoring.

This module provides utilities for:
1. System monitoring (GPU, CPU, memory)
2. Environment setup and authentication
3. DVC and repository configuration
4. Cloud instance metadata and identification
"""

import base64
import json
import logging
import os
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)


def get_instance_metadata(timeout: int = 2) -> Dict[str, str]:
    """
    Get instance metadata from various cloud providers.

    This function attempts to retrieve metadata from GCP, AWS, and other cloud environments.
    It tries different metadata endpoints and returns a consolidated dictionary
    with information about the current cloud instance.

    Args:
        timeout: Timeout in seconds for HTTP requests

    Returns:
        Dictionary containing instance metadata with keys:
        - provider: Cloud provider name ('gcp', 'aws', 'azure', 'unknown')
        - instance_id: Unique instance identifier
        - instance_name: Name of the instance (if available)
        - instance_type: Type/size of the instance (e.g., 't2.micro', 'n1-standard-1')
        - region: Region where the instance is running
        - zone: Availability zone
    """
    metadata = {
        "provider": "unknown",
        "instance_id": "unknown",
        "instance_name": "unknown",
        "instance_type": "unknown",
        "region": "unknown",
        "zone": "unknown",
    }

    # Try GCP metadata
    try:
        headers = {"Metadata-Flavor": "Google"}
        # Check if we're in GCP
        response = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/id",
            headers=headers,
            timeout=timeout,
        )
        if response.status_code == 200:
            metadata["provider"] = "gcp"
            metadata["instance_id"] = response.text

            # Get instance name
            response = requests.get(
                "http://metadata.google.internal/computeMetadata/v1/instance/name",
                headers=headers,
                timeout=timeout,
            )
            if response.status_code == 200:
                metadata["instance_name"] = response.text

            # Get machine type
            response = requests.get(
                "http://metadata.google.internal/computeMetadata/v1/instance/machine-type",
                headers=headers,
                timeout=timeout,
            )
            if response.status_code == 200:
                machine_type_path = response.text
                metadata["instance_type"] = machine_type_path.split("/")[-1]

            # Get zone
            response = requests.get(
                "http://metadata.google.internal/computeMetadata/v1/instance/zone",
                headers=headers,
                timeout=timeout,
            )
            if response.status_code == 200:
                zone_path = response.text
                metadata["zone"] = zone_path.split("/")[-1]
                # Extract region from zone (e.g., us-central1-a -> us-central1)
                if "-" in metadata["zone"]:
                    metadata["region"] = "-".join(metadata["zone"].split("-")[:-1])

            return metadata
    except Exception as e:
        logger.debug(f"Not a GCP instance or metadata server not available: {e}")

    # Try AWS metadata
    try:
        token_response = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            timeout=timeout,
        )
        if token_response.status_code == 200:
            token = token_response.text
            headers = {"X-aws-ec2-metadata-token": token}

            metadata["provider"] = "aws"

            # Get instance ID
            response = requests.get(
                "http://169.254.169.254/latest/meta-data/instance-id",
                headers=headers,
                timeout=timeout,
            )
            if response.status_code == 200:
                metadata["instance_id"] = response.text

            # Get instance type
            response = requests.get(
                "http://169.254.169.254/latest/meta-data/instance-type",
                headers=headers,
                timeout=timeout,
            )
            if response.status_code == 200:
                metadata["instance_type"] = response.text

            # Get availability zone
            response = requests.get(
                "http://169.254.169.254/latest/meta-data/placement/availability-zone",
                headers=headers,
                timeout=timeout,
            )
            if response.status_code == 200:
                metadata["zone"] = response.text
                # Extract region from availability zone (e.g., us-east-1a -> us-east-1)
                metadata["region"] = metadata["zone"][:-1]

            # AWS doesn't provide an instance name directly,
            # but we can use the hostname or instance-id as a fallback
            try:
                response = requests.get(
                    "http://169.254.169.254/latest/meta-data/hostname",
                    headers=headers,
                    timeout=timeout,
                )
                if response.status_code == 200:
                    metadata["instance_name"] = response.text
                else:
                    metadata["instance_name"] = metadata["instance_id"]
            except:
                metadata["instance_name"] = metadata["instance_id"]

            return metadata
    except Exception as e:
        logger.debug(f"Not an AWS EC2 instance or metadata server not available: {e}")

    # Try Azure metadata (if needed in the future)
    # ...

    # As a fallback, try to get some basic info from the host
    try:
        metadata["instance_name"] = socket.gethostname()
        # Check if we're running in a container environment
        if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
            metadata["provider"] = "container"
        # Check batch environment variables
        if os.getenv("BATCH_TASK_INDEX") is not None:
            metadata["provider"] = "gcp-batch"
            metadata["instance_name"] = f"batch-task-{os.getenv('BATCH_TASK_INDEX')}"
        elif os.getenv("AWS_BATCH_JOB_ID") is not None:
            metadata["provider"] = "aws-batch"
            metadata["instance_name"] = f"aws-batch-{os.getenv('AWS_BATCH_JOB_ID')}"
    except Exception as e:
        logger.debug(f"Error getting hostname: {e}")

    return metadata


def get_instance_name() -> str:
    """
    Get the name of the current cloud instance or VM.

    This is a cross-platform replacement for the old get_vm_name() function.
    Works with GCP, AWS, and other environments.

    Returns:
        A string containing the instance name, hostname, or ID
    """
    metadata = get_instance_metadata()
    return metadata["instance_name"]


def get_instance_type() -> str:
    """
    Get the machine type/size of the current cloud instance.

    This is a cross-platform replacement for the old get_vm_type() function.
    Works with GCP (e.g., n1-standard-1), AWS (e.g., t2.micro), and other environments.

    Returns:
        A string representing the instance type/size, or 'unknown' if not available
    """
    metadata = get_instance_metadata()
    return metadata["instance_type"]


def get_cloud_provider() -> str:
    """
    Get the cloud provider where this code is running.

    Returns:
        A string identifying the cloud provider ('gcp', 'aws', 'azure', 'container', 'unknown')
    """
    metadata = get_instance_metadata()
    return metadata["provider"]


def move_to_repo_root() -> None:
    """Move to the repository root directory.

    Determines the repository root through multiple methods (in order):
    1. Direct specification via REPO_ROOT environment variable
    2. Standard marker files (.git, setup.py, pyproject.toml)
    3. Container standard paths (/app if it exists and contains expected files)
    4. NAME_OF_THIS_REPO environment variable (for VM environments)

    Raises:
        OSError: If repository root cannot be determined
    """
    try:
        # Check if REPO_ROOT is directly specified
        if "REPO_ROOT" in os.environ:
            root_path = Path(os.environ["REPO_ROOT"])
            if root_path.exists():
                logger.info(f"Using environment-specified REPO_ROOT: {root_path}")
                os.chdir(root_path)
                return

        # Try to find repo root by looking for standard files
        current = Path.cwd()
        while current != current.parent:
            if any(
                (current / marker).exists()
                for marker in [".git", "setup.py", "pyproject.toml"]
            ):
                logger.info(f"Found repository root at: {current}")
                os.chdir(current)
                return
            current = current.parent

        # Check for container standard paths
        container_paths = ["/app", "/workspace", "/code"]
        for path in container_paths:
            container_root = Path(path)
            if container_root.exists() and any(
                (container_root / subdir).exists()
                for subdir in ["src", "swarm", "dayhoff_tools"]
            ):
                logger.info(f"Using container standard path: {container_root}")
                os.chdir(container_root)
                return

        # Fallback to environment variable if available
        try:
            name_of_this_repo = os.environ["NAME_OF_THIS_REPO"]
            root_path = Path(f"/workspaces/{name_of_this_repo}")
            if root_path.exists():
                logger.info(f"Using workspace repository path: {root_path}")
                os.chdir(root_path)
                return
        except KeyError as e:
            logger.warning(f"NAME_OF_THIS_REPO environment variable not set: {e}")

        # If we're already at what looks like a valid root, just stay here
        if any(
            Path.cwd().joinpath(marker).exists()
            for marker in ["setup.py", "pyproject.toml", "src", "dayhoff_tools"]
        ):
            logger.info(f"Current directory appears to be a valid root: {Path.cwd()}")
            return

        raise OSError("Could not determine repository root")
    except Exception as e:
        logger.error(f"ERROR: Could not move to repository root: {e}")
        raise


def upload_folder_to_gcs(local_folder: str, bucket, gcs_folder: str):
    """
    Upload all files from a local folder to a GCS folder

    Args:
        local_folder: Path to the local folder
        bucket: GCS bucket object
        gcs_folder: Destination folder path in GCS
    """
    local_path = Path(local_folder)

    for local_file in local_path.glob("**/*"):
        if local_file.is_file():
            # Construct the GCS path
            relative_path = local_file.relative_to(local_path)
            gcs_path = f"{gcs_folder.rstrip('/')}/{relative_path}"

            # Upload the file
            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(str(local_file))
            logger.info(f"Uploaded {local_file} to {gcs_path}")


@dataclass
class SystemStats:
    """Container for system statistics."""

    timestamp: str
    vm_id: str
    cpu_usage: float
    mem_usage: float
    gpu_usage: Optional[float]
    disk_usage: float

    def __str__(self) -> str:
        """Format system stats for logging."""
        return (
            f"VM:{self.vm_id} "
            f"CPU:{self.cpu_usage:.1f}% "
            f"MEM:{self.mem_usage:.1f}% "
            f"DISK:{self.disk_usage:.1f}% "
            f"GPU:{self.gpu_usage if self.gpu_usage is not None else 'N/A'}%"
        )


class SystemMonitor:
    """Monitor system resources and GPU availability."""

    def __init__(self, fail_without_gpu: bool = False):
        """Initialize system monitor.

        Args:
            fail_without_gpu: Whether to terminate if GPU becomes unavailable.
        """
        self.fail_without_gpu = fail_without_gpu
        self.should_run = True
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start system monitoring in a background thread."""
        if self._thread is not None:
            return

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop system monitoring."""
        self.should_run = False
        if self._thread is not None:
            self._thread.join()
            self._thread = None

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.should_run:
            try:
                if self.fail_without_gpu and not is_gpu_available():
                    logger.error(
                        f"[{self._get_vm_id()}] GPU became unavailable. Terminating process."
                    )
                    self._kill_wandb()
                    # Force exit the entire process
                    os._exit(1)

                stats = self._get_system_stats()
                logger.info(str(stats))

                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(300)  # Continue monitoring even if there's an error

    def _kill_wandb(self) -> None:
        """Kill wandb agent process."""
        try:
            subprocess.run(["pkill", "-f", "wandb agent"], check=True)
        except subprocess.CalledProcessError:
            pass  # Process might not exist

    def _get_vm_id(self) -> str:
        """Get VM identifier from GCP metadata server."""
        try:
            response = requests.get(
                "http://metadata.google.internal/computeMetadata/v1/instance/id",
                headers={"Metadata-Flavor": "Google"},
                timeout=5,
            )
            return response.text
        except Exception:
            return "unknown"

    def _get_system_stats(self) -> SystemStats:
        """Collect current system statistics."""
        # Get timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Get VM ID
        vm_id = self._get_vm_id()

        # Get CPU usage
        cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'"
        cpu_usage = float(subprocess.check_output(cpu_cmd, shell=True).decode().strip())

        # Get memory usage
        mem_cmd = "free | grep Mem | awk '{print $3/$2 * 100.0}'"
        mem_usage = float(subprocess.check_output(mem_cmd, shell=True).decode().strip())

        # Get GPU usage if available
        gpu_usage = None
        if is_gpu_available():
            try:
                gpu_cmd = "nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits"
                gpu_usage = float(
                    subprocess.check_output(gpu_cmd, shell=True).decode().strip()
                )
            except (subprocess.CalledProcessError, ValueError):
                pass

        # Add disk usage check
        disk_cmd = "df -h / | awk 'NR==2 {print $5}' | sed 's/%//'"
        disk_usage = float(
            subprocess.check_output(disk_cmd, shell=True).decode().strip()
        )

        return SystemStats(
            timestamp, vm_id, cpu_usage, mem_usage, gpu_usage, disk_usage
        )


def is_gpu_available() -> bool:
    """Check if NVIDIA GPU is available.

    Returns:
        bool: True if GPU is available and functioning
    """
    try:
        subprocess.run(["nvidia-smi"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_required_env_var(name: str) -> str:
    """Get an environment variable or raise an error if it's not set"""
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Required environment variable {name} is not set")
    return value


def authenticate_gcp() -> None:
    """Authenticate with Google Cloud Platform.

    Uses GOOGLE_APPLICATION_CREDENTIALS_BASE64 from environment.
    Skips if no credentials are available.
    """
    credentials_base64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_BASE64")
    if not credentials_base64:
        logger.info("No GCP credentials provided, skipping authentication")
        return

    logger.info("Authenticating with Google Cloud")

    # Decode and save credentials
    credentials = base64.b64decode(credentials_base64).decode("utf-8")
    with open("workerbee.json", "w") as f:
        f.write(credentials)

    # Activate service account (suppress survey output)
    subprocess.run(
        ["gcloud", "auth", "activate-service-account", "--key-file=workerbee.json"],
        check=True,
        capture_output=True,
    )

    # Configure project
    subprocess.run(
        ["gcloud", "config", "set", "project", "enzyme-discovery"],
        check=True,
        capture_output=True,
    )
    logger.info("Set project to enzyme-discovery")

    # Verify configuration
    subprocess.run(
        ["gcloud", "config", "get-value", "project"],
        check=True,
        capture_output=True,
    )

    # Get and print active service account
    result = subprocess.run(
        ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
        check=True,
        capture_output=True,
        text=True,
    )
    logger.info(f"Activated service account credentials for: {result.stdout.strip()}")

    # Set explicit credentials path if it exists
    if os.path.exists("workerbee.json"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("workerbee.json")
        logger.info(
            f"Set GOOGLE_APPLICATION_CREDENTIALS to {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}"
        )


def setup_dvc() -> None:
    """Initialize and configure DVC with GitHub remote.

    Only runs if USE_DVC="true" in environment.
    Requires GCP authentication to be already set up.
    """
    if os.getenv("USE_DVC", "").lower() != "true":
        logger.info("DVC not enabled, skipping setup")
        return

    if not os.path.exists("workerbee.json"):
        logger.info("GCP credentials not found, skipping DVC setup")
        return

    logger.info("Initializing DVC")

    # Initialize DVC without git
    subprocess.run(["dvc", "init", "--no-scm"], check=True, capture_output=True)

    # Get GitHub PAT from GCP secrets
    warehouse_pat = subprocess.run(
        [
            "gcloud",
            "secrets",
            "versions",
            "access",
            "latest",
            "--secret=warehouse-read-pat",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    # Configure DVC remote
    subprocess.run(
        [
            "dvc",
            "remote",
            "add",
            "--default",
            "warehouse",
            "https://github.com/dayhofflabs/warehouse.git",
        ],
        check=True,
    )
    subprocess.run(
        ["dvc", "remote", "modify", "warehouse", "auth", "basic"], check=True
    )
    subprocess.run(
        [
            "dvc",
            "remote",
            "modify",
            "warehouse",
            "--local",
            "user",
            "DanielMartinAlarcon",
        ],
        check=True,
    )
    subprocess.run(
        ["dvc", "remote", "modify", "warehouse", "--local", "password", warehouse_pat],
        check=True,
    )

    # Setup GitHub HTTPS access
    git_config_path = Path.home() / ".git-credentials"
    git_config_path.write_text(
        f"https://DanielMartinAlarcon:{warehouse_pat}@github.com\n"
    )
    subprocess.run(
        ["git", "config", "--global", "credential.helper", "store"], check=True
    )


def setup_rxnfp() -> None:
    """Clone rxnfp library.

    Only runs if USE_RXNFP="true" in environment.
    """
    if os.getenv("USE_RXNFP", "").lower() != "true":
        logger.info("RXNFP not enabled, skipping setup")
        return

    logger.info("Cloning rxnfp library...")
    subprocess.run(
        ["git", "clone", "https://github.com/rxn4chemistry/rxnfp.git"], check=True
    )


def clean_docker_config() -> None:
    """Clean Docker configuration to avoid credential helper conflicts.

    VS Code dev containers can set up credential helpers that interfere with
    Docker builds and registry operations. This function creates a clean
    configuration that disables problematic credential helpers.

    This is automatically called before Docker builds and registry operations
    to prevent authentication failures.
    """
    docker_config_dir = os.path.expanduser("~/.docker")
    os.makedirs(docker_config_dir, exist_ok=True)

    # Write a minimal config file that disables credential helpers
    with open(os.path.join(docker_config_dir, "config.json"), "w") as f:
        json.dump({"auths": {}, "credsStore": ""}, f)


def docker_login(registry: str, username: str, password: str) -> None:
    """Login to a Docker registry using provided credentials.

    Args:
        registry: Registry URI to login to
        username: Username for registry authentication
        password: Password for registry authentication

    Raises:
        subprocess.CalledProcessError: If Docker login fails
    """
    # Clean Docker config to avoid credential helper conflicts
    clean_docker_config()

    # Login to Docker using the credentials
    login_process = subprocess.run(
        [
            "docker",
            "login",
            "--username",
            username,
            "--password-stdin",
            registry,
        ],
        input=password.encode(),
        capture_output=True,
        check=True,
    )

    if login_process.stderr:
        logger.warning(f"Docker login warning: {login_process.stderr.decode()}")


def get_container_env_vars(config: dict) -> dict:
    """Get all environment variables for the container.

    This function collects environment variables from multiple sources:
    1. Feature flags from config.features
    2. Feature-specific variables (e.g. WANDB_API_KEY, GCP credentials)
    3. Additional variables specified in config.env_vars

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary of environment variables

    Raises:
        FileNotFoundError: If GCP credentials file is not found when use_gcp_auth is True
    """
    env_vars = {}

    # Process features section to set feature flags
    features = config.get("features")
    # Handle case where features key exists but has no value (None)
    if features is None:
        features = []

    # Handle boolean features that don't have associated credentials
    bool_features = {
        "use_dvc": "USE_DVC",
        "use_rxnfp": "USE_RXNFP",
        "fail_without_gpu": "FAIL_WITHOUT_GPU",
    }

    # Initialize all features to "false"
    for env_var in bool_features.values():
        env_vars[env_var] = "false"

    # Set enabled features to "true"
    for feature in features:
        if isinstance(feature, str) and feature in bool_features:
            env_vars[bool_features[feature]] = "true"
        elif isinstance(feature, dict):
            # Handle job_command if present
            if "job_command" in feature:
                env_vars["JOB_COMMAND"] = feature["job_command"]

    # Add feature-specific variables when their features are enabled
    features_set = {f if isinstance(f, str) else next(iter(f)) for f in features}

    if "use_wandb" in features_set:
        wandb_key = os.getenv("WANDB_API_KEY", "WANDB_API_KEY_NOT_SET")
        env_vars["WANDB_API_KEY"] = wandb_key
        logger.info(f"Loading WANDB_API_KEY into container: {wandb_key}")

    if "use_gcp_auth" in features_set:
        key_file = ".config/workerbee.json"
        if not os.path.exists(key_file):
            raise FileNotFoundError(
                f"GCP credentials file not found: {key_file}. Required when use_gcp_auth=True"
            )

        # base64-encode the workerbee service account key file
        creds = subprocess.run(
            f"base64 {key_file} | tr -d '\n'",
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        env_vars["GOOGLE_APPLICATION_CREDENTIALS_BASE64"] = creds
        logger.info(f"Loaded GCP credentials into container: {key_file}")

    # Get environment variables from config
    config_env_vars = config.get("env_vars")
    # Handle case where env_vars key exists but has no value (None)
    if config_env_vars is None:
        config_env_vars = {}

    # Add them to the envvars made here
    env_vars.update(config_env_vars)

    return env_vars


def determine_worker_count(logger=None) -> int:
    """Determine optimal worker count based on CPU cores and environment.

    Uses different strategies depending on the detected environment:
    - For batch environments (GCP Batch, AWS Batch), uses (CPU_COUNT - 1)
    - For development environments, uses (CPU_COUNT // 2)
    - Always ensures at least 1 worker is returned

    Args:
        logger: Optional logger to output the decision (defaults to None)

    Returns:
        int: Recommended number of worker processes
    """
    import multiprocessing
    import os

    # Detect CPU cores
    cpu_count = multiprocessing.cpu_count()

    # Detect if running in a cloud batch environment:
    # - GCP Batch sets BATCH_TASK_INDEX
    # - AWS Batch sets AWS_BATCH_JOB_ID
    is_batch_env = (
        os.getenv("BATCH_TASK_INDEX") is not None  # GCP Batch
        or os.getenv("AWS_BATCH_JOB_ID") is not None  # AWS Batch
    )

    if is_batch_env:
        # In batch environment, use most cores
        num_workers = max(1, cpu_count - 1)
        if logger:
            logger.info(
                f"Batch environment detected. Using {num_workers} of {cpu_count} cores"
            )
    else:
        # In dev environment, be more conservative
        num_workers = max(1, cpu_count // 2)
        if logger:
            logger.info(
                f"Development environment detected. Using {num_workers} of {cpu_count} cores"
            )

    return num_workers
