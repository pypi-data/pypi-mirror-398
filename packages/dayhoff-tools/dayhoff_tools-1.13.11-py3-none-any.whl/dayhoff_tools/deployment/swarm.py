"""
Gets the data that the current worker needs.
Interacts with Firebase (where the data is listed)
and GCS (where it is hosted).
"""

import json
import logging
import os
import re
import signal
import threading
import time
from datetime import datetime
from typing import List, Set, Tuple
from zoneinfo import ZoneInfo

import firebase_admin
import requests
from dayhoff_tools.deployment.deploy_utils import get_instance_name, get_instance_type
from dayhoff_tools.deployment.processors import Processor
from firebase_admin import firestore
from google.cloud import storage
from google.cloud.firestore import transactional
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)

# AWS IMDSv2 endpoints
AWS_IMDS_TOKEN_URL = "http://169.254.169.254/latest/api/token"
AWS_INSTANCE_ACTION_URL = "http://169.254.169.254/latest/meta-data/spot/instance-action"

# GCP preemption endpoints
GCP_PREEMPTION_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/preempted"
)
GCP_PREEMPTION_WARNING_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/maintenance-event"
)

# Shutdown signal received flag (shared between threads)
_shutdown_requested = threading.Event()


def initialize_firebase():
    try:
        # Attempts to get the default app, if it's already initialized.
        firebase_admin.get_app()
    except ValueError:
        # If the default app has not been initialized, then initialize it.
        firebase_admin.initialize_app()


def assert_sequential_files_in_gcs_folder(
    bucket_name: str, folder_name: str, expected_number: int | None = None
) -> Tuple[List[str], Set[str]]:
    """
    Check a GCS folder for sequential files that have names ending with '_x' where x is an int,
    regardless of file extension.
    Determine if any files are missing or duplicate.
    The number of files is inferred from the name of the last one, unless provided.

    Args:
        bucket_name (str): Name of the GCS bucket
        folder_name (str): Name of the folder within the bucket
        expected_number (int | None): The expected number of files in the folder.

    Returns:
        Tuple[List[str], Set[str]]: Sorted list of missing files, set of duplicate files.
    """
    # Initialize the GCS client
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)

    # Ensure folder_name ends with a slash
    folder_name = folder_name.rstrip("/") + "/"

    # List all blobs in the folder
    blobs = list(bucket.list_blobs(prefix=folder_name))

    # Extract file numbers and names
    file_numbers = {}
    max_number = 0
    for blob in blobs:
        # Handle both actual Blob objects and Mock objects
        if isinstance(blob, storage.Blob):
            blob_name = blob.name
        else:
            blob_name = blob.name if isinstance(blob.name, str) else str(blob.name)

        # Ensure blob_name is a string before using in re.search
        if blob_name is None:
            continue

        # Make sure blob_name is a string
        blob_name_str = str(blob_name)
        match = re.search(r"_(\d+)(?:\.[^.]+)?$", blob_name_str)
        if match:
            number = int(match.group(1))
            max_number = max(max_number, number)
            if number in file_numbers:
                file_numbers[number].append(blob_name_str)
            else:
                file_numbers[number] = [blob_name_str]

    # Determine the expected number of files
    if expected_number is None:
        expected_number = max_number

    # Find missing and duplicate files
    missing_files = []
    duplicate_files = set()

    for i in range(1, expected_number + 1):
        if i not in file_numbers:
            missing_files.append(f"{folder_name}file_{i}")
        elif len(file_numbers[i]) > 1:
            duplicate_files.update(file_numbers[i])

    print(f"Files expected: {expected_number}")
    print(f"Files missing: {missing_files}")
    print(f"Files duplicated: {duplicate_files}")

    return missing_files, duplicate_files


def publish_cards(
    names: List[str],
    firestore_collection: str,
):
    """Publish cards to Firebase using batch writes for optimal performance.

    Expects a list of filenames (not full paths), which will each be published
    as a new document in the collection. Uses Firestore batch writes to minimize
    network round-trips and improve performance.

    Args:
        names: List of packet filenames to publish as cards
        firestore_collection: Name of the Firestore collection to write to
    """
    if not names:
        print("No cards to upload.")
        return

    initialize_firebase()
    db = firestore.client()
    collection = db.collection(firestore_collection)

    # Firestore batch limit is 500 operations
    BATCH_SIZE = 500
    total_cards = len(names)
    cards_processed = 0

    # Process names in batches of up to 500
    for i in range(0, total_cards, BATCH_SIZE):
        batch = db.batch()
        batch_names = names[i : i + BATCH_SIZE]

        # Add all operations for this batch
        for name in batch_names:
            doc_ref = collection.document()  # Auto-generate document ID
            batch.set(
                doc_ref,
                {
                    "status": "available",
                    "packet_filename": name,
                    "created": datetime.now(ZoneInfo("America/Los_Angeles")),
                },
            )

        # Commit the entire batch atomically
        batch.commit()
        cards_processed += len(batch_names)

        print(
            f"Batch {i // BATCH_SIZE + 1}: Created {len(batch_names)} cards "
            f"({cards_processed}/{total_cards} total)"
        )

    print(
        f"Successfully uploaded {total_cards} cards in {(total_cards + BATCH_SIZE - 1) // BATCH_SIZE} batch(es)."
    )


