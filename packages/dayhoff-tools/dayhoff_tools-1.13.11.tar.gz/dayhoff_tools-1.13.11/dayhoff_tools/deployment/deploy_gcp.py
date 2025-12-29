"""GCP-specific deployment functionality."""

import json
import os
import subprocess
import tempfile

from dayhoff_tools.deployment.deploy_utils import get_container_env_vars


def check_job_exists(job_name: str, region: str) -> bool:
    """Check if a job with the given name already exists in GCP Batch.

    Args:
        job_name: Name of the job to check
        region: GCP region to check in

    Returns:
        bool: True if the job exists, False otherwise

    Note:
        This uses gcloud batch jobs describe, which will return a non-zero
        exit code if the job doesn't exist.
    """
    try:
        subprocess.run(
            [
                "gcloud",
                "batch",
                "jobs",
                "describe",
                job_name,
                "--location",
                region,
            ],
            check=True,
            capture_output=True,  # Suppress output
        )
        return True
    except subprocess.CalledProcessError:
        return False


def create_batch_job_config(config: dict, image_uri: str) -> dict:
    """Create a GCP Batch job configuration from YAML config.

    Args:
        config: Dictionary containing the configuration loaded from YAML
        image_uri: URI of the Docker image to use

    Returns:
        Dictionary containing GCP Batch job configuration

    Raises:
        ValueError: If the configuration contains unexpected keys.
    """
    gcp_config = config["gcp"]

    # Validate top-level gcp_config keys used for Batch job JSON construction
    EXPECTED_GCP_CONFIG_KEYS = {
        "allocation_policy",  # Goes into batch_config.allocationPolicy
        "logs_policy",  # Goes into batch_config.logsPolicy
        "batch_job",  # Contains detailed task and resource specs
        "image_uri",
        # Keys like job_name, region, registry_uri, repository are used by other functions
        # or for other purposes, not directly for constructing the core batch_config JSON here.
    }
    actual_gcp_keys = set(gcp_config.keys())
    # Filter out keys not relevant to this function's direct Batch config construction
    # These keys are used by the calling context or other parts of the deployment.
    keys_to_ignore_for_this_check = {"job_name", "region", "registry_uri", "repository"}
    relevant_gcp_keys = {
        key for key in actual_gcp_keys if key not in keys_to_ignore_for_this_check
    }

    unhandled_gcp_keys = relevant_gcp_keys - EXPECTED_GCP_CONFIG_KEYS
    if unhandled_gcp_keys:
        raise ValueError(
            f"Unexpected keys in 'gcp' configuration section: {unhandled_gcp_keys}. "
            f"Expected keys for Batch job JSON construction are: {EXPECTED_GCP_CONFIG_KEYS}"
        )

    # Validate keys within gcp_config["batch_job"]
    if "batch_job" not in gcp_config:
        raise ValueError("Missing 'batch_job' section in 'gcp' configuration.")

    gcp_batch_job_config = gcp_config["batch_job"]
    EXPECTED_GCP_BATCH_JOB_KEYS = {
        "taskCount",
        "parallelism",
        "computeResource",
        "instance",  # Contains machineType, accelerators
        "volumes",
    }
    actual_batch_job_keys = set(gcp_batch_job_config.keys())
    unhandled_batch_job_keys = actual_batch_job_keys - EXPECTED_GCP_BATCH_JOB_KEYS
    if unhandled_batch_job_keys:
        raise ValueError(
            f"Unexpected keys in 'gcp.batch_job' configuration section: {unhandled_batch_job_keys}. "
            f"Expected keys are: {EXPECTED_GCP_BATCH_JOB_KEYS}"
        )

    # Start with the allocation and logs policies
    batch_config = {
        "allocationPolicy": gcp_config["allocation_policy"],
        "logsPolicy": gcp_config["logs_policy"],
    }

    entrypoint_command = config["docker"].get("container_entrypoint")
    if entrypoint_command is None:
        raise ValueError("docker.container_entrypoint is required in configuration")

    if not isinstance(entrypoint_command, list) or not all(
        isinstance(x, str) for x in entrypoint_command
    ):
        raise ValueError("docker.container_entrypoint must be a list of strings")

    # Build the container configuration with bash entrypoint
    container_config = {
        "imageUri": image_uri,
        "entrypoint": "/bin/bash",
        "commands": ["-c", " ".join(entrypoint_command)],
    }

    # Handle container options - both shared memory and any custom options
    docker_options = []

    # Add shared memory option if specified
    if "shared_memory" in config.get("docker", {}):
        docker_options.append(f"--shm-size={config['docker']['shared_memory']}")

    # Add any custom Docker options if specified
    if "options" in config.get("docker", {}):
        docker_options.append(config["docker"]["options"])

    # Set the options field if any options were collected
    if docker_options:
        container_config["options"] = " ".join(docker_options)

    # Build the task group configuration
    task_group = {
        "taskCount": gcp_batch_job_config["taskCount"],
        "parallelism": gcp_batch_job_config["parallelism"],
        "taskSpec": {
            "computeResource": gcp_batch_job_config["computeResource"],
            "runnables": [{"container": container_config}],
        },
    }

    # Get all environment variables, including special ones like WANDB_API_KEY and GCP credentials
    env_vars = get_container_env_vars(config)

    # Add environment variables if any exist
    if env_vars:
        task_group["taskSpec"]["runnables"][0]["environment"] = {"variables": env_vars}

    # Add volumes to the taskSpec if specified in the config
    if "volumes" in gcp_batch_job_config and gcp_batch_job_config["volumes"]:
        task_group["taskSpec"]["volumes"] = gcp_batch_job_config["volumes"]

    # Add machine type and optional accelerators from instance config
    instance_config = gcp_batch_job_config["instance"]
    if "machineType" in instance_config:
        # Add machine type to the allocation policy
        if "policy" not in batch_config["allocationPolicy"]["instances"]:
            batch_config["allocationPolicy"]["instances"]["policy"] = {}
        batch_config["allocationPolicy"]["instances"]["policy"]["machineType"] = (
            instance_config["machineType"]
        )

    # Add accelerators if present (optional)
    if "accelerators" in instance_config:
        batch_config["allocationPolicy"]["instances"]["policy"]["accelerators"] = (
            instance_config["accelerators"]
        )

    # Add the task group to the configuration
    batch_config["taskGroups"] = [task_group]

    # Debug logging to verify configuration
    print("\nGCP Batch Configuration:")
    print("------------------------")
    try:
        policy = batch_config["allocationPolicy"]["instances"]["policy"]
        print("Machine Type:", policy.get("machineType", "Not specified"))
        print("Accelerators:", policy.get("accelerators", "Not specified"))
        print("Environment Variables:", list(env_vars.keys()))
        if (
            "runnables" in task_group["taskSpec"]
            and task_group["taskSpec"]["runnables"]
        ):
            print(
                "Container Options:",
                task_group["taskSpec"]["runnables"][0]
                .get("container", {})
                .get("options", "Not specified"),
            )

    except KeyError as e:
        print(f"Warning: Could not find {e} in configuration")

    return batch_config


def submit_gcp_batch_job(config: dict, image_uri: str) -> None:
    """Submit a job to GCP Batch.

    Args:
        config: Dictionary containing the configuration loaded from YAML
        image_uri: URI of the Docker image to use

    Raises:
        ValueError: If a job with the same name already exists
    """
    job_name = config["gcp"]["job_name"]
    region = config["gcp"]["region"]

    # Check if job already exists
    if check_job_exists(job_name, region):
        raise ValueError(
            f"Job '{job_name}' already exists in region {region}. "
            "Please choose a different job name or delete the existing job first."
        )

    # Create GCP Batch job configuration
    batch_config = create_batch_job_config(config, image_uri)

    # Write the configuration to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        json.dump(batch_config, temp_file, indent=2)
        temp_config_path = temp_file.name

    try:
        # Submit the job using gcloud
        command = [
            "gcloud",
            "batch",
            "jobs",
            "submit",
            job_name,
            "--location",
            region,
            "--config",
            temp_config_path,
        ]
        subprocess.run(command, check=True)
    finally:
        # Clean up the temporary file
        os.unlink(temp_config_path)
