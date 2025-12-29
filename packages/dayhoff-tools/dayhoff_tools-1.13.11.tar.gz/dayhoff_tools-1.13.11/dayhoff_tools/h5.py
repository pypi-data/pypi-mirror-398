import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set, Union

import h5py
import numpy as np
from tqdm import tqdm


def combine_h5_files(
    input_files: Union[str, List[str]], output_file: str, chunk_size: int = 10000
) -> None:
    """Combine several .h5 embedding files into one efficiently, with detailed progress indication.
    Assumes they have two datasets: `ids` and `vectors`, within which order is important.

    Args:
        input_files (Union[str, List[str]]): Either a path to the folder containing .h5 files,
                                             or a list of paths to individual .h5 files.
        output_file (str): The path to the output .h5 file.
        chunk_size (int): Number of rows to process at a time. Default is 10000.

    Raises:
        FileExistsError: If the output file already exists.
    """
    if os.path.exists(output_file):
        raise FileExistsError(
            f"Output file '{output_file}' already exists. Please choose a different output file name."
        )

    def get_file_list(input_files: Union[str, List[str]]) -> List[str]:
        if isinstance(input_files, str):
            if os.path.isdir(input_files):
                files = [f for f in os.listdir(input_files) if f.endswith(".h5")]
                files = [os.path.join(input_files, f) for f in files]
            else:
                raise ValueError(
                    "If a string is provided, it must be a directory path."
                )
        elif isinstance(input_files, list):
            files = [f for f in input_files if os.path.isfile(f) and f.endswith(".h5")]
            if len(files) != len(input_files):
                raise ValueError("All input files must exist and have .h5 extension.")
        else:
            raise TypeError(
                "input_files must be either a string (directory path) or a list of file paths."
            )

        return sorted(
            files,
            key=lambda x: (
                int(re.search(r"_(\d+)\.h5$", x).group(1))
                if re.search(r"_(\d+)\.h5$", x)
                else float("inf")
            ),
        )

    files = get_file_list(input_files)

    # First pass: calculate total size and determine vector dimension
    total_rows = 0
    vector_dim = None
    for file_path in tqdm(files, desc="Calculating total size"):
        with h5py.File(file_path, "r") as h5_in:
            total_rows += h5_in["ids"].shape[0]
            if vector_dim is None:
                vector_dim = h5_in["vectors"].shape[1]

    with h5py.File(output_file, "w") as h5_out:
        # Initialize datasets in the output file
        id_dataset = h5_out.create_dataset(
            "ids",
            shape=(total_rows,),
            dtype=h5py.special_dtype(vlen=str),
            chunks=True,
        )
        vector_dataset = h5_out.create_dataset(
            "vectors",
            shape=(total_rows, vector_dim),
            dtype=np.float32,
            chunks=True,
        )

        # Second pass: copy data with more granular progress updates
        current_index = 0
        with tqdm(total=total_rows, desc="Combining files", unit="rows") as pbar:
            for file_path in files:
                with h5py.File(file_path, "r") as h5_in:
                    file_size = h5_in["ids"].shape[0]

                    for i in range(0, file_size, chunk_size):
                        end = min(i + chunk_size, file_size)
                        chunk_size_actual = end - i

                        # Read and write IDs
                        ids = h5_in["ids"][i:end]
                        id_dataset[
                            current_index : current_index + chunk_size_actual
                        ] = [id.decode("utf-8") for id in ids]

                        # Read and write vectors
                        vectors = h5_in["vectors"][i:end]
                        vector_dataset[
                            current_index : current_index + chunk_size_actual
                        ] = vectors

                        current_index += chunk_size_actual
                        pbar.update(chunk_size_actual)

        print(f"Combined {total_rows} rows into {output_file}")