@transactional
def _assign_card_in_transaction(
    transaction,
    query,
    collection,
    vm_name: str,
    vm_type: str,
    batch_worker: str,
):
    """Draw an `available` card and update it to `assigned`.
    Do so in an atomic transaction.

    This function can't be a class function because the decorator
    expects a transaction (not self) as the first argument."""

    # Exit the function if no documents are found
    query_output = list(query.stream(transaction=transaction))
    if not query_output:
        logger.error("No cards are available.")
        return None

    card_id = query_output[0].id
    card_reference = collection.document(card_id)
    packet_filename = card_reference.get().get("packet_filename")

    # Update the document within the transaction
    now = datetime.now(ZoneInfo("America/Los_Angeles"))
    transaction.update(
        card_reference,
        {
            "status": "assigned",
            "packet_filename": packet_filename,
            "vm_name": vm_name,
            "vm_type": vm_type,
            "batch_index": batch_worker,
            "first_update": now,
            "last_update": now,
        },
    )
    return card_reference


class FirestoreService:
    """Handles all Firestore database operations"""

    def __init__(self, collection_name, tachycardic=False):
        initialize_firebase()
        self.db = firestore.client()
        self.collection = self.db.collection(collection_name)
        self.vm_name = get_instance_name()
        self.vm_type = get_instance_type()
        self.batch_worker = os.getenv("BATCH_TASK_INDEX", "Not processed in Batch")
        self.current_card = None
        self.heartstopper = threading.Event()
        self.tachycardic = tachycardic

    def draw_card(self) -> str | None:
        """Draw an `available` card from Firestore and update it to `assigned`.
        Return the packet_filename contained in that card."""
        # Start a transaction and use the wrapper function
        transaction = self.db.transaction()
        query = self.collection.where(
            filter=FieldFilter("status", "==", "available")
        ).limit(1)
        self.current_card = _assign_card_in_transaction(
            transaction,
            query,
            self.collection,
            self.vm_name,
            self.vm_type,
            self.batch_worker,
        )
        if self.current_card is None:
            return None
        else:
            packet_filename = str(self.current_card.get().get("packet_filename"))
            logger.info("Card drawn: %s", packet_filename)
            return packet_filename

    def start_heart(self):
        """Start the heartbeat thread."""
        logger.info("Heartbeat started.")
        self.heartstopper = threading.Event()
        self.heartbeat_thread = threading.Thread(target=self._send_heartbeat)
        self.heartbeat_thread.start()

    def close_card(self):
        """Update the current card to `processed`"""
        if not self.current_card:
            logger.info("No current card to close")
            return

        self.current_card.update(
            {
                "status": "processed",
                "last_update": datetime.now(ZoneInfo("America/Los_Angeles")),
            }
        )

    def stop_heart(self):
        """Stop the heartbeat thread."""
        if self.heartstopper is None:
            logger.info("No current heartbeat to stop")
            return
        self.heartstopper.set()
        self.heartbeat_thread.join()

    def record_failure(self, failure: str):
        """Record the cause of death for the current card."""
        if not self.current_card:
            logger.info("No current card for which to record failure")
            return

        self.current_card.update(  # type: ignore
            {
                "status": "failed",
                "last_update": datetime.now(ZoneInfo("America/Los_Angeles")),
                "failure": failure,
            }
        )

    def _send_heartbeat(self):
        """Periodically update the 'last_update' field for the current card.
        Listen for a heartstopper signal."""

        if self.tachycardic:
            update_interval = 2
            sleep_interval = 1
        else:
            update_interval = 5 * 60  # 5 minutes expressed in seconds
            sleep_interval = 5  # Check the heartstopper every 5 seconds

        counter = 0
        while (
            self.current_card and self.heartstopper and not self.heartstopper.is_set()
        ):
            if counter >= update_interval:
                try:
                    # Perform the database update
                    self.current_card.update(
                        {
                            "last_update": datetime.now(
                                ZoneInfo("America/Los_Angeles")
                            ),
                        }
                    )
                    logger.debug("Heartbeat updated.")
                    counter = 0  # Reset counter after update
                except Exception as e:
                    logger.error(f"Error updating heartbeat: {e}")
                    break  # Exit the loself.firestore if there's an error

            time.sleep(sleep_interval)  # Sleep for the short interval

            # Increment counter by the number of seconds slept
            counter += sleep_interval

        logger.info("Heartbeat stopped.")

    def release_card(self):
        """Release the current card back to 'available' state.
        Used when a spot instance is being terminated to allow another worker to pick it up.
        """
        if not self.current_card:
            logger.info("No current card to release")
            return

        packet_filename = self.current_card.get().get("packet_filename")

        # Create a new available card
        self.db.collection(self.collection.id).document().set(
            {
                "status": "available",
                "packet_filename": packet_filename,
                "created": datetime.now(ZoneInfo("America/Los_Angeles")),
                "released_from": self.vm_name,
            }
        )

        # Update the current card to show it was released due to termination
        self.current_card.update(
            {
                "status": "released",
                "last_update": datetime.now(ZoneInfo("America/Los_Angeles")),
                "release_reason": "spot_termination",
            }
        )

        logger.info(
            f"Card {packet_filename} released back to available pool due to spot termination"
        )
        self.current_card = None


