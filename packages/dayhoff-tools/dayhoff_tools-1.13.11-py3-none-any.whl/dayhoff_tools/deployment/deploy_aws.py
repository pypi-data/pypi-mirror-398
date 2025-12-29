"""AWS deployment functionality for running jobs on AWS Batch."""

import base64
import datetime
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

import boto3
import yaml
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    ProfileNotFound,
    SSOTokenLoadError,
)
from dayhoff_tools.deployment.deploy_utils import docker_login, get_container_env_vars


def get_boto_session(config: dict[str, Any]) -> boto3.Session:
    """Creates a Boto3 session using the profile specified in the config.

    Args:
        config: Dictionary containing the configuration loaded from YAML

    Returns:
        A Boto3 session object

    Raises:
        RuntimeError: If the profile is not specified in the config or if credentials cannot be loaded
    """
    aws_config = config.get("aws", {})
    profile_name = aws_config.get("aws_profile")
    region = aws_config.get("region", "us-east-1")

    if not profile_name:
        print(
            "Warning: aws.aws_profile not specified in config. Using default AWS credential chain in ~/.aws/config."
        )
        return boto3.Session(region_name=region)

    try:
        print(f"Using AWS profile: {profile_name}")
        session = boto3.Session(profile_name=profile_name, region_name=region)
        sts = session.client("sts")
        sts.get_caller_identity()
        return session
    except ProfileNotFound:
        raise RuntimeError(
            f"AWS profile '{profile_name}' not found in `~/.aws/config`."
        )
    except (NoCredentialsError, ClientError, SSOTokenLoadError) as e:
        raise RuntimeError(
            f"Could not load credentials for AWS profile '{profile_name}'. "
            f"Ensure you are logged in via SSO ('aws sso login --profile {profile_name}') "
            f"or have valid credentials configured. Original error: {e}"
        ) from e


def _extract_run_name_from_config(
    config: dict[str, Any], _test_file_content: Optional[str] = None
) -> Optional[str]:
    """Extract run name from the config file referenced in job_command.

    Args:
        config: Dictionary containing the configuration loaded from YAML
        _test_file_content: Optional parameter for testing to override file content

    Returns:
        Run name if found, None otherwise
    """
    # Check if features and job_command exist in config
    if "features" not in config:
        return None

    # Find job_command in features
    job_command = None
    for feature in config["features"]:
        if isinstance(feature, dict) and "job_command" in feature:
            job_command = feature["job_command"]
            break
        elif isinstance(feature, str) and feature.startswith("job_command:"):
            job_command = feature.split(":", 1)[1].strip()
            break

    if not job_command:
        return None

    # Extract config file path using regex
    config_match = re.search(r'--config=([^\s"]+)', job_command)
    if not config_match:
        return None

    config_path = config_match.group(1)

    # For testing, we can bypass file operations
    if _test_file_content is not None:
        run_config = yaml.safe_load(_test_file_content)
    else:
        # Resolve path relative to repo root
        # Assuming we're in the repo root when this function is called
        full_config_path = Path(config_path)

        # Check if file exists
        if not full_config_path.exists():
            print(f"Warning: Config file {full_config_path} not found")
            return None

        try:
            # Load the config file
            with open(full_config_path, "r") as f:
                run_config = yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Failed to extract run_name from {full_config_path}: {e}")
            return None

    # Extract run_name from wandb section
    if (
        run_config
        and "init" in run_config
        and "wandb" in run_config["init"]
        and "run_name" in run_config["init"]["wandb"]
    ):
        return run_config["init"]["wandb"]["run_name"]

    return None