def extract_h5_entries(
    input_file: str, output_file: str, targets: Set[str], chunk_size: int = 10000
) -> Set[str]:
    """
    Extract specific entries from a large H5 file based on target IDs and save them to a new H5 file.

    This function reads 'ids' and 'vectors' datasets from the input H5 file in chunks,
    finds the entries corresponding to the target IDs, and saves them
    to the output H5 file. The order of entries in the output file may differ
    from the input file, but the correspondence between IDs and vectors is preserved.

    Args:
        input_file (str): Path to the input H5 file.
        output_file (str): Path to the output H5 file.
        targets (Set[str]): Set of IDs to extract.
        chunk_size (int): Number of entries to process at a time. Default is 10000.

    Returns:
        Set[str]: A set of IDs that were not found in the H5 file.

    Raises:
        ValueError: If 'ids' or 'vectors' datasets are not found in the input file.
        ValueError: If the number of IDs and vectors in the input file don't match.
        FileExistsError: If the output file already exists.
    """
    if os.path.exists(output_file):
        raise FileExistsError(
            f"Output file '{output_file}' already exists. Please choose a different output file name."
        )

    print(f"Opening input file: {input_file}")
    with h5py.File(input_file, "r") as in_file, h5py.File(output_file, "w") as out_file:
        if "ids" not in in_file or "vectors" not in in_file:
            raise ValueError("Input file must contain 'ids' and 'vectors' datasets")

        ids_dataset = in_file["ids"]
        vectors_dataset = in_file["vectors"]

        if len(ids_dataset) != len(vectors_dataset):
            raise ValueError("Number of IDs and vectors in input file don't match")

        total_entries = len(ids_dataset)
        vector_shape = vectors_dataset.shape[1:]

        # Create datasets in the output file
        out_ids = out_file.create_dataset(
            "ids", shape=(0,), maxshape=(None,), dtype=ids_dataset.dtype
        )
        out_vectors = out_file.create_dataset(
            "vectors",
            shape=(0,) + vector_shape,
            maxshape=(None,) + vector_shape,
            dtype=vectors_dataset.dtype,
        )

        found_count = 0
        not_found_ids = set(targets)  # Initialize with all target IDs

        for start_idx in tqdm(
            range(0, total_entries, chunk_size), desc="Processing chunks"
        ):
            end_idx = min(start_idx + chunk_size, total_entries)

            chunk_ids = ids_dataset[start_idx:end_idx]
            chunk_vectors = vectors_dataset[start_idx:end_idx]

            # Find matching IDs in the current chunk
            chunk_id_set = set(id.decode() for id in chunk_ids)
            matching_ids = chunk_id_set.intersection(not_found_ids)

            if matching_ids:
                mask = np.array([id.decode() in matching_ids for id in chunk_ids])
                matching_chunk_ids = chunk_ids[mask]
                matching_chunk_vectors = chunk_vectors[mask]

                # Resize output datasets
                current_size = out_ids.shape[0]
                new_size = current_size + len(matching_chunk_ids)
                out_ids.resize(new_size, axis=0)
                out_vectors.resize(new_size, axis=0)

                # Add matching data to output datasets
                out_ids[current_size:new_size] = matching_chunk_ids
                out_vectors[current_size:new_size] = matching_chunk_vectors

                found_count += len(matching_chunk_ids)
                not_found_ids -= matching_ids

    print(f"Found {found_count} out of {len(targets)} target IDs.")
    print(f"Still missing: {len(not_found_ids)}")
    return not_found_ids


def extract_h5_ids(file_path: str) -> Set[str]:
    """
    Extract and decode IDs from an HDF5 file, keeping track of duplicates.
    This function opens an HDF5 file, reads the 'ids' dataset,
    decodes each ID from bytes to UTF-8 strings, and returns
    a set of unique IDs. It also prints the number of duplicate IDs found.

    Args:
        file_path (str): The path to the HDF5 file.

    Returns:
        Set[str]: A set of unique, decoded IDs.

    Raises:
        IOError: If the file cannot be opened or read.
        KeyError: If the 'ids' dataset is not found in the file.
    """
    with h5py.File(file_path, "r") as h5_file:
        ids = h5_file["ids"][:]
        id_counter = Counter()
        for id in tqdm(ids, desc="Extracting IDs", unit="id"):
            id_counter[id.decode("utf-8")] += 1

    id_set = set(id_counter.keys())
    duplicate_count = sum(count - 1 for count in id_counter.values() if count > 1)

    print(f"Successfully extracted {len(id_set):,} unique ids")
    print(f"Also noticed {duplicate_count:,} duplicate ids")

    return id_set