class GCSService:
    """Handles all GCS operations"""

    def __init__(
        self,
        bucket_name: str,
        gcs_input_folder: str,
        gcs_output_folder: str,
    ):
        storage_client = storage.Client()
        self.bucket = storage_client.bucket(bucket_name)
        self.gcs_input_folder = gcs_input_folder
        self.gcs_output_folder = gcs_output_folder

    def download_data(self, packet_filename: str):
        """Download the data from GCS."""
        logger.info(f"Downloading {packet_filename}")

        # Download packet with original name
        source_blob = self.bucket.blob(f"{self.gcs_input_folder}/{packet_filename}")
        source_blob.download_to_filename(packet_filename)

    def upload_results(self, path_to_upload: str):
        """Upload the results back to GCS.

        Args:
            path_to_upload: Path to the file or folder to upload
        """
        logger.info(f"Uploading {path_to_upload}")

        if os.path.isfile(path_to_upload):
            # Upload single file to GCS
            gcs_path = f"{self.gcs_output_folder}/{path_to_upload}"
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(path_to_upload)
            logger.info(f"Uploaded file {path_to_upload} to {gcs_path}")
        elif os.path.isdir(path_to_upload):
            # Upload entire folder to GCS
            gcs_folder = f"{self.gcs_output_folder}/{os.path.basename(path_to_upload)}"
            from dayhoff_tools.deployment.deploy_utils import upload_folder_to_gcs

            upload_folder_to_gcs(path_to_upload, self.bucket, gcs_folder)
            logger.info(f"Uploaded folder {path_to_upload} to {gcs_folder}")
        else:
            raise FileNotFoundError(
                f"The path {path_to_upload} does not exist or is not accessible"
            )


