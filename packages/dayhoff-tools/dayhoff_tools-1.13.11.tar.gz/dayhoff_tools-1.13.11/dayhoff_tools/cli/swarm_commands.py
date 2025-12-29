"""CLI commands specific for this repo."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import typer


def get_firestore_collection_status(
    firestore_collection: str = typer.Argument(),
) -> None:
    """Count the various statuses of items in a given collection."""
    print(f"Checking collection: {firestore_collection}")

    # Import heavy libraries inside the function
    from dayhoff_tools.deployment.swarm import initialize_firebase
    from firebase_admin import firestore

    initialize_firebase()
    collection = firestore.client().collection(firestore_collection)
    docs = collection.stream()

    # Instead of directly counting, we'll aggregate based on values
    value_counts = {}
    for doc in docs:
        doc_data = doc.to_dict()
        value = doc_data.get("status", None) if doc_data else None
        if value is not None:
            value_counts[value] = value_counts.get(value, 0) + 1

    for value, count in value_counts.items():
        typer.echo(f"status == {value}: {count}")


def reset_failed_cards(
    firestore_collection: str = typer.Option(prompt=True),
    old_status: str = typer.Option(default="failed", prompt=True),
    new_status: str = typer.Option(default="available", prompt=True),
    delete_old: bool = typer.Option(default=True, prompt=True),
):
    """Find all the documents in the database with a given status, and
    make a new document with the same name and a new status."""
    # Import heavy libraries inside the function
    from dayhoff_tools.deployment.swarm import initialize_firebase
    from firebase_admin import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter

    initialize_firebase()
    collection = firestore.client().collection(firestore_collection)
    failed_cards = collection.where(
        filter=FieldFilter("status", "==", old_status)
    ).stream()

    # Count the number of documents that would be changed
    change_count = sum(1 for _ in failed_cards)

    # Ask for confirmation before proceeding
    confirmation = input(
        f"This operation will change {change_count} documents. Do you want to continue? (Y/n): "
    )
    if confirmation.lower() not in ["y", "Y", ""]:
        print("Operation cancelled.")
        return

    # Reset the failed_cards generator
    failed_cards = collection.where(
        filter=FieldFilter("status", "==", old_status)
    ).stream()

    reset_count = 0
    for card in failed_cards:
        # Make a fresh new one
        packet_filename = card.to_dict()["packet_filename"]  # type: ignore
        collection.document().set(
            {
                "status": new_status,
                "packet_filename": packet_filename,
                "created": datetime.now(ZoneInfo("America/Los_Angeles")),
            }
        )
        reset_count += 1
        if delete_old:
            card.reference.delete()

    print(f"Done: {reset_count} new '{new_status}' cards were created.")
    if delete_old:
        print(f"Done: {reset_count} '{old_status}' cards were deleted.")


def reset_zombie_cards(
    firestore_collection: str = typer.Option(prompt=True),
    delete_old: bool = typer.Option(default=True, prompt=True),
    minutes_threshold: int = typer.Option(default=20, prompt=True),
):
    """Find all the documents in the database with status "assigned", and "last_update"
    older than a specified threshold, and make a new "available" document for them.

    This implementation avoids requiring a composite index by filtering on the client side.
    """
    # Import heavy libraries inside the function
    from dayhoff_tools.deployment.swarm import initialize_firebase
    from firebase_admin import firestore
    from google.cloud.firestore_v1.base_query import FieldFilter

    initialize_firebase()
    collection = firestore.client().collection(firestore_collection)
    current_time = datetime.now(ZoneInfo("America/Los_Angeles"))
    threshold_time = current_time - timedelta(minutes=minutes_threshold)

    # First, get all documents with status "assigned"
    assigned_cards = collection.where(
        filter=FieldFilter("status", "==", "assigned")
    ).stream()

    # Filter client-side for those with last_update older than threshold
    zombie_cards = []
    for card in assigned_cards:
        card_data = card.to_dict()
        last_update = card_data.get(
            "last_update"
        )  # Note: field is "last_update", not "last_updated"
        if last_update and last_update < threshold_time:
            zombie_cards.append(card)

    # Ask for confirmation before proceeding
    change_count = len(zombie_cards)
    if change_count == 0:
        print("No zombie cards found. Nothing to do.")
        return

    confirmation = input(
        f"This operation will reset {change_count} zombie documents. Do you want to continue? (Y/n): "
    )
    if confirmation.lower() not in ["y", "Y", ""]:
        print("Operation cancelled.")
        return

    reset_count = 0
    for card in zombie_cards:
        # Make a fresh new one
        card_data = card.to_dict()
        packet_filename = card_data["packet_filename"]
        collection.document().set(
            {
                "status": "available",
                "packet_filename": packet_filename,
                "created": current_time,
            }
        )
        reset_count += 1
        if delete_old:
            card.reference.delete()

    print(f"Done: {reset_count} new 'available' cards were created.")
    if delete_old:
        print(f"Done: {reset_count} 'assigned' zombie cards were deleted.")