def deduplicate_h5_file(input_filename, output_filename, chunk_size=10000):
    """
    Create a de-duplicated version of the input H5 file, optimized for very large files.
    Works without knowing the total number of entries in advance.

    :param input_filename: Name of the input H5 file
    :param output_filename: Name of the output H5 file
    :param chunk_size: Number of entries to process at a time
    :return: Number of duplicates removed
    :raises FileExistsError: If the output file already exists
    """
    if os.path.exists(output_filename):
        raise FileExistsError(
            f"Output file '{output_filename}' already exists. Please choose a different output file name."
        )

    with (
        h5py.File(input_filename, "r") as input_file,
        h5py.File(output_filename, "w") as output_file,
    ):
        # Get dataset information
        ids_dataset = input_file["ids"]
        vectors_dataset = input_file["vectors"]
        total_entries = ids_dataset.shape[0]

        # Create datasets in the output file with unlimited max shape
        output_ids = output_file.create_dataset(
            "ids", shape=(0,), dtype=ids_dataset.dtype, maxshape=(None,), chunks=True
        )
        output_vectors = output_file.create_dataset(
            "vectors",
            shape=(0, vectors_dataset.shape[1]),
            dtype=vectors_dataset.dtype,
            maxshape=(None, vectors_dataset.shape[1]),
            chunks=True,
        )

        unique_ids = {}

        # Process the file in chunks
        with tqdm(total=total_entries, desc="De-duplicating", unit="entry") as pbar:
            for start_idx in range(0, total_entries, chunk_size):
                end_idx = min(start_idx + chunk_size, total_entries)

                chunk_ids = ids_dataset[start_idx:end_idx]
                chunk_vectors = vectors_dataset[start_idx:end_idx]

                for i, id_value in enumerate(chunk_ids):
                    id_str = id_value.decode("utf-8")
                    if id_str not in unique_ids:
                        unique_ids[id_str] = len(unique_ids)

                # Resize output datasets
                new_size = len(unique_ids)
                output_ids.resize((new_size,))
                output_vectors.resize((new_size, vectors_dataset.shape[1]))

                # Write new unique entries
                for i, id_value in enumerate(chunk_ids):
                    id_str = id_value.decode("utf-8")
                    index = unique_ids[id_str]
                    output_ids[index] = id_value
                    output_vectors[index] = chunk_vectors[i]

                pbar.update(end_idx - start_idx)

    duplicates_removed = total_entries - len(unique_ids)
    print(f"De-duplication complete. Unique entries: {len(unique_ids)}")
    print(f"Number of duplicates removed: {duplicates_removed}")
    return duplicates_removed


def create_id_mapping(correct_ids: Set[str]) -> Dict[str, str]:
    """
    Create a mapping from incorrectly underscored IDs to correct IDs.
    Only considers IDs that contain a period (.) in the correct version.

    Args:
        correct_ids (Set[str]): Set of correct IDs.

    Returns:
        Dict[str, str]: A dictionary mapping incorrectly underscored IDs to correct IDs.

    Raises:
        ValueError: If the set of correct IDs is empty.
    """
    if not correct_ids:
        raise ValueError("The set of correct IDs is empty")

    id_mapping = {}
    for correct_id in correct_ids:
        if "." in correct_id:
            incorrect_id = correct_id.replace(".", "_")
            id_mapping[incorrect_id] = correct_id

    print(f"Created mapping for {len(id_mapping)} IDs")
    return id_mapping


