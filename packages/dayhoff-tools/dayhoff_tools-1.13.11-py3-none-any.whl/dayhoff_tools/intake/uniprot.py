import csv
import gzip
import io
import os
import time
from typing import Iterator, List, Set

import h5py
import numpy as np
import pandas as pd
from Bio import SwissProt
from tqdm import tqdm


def parse_entries(file: Iterator[str]) -> Iterator[str]:
    """
    Generator function to parse SwissProt entries efficiently.
    """
    buffer = io.StringIO()
    for line in file:
        buffer.write(line)
        if line.startswith("//"):
            yield buffer.getvalue()
            buffer = io.StringIO()
    if buffer.getvalue():
        yield buffer.getvalue()


def extract_cofactors(inpath: str, outpath: str, source_db: str):
    """
    Read a compressed .dat.gz file, extract the cofactors for each entry,
    and write the results to a TSV file.

    Args:
        inpath (str): Path to the input .dat.gz file as obtained from UniProt
        outpath (str): Path to the output TSV file
        source_db (str): Name of the database to list as a source for this data
    """
    unparseable_entries = 0
    total_entries = 0

    with gzip.open(inpath, "rt") as file, open(outpath, "w", newline="") as tsv_file:
        tsv_writer = csv.writer(tsv_file, delimiter="\t")
        tsv_writer.writerow(
            ["protein_id", "cofactor_names", "cofactor_chebi", "source_db"]
        )

        for entry in parse_entries(file):
            total_entries += 1
            if total_entries % 1_000_000 == 0:
                print(f"Processed {total_entries:,} entries")

            try:
                record = SwissProt.read(io.StringIO(entry))
                ac = record.accessions[0]
                all_names = []
                all_chebis = []

                for comment in record.comments:
                    if "COFACTOR" in comment:
                        names = []
                        chebis = []
                        parts = comment.split(";")
                        for part in parts:
                            if "Name=" in part:
                                names.append(part.split("Name=")[1].strip())
                            if "Xref=ChEBI:CHEBI:" in part:
                                chebis.append(
                                    part.split("Xref=ChEBI:CHEBI:")[1].strip()
                                )
                        if names and chebis:
                            all_names.append("|".join(names))
                            all_chebis.append("|".join(chebis))

                tsv_writer.writerow(
                    [
                        ac,
                        ";".join(all_names) if all_names else None,
                        ";".join(all_chebis) if all_chebis else None,
                        source_db,
                    ]
                )
            except SwissProt.SwissProtParserError:
                unparseable_entries += 1

    print(f"Total entries processed: {total_entries:,}")
    print(f"Number of entries that couldn't be parsed: {unparseable_entries:,}")


def one_hot_encode_cofactors(df: pd.DataFrame) -> pd.DataFrame:
    """
    One-hot encode the cofactors in the 'cofactor_chebi' column of a dataframe.

    This function takes a dataframe with a 'cofactor_chebi' column and creates new columns
    for each unique cofactor, with binary values indicating the presence or absence of
    each cofactor for each protein.

    Parameters:
    -----------
    df : pandas.DataFrame
        The input dataframe containing the 'cofactor_chebi' column.

    Returns:
    --------
    pandas.DataFrame
        A new dataframe with additional columns for each unique cofactor.

    Notes:
    ------
    - The function handles multiple cofactors separated by '|' or ';'.
    - NaN values and empty strings in the 'cofactor_chebi' column are preserved.
    - The function uses TQDM to show progress during processing.
    - Print statements are included to indicate major transitions in the process.
    - Duplicate cofactors in a single entry are handled correctly (only encoded once).
    """
    print("Starting one-hot encoding process...")

    # Extract unique cofactors
    print("Extracting unique cofactors...")
    all_cofactors = set(
        cofactor.strip()
        for cofactors in df["cofactor_chebi"].dropna()
        for cofactor in cofactors.replace("|", ";").split(";")
        if cofactor.strip()
    )
    print(f"Found {len(all_cofactors)} unique cofactors.")

    # Create a dictionary to map cofactors to column indices
    cofactor_to_index = {cofactor: i for i, cofactor in enumerate(all_cofactors)}

    # Initialize the result array
    print("Initializing result array...")
    result_array = np.zeros((len(df), len(all_cofactors)), dtype=np.int8)

    # Perform one-hot encoding
    print("Performing one-hot encoding...")
    mask = df["cofactor_chebi"].notna()
    for idx, cofactors in tqdm(
        df.loc[mask, "cofactor_chebi"].items(), total=mask.sum(), desc="Processing rows"
    ):
        if cofactors.strip():
            for cofactor in set(
                cofactor.strip() for cofactor in cofactors.replace("|", ";").split(";")
            ):
                if cofactor:
                    result_array[idx, cofactor_to_index[cofactor]] = 1

    # Create the result dataframe
    print("Creating result dataframe...")
    result_df = pd.DataFrame(result_array, columns=list(all_cofactors), index=df.index)

    # Combine with original dataframe
    print("Combining results...")
    result_df = pd.concat([df, result_df], axis=1)

    print("One-hot encoding process completed.")
    return result_df