class Operator:
    """Communicates with the Firestore and GCS services to constantly get
    data, then assigns it to the processor. Also manages errors and
    sending a constant heartbeat to Firestore."""

    def __init__(
        self,
        firestore_service: FirestoreService,
        gcs_service: GCSService,
        processor: Processor,
    ):
        self.firestore = firestore_service
        self.gcs = gcs_service
        self.processor = processor
        self.termination_checker = None
        self._setup_shutdown_handlers()

    def _setup_shutdown_handlers(self):
        """Set up handlers for spot instance termination and system shutdown signals."""
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)

        # Start a thread to check for AWS spot instance termination
        self.termination_checker = threading.Thread(target=self._check_for_termination)
        self.termination_checker.daemon = True
        self.termination_checker.start()

        logger.info("Spot instance termination handlers initialized")

    def _handle_shutdown_signal(self, signum, frame):
        """Handle shutdown signals by releasing card and stopping gracefully."""
        logger.warning(
            f"Received shutdown signal {signum}. Preparing for graceful shutdown."
        )
        _shutdown_requested.set()

        # Release the current card if there is one
        if self.firestore.current_card:
            logger.info("Releasing card due to shutdown signal")
            self.firestore.release_card()
            self.firestore.stop_heart()

    def _check_for_termination(self):
        """Periodically check for AWS and GCP instance termination notices.

        - For AWS spot instances, uses IMDSv2 to check instance-action metadata
        - For GCP preemptible VMs, checks both maintenance-event and preempted metadata
        """
        while not _shutdown_requested.is_set():
            try:
                # Check AWS spot termination using IMDSv2 (token-based auth)
                token_response = requests.put(
                    AWS_IMDS_TOKEN_URL,
                    headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
                    timeout=2,
                )

                if token_response.status_code == 200:
                    # Use token to check instance-action
                    token = token_response.text
                    action_response = requests.get(
                        AWS_INSTANCE_ACTION_URL,
                        headers={"X-aws-ec2-metadata-token": token},
                        timeout=2,
                    )

                    # If 200 response and contains action, termination is imminent
                    if action_response.status_code == 200:
                        try:
                            action_data = json.loads(action_response.text)
                            action = action_data.get("action")
                            action_time = action_data.get("time")

                            logger.warning(
                                f"AWS Spot instance interruption notice received: "
                                f"action={action}, time={action_time}"
                            )

                            # Release the current card if there is one
                            if self.firestore.current_card:
                                logger.info(
                                    f"Releasing card due to spot termination notice (action: {action})"
                                )
                                self.firestore.release_card()
                                self.firestore.stop_heart()

                            _shutdown_requested.set()
                            break
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Failed to parse instance-action response: {action_response.text}"
                            )
            except requests.RequestException:
                # This is expected on GCP or non-spot instances
                pass

            try:
                # Check GCP preemption warning (gives more lead time)
                gcp_warning_response = requests.get(
                    GCP_PREEMPTION_WARNING_URL,
                    headers={"Metadata-Flavor": "Google"},
                    timeout=2,
                )

                # If we get a response containing TERMINATE, preemption is coming soon
                if (
                    gcp_warning_response.status_code == 200
                    and "TERMINATE" in gcp_warning_response.text
                ):
                    logger.warning(
                        f"GCP preemptible VM maintenance event detected: {gcp_warning_response.text}"
                    )

                    # Release the current card if there is one
                    if self.firestore.current_card:
                        logger.info("Releasing card due to GCP preemption warning")
                        self.firestore.release_card()
                        self.firestore.stop_heart()

                    _shutdown_requested.set()
                    break

                # Check GCP actual preemption (fallback check)
                gcp_response = requests.get(
                    GCP_PREEMPTION_URL, headers={"Metadata-Flavor": "Google"}, timeout=2
                )

                # If we get a 200 response with "TRUE", termination is already happening
                if (
                    gcp_response.status_code == 200
                    and gcp_response.text.upper() == "TRUE"
                ):
                    logger.warning("GCP preemptible VM is being terminated now")

                    # Release the current card if there is one
                    if self.firestore.current_card:
                        logger.info("Releasing card due to GCP preemption in progress")
                        self.firestore.release_card()
                        self.firestore.stop_heart()

                    _shutdown_requested.set()
                    break
            except requests.RequestException:
                # This is expected on AWS or non-preemptible instances
                pass

            # Check every 5 seconds as recommended by AWS
            time.sleep(5)

    def run(self):
        while not _shutdown_requested.is_set():
            try:
                packet_filename = self.firestore.draw_card()
                if packet_filename is None:
                    break
                self.firestore.start_heart()
                self.gcs.download_data(packet_filename)

                # Check if termination was requested while downloading
                if _shutdown_requested.is_set():
                    logger.warning("Shutdown requested during download, releasing card")
                    self.firestore.release_card()
                    self.firestore.stop_heart()
                    break

                output_path = self.processor.run(input_file=packet_filename)

                # Check if termination was requested during processing
                if _shutdown_requested.is_set():
                    logger.warning(
                        "Shutdown requested during processing, releasing card"
                    )
                    self.firestore.release_card()
                    self.firestore.stop_heart()
                    break

                self.gcs.upload_results(path_to_upload=output_path)
                self.firestore.close_card()
                self.firestore.stop_heart()

                # Clean up the output based on whether it's a file or directory
                if os.path.isfile(output_path):
                    os.remove(output_path)
                elif os.path.isdir(output_path):
                    import shutil

                    shutil.rmtree(output_path)
            except Exception as e:
                logger.error(e)
                self.firestore.record_failure(str(e))
                self.firestore.stop_heart()
            except KeyboardInterrupt:
                logger.error("KeyboardInterrupt")
                self.firestore.record_failure("KeyboardInterrupt")
                self.firestore.stop_heart()
                break

        logger.info("Operator is done.")
