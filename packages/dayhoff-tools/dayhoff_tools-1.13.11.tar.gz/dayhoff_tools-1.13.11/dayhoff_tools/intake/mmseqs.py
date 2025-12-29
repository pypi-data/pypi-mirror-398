import csv
from typing import Dict, List, Set

import pandas as pd
from tqdm import tqdm


def pick_mmseqs_cluster_representatives(
    tsv_file: str,
    priority_sets: List[Set[str]],
    avoid_sets: List[Set[str]] | None = None,
) -> Dict[str, Set[str]]:
    """
    Select representative protein IDs from clusters and return full cluster information.

    This function reads a TSV file containing protein cluster information, where each line
    represents a cluster with a representative sequence and a member. It then selects a
    representative for each cluster using the following priority:
    1. IDs from priority_sets (in order of the sets)
    2. IDs not in avoid_sets (if avoid_sets is provided)
    3. Original representative as fallback

    Progress is displayed using TQDM progress bars.

    Args:
        tsv_file (str): Path to the TSV file containing cluster information.
            Each line should be in the format: representative_id\tmember_id
        priority_sets (List[Set[str]]): An ordered list of sets of protein IDs to prioritize
            as representatives. Earlier sets in the list have higher priority.
        avoid_sets (List[Set[str]] | None, optional): An ordered list of sets of protein IDs to avoid
            when selecting representatives. Only used if no priority IDs are found.
            Defaults to None.

    Returns:
        Dict[str, Set[str]]: A dictionary where keys are selected representative protein IDs
        and values are sets of all members in the cluster (including the representative).

    Raises:
        FileNotFoundError: If the specified TSV file does not exist.
        ValueError: If the TSV file is not properly formatted.
    """
    cluster_dict: Dict[str, Set[str]] = {}
    final_clusters: Dict[str, Set[str]] = {}

    # First pass: count lines for TQDM
    print("Counting TSV lines")
    total_lines = sum(1 for _ in open(tsv_file, "r"))

    # Read the TSV file and build the cluster dictionary
    try:
        with (
            open(tsv_file, "r") as file,
            tqdm(total=total_lines, desc="Reading TSV", unit="lines") as pbar,
        ):
            for line in file:
                parts = line.strip().split("\t")
                if len(parts) != 2:
                    raise ValueError(f"Invalid line format in TSV file: {line}")
                rep, member = parts
                if rep not in cluster_dict:
                    cluster_dict[rep] = set()
                cluster_dict[rep].add(member)
                cluster_dict[rep].add(
                    rep
                )  # Ensure the representative is also in the cluster set
                pbar.update(1)
    except FileNotFoundError:
        raise FileNotFoundError(f"The TSV file '{tsv_file}' was not found.")

    # Process each cluster and select a representative
    for rep, cluster in tqdm(
        cluster_dict.items(), desc="Selecting representatives", unit="clusters"
    ):
        selected_rep = None

        # First try to find IDs from priority sets
        for priority_set in priority_sets:
            priority_rep = cluster.intersection(priority_set)
            if priority_rep:
                selected_rep = min(
                    priority_rep
                )  # Choose the lexicographically first ID
                break

        # If no priority ID found and avoid_sets provided, try to find non-avoided IDs
        if selected_rep is None and avoid_sets is not None:
            # Create a set of all IDs to avoid
            all_avoid_ids = set().union(*avoid_sets)
            # Find IDs that are not in any avoid set
            non_avoided_ids = cluster - all_avoid_ids
            if non_avoided_ids:
                selected_rep = min(
                    non_avoided_ids
                )  # Choose the lexicographically first non-avoided ID
            elif rep not in all_avoid_ids:
                # If no non-avoided IDs found but original rep is not avoided, use it
                selected_rep = rep

        # If still no representative found, use the original representative
        if selected_rep is None:
            selected_rep = rep

        final_clusters[selected_rep] = cluster

    return final_clusters


def replace_proteins_with_representatives(
    df: pd.DataFrame, reps: Dict[str, Set[str]]
) -> pd.DataFrame:
    """
    Replace protein IDs in a DataFrame with their cluster representatives.

    This function takes a DataFrame containing protein IDs and a dictionary of
    cluster representatives. It replaces each protein ID in the DataFrame with
    its corresponding cluster representative.

    Args:
        df (pd.DataFrame): Input DataFrame with columns ["pr_id", "reaction_id", "protein_id"].
        reps (Dict[str, Set[str]]): A dictionary where keys are representative protein IDs
            and values are sets of all members in the cluster (including the representative).

    Returns:
        pd.DataFrame: A new DataFrame with protein IDs replaced by their cluster representatives.

    Raises:
        ValueError: If the input DataFrame doesn't have the required columns.
    """
    if not all(col in df.columns for col in ["pr_id", "reaction_id", "protein_id"]):
        raise ValueError(
            "Input DataFrame must have columns: 'pr_id', 'reaction_id', 'protein_id'"
        )

    print("Starting protein ID replacement process...")

    # Create a mapping of all proteins to their representatives
    protein_to_rep = {}
    for rep, cluster in reps.items():
        for protein in cluster:
            protein_to_rep[protein] = rep

    print("Protein to representative mapping created.")

    # Create a copy of the input DataFrame to avoid modifying the original
    df_copy = df.copy()

    # Replace protein IDs with their representatives
    tqdm.pandas(desc="Replacing protein IDs")
    df_copy["protein_id"] = df_copy["protein_id"].progress_map(
        lambda x: protein_to_rep.get(x, x)
    )

    print("Protein ID replacement completed.")
    return df_copy


def write_clusters_to_tsv(clusters, output_file):
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["protein_id", "cluster_rep"])  # Write header

        for cluster_rep, members in tqdm(clusters.items(), desc="Writing clusters"):
            for protein_id in members:
                writer.writerow([protein_id, cluster_rep])
