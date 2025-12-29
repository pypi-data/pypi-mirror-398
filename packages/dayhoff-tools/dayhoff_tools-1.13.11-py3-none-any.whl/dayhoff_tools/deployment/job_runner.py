"""Job runner for container-based deployments.

This module serves as the unified entry point for both setup and execution modes.
It can be run in three ways:
1. dh job setup - Only performs environment setup
2. dh job execute - Only executes the command (assumes setup is done)
3. dh job setup_and_execute - Performs setup and then executes (default)

Configuration is provided through environment variables:
- JOB_COMMAND: Command to execute (if any)
- REPO_ROOT: Optional path to repository root directory (for container environments)
- GOOGLE_APPLICATION_CREDENTIALS_BASE64: Enables GCP authentication when present
- USE_DVC: Set to "true" to enable DVC (requires GCP auth)
- USE_RXNFP: Set to "true" to enable RXNFP library
- FAIL_WITHOUT_GPU: Set to "true" to fail if GPU is unavailable

Additional environment variables are preserved and passed to the job orchestrator.
"""

import logging
import os
import subprocess
import sys

import typer
from dayhoff_tools.deployment.deploy_utils import (
    SystemMonitor,
    authenticate_gcp,
    move_to_repo_root,
    setup_dvc,
    setup_rxnfp,
)
from dayhoff_tools.logs import configure_logs

logger = logging.getLogger(__name__)


def run_setup() -> None:
    """Run all enabled setup steps.

    Each setup function checks its own requirements and skips if not enabled.
    """
    logger.info("Starting job setup")

    # Only log important environment variables
    important_vars = [
        "JOB_COMMAND",
        "REPO_ROOT",
        "USE_DVC",
        "USE_RXNFP",
        "FAIL_WITHOUT_GPU",
    ]
    for key in important_vars:
        if key in os.environ:
            logger.info(f"{key}={os.environ[key]}")

    move_to_repo_root()

    # Run setup steps
    authenticate_gcp()  # Checks for GOOGLE_APPLICATION_CREDENTIALS_BASE64
    setup_dvc()  # Checks for USE_DVC="true"
    setup_rxnfp()  # Checks for USE_RXNFP="true"
    logger.info("Setup completed successfully")


def run_command() -> None:
    """Execute the job command if specified.

    Raises:
        ValueError: If no job command is specified
    """
    job_command = os.getenv("JOB_COMMAND")
    if not job_command:
        raise ValueError("No job command specified")

    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Executing job command: {job_command}")

    # Start monitoring if FAIL_WITHOUT_GPU is enabled
    monitor = None
    if os.getenv("FAIL_WITHOUT_GPU", "").lower() == "true":
        logger.info("Starting system monitoring...")
        monitor = SystemMonitor(fail_without_gpu=True)
        monitor.start()

    try:
        # Run command directly, allowing output to flow to parent process
        # This avoids buffering issues and simplifies logging
        result = subprocess.run(
            job_command,
            shell=True,
            check=True,
            stdout=None,  # Use parent's stdout
            stderr=None,  # Use parent's stderr
        )

        logger.info("Job command completed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Job command failed with return code: {e.returncode}")
        raise
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        raise
    finally:
        if monitor:
            logger.info("Stopping system monitor")
            monitor.stop()


def run_job(
    mode: str = typer.Argument(
        default="setup_and_execute",
        help="Mode to run in: setup (setup only), execute (execute only), or setup_and_execute (both)",
    )
) -> None:
    """Run a job command in the specified mode.

    This function executes the job command given by the JOB_COMMAND environment variable,
    if it is present. This method is meant for use in job containers after deployment.

    Args:
        mode: The execution mode to use. One of:
            - setup: Only performs environment setup
            - execute: Only executes the command (assumes setup is done)
            - setup_and_execute: Performs setup and then executes (default)

    Raises:
        ValueError: If an invalid mode is specified
        Exception: If any step of the process fails
    """
    # Configure logging first thing
    configure_logs()
    logger = logging.getLogger(__name__)

    logger.info(f"Job runner starting in mode: {mode}")
    import importlib.metadata

    try:
        version = importlib.metadata.version("dayhoff-tools")
        logger.info(f"dayhoff-tools version: {version}")
    except importlib.metadata.PackageNotFoundError:
        logger.warning("Could not determine dayhoff-tools version")

    if mode not in ["setup", "execute", "setup_and_execute"]:
        logger.error(f"Invalid mode: {mode}")
        raise ValueError(f"Invalid mode: {mode}")

    try:
        # Run in appropriate mode
        if mode in ["setup", "setup_and_execute"]:
            run_setup()

        if mode in ["execute", "setup_and_execute"]:
            run_command()

    except Exception as e:
        logger.error(f"Job failed with error: {str(e)}", exc_info=True)
        sys.exit(1)