def _extract_job_name_from_uri(image_uri: str, config: dict[str, Any]) -> str:
    """Extract job name from image URI and config.

    Args:
        image_uri: Full URI of the container image
        config: Dictionary containing the configuration loaded from YAML

    Returns:
        Job name in format: username__jobname__uniquehex

        The job name components are:
        - username: The LOCAL_USER environment variable or "unknown_user"
        - jobname: Either from aws.job_name config, wandb run_name, or omitted
        - uniquehex: A hexadecimal string (typically 7 characters)
          representing seconds since January 1, 2020

        If aws.job_name is specified in the config:
        - If aws.job_name is "use_wandb_run_name", the run_name from the wandb config will be used
        - Otherwise, the specified job_name will be used

        If no job_name is specified or if "use_wandb_run_name" is specified but no run_name is found,
        the format will be username__uniquehex (without the middle component).
    """
    # Get username from environment
    username = os.getenv("LOCAL_USER", "unknown_user")

    # Generate a unique hex string based on seconds since 2020-01-01
    epoch_2020 = datetime.datetime(2020, 1, 1).timestamp()
    current_time = datetime.datetime.now().timestamp()
    seconds_since_2020 = int(current_time - epoch_2020)
    unique_hex = format(
        seconds_since_2020, "x"
    )  # Simple hex representation, typically 7 chars

    # Check if job_name is specified in AWS config
    if "aws" in config and "job_name" in config["aws"]:
        job_name = config["aws"]["job_name"]

        # Special handling for "use_wandb_run_name"
        if job_name == "use_wandb_run_name":
            # Get run name from config
            run_name = _extract_run_name_from_config(config)
            if run_name:
                # Return username__runname__uniquehex
                return f"{username}__{run_name}__{unique_hex}"
        else:
            # Use the specified job_name but format it as username__jobname__uniquehex
            return f"{username}__{job_name}__{unique_hex}"

    # Default behavior if job_name is not specified or "use_wandb_run_name" with no run_name
    # Get run name from config
    run_name = _extract_run_name_from_config(config)

    # Build job name based on available components
    job_name_parts = []

    # Add username (use default if None)
    job_name_parts.append(username or "unknown_user")

    # Add run name if available
    if run_name:
        job_name_parts.append(run_name)

    # Add the unique hex string
    job_name_parts.append(unique_hex)

    # Join parts with double underscores
    return "__".join(job_name_parts)


def push_image_to_ecr(image_uri: str, config: dict[str, Any]) -> None:
    """Push a Docker image to Amazon ECR.

    Args:
        image_uri: Full URI of the image to push
        config: Dictionary containing the configuration loaded from YAML

    Raises:
        subprocess.CalledProcessError: If ECR login or push fails
        ClientError: If ECR authentication fails
    """
    print("\nPushing image to ECR")

    session = get_boto_session(config)
    aws_config = config["aws"]
    registry = aws_config["registry_uri"]

    # Get ECR login token using the specific session client
    ecr_client = session.client("ecr")
    try:
        token = ecr_client.get_authorization_token()
        username, password = (
            base64.b64decode(token["authorizationData"][0]["authorizationToken"])
            .decode()
            .split(":")
        )

        # Login to Docker registry
        docker_login(registry, username, password)

        # Push the image
        print(f"\nPushing image: {image_uri}")
        subprocess.run(["docker", "push", image_uri], check=True)

        print(f"\nSuccessfully pushed image to ECR: {image_uri}")

    except ClientError as e:
        print(f"AWS ECR error using profile '{session.profile_name}': {str(e)}")
        raise
    except subprocess.CalledProcessError as e:
        print(f"Docker command failed: {e.stderr.decode() if e.stderr else str(e)}")
        raise