def merge_one_hot_encoded_datasets(
    df1: pd.DataFrame, df2: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge two dataframes with one-hot encoded cofactors, preserving the encoding structure.

    Args:
        df1 (pd.DataFrame): The first input dataframe containing one-hot encoded cofactor columns.
        df2 (pd.DataFrame): The second input dataframe containing one-hot encoded cofactor columns.

    Returns:
        pd.DataFrame: A new dataframe with all original columns and a complete set of one-hot encoded cofactor columns.

    Raises:
        ValueError: If any cofactor column in the input dataframes contains NaN values.
        ValueError: If the input dataframes do not contain the expected original columns.

    Notes:
        This function assumes that the non-cofactor columns are:
        ["protein_id", "cofactor_names", "cofactor_chebi", "source_db"]
    """
    expected_columns: List[str] = [
        "protein_id",
        "cofactor_names",
        "cofactor_chebi",
        "source_db",
    ]

    def check_original_columns(df: pd.DataFrame, name: str) -> None:
        missing_columns = set(expected_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(
                f"{name} is missing the following expected columns: {', '.join(missing_columns)}"
            )

    check_original_columns(df1, "First dataframe")
    check_original_columns(df2, "Second dataframe")

    def get_cofactor_columns(df: pd.DataFrame) -> List[str]:
        return [col for col in df.columns if col not in expected_columns]

    cofactor_columns1 = get_cofactor_columns(df1)
    cofactor_columns2 = get_cofactor_columns(df2)

    # Verify no NaN values in cofactor columns
    for df, cols, name in [
        (df1, cofactor_columns1, "First dataframe"),
        (df2, cofactor_columns2, "Second dataframe"),
    ]:
        if df[cols].isna().any().any():
            raise ValueError(f"Input dataframe contains NaN values in cofactor columns")

    all_cofactor_columns = sorted(set(cofactor_columns1 + cofactor_columns2))

    def add_missing_columns(df: pd.DataFrame, all_columns: List[str]) -> pd.DataFrame:
        for col in all_columns:
            if col not in df.columns:
                df[col] = 0
        return df

    df1_complete = add_missing_columns(df1, all_cofactor_columns)
    df2_complete = add_missing_columns(df2, all_cofactor_columns)

    column_order = expected_columns + all_cofactor_columns
    df1_complete = df1_complete[column_order]
    df2_complete = df2_complete[column_order]

    merged_df = pd.concat([df1_complete, df2_complete], axis=0, ignore_index=True)

    return merged_df


def filter_tsv_by_protein_ids(
    input_file: str,
    output_file: str,
    protein_id_set: Set[str],
    batch_size: int = 10000,
    report_interval: float = 5.0,
) -> None:
    """
    Filter a TSV file based on a set of protein IDs and write the results to a new file.

    This function reads the input TSV file, filters rows based on the provided protein ID set,
    and writes the filtered data to the output file. It also provides progress reporting
    during the process.

    Args:
        input_file (str): Path to the input TSV file.
        output_file (str): Path to the output TSV file.
        protein_id_set (Set[str]): Set of protein IDs to filter by in the 'protein_id' column.
        batch_size (int, optional): Number of rows to write in each batch. Defaults to 10000.
        report_interval (float, optional): Interval in seconds for progress reporting. Defaults to 5.0.

    Raises:
        FileNotFoundError: If the input file is not found.
        ValueError: If the 'protein_id' column is missing in the input file.
    """
    try:
        start_time = time.time()
        last_report_time = start_time

        total_rows = sum(1 for _ in open(input_file, "r"))
        processed_rows = 0
        matched_rows = 0

        with (
            open(input_file, "r", newline="") as infile,
            open(output_file, "w", newline="") as outfile,
        ):
            reader = csv.DictReader(infile, delimiter="\t")
            if "protein_id" not in reader.fieldnames:
                raise ValueError(
                    "Required column 'protein_id' is missing in the input file."
                )

            writer = csv.DictWriter(
                outfile, fieldnames=reader.fieldnames, delimiter="\t"
            )
            writer.writeheader()

            batch = []

            for row in reader:
                processed_rows += 1

                if row["protein_id"] in protein_id_set:
                    batch.append(row)
                    matched_rows += 1

                if len(batch) >= batch_size:
                    writer.writerows(batch)
                    batch = []

                current_time = time.time()
                if current_time - last_report_time >= report_interval:
                    progress = processed_rows / total_rows
                    elapsed_time = current_time - start_time
                    estimated_total_time = (
                        elapsed_time / progress if progress > 0 else 0
                    )
                    estimated_remaining_time = max(
                        estimated_total_time - elapsed_time, 0
                    )
                    print(
                        f"Progress: {progress:.2%} | Rows processed: {processed_rows}/{total_rows} | "
                        f"Matches: {matched_rows} | Est. time remaining: {estimated_remaining_time:.2f} seconds"
                    )
                    last_report_time = current_time

            if batch:
                writer.writerows(batch)

        print(f"Processing complete. Output written to {output_file}")
        print(f"Total rows processed: {processed_rows}")
        print(f"Total matches found: {matched_rows}")
        print(f"Total processing time: {time.time() - start_time:.2f} seconds")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        raise
    except ValueError as e:
        print(f"Error: {str(e)}")
        raise


def concatenate_embeddings_with_ohe(
    embedding_file: str,
    ohe_file: str,
    output_file: str,
    non_ohe_columns: List[str] = [
        "protein_id",
        "cofactor_names",
        "cofactor_chebi",
        "source_db",
    ],
    chunk_size: int = 10000,
) -> Set[str]:
    """
    Concatenate protein embeddings from a large H5 file with one-hot encoded (OHE) cofactor data from a TSV file.

    This function efficiently processes large H5 files by reading and writing in chunks.
    It handles missing proteins by filling their OHE data with zeros.
    Progress updates include elapsed time and estimated time remaining.

    Args:
        embedding_file (str): Path to the input H5 file containing protein embeddings.
        ohe_file (str): Path to the input TSV file containing OHE cofactor data.
        output_file (str): Path to the output H5 file where concatenated data will be written.
        non_ohe_columns (List[str]): List of column names in the TSV file that are not OHE data.
        chunk_size (int): Number of proteins to process in each chunk.

    Returns:
        Set[str]: A set of protein IDs that were in the embedding file but not in the OHE file.

    Raises:
        FileNotFoundError: If either input file is not found.
        ValueError: If the input H5 file is empty or in an unexpected format.
    """
    start_time = time.time()
    print(
        f"Starting optimized protein embedding concatenation process at {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # Check if input files exist
    if not os.path.exists(embedding_file) or not os.path.exists(ohe_file):
        raise FileNotFoundError("One or both input files not found.")

    # Load protein IDs from H5 file
    with h5py.File(embedding_file, "r") as h5_in:
        protein_ids = [id.decode("utf-8") for id in h5_in["ids"]]

    if not protein_ids:
        raise ValueError("Input H5 file is empty or in unexpected format.")

    print(f"Loaded {len(protein_ids)} protein IDs from H5 file.")

    # Load and process OHE data
    print("Loading and filtering OHE data...")
    ohe_df = pd.read_csv(ohe_file, sep="\t")
    ohe_columns = [col for col in ohe_df.columns if col not in non_ohe_columns]
    ohe_df = ohe_df.set_index("protein_id")

    num_ohe_columns = len(ohe_columns)

    # Identify missing proteins
    missing_proteins = set(protein_ids) - set(ohe_df.index)
    print(f"Number of proteins missing from OHE data: {len(missing_proteins)}")

    # Process data in chunks and write to output file
    with h5py.File(embedding_file, "r") as h5_in, h5py.File(output_file, "w") as h5_out:
        # Create datasets in output file
        h5_out.create_dataset("ids", data=[id.encode("utf-8") for id in protein_ids])

        embedding_size = h5_in["vectors"].shape[1]
        h5_out.create_dataset(
            "vectors",
            shape=(len(protein_ids), embedding_size + num_ohe_columns),
            dtype=np.float32,
        )

        total_chunks = (len(protein_ids) + chunk_size - 1) // chunk_size
        for chunk_index in range(total_chunks):
            chunk_start_time = time.time()
            start_idx = chunk_index * chunk_size
            end_idx = min((chunk_index + 1) * chunk_size, len(protein_ids))

            chunk_proteins = protein_ids[start_idx:end_idx]
            embedding_vectors = h5_in["vectors"][start_idx:end_idx]

            # Create OHE vectors for the chunk, filling with zeros for missing proteins
            ohe_vectors = np.zeros((len(chunk_proteins), num_ohe_columns))
            for i, protein_id in enumerate(chunk_proteins):
                if protein_id in ohe_df.index:
                    ohe_vectors[i] = ohe_df.loc[protein_id, ohe_columns].values

            # Concatenate embedding vectors with OHE vectors
            concatenated_vectors = np.hstack((embedding_vectors, ohe_vectors))
            h5_out["vectors"][start_idx:end_idx] = concatenated_vectors

            # Calculate and print progress information
            elapsed_time = time.time() - start_time
            estimated_total_time = elapsed_time * total_chunks / (chunk_index + 1)
            estimated_remaining_time = estimated_total_time - elapsed_time

            print(f"Processed chunk {chunk_index + 1}/{total_chunks}")
            print(f"  Elapsed time: {elapsed_time:.2f} seconds")
            print(f"  Estimated time remaining: {estimated_remaining_time:.2f} seconds")
            print(f"  Estimated total time: {estimated_total_time:.2f} seconds")

    total_time = time.time() - start_time
    print(
        f"Concatenation complete. Written {len(protein_ids)} proteins to output file."
    )
    print(f"Total execution time: {total_time:.2f} seconds")
    return missing_proteins
