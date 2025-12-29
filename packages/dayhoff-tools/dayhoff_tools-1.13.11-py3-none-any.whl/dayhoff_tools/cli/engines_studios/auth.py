"""AWS authentication and identity helpers."""

import boto3
import click
from botocore.exceptions import ClientError, NoCredentialsError, TokenRetrievalError


def detect_aws_environment() -> str:
    """Detect environment (dev/sand/prod) from AWS account ID.

    Returns:
        Environment name: "dev", "sand", or "prod"

    Raises:
        click.ClickException: If account cannot be detected or is not recognized
    """
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        account_id = identity["Account"]

        # Map account IDs to environments (from aws_config)
        account_to_env = {
            "074735440724": "dev",
            "006207983460": "sand",
            "011117009798": "prod",
        }

        env = account_to_env.get(account_id)
        if not env:
            raise click.ClickException(
                f"✗ Unknown AWS account: {account_id}\n\n"
                f"This account is not recognized as dev, sand, or prod.\n"
                f"Please specify --env explicitly."
            )

        return env

    except (NoCredentialsError, ClientError, TokenRetrievalError) as e:
        raise click.ClickException(
            "✗ Could not detect AWS environment\n\n"
            "Please authenticate first or specify --env explicitly:\n"
            "  dh aws login --profile <profile-name>"
        ) from e


def check_aws_auth() -> None:
    """Check AWS authentication status and provide clear error if not authenticated.

    This function proactively checks AWS credentials before any AWS API calls
    to provide clear, actionable error messages.

    Raises:
        click.ClickException: If not authenticated to AWS with instructions to fix
    """
    try:
        sts = boto3.client("sts")
        sts.get_caller_identity()
    except NoCredentialsError:
        raise click.ClickException(
            "✗ Not authenticated to AWS\n\n"
            "Please authenticate using one of these methods:\n"
            "  • dh aws login --profile <profile-name>\n"
            "  • aws sso login --profile <profile-name>\n"
            "  • export AWS_PROFILE=<profile-name> && aws sso login"
        )
    except TokenRetrievalError as e:
        # SSO token retrieval errors - most common case for expired SSO sessions
        error_msg = str(e)
        if "Token has expired" in error_msg and "refresh failed" in error_msg:
            raise click.ClickException(
                "✗ AWS SSO token has expired\n\n"
                "Please refresh your AWS SSO session:\n"
                "  dh aws login --profile <profile-name>"
            )
        # Other token retrieval errors
        raise click.ClickException(
            f"✗ AWS SSO token error\n\n"
            f"Error: {error_msg}\n\n"
            f"Please refresh your AWS SSO session:\n"
            f"  dh aws login --profile <profile-name>"
        )
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_msg = str(e)

        # SSO token error - check this first as it's more specific than general "expired"
        # This is the specific case from the user's terminal
        if "Token has expired" in error_msg and "refresh failed" in error_msg:
            raise click.ClickException(
                "✗ AWS SSO token has expired\n\n"
                "Please refresh your AWS SSO session:\n"
                "  dh aws login --profile <profile-name>"
            )

        # Token expired error (generic)
        if "ExpiredToken" in error_code or "expired" in error_msg.lower():
            raise click.ClickException(
                "✗ AWS credentials have expired\n\n"
                "Please refresh your credentials:\n"
                "  dh aws login --profile <profile-name>"
            )

        # Generic auth error
        raise click.ClickException(
            f"✗ AWS authentication error\n\n"
            f"Error: {error_msg}\n\n"
            f"Try refreshing your credentials:\n"
            f"  dh aws login --profile <profile-name>"
        )


def get_aws_username() -> str:
    """Get username from AWS STS caller identity.

    Parses username from the AWS SSO assumed role ARN.
    This works even when running as root in containers where $USER is empty.

    Returns:
        Username from AWS identity

    Raises:
        RuntimeError: If not authenticated to AWS
    """
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()

        # Parse username from assumed role ARN
        # Format: arn:aws:sts::123456789012:assumed-role/AWSReservedSSO_DeveloperAccess_xxxx/username
        arn = identity["Arn"]

        if "assumed-role" in arn:
            # SSO auth - username is last component
            username = arn.split("/")[-1]
            return username
        else:
            # Other auth methods - use last part of UserId
            return identity["UserId"].split(":")[-1]

    except (NoCredentialsError, ClientError, TokenRetrievalError) as e:
        raise RuntimeError(
            "Not authenticated to AWS. " "Run: dh aws login --profile <profile-name>"
        ) from e