def create_or_update_job_definition(
    image_uri: str,
    config: dict[str, Any],
) -> str:
    """Create or update a job definition for the container.

    Args:
        image_uri: Full URI of the container image
        config: Dictionary containing the configuration loaded from YAML

    Returns:
        Name of the created/updated job definition

    Raises:
        ValueError: If job_role_arn is not specified in AWS configuration
    """
    session = get_boto_session(config)
    aws_config = config["aws"]

    # Verify that job_role_arn is present
    if "job_role_arn" not in aws_config:
        raise ValueError(
            "job_role_arn must be specified in AWS configuration. "
            "This role is required for your container to access AWS resources after the "
            "initial 15-minute temporary credential window."
        )

    batch = session.client("batch")
    base_name = config["docker"]["base_name"]
    job_def_name = f"job-def-{base_name}"

    # Get compute specs from config
    compute_specs = aws_config["batch_job"]["compute_specs"]
    gpu_requirements = (
        [{"type": "GPU", "value": str(compute_specs["gpus"])}]
        if compute_specs.get("gpus", 0) > 0
        else []
    )

    entrypoint_command = config["docker"].get("container_entrypoint")
    if entrypoint_command is None:
        raise ValueError("docker.container_entrypoint is required in configuration")

    # Create linux parameters with devices
    linux_params: dict[str, Any] = {}
    if compute_specs.get("gpus", 0) > 0:
        linux_params["devices"] = [
            {
                "hostPath": "/dev/nvidia0",
                "containerPath": "/dev/nvidia0",
                "permissions": ["READ", "WRITE"],
            },
        ]

    # Add shared memory configuration if specified in docker config
    if "shared_memory" in config.get("docker", {}):
        shared_mem = config["docker"]["shared_memory"]
        # Convert to MiB (e.g., "16g" -> 16384 MiB)
        if isinstance(shared_mem, str):
            if shared_mem.endswith("g"):
                # Convert GB to MiB (1G = 1024 MiB)
                shared_memory_mib = int(float(shared_mem[:-1]) * 1024)
            elif shared_mem.endswith("m"):
                # Convert MB to MiB (approximate conversion)
                shared_memory_mib = int(float(shared_mem[:-1]))
            else:
                # Assume the value is already in MiB
                shared_memory_mib = int(float(shared_mem))
        else:
            # Assume the value is already in MiB if not a string
            shared_memory_mib = int(shared_mem)

        # Add shared memory size to linux parameters
        linux_params["sharedMemorySize"] = shared_memory_mib
        print(f"Setting shared memory size to {shared_memory_mib} MiB")

    # Prepare containerProperties
    container_properties = {
        "image": image_uri,
        "vcpus": compute_specs["vcpus"],
        "memory": compute_specs["memory"],
        "resourceRequirements": gpu_requirements,
        "executionRoleArn": aws_config["execution_role_arn"],
        "jobRoleArn": aws_config["job_role_arn"],
        "privileged": compute_specs.get("gpus", 0) > 0,
        "command": entrypoint_command,
    }

    if linux_params:
        container_properties["linuxParameters"] = linux_params

    # Add volumes and mount points if defined in AWS batch_job config
    batch_job_config = aws_config.get("batch_job", {})
    if "volumes" in batch_job_config:
        container_properties["volumes"] = batch_job_config["volumes"]
        print(f"Adding volumes to job definition: {batch_job_config['volumes']}")
    if "mountPoints" in batch_job_config:
        container_properties["mountPoints"] = batch_job_config["mountPoints"]
        print(
            f"Adding mount points to job definition: {batch_job_config['mountPoints']}"
        )

    # Mount Primordial Drive if explicitly enabled via feature flag
    # Add 'mount_primordial_drive' to features list to mount shared EFS at /primordial/
    features = config.get("features", []) or []
    features_set = {f if isinstance(f, str) else next(iter(f)) for f in features}
    mount_primordial = "mount_primordial_drive" in features_set

    if mount_primordial:
        primordial_fs_id = get_primordial_fs_id(session)
        if primordial_fs_id:
            print(f"Adding Primordial Drive configuration (fs_id: {primordial_fs_id})")

            # Add volume configuration
            efs_volume = {
                "name": "primordial",
                "efsVolumeConfiguration": {
                    "fileSystemId": primordial_fs_id,
                    "rootDirectory": "/",
                },
            }

            if "volumes" not in container_properties:
                container_properties["volumes"] = []

            # Check if already added to avoid duplicates
            if not any(
                v.get("name") == "primordial" for v in container_properties["volumes"]
            ):
                container_properties["volumes"].append(efs_volume)

            # Add mount point
            mount_point = {
                "sourceVolume": "primordial",
                "containerPath": "/primordial",
                "readOnly": False,
            }

            if "mountPoints" not in container_properties:
                container_properties["mountPoints"] = []

            # Check if already added
            if not any(
                mp.get("containerPath") == "/primordial"
                for mp in container_properties["mountPoints"]
            ):
                container_properties["mountPoints"].append(mount_point)
        else:
            print(
                "Warning: mount_primordial_drive enabled but Primordial Drive not found in this environment"
            )

    # Check if job definition already exists using the session client
    try:
        existing = batch.describe_job_definitions(
            jobDefinitionName=job_def_name, status="ACTIVE"
        )["jobDefinitions"]

        if existing:
            print(f"\nUpdating existing job definition: {job_def_name}")
        else:
            print(f"\nCreating new job definition: {job_def_name}")

    except batch.exceptions.ClientError as e:
        if e.response.get("Error", {}).get(
            "Code"
        ) == "ClientError" and "JobDefinitionNotFoundException" in str(
            e
        ):  # More specific check for not found
            print(f"\nCreating new job definition: {job_def_name}")
        else:
            raise

    # Prepare job definition arguments
    job_definition_args = {
        "jobDefinitionName": job_def_name,
        "type": "container",
        "containerProperties": container_properties,
        "platformCapabilities": ["EC2"],
        "timeout": {"attemptDurationSeconds": aws_config.get("timeout_seconds", 86400)},
    }

    # Add tags if specified in config
    if "tags" in aws_config:
        job_definition_args["tags"] = aws_config["tags"]
        print(f"Adding tags to job definition: {aws_config['tags']}")

    # Register new revision using the session client
    response = batch.register_job_definition(**job_definition_args)

    return response["jobDefinitionName"]