def fix_underscored_ids_in_h5(
    input_file: str,
    output_file: str,
    id_mapping: Dict[str, str],
    chunk_size: int = 10000,
) -> None:
    """
    Fix underscored IDs in a large H5 file based on the provided mapping and write to a new file.

    This function processes the input file in chunks to minimize memory usage and improve
    efficiency when working with large files.

    Args:
        input_file (str): Path to the input H5 file to be fixed.
        output_file (str): Path to the output H5 file with fixed IDs.
        id_mapping (Dict[str, str]): A dictionary mapping incorrectly underscored IDs to correct IDs.
        chunk_size (int): Number of rows to process at a time. Default is 10000.

    Raises:
        FileNotFoundError: If the specified input file does not exist.
        KeyError: If the 'ids' dataset is not found in the H5 file.
        FileExistsError: If the output file already exists.
    """
    if os.path.exists(output_file):
        raise FileExistsError(
            f"Output file '{output_file}' already exists. Please choose a different output file name."
        )

    with h5py.File(input_file, "r") as in_file, h5py.File(output_file, "w") as out_file:
        if "ids" not in in_file or "vectors" not in in_file:
            raise KeyError("The 'ids' or 'vectors' dataset is not found in the H5 file")

        total_rows = in_file["ids"].shape[0]
        vector_dim = in_file["vectors"].shape[1]

        # Create datasets in the output file
        out_ids = out_file.create_dataset(
            "ids", shape=(total_rows,), dtype=h5py.special_dtype(vlen=str), chunks=True
        )
        out_vectors = out_file.create_dataset(
            "vectors",
            shape=(total_rows, vector_dim),
            dtype=in_file["vectors"].dtype,
            chunks=True,
        )

        print("Processing file in chunks")
        for start_idx in tqdm(
            range(0, total_rows, chunk_size), desc="Fixing IDs", unit="chunk"
        ):
            end_idx = min(start_idx + chunk_size, total_rows)

            # Read chunk of IDs and vectors
            chunk_ids = in_file["ids"][start_idx:end_idx]
            chunk_vectors = in_file["vectors"][start_idx:end_idx]

            # Fix IDs in the chunk
            fixed_chunk_ids = [
                id_mapping.get(id.decode(), id.decode()) for id in chunk_ids
            ]

            # Write fixed IDs and corresponding vectors to output file
            out_ids[start_idx:end_idx] = fixed_chunk_ids
            out_vectors[start_idx:end_idx] = chunk_vectors

    print("IDs have been successfully fixed and written to the new file")


