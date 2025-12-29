import logging
import os
from typing import Tuple

import requests
from dayhoff_tools.file_ops import natural_sort_key
from google.cloud import storage

logger = logging.getLogger(__name__)


def upload_folder_to_gcs(
    bucket_name: str,
    source_folder: str,
    destination_path: str,
) -> None:
    """
    Uploads a local folder to Google Cloud Storage

    :param bucket_name: The name of the GCS bucket to upload to
    :param source_folder: The path to the local folder to upload
    :param destination_path: The destination path in the GCS bucket (without leading '/')
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    if destination_path.startswith("gs://"):
        destination_path = destination_path[5:]

    if destination_path.startswith(bucket_name):
        destination_path = destination_path[len(bucket_name) + 1 :]

    # Iterate through local files and upload them to GCS
    for root, _, files in os.walk(source_folder):
        for file_name in sorted(files, key=natural_sort_key):
            local_file_path = os.path.join(root, file_name)

            # Create a blob object in the destination path
            relative_path = os.path.relpath(local_file_path, source_folder)
            blob_path = os.path.join(destination_path, relative_path)
            blob = bucket.blob(blob_path)

            # Upload the local file to the blob
            blob.upload_from_filename(local_file_path)
            print(f"{local_file_path} uploaded to gs://{bucket_name}/")


def get_vm_name() -> str:
    """Query the Google Compute Engine metadata server to get the name of the current instance.
    Only works on GCE VMs, of course.
    """
    url = "http://metadata.google.internal/computeMetadata/v1/instance/name"
    headers = {"Metadata-Flavor": "Google"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        logger.error("Error retrieving machine type: %s", e)

    return "Not a Google Compute Engine VM"


def get_vm_type() -> str:
    """Query the Google Compute Engine metadata server to get the type
    (eg, n1-highmem-8) of the current instance. Only works on GCE VMs.
    """
    metadata_url = (
        "http://metadata.google.internal/computeMetadata/v1/instance/machine-type"
    )
    headers = {"Metadata-Flavor": "Google"}

    try:
        response = requests.get(metadata_url, headers=headers)
        if response.status_code == 200:
            # The response includes the full path. Extract just the machine type.
            machine_type_path = response.text
            # Example response: projects/123456789/machineTypes/n1-standard-1
            # Extract machine type from the last segment of the path
            machine_type = machine_type_path.split("/")[-1]
            return machine_type
    except Exception as e:
        logger.error("Error retrieving machine type: %s", e)

    return "Not a Google Compute Engine VM"