def get_primordial_fs_id(session: boto3.Session) -> Optional[str]:
    """Fetch Primordial Drive EFS ID from SSM.

    Args:
        session: Boto3 session

    Returns:
        FileSystemId if found, None otherwise
    """
    ssm = session.client("ssm")

    # Determine environment from profile name
    # Default to dev if cannot determine
    env = "dev"
    if session.profile_name and "sand" in session.profile_name:
        env = "sand"

    param_name = f"/{env}/primordial/fs_id"

    try:
        response = ssm.get_parameter(Name=param_name)
        return response["Parameter"]["Value"]
    except ClientError as e:
        # Silently fail if not found - Primordial might not be deployed in this env
        # or we might not have permissions
        # ParameterNotFound is a ClientError with error code "ParameterNotFound"
        return None
    except Exception as e:
        print(f"Warning: Failed to check for Primordial Drive: {e}")
        return None


def submit_aws_batch_job(
    image_uri: str,
    config: dict[str, Any],
) -> tuple[str, str]:
    """Submit a job to AWS Batch.

    Args:
        image_uri: Full URI of the container image
        config: Dictionary containing the configuration loaded from YAML

    Returns:
        Tuple containing (job_id, job_name) of the submitted job

    Raises:
        ValueError: If job_role_arn is not present in AWS configuration
    """
    session = get_boto_session(config)
    aws_config = config["aws"]
    region = session.region_name or aws_config["region"]
    batch = session.client("batch")

    # Generate job name (already includes unique hex string)
    job_name = _extract_job_name_from_uri(image_uri, config)
    print(f"\nGenerated job name: {job_name}")

    # Log the job submission details
    print("\nSubmitting job with configuration:")
    print(f"Job Name: {job_name}")
    print(f"Queue: {aws_config['job_queue']}")
    print("Container Configuration:")
    print(f"- Image: {image_uri}")
    print(f"- vCPUs: {aws_config['batch_job']['compute_specs']['vcpus']}")
    print(f"- Memory: {aws_config['batch_job']['compute_specs']['memory']} MiB")
    print(f"- GPUs: {aws_config['batch_job']['compute_specs'].get('gpus', 0)}")
    print(f"- Timeout: {aws_config.get('timeout_seconds', 86400)} seconds")
    print(f"- Job Role: {aws_config['job_role_arn']}")

    # Get all environment variables, including special ones like WANDB_API_KEY and GCP credentials
    env_vars_map = get_container_env_vars(config)  # This returns a dict

    # If EFS is configured for InterProScan, override INTERPROSCAN_INSTALL_DIR
    # Check based on the conventional volume name used in interp_bulk.yaml
    efs_interproscan_mount_path = None
    aws_batch_job_config = aws_config.get("batch_job", {})
    if "mountPoints" in aws_batch_job_config:
        for mp in aws_batch_job_config["mountPoints"]:
            if (
                mp.get("sourceVolume") == "interproscan-efs-volume"
            ):  # Convention from YAML
                efs_interproscan_mount_path = mp.get("containerPath")
                break

    if efs_interproscan_mount_path:
        env_vars_map["INTERPROSCAN_INSTALL_DIR"] = efs_interproscan_mount_path
        print(
            f"INTERPROSCAN_INSTALL_DIR overridden to EFS mount path: {efs_interproscan_mount_path}"
        )

    print(
        "Environment Variables (after potential EFS override):",
        list(env_vars_map.keys()),
    )

    # Create/Update Job Definition using the config (now implicitly uses the correct session)
    job_definition = create_or_update_job_definition(image_uri, config)
    print(f"\nUsing job definition: {job_definition}")

    # Prepare job submission arguments
    job_submit_args = {
        "jobName": job_name,
        "jobQueue": aws_config["job_queue"],
        "jobDefinition": job_definition,
        "containerOverrides": {
            "environment": [
                {"name": key, "value": str(value)}
                for key, value in env_vars_map.items()
            ],
        },
    }

    # Add array job configuration if specified
    if "array_size" in aws_config:
        array_size = aws_config["array_size"]
        if array_size > 1:
            print(f"\nConfiguring as array job with {array_size} instances")
            job_submit_args["arrayProperties"] = {"size": array_size}

    # Configure retry strategy for array jobs
    retry_attempts = aws_config.get("retry_attempts", 2)
    print(f"Setting retry attempts to {retry_attempts}")
    job_submit_args["retryStrategy"] = {"attempts": retry_attempts}

    # Automatically add User tag for cost tracking
    username = os.getenv("LOCAL_USER", "unknown_user")
    default_tags = {"User": username}

    # Merge with any tags specified in config (config tags take precedence)
    if "tags" in aws_config:
        tags = {**default_tags, **aws_config["tags"]}
    else:
        tags = default_tags

    job_submit_args["tags"] = tags
    job_submit_args["propagateTags"] = (
        True  # Propagate tags to ECS tasks and EC2 instances
    )
    print(f"Adding tags to batch job: {tags}")

    # Submit the job using the session client
    response = batch.submit_job(**job_submit_args)

    job_id = response["jobId"]
    print(f"\nJob submitted with ID: {job_id}")

    # Print instructions for monitoring
    print("\nTo monitor your job:")
    print(
        f"  1. AWS Console: https://{region}.console.aws.amazon.com/batch/home?region={region}#jobs/detail/{job_id}"
    )
    print(f"  2. CloudWatch Logs: Check logs for job {job_name} (ID: {job_id})")

    # For array jobs, provide additional monitoring info
    if "array_size" in aws_config and aws_config["array_size"] > 1:
        print(f"  3. This is an array job with {aws_config['array_size']} child jobs")
        print(
            f"     Child jobs: https://{region}.console.aws.amazon.com/batch/home?region={region}#jobs/array-jobs/{job_id}"
        )

    return job_id, job_name