def optimize_protein_embedding_chunks(
    src_path: str | Path, dst_path: str | Path, train_batch_size: int = 16384
):
    """
    Create a new HDF5 file with chunking optimized for protein embedding access during training.

    This function specifically optimizes HDF5 chunking for protein embedding files that contain:
    - 'ids': Protein identifiers
    - 'vectors': Protein embeddings (typically 1024-dimensional ProtT5 vectors)

    The chunking strategy is optimized for the training access pattern where we load
    batches of protein embeddings sequentially. Poor chunk sizing can severely impact
    performance because:
    1. If chunks are too small (e.g., 64 proteins), reading a training batch of 16384
       proteins requires reading 256 separate chunks from disk
    2. If chunks are poorly shaped (e.g., 27317x4), reading a single protein's embedding
       requires loading data for thousands of other proteins

    Args:
        src_path: Source HDF5 file path containing protein embeddings
        dst_path: Destination HDF5 file path for optimized version
        train_batch_size: Batch size used during training (default: 16384)
                         This should match the train_batch_size in your training config

    Raises:
        FileNotFoundError: If the source file doesn't exist
        KeyError: If required datasets are missing
        FileExistsError: If the destination file already exists
        ValueError: If the input file contains empty datasets
    """
    src_path = Path(src_path)
    dst_path = Path(dst_path)

    if dst_path.exists():
        raise FileExistsError(f"Output file '{dst_path}' already exists")

    print(f"Optimizing chunking for {src_path.name}")
    print(f"Writing to {dst_path}")

    with h5py.File(src_path, "r") as src, h5py.File(dst_path, "w") as dst:
        # Get total size for progress bar
        if "ids" not in src or "vectors" not in src:
            raise KeyError("Input file must contain 'ids' and 'vectors' datasets")

        total_vectors = src["vectors"].shape[0]
        if total_vectors == 0:
            raise ValueError("Input file contains empty datasets")

        # Calculate optimal chunk size (min of dataset size and batch size)
        chunk_size = min(total_vectors, train_batch_size)

        # Copy ids with optimized chunking
        print("Copying ids dataset...")
        dst.create_dataset(
            "ids",
            data=src["ids"][:],
            chunks=(chunk_size,),
            dtype=h5py.special_dtype(vlen=str),
        )

        # Create vectors dataset with optimized chunking
        print("Creating vectors dataset...")
        vectors_shape = src["vectors"].shape
        dst.create_dataset(
            "vectors",
            shape=vectors_shape,
            chunks=(chunk_size, vectors_shape[1]),
            dtype=np.float32,
        )

        # Copy vectors in chunks to manage memory
        print("Copying vectors dataset...")
        for i in tqdm(range(0, total_vectors, chunk_size)):
            end_idx = min(i + chunk_size, total_vectors)
            dst["vectors"][i:end_idx] = src["vectors"][i:end_idx].astype(np.float32)

    # Verify the copy
    print("Verifying copy...")
    with h5py.File(src_path, "r") as src, h5py.File(dst_path, "r") as dst:
        assert np.all(src["ids"][:5] == dst["ids"][:5]), "IDs don't match"
        assert np.allclose(
            src["vectors"][:5], dst["vectors"][:5], rtol=1e-6, atol=1e-6
        ), "Vectors don't match"
        print(f"Original chunks: {src['vectors'].chunks}")
        print(f"New chunks: {dst['vectors'].chunks}")

    print("Done!")


def test_protein_embedding_read_speed(filepath: str, batch_size: int = 16384):
    """
    Test read speed for random batches of protein embeddings from an HDF5 file.

    This function performs a simple benchmark by reading 50 random batches of protein
    embeddings and calculating the average read time. This can be useful for:
    1. Comparing different chunking strategies
    2. Validating I/O performance after file optimization
    3. Debugging slow read performance

    Args:
        filepath: Path to the HDF5 file containing protein embeddings.
                 Must contain a 'vectors' dataset.
        batch_size: Number of embeddings to read in each batch.
                   Default is 16384 to match typical training batch sizes.

    Prints:
        Average time taken to read a batch of embeddings.

    Raises:
        FileNotFoundError: If the specified file doesn't exist
        KeyError: If the file doesn't contain a 'vectors' dataset
        ValueError: If batch_size is larger than the total number of vectors
    """
    with h5py.File(filepath, "r") as f:
        vectors = f["vectors"]
        total_vectors = vectors.shape[0]

        if batch_size > total_vectors:
            raise ValueError(
                f"Batch size ({batch_size}) cannot be larger than "
                f"total number of vectors ({total_vectors})"
            )

        read_times = []

        for _ in tqdm(range(50), desc="Testing read speed", unit="batch"):
            batch_start = time.time()
            idx = np.random.randint(0, total_vectors - batch_size)
            _ = vectors[idx : idx + batch_size]
            read_times.append(time.time() - batch_start)

        avg_time = sum(read_times) / len(read_times)
        print(f"\nResults:")
        print(f"  Average time per read: {avg_time:.3f} seconds")
        print(f"  Min time per read:     {min(read_times):.3f} seconds")
        print(f"  Max time per read:     {max(read_times):.3f} seconds")
