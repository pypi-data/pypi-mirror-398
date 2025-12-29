import gzip
import logging
import math
import multiprocessing
import os
import re
import sqlite3
import time
from functools import partial
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple, Union

import requests
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

logger = logging.getLogger(__name__)


def _clean_noncanonical_fasta(
    input_path: str,
    output_path: Optional[str] = None,
    split_char: str = " ",
    id_field: int = 0,
) -> Optional[dict[str, str]]:
    """
    Read in a FASTA file containing multiple sequences, replace non-canonical amino acids,
    remove stop codons, remove empty sequences, and either write the sequences to a new FASTA file or return them as a dictionary.

    Args:
        input_path (str): Path to the input FASTA file.
        output_path (Optional[str]): Path to the output FASTA file. If None, the sequences are returned as a dictionary.
        split_char (str): Character used to split the identifier in the header.
        id_field (int): Field index for the identifier after splitting.

    Returns:
        Optional[dict[str, str]]: A dictionary with sequence identifiers as keys and cleaned sequences as values if output_path is None.
    """
    logger.info("Reading FASTA file: %s", input_path)
    if output_path:
        logger.info("Writing FASTA file: %s", output_path)

    sequences = {}
    with open(input_path, "r") as fasta_file:
        seq_id = ""
        seq_lines = []

        for line in fasta_file:
            if line.startswith(">"):
                if seq_id and seq_lines:
                    seq = (
                        "".join(seq_lines)
                        .translate(str.maketrans("OJUZB", "XLCED"))
                        .replace("*", "")
                    )
                    if seq.strip():  # Only process non-empty sequences
                        sequences[seq_id] = seq
                        if output_path:
                            with open(output_path, "a") as output_file:
                                output_file.write(f">{seq_id}\n{seq}\n")
                seq_lines = []
                seq_id = line[1:].strip().split(split_char)[id_field]
            else:
                seq_lines.append(line.strip().replace("-", "").upper())

        # Process the last sequence
        if seq_id and seq_lines:
            seq = (
                "".join(seq_lines)
                .translate(str.maketrans("OJUZB", "XLCED"))
                .replace("*", "")
            )
            if seq.strip():  # Only process non-empty sequences
                sequences[seq_id] = seq
                if output_path:
                    with open(output_path, "a") as output_file:
                        output_file.write(f">{seq_id}\n{seq}\n")

    logger.info("FASTA file processing completed.")
    if not output_path:
        return sequences


def _check_output_file(output_path: str) -> None:
    """
    Check if the output file already exists and raise an error if it does.

    Args:
        output_path (str): Path to the output file.

    Raises:
        FileExistsError: If the output file already exists.
    """
    if os.path.exists(output_path):
        raise FileExistsError(f"Output file already exists: {output_path}")


def clean_noncanonical_fasta(
    input_path: str, output_path: str, split_char: str = " ", id_field: int = 0
):
    """
    Read in a FASTA file containing multiple sequences and write the sequences to a new FASTA file.
    Replace non-canonical amino acids and remove stop codons along the way.

    Args:
        input_path (str): Path to the input FASTA file.
        output_path (str): Path to the output FASTA file.
        split_char (str): Character used to split the identifier in the header.
        id_field (int): Field index for the identifier after splitting.

    Raises:
        FileExistsError: If the output file already exists.
    """
    _check_output_file(output_path)
    _clean_noncanonical_fasta(input_path, output_path, split_char, id_field)


def clean_noncanonical_fasta_to_dict(
    input_path: str, split_char: str = " ", id_field: int = 0
) -> dict[str, str]:
    """
    Read in a FASTA file containing multiple sequences and return the sequences as a dictionary.
    Replace non-canonical amino acids and remove stop codons along the way.

    Args:
        input_path (str): Path to the input FASTA file.
        split_char (str): Character used to split the identifier in the header.
        id_field (int): Field index for the identifier after splitting.

    Returns:
        dict[str, str]: A dictionary with sequence identifiers as keys and cleaned sequences as values.
    """
    ans = _clean_noncanonical_fasta(input_path, None, split_char, id_field)
    if not ans:
        return {}

    return ans


def combine_fasta_files(input_path: Union[str, List[str]], output_path: str) -> None:
    """Combine several FASTA files into one.
    Args:
        input_path (Union[str, List[str]]): Folder of fasta files or list of file paths to be combined.
        output_path (str): Output path for the combined fasta file.

    Raises:
        FileExistsError: If the output file already exists.
    """
    from tqdm import tqdm

    _check_output_file(output_path)

    if isinstance(input_path, str):
        # If input_path is a string, treat it as a folder path
        fasta_files = sorted(
            [
                os.path.join(input_path, file)
                for file in os.listdir(input_path)
                if file.endswith((".fasta", ".faa"))
            ]
        )
    else:
        # If input_path is a list, use it directly
        fasta_files = input_path

    total_size = sum(os.path.getsize(file) for file in fasta_files)

    with open(output_path, "w") as outfile:
        with tqdm(
            total=total_size, unit="B", unit_scale=True, desc="Combining files"
        ) as pbar:
            for fasta_file in fasta_files:
                file_size = os.path.getsize(fasta_file)
                with open(fasta_file, "r") as infile:
                    for chunk in iter(lambda: infile.read(8192), ""):
                        outfile.write(chunk)
                        pbar.update(len(chunk))
                outfile.write("\n")
                pbar.update(file_size - pbar.n + pbar.last_print_n)

    print(f"Combined {len(fasta_files)} .fasta files into {output_path}.")


def extract_uniprot_dat_to_fasta(
    dat_file_path: str, fasta_file_path: str, max_entries: int | None = None
):
    """Extract all the sequences from a Uniprot DAT file into a FASTA file.

    Args:
        dat_file_path (str): Path to the input Uniprot DAT file.
        fasta_file_path (str): Path to the output FASTA file.
        max_entries (int | None, optional): Maximum number of entries to extract.
                                        If None, all entries are processed.

    Raises:
        FileExistsError: If the output file already exists.
    """
    _check_output_file(fasta_file_path)
    start_time = time.time()

    with open(dat_file_path, "r") as dat_file:
        print("Calculating file length...")
        total_lines = sum(1 for _ in dat_file)
        print(f"File has {total_lines:,} lines.")

    with open(dat_file_path, "r") as dat_file:
        with open(fasta_file_path, "w") as fasta_file:
            current_id = ""
            sequence = ""
            recording_sequence = False
            entries_count = 0
            batch_size = 1000
            buffer = []
            processed_lines = 0
            update_interval = 1000000  # Update progress every 1 million lines

            for line in dat_file:
                processed_lines += 1

                if line.startswith("AC"):
                    # Extract the ID
                    current_id = line.strip().split()[1].rstrip(";")
                elif line.startswith("SQ"):
                    # Start recording the sequence lines after this
                    recording_sequence = True
                    sequence = ""
                elif recording_sequence and line.startswith("  "):
                    # Concatenate sequence lines directly
                    sequence += line.strip()
                elif line.startswith("//"):
                    # End of an entry; write to FASTA file if we have a sequence
                    if sequence and current_id:
                        buffer.append(f">{current_id}\n{sequence.replace(' ', '')}\n")
                        entries_count += 1

                        if len(buffer) >= batch_size:
                            fasta_file.write("".join(buffer))
                            buffer = []

                    # Reset for the next entry
                    recording_sequence = False
                    current_id = ""
                    sequence = ""

                    # Check if we've reached the maximum number of entries to extract
                    if max_entries and entries_count >= max_entries:
                        break

                # Print progress update every update_interval lines
                if processed_lines % update_interval == 0:
                    elapsed_time = time.time() - start_time
                    progress_percentage = (processed_lines / total_lines) * 100
                    print(
                        f"Done with {progress_percentage:.2f}% : {entries_count:,} sequences in {elapsed_time:.2f} seconds."
                    )

            # Write any remaining entries in the buffer
            if buffer:
                fasta_file.write("".join(buffer))

    end_time = time.time()
    execution_time = end_time - start_time

    # Print final count and execution time
    print(f"\nTotal sequences processed: {entries_count:,}")
    print(f"Total lines processed: {processed_lines:,}")
    print(f"Execution time: {execution_time:.2f} seconds")


def split_fasta(
    fasta_file: str,
    target_folder: str,
    base_name: str,
    sequences_per_file: int = 1000,
    max_files: int | None = None,
    show_progress: bool = True,
    target_chunk_size_bytes: int | None = None,
) -> int:
    """Split a FASTA file into multiple smaller files within a target folder,
    with an overall progress bar. Files can be split based on a target number
    of sequences or an approximate target file size in bytes.

    Args:
        fasta_file (str): Path to the input FASTA file.
        target_folder (str): Path to the folder where output files will be saved.
        base_name (str): Used to make output filenames: eg, basename_1.fasta.
        sequences_per_file (int): Number of sequences per output file.
            This is used if target_chunk_size_bytes is None.
        max_files (int, optional): Maximum number of files to create.
            If None, all sequences are processed.
        show_progress (bool): If True, display a progress bar based on
            file size processed. Defaults to True.
        target_chunk_size_bytes (int, optional): Approximate target size for
            each output file in bytes. If set, this takes precedence over
            sequences_per_file. The actual file size may be slightly larger to
            ensure full FASTA entries. Defaults to None.

    Returns:
        int: The number of output files created.
    """
    from typing import TYPE_CHECKING, Optional

    if TYPE_CHECKING:
        from tqdm import tqdm

    # Ensure the target folder exists
    os.makedirs(target_folder, exist_ok=True)

    # We create output files lazily (on first sequence) so we don't end up with
    # spurious empty files.  `files_created` tracks the number of *real* files
    # present on disk when we finish.
    files_created = 0
    current_output_file_sequence_count = 0
    current_output_file_bytes_written = 0
    pbar: Optional["tqdm"] = None
    output_file = None  # Will be opened when we encounter the first header line
    output_file_path = ""

    if target_chunk_size_bytes is not None:
        print(
            f"Splitting by target chunk size: {target_chunk_size_bytes / (1024*1024):.2f} MB"
        )
    else:
        print(f"Splitting by sequences per file: {sequences_per_file}")

    try:
        # Open the large FASTA file for reading
        with open(fasta_file, "r", buffering=1024 * 1024) as fasta:
            if show_progress:
                from tqdm import tqdm

                total_size = os.path.getsize(fasta_file)
                pbar = tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    desc=f"Splitting {os.path.basename(fasta_file)}",
                )

            # We create output files on demand.  The very first file is not
            # opened until we see the first sequence header.  This prevents
            # an empty file from being created when the input FASTA is empty
            # or when `max_files` is reached before any data are written.
            def _open_new_output_file():
                nonlocal output_file, output_file_path, files_created

                files_created += 1
                output_file_path = os.path.join(
                    target_folder, f"{base_name}_{files_created}.fasta"
                )
                output_file = open(output_file_path, "w", buffering=1024 * 1024)

            # Helper for logging and closing the current file
            def _close_current_output_file():
                nonlocal output_file, current_output_file_sequence_count, current_output_file_bytes_written
                if output_file and not output_file.closed:
                    output_file.close()
                    print(
                        f"File written: {output_file_path} "
                        f"(Sequences: {current_output_file_sequence_count}, "
                        f"Bytes: {current_output_file_bytes_written} / {(current_output_file_bytes_written / (1024*1024)):.2f} MB)"
                    )

            for line in fasta:
                line_bytes = len(line.encode("utf-8"))
                if pbar:
                    pbar.update(line_bytes)

                # Note: we don't enforce `max_files` here; we enforce it only when we
                # are about to create *another* file (see logic further below). This
                # ensures we finish writing the current file before stopping.

                # If line starts with ">", it's the beginning of a new sequence
                if line.startswith(">"):
                    # Decide whether we need to roll over to a new output file.
                    needs_new_file = False  # reset each time we encounter a header

                    if (
                        output_file is not None
                        and current_output_file_sequence_count > 0
                    ):
                        if target_chunk_size_bytes is not None:
                            # Size-based splitting takes precedence over sequence count.
                            if (
                                current_output_file_bytes_written
                                >= target_chunk_size_bytes
                            ):
                                needs_new_file = True
                        else:
                            # Fallback to sequence-count based splitting.
                            if current_output_file_sequence_count >= sequences_per_file:
                                needs_new_file = True

                    if needs_new_file:
                        _close_current_output_file()

                        # Respect `max_files`: do not create another file if limit reached
                        if max_files is not None and files_created >= max_files:
                            break

                        _open_new_output_file()
                        current_output_file_sequence_count = 0
                        current_output_file_bytes_written = 0

                    # Opening first file if not already open
                    if output_file is None:
                        _open_new_output_file()

                    current_output_file_sequence_count += 1

                # Write the line to the current output file (which should now exist)
                if output_file is not None:
                    output_file.write(line)
                    current_output_file_bytes_written += line_bytes

            # After loop, ensure the last file is handled
            _close_current_output_file()

    finally:
        if pbar:
            pbar.close()
        # Ensure the file is closed in case of an exception before the natural end
        if output_file and not output_file.closed:
            output_file.close()
            # It's hard to know the state to print a meaningful message here if an exception occurred mid-file.
            # The primary 'File written' messages are handled within the loop and at the end of normal processing.

    # If the last file was empty and removed, and it was the only file, file_count might be 1.
    # Adjust file_count if the last output file was empty and removed.
    if os.path.exists(output_file_path) and os.path.getsize(output_file_path) == 0:
        # This can happen if max_files is hit exactly when a new file is due to be created,
        # or if the input file itself is empty or contains no FASTA entries after the last split point.
        # We should not count this empty file if it was removed.
        # However, file_count is already incremented *before* a new file is opened.
        # The logic for removing empty files is tricky to perfectly align with file_count
        # without more complex state tracking. The current return reflects the number of
        # *attempted* file creations that weren't immediately curtailed by max_files.
        # For simplicity, we'll return the file_count as is, understanding it might
        # include an empty file that was subsequently removed if it was the very last one.
        # A more robust approach might decrement file_count if the last created file path was removed.
        pass

    return files_created


def subtract_fasta_files(file1: str, file2: str, output_file: str):
    """Load two fasta files and get their set subtraction as a new fasta file.
    The TQDM progress bar for loading files is broken, but adds a little
    feedback and is better than nothing.

    Args:
        file1 (str): File with everything you want
        file2 (str): File with everything you don't want
        output_file (str): Everything in file1, unless it's in file2

    Raises:
        FileExistsError: If the output file already exists.
    """
    from Bio import SeqIO
    from tqdm import tqdm

    _check_output_file(output_file)

    # Load sequences from file1 with a progress bar
    print(f"Loading sequences from {file1}")
    sequences_file1 = {
        record.id: record
        for record in tqdm(
            SeqIO.parse(file1, "fasta"), desc="Loading sequences from file1"
        )
    }
    print(f"Number of sequences in {file1}: {len(sequences_file1)}")

    # Load sequences from file2 with a progress bar
    print(f"Loading sequences from {file2}")
    sequences_file2 = {
        record.id: record
        for record in tqdm(
            SeqIO.parse(file2, "fasta"), desc="Loading sequences from file2"
        )
    }

    print(f"Number of sequences in {file2}: {len(sequences_file2)}")

    # Find sequences that are in file1 but not in file2
    unique_sequences = [
        record for id, record in sequences_file1.items() if id not in sequences_file2
    ]

    print(f"Number of UNIQUE sequences in {file1}: {len(unique_sequences)}")

    # Write unique sequences to the output file with a progress bar
    with open(output_file, "w") as output_handle:
        for record in tqdm(
            unique_sequences, desc="Writing unique sequences to output file"
        ):
            SeqIO.write(record, output_handle, "fasta")


def simplify_fasta_ids(
    input_fasta: str, output_fasta: str, progress_interval=100000
) -> None:
    """Take a fasta file with either full IDs that UNIPROT normally publishes
    or IDs in the format 'eco:b0002 description', and rewrite it into a file
    with the same sequences but simplified IDs that are just the accession numbers.

    For UNIPROT-style IDs, the accession number is assumed to be the second part between '|' characters.
    For 'eco:b0002' style IDs, the entire 'eco:b0002' is considered the accession number.

    Args:
        input_fasta (str): path to the input file
        output_fasta (str): path where to write the output
        progress_interval (int, optional): print out progress every n sequences. Defaults to 100k.

    Raises:
        FileExistsError: If the output file already exists.
    """
    from Bio import SeqIO

    _check_output_file(output_fasta)

    count = 0

    with (
        open(input_fasta, "r") as input_handle,
        open(output_fasta, "w") as output_handle,
    ):
        for record in SeqIO.parse(input_handle, "fasta"):
            # Check if the ID contains '|' characters (UNIPROT style)
            if "|" in record.id:
                accession = record.id.split("|")[1]
            else:
                # For 'eco:b0002' style, extract everything up to the first space
                accession = record.id.split()[0]

            # Update the record id and description
            record.id = accession
            record.description = ""
            # Write the updated record to the output file
            SeqIO.write(record, output_handle, "fasta")

            # Print progress
            count += 1
            if count % progress_interval == 0:
                print(f"Processed {count} sequences")

        # Final progress update
        print(f"Processed {count} sequences in total")


def estimate_sequences(fasta_file: str, sample_size: int = 100000) -> int:
    """
    Estimate the number of sequences in a FASTA file based on file size and a sample.

    Args:
        fasta_file (str): Path to the input FASTA file (can be .fasta or .fasta.gz).
        sample_size (int): Number of bytes to sample for estimation.

    Returns:
        int: Estimated number of sequences in the FASTA file.
    """
    print("Estimating number of sequences in FASTA file...")
    file_size = os.path.getsize(fasta_file)
    if file_size == 0:
        return 0

    is_gzipped = fasta_file.endswith(".gz")
    open_func = gzip.open if is_gzipped else open

    with open_func(fasta_file, "rt") as handle:
        sample = handle.read(min(sample_size, file_size))
        sample_sequences = sample.count(">")

    if len(sample) == 0:
        return 0

    # Estimate total sequences based on the sample
    estimated_sequences = int((sample_sequences / len(sample)) * file_size)

    # Adjust for potential underestimation due to short sequences
    adjustment_factor = 1.1  # 10% increase
    return max(int(estimated_sequences * adjustment_factor), 1)


def extract_ids_from_fasta(fasta_file: str) -> Set[str]:
    """
    Extract all sequence IDs from a large FASTA file (compressed or uncompressed) using BioPython.

    Args:
        fasta_file (str): Path to the input FASTA file (can be .fasta or .fasta.gz).

    Returns:
        Set[str]: A set containing all unique sequence IDs found in the FASTA file.

    Raises:
        ValueError: If there's an issue reading or parsing the input file.
    """
    from Bio import SeqIO
    from tqdm import tqdm

    sequence_ids: Set[str] = set()
    try:
        estimated_records = estimate_sequences(fasta_file)

        if estimated_records == 0:
            return sequence_ids  # Return empty set for empty files

        is_gzipped = fasta_file.endswith(".gz")
        open_func = gzip.open if is_gzipped else open

        with open_func(fasta_file, "rt") as handle:
            with tqdm(total=estimated_records, desc="Extracting IDs") as pbar:
                for record in SeqIO.parse(handle, "fasta"):
                    sequence_ids.add(record.id)
                    pbar.update(1)

    except Exception as e:
        print(f"An error occurred while processing the file: {e}")
        raise ValueError(f"Error parsing FASTA file: {e}")

    print(f"\nExtracted {len(sequence_ids)} unique sequence IDs")
    return sequence_ids


def process_chunk(
    chunk: List[str], target_ids_lower: Set[str], exclude: bool
) -> Tuple[List[str], Set[str]]:
    output_sequences = []
    written_ids = set()
    current_id: str = ""
    current_seq: List[str] = []

    # Get a unique worker ID, could be process ID
    worker_id = os.getpid()
    logger.debug(
        f"SUBSET_FASTA_PROCESS_CHUNK: Worker {worker_id} processing a chunk. Target IDs count: {len(target_ids_lower)}, Exclude: {exclude}"
    )
    try:

        def id_matches(seq_id: str) -> bool:
            return any(part.lower() in target_ids_lower for part in seq_id.split("|"))

        for line in chunk:
            line = line.strip()
            if line.startswith(">"):
                if current_id and current_seq:
                    if id_matches(current_id) != exclude:
                        output_sequences.append(
                            f">{current_id}\n{''.join(current_seq)}\n"
                        )
                        written_ids.add(current_id)
                current_id = line[1:]
                current_seq = []
            elif current_id:
                current_seq.append(line)

        # Process the last sequence in the chunk
        if current_id and current_seq and id_matches(current_id) != exclude:
            output_sequences.append(f">{current_id}\n{''.join(current_seq)}\n")
            written_ids.add(current_id)

    except Exception as e:
        logger.error(
            f"SUBSET_FASTA_PROCESS_CHUNK: Worker {worker_id} encountered error: {e}",
            exc_info=True,
        )
        # Re-raising the exception so the main process's pool error handling can catch it
        raise
    logger.debug(
        f"SUBSET_FASTA_PROCESS_CHUNK: Worker {worker_id} finished chunk. Output sequences: {len(output_sequences)}, Written IDs: {len(written_ids)}"
    )
    return output_sequences, written_ids


def subset_fasta(
    fasta_file: str,
    output_path: str,
    target_ids: Set[str],
    exclude: bool = False,
    return_written_ids: bool = False,
) -> Optional[Set[str]]:
    """
    Create a new FASTA file with sequences that either match or don't match the target IDs.
    Optimized for very large files and uses all available CPU cores.

    Args:
        fasta_file (str): Path to the input FASTA file.
        output_path (str): Path to the output FASTA file.
        target_ids (Set[str]): A set of sequence IDs to match.
        exclude (bool): If True, write sequences that don't match target_ids. If False, write matching sequences.
        return_written_ids (bool): If True, return the set of sequence IDs that were written to the output file.

    Returns:
        Optional[Set[str]]: A set of sequence IDs that were written to the output file if return_written_ids is True,
                           otherwise None.

    Raises:
        FileExistsError: If the output file already exists.
    """
    logger.info(
        f"SUBSET_FASTA: Starting for input '{fasta_file}', output '{output_path}'. Target IDs: {len(target_ids)}, Exclude: {exclude}"
    )
    _check_output_file(output_path)

    target_ids_lower = {id.lower() for id in target_ids}
    total_size = os.path.getsize(fasta_file)

    # Determine a reasonable number of processes
    num_processes = multiprocessing.cpu_count()
    # Adjust chunk size based on number of processes to balance load vs memory
    # Aim for at least a few chunks per process if possible, but not too many small chunks.
    # This is a heuristic and might need tuning.
    # Let's make chunks reasonably large, e.g., 10-50MB, or ensure at least num_processes chunks.
    # If total_size is very small, chunk_size could become 0 if not handled.
    desired_chunk_size_mb = 32
    chunk_size = max(1, desired_chunk_size_mb * 1024 * 1024)
    num_chunks = max(1, math.ceil(total_size / chunk_size))

    def chunk_reader(
        file_obj, cs: int
    ) -> Iterator[List[str]]:  # Explicitly Iterator[List[str]]
        chunk = []
        chunk_bytes = 0
        for line in file_obj:
            chunk.append(line)
            chunk_bytes += len(line)
            if chunk_bytes >= cs and line.startswith(">"):
                yield chunk
                chunk = [line]
                chunk_bytes = len(line)
        if chunk:
            yield chunk

    mode = "rt"  # text mode for both gzip and regular open

    all_written_ids: Set[str] = set()
    try:
        with open(fasta_file, mode) as input_file:
            logger.info(
                f"SUBSET_FASTA: Using up to {num_processes} worker processes for {num_chunks} potential chunks."
            )

            with multiprocessing.Pool(processes=num_processes) as pool:
                logger.info(
                    f"SUBSET_FASTA: Multiprocessing pool created (intended processes: {num_processes})."
                )

                process_func = partial(
                    process_chunk, target_ids_lower=target_ids_lower, exclude=exclude
                )

                # Using imap_unordered can sometimes be better for memory with many results,
                # as results are processed as they complete.
                # However, for aggregation later, order doesn't strictly matter for building the final set/list of strings.
                # tqdm will work with imap and imap_unordered.

                # Calculate total for tqdm more robustly
                actual_num_chunks_for_tqdm = num_chunks  # Use the calculated num_chunks

                try:
                    from tqdm import tqdm

                    results_buffer = []
                    for result_tuple in tqdm(
                        pool.imap(process_func, chunk_reader(input_file, chunk_size)),
                        total=actual_num_chunks_for_tqdm,  # Use calculated number of chunks
                        desc="Processing FASTA (subset_fasta)",
                    ):
                        results_buffer.append(result_tuple)
                    logger.debug("SUBSET_FASTA: pool.imap completed.")
                except Exception as e_pool:
                    logger.error(
                        f"SUBSET_FASTA: Error during multiprocessing pool.imap: {e_pool}",
                        exc_info=True,
                    )
                    raise

        logger.debug(
            f"SUBSET_FASTA: Aggregating results from {len(results_buffer)} processed chunks."
        )
        with open(output_path, "w") as output_file:
            for output_sequences, written_ids_chunk in results_buffer:
                output_file.writelines(output_sequences)
                all_written_ids.update(written_ids_chunk)
    except Exception as e_main:
        logger.error(
            f"SUBSET_FASTA: Error in main processing logic: {e_main}", exc_info=True
        )
        raise

    logger.info(
        f"SUBSET_FASTA: Wrote {len(all_written_ids)} sequences to {output_path}. Finished."
    )
    return all_written_ids if return_written_ids else None


def load_fasta_as_dict(fasta_file: str) -> Dict[str, "SeqRecord"]:
    """
    Load a FASTA file into a dictionary with record IDs as keys.
    Keep only the first instance of each identifier.

    Args:
        fasta_file (str): Path to the FASTA file.

    Returns:
        Dict[str, SeqRecord]: A dictionary with record IDs as keys and SeqRecord objects as values.
    """
    from Bio import SeqIO
    from Bio.SeqRecord import SeqRecord
    from tqdm import tqdm

    record_dict: Dict[str, SeqRecord] = {}
    estimated_sequences = estimate_sequences(fasta_file)

    with tqdm(total=estimated_sequences, desc="Loading FASTA") as pbar:
        for record in SeqIO.parse(fasta_file, "fasta"):
            if record.id not in record_dict:
                record_dict[record.id] = record
            pbar.update(1)

    return record_dict


def fasta_to_sqlite(fasta_file: str, db_file: str, batch_size: int = 1000) -> None:
    """
    Convert a FASTA file to a SQLite database containing protein IDs and sequences.

    This function performs the following steps:
    1. Creates a new SQLite database with a 'proteins' table.
    2. Estimates the number of sequences in the FASTA file.
    3. Reads the FASTA file and extracts protein IDs and sequences.
    4. Inserts the protein data into the SQLite database in batches.

    Args:
        fasta_file (str): Path to the input FASTA file.
        db_file (str): Path to the output SQLite database file.
        batch_size (int, optional): Number of records to insert in each batch. Defaults to 1000.

    Raises:
        FileNotFoundError: If the input FASTA file doesn't exist.
        sqlite3.Error: If there's an error in database operations.
        FileExistsError: If the output database file already exists.

    Example:
        fasta_to_sqlite("proteins.fasta", "proteins.db")
    """
    from Bio import SeqIO
    from tqdm import tqdm

    _check_output_file(db_file)

    if not os.path.exists(fasta_file):
        raise FileNotFoundError(f"FASTA file not found: {fasta_file}")

    print(f"Starting conversion of {fasta_file} to SQLite database {db_file}")

    # Create the SQLite database and table
    print("Creating SQLite database...")
    with sqlite3.connect(db_file) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS proteins (
                protein_id TEXT PRIMARY KEY,
                sequence TEXT NOT NULL
            )
        """
        )
    print("Database created successfully.")

    # Estimate number of records for progress bar
    estimated_records = estimate_sequences(fasta_file)
    print(f"Estimated number of sequences: {estimated_records}")

    # Insert protein data
    print("Inserting protein data into the database...")
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        batch = []

        for protein_id, sequence in tqdm(
            _protein_generator(Path(fasta_file)),  # Pass as Path object
            total=estimated_records,
            desc="Processing proteins",
        ):
            batch.append((protein_id, sequence))

            if len(batch) >= batch_size:
                cursor.executemany(
                    "INSERT OR IGNORE INTO proteins (protein_id, sequence) VALUES (?, ?)",
                    batch,
                )
                conn.commit()
                batch.clear()

        # Insert any remaining records
        if batch:
            cursor.executemany(
                "INSERT OR IGNORE INTO proteins (protein_id, sequence) VALUES (?, ?)",
                batch,
            )
            conn.commit()

    print(f"Conversion completed. SQLite database saved to {db_file}")


def _protein_generator(
    fasta_path: Path,
) -> Iterator[tuple[str, str]]:  # fasta_path is Path
    """
    Generate protein data from a FASTA file.
    Args:
        fasta_path (Path): Path to the FASTA file.
    Yields:
        tuple[str, str]: A tuple containing protein_id and sequence.
    """
    from Bio import SeqIO

    # Ensure we use 'rt' for text mode reading, especially if gzipped
    open_func = gzip.open if str(fasta_path).endswith(".gz") else open
    mode = "rt"

    with open_func(fasta_path, mode) as handle:
        for record in SeqIO.parse(handle, "fasta"):
            protein_id = record.id.split()[
                0
            ]  # Assumes the first part of the id is the protein_id
            sequence = str(record.seq)
            yield protein_id, sequence


def check_fasta_duplicates(fasta_path: str) -> tuple[set[str], set[str]]:
    """
    Check a FASTA file for duplicate IDs, optimized for very large files.
    Uses a memory-efficient approach and displays progress.

    Args:
        fasta_path: Path to the FASTA file to check.

    Returns:
        A tuple containing:
        - set of duplicate IDs found
        - empty set (for API compatibility)

    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the FASTA file is malformed
    """
    from Bio import SeqIO
    from tqdm import tqdm

    if not os.path.exists(fasta_path):
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    # Get estimated number of sequences for progress bar
    estimated_sequences = estimate_sequences(fasta_path)

    seen_ids: dict[str, int] = {}
    duplicate_ids: set[str] = set()
    processed_sequences = 0

    try:
        with open(fasta_path, "rt") as handle:
            with tqdm(
                total=estimated_sequences, desc="Checking for duplicates"
            ) as pbar:
                for record in SeqIO.parse(handle, "fasta"):
                    if record.id in seen_ids:
                        duplicate_ids.add(record.id)
                        seen_ids[record.id] += 1
                    else:
                        seen_ids[record.id] = 1

                    processed_sequences += 1
                    pbar.update(1)

        # Print summary of findings
        total_ids = len(seen_ids)
        total_duplicates = len(duplicate_ids)
        if total_duplicates > 0:
            print(
                f"\nFound {total_duplicates:,} duplicate IDs out of {total_ids:,} total IDs"
            )
            # Print details for the first few duplicates
            sample_size = min(5, len(duplicate_ids))
            if sample_size > 0:
                print("\nExample duplicates (showing first 5):")
                for dup_id in list(duplicate_ids)[:sample_size]:
                    print(f"  {dup_id}: appears {seen_ids[dup_id]} times")
        else:
            print(f"\nNo duplicates found in {total_ids:,} sequences")

    except ValueError as e:
        raise ValueError(f"Malformed FASTA file: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error parsing FASTA file: {str(e)}")

    return duplicate_ids, set()  # Return empty set for sequences to maintain API


def clean_fasta_duplicates(
    input_path: str, output_path: str
) -> tuple[set[str], set[str]]:
    """Clean duplicate entries from a FASTA file.

    For each duplicate ID found:
    - If all sequences for that ID are identical, keep only the first occurrence
    - If sequences differ, skip that ID and report it as a conflict

    Optimized for very large files by:
    - Using memory-efficient data structures
    - Processing in chunks
    - Using generators where possible

    Args:
        input_path (str): Path to input FASTA file
        output_path (str): Path to write cleaned FASTA file

    Returns:
        tuple[set[str], set[str]]: A tuple containing:
            - set of IDs that were deduplicated (had identical sequences)
            - set of IDs that had sequence conflicts

    Raises:
        FileExistsError: If the output file already exists
        FileNotFoundError: If the input file doesn't exist
    """
    from Bio import SeqIO
    from tqdm import tqdm

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input FASTA file not found: {input_path}")

    _check_output_file(output_path)

    # First pass: collect sequence hashes for each ID
    # Using hashes instead of full sequences saves memory
    id_hashes: dict[str, set[str]] = {}
    id_count: dict[str, int] = {}
    estimated_sequences = estimate_sequences(input_path)

    print("Analyzing sequences...")
    with open(input_path, "rt", buffering=1024 * 1024) as handle:  # 1MB buffer
        for record in tqdm(SeqIO.parse(handle, "fasta"), total=estimated_sequences):
            seq_hash = str(hash(str(record.seq)))  # Hash the sequence
            if record.id not in id_hashes:
                id_hashes[record.id] = {seq_hash}
                id_count[record.id] = 1
            else:
                id_hashes[record.id].add(seq_hash)
                id_count[record.id] += 1

    # Identify duplicates and conflicts
    duplicate_ids = {id for id, count in id_count.items() if count > 1}
    if not duplicate_ids:
        print("No duplicates found. Creating identical copy of input file...")
        # Use shutil.copyfile for efficient file copying
        import shutil

        shutil.copyfile(input_path, output_path)
        return set(), set()

    cleaned_ids = {id for id in duplicate_ids if len(id_hashes[id]) == 1}
    conflict_ids = {id for id in duplicate_ids if len(id_hashes[id]) > 1}

    # Print summary
    if conflict_ids:
        print("\nFound sequence conflicts for these IDs:")
        for id in conflict_ids:
            print(f"  {id}: {len(id_hashes[id])} different sequences")

    if cleaned_ids:
        print(f"\nCleaning {len(cleaned_ids)} IDs with identical duplicates...")

    # Second pass: write cleaned file
    # Use a larger buffer size for better I/O performance
    seen_ids = set()
    with (
        open(input_path, "rt", buffering=1024 * 1024) as infile,
        open(output_path, "wt", buffering=1024 * 1024) as outfile,
    ):
        for record in tqdm(SeqIO.parse(infile, "fasta"), total=estimated_sequences):
            # Skip if we've seen this ID before and it's a duplicate we're cleaning
            if record.id in seen_ids and record.id in cleaned_ids:
                continue
            # Skip if this ID has conflicting sequences
            if record.id in conflict_ids:
                continue
            # Write the record and mark as seen
            SeqIO.write(record, outfile, "fasta")
            seen_ids.add(record.id)

    print(f"\nWrote cleaned FASTA to {output_path}")
    if cleaned_ids:
        print(f"Removed duplicates for {len(cleaned_ids)} IDs")
    if conflict_ids:
        print(f"Skipped {len(conflict_ids)} IDs with sequence conflicts")

    return cleaned_ids, conflict_ids


def fetch_uniprot_fasta(
    accession_set,
    batch_size=100,
    output_file=None,
    show_preview=True,
    simple_headers=True,
):
    """
    Retrieve FASTA sequences for a set of UniProt accession numbers with progress reporting.

    Args:
        accession_set (set): Set of UniProt accession numbers
        batch_size (int): Number of accessions to process per batch
        output_file (str): Path to output FASTA file. If None, will use "uniprot_sequences.fasta"
        show_preview (bool): Whether to show the first few lines of the output file
        simple_headers (bool): If True, replace FASTA headers with just the accession number

    Returns:
        tuple: (success_count, failed_count, output_filepath, failed_accessions)
    """
    from tqdm.notebook import tqdm as tqdm_notebook

    # Convert set to list for batch processing
    accession_list = list(accession_set)

    # Set default output file if not provided
    if output_file is None:
        output_file = "uniprot_sequences.fasta"

    print(f"Starting download of {len(accession_list)} UniProt sequences")
    print(f"Output file: {os.path.abspath(output_file)}")
    print(f"Using {'simple' if simple_headers else 'full'} FASTA headers")

    start_time = time.time()

    # Open the output file
    with open(output_file, "w") as f:
        # Initialize counters
        success_count = 0
        failed_count = 0
        failed_accessions = set()

        # Calculate number of batches for progress bar
        num_batches = math.ceil(len(accession_list) / batch_size)

        # Process accessions in batches with progress bar (using notebook version)
        for i in tqdm_notebook(
            range(0, len(accession_list), batch_size),
            desc="Downloading sequences",
            total=num_batches,
        ):

            batch = accession_list[i : i + batch_size]
            batch_size_actual = len(batch)
            batch_set = set(batch)

            # Construct the query string with OR operators
            accession_query = " OR ".join([f"accession:{acc}" for acc in batch])

            # Define the API endpoint and parameters
            url = "https://rest.uniprot.org/uniprotkb/stream"
            params = {"query": accession_query, "format": "fasta"}

            # Set headers
            headers = {"Accept": "text/fasta"}

            # Make the API request with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(
                        url, params=params, headers=headers, timeout=30
                    )
                    response.raise_for_status()  # Raise exception for 4XX/5XX responses

                    # Check if we got FASTA content
                    if response.text and ">" in response.text:
                        # Process the FASTA content
                        if simple_headers:
                            # Simplify headers to just the accession number
                            fasta_content = []
                            current_accession = None
                            sequence_lines = []

                            for line in response.text.splitlines():
                                if line.startswith(">"):
                                    # If we have collected sequence lines for a previous accession, write them
                                    if current_accession and sequence_lines:
                                        f.write(f">{current_accession}\n")
                                        f.write("\n".join(sequence_lines) + "\n")
                                        sequence_lines = []

                                    # Extract accession from the header line
                                    # UniProt FASTA headers typically follow format: >db|ACCESSION|NAME
                                    parts = line.split("|")
                                    if len(parts) >= 2:
                                        current_accession = parts[1]
                                    else:
                                        # Fallback if header format is unexpected
                                        match = re.search(r">(\S+)", line)
                                        current_accession = (
                                            match.group(1) if match else line[1:]
                                        )
                                else:
                                    # Collect sequence lines
                                    sequence_lines.append(line)

                            # Write the last sequence
                            if current_accession and sequence_lines:
                                f.write(f">{current_accession}\n")
                                f.write("\n".join(sequence_lines) + "\n")
                        else:
                            # Write original FASTA content
                            f.write(response.text)

                        # Count successful retrievals by parsing FASTA headers
                        retrieved_accessions = set()
                        for line in response.text.splitlines():
                            if line.startswith(">"):
                                # Extract accession number from FASTA header line
                                parts = line.split("|")
                                if len(parts) >= 2:
                                    retrieved_accessions.add(parts[1])

                        # Determine which accessions weren't retrieved
                        missing_accessions = batch_set - retrieved_accessions
                        failed_accessions.update(missing_accessions)

                        success_in_batch = len(retrieved_accessions)
                        failed_in_batch = batch_size_actual - success_in_batch

                        if failed_in_batch > 0:
                            print(
                                f"Warning: Batch {i//batch_size + 1} missing {failed_in_batch} sequences"
                            )

                        success_count += success_in_batch
                        failed_count += failed_in_batch
                    else:
                        print(
                            f"Warning: Batch {i//batch_size + 1} returned no valid FASTA data"
                        )
                        failed_count += batch_size_actual
                        failed_accessions.update(batch_set)

                    # Successful request, break the retry loop
                    break

                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        wait_time = 2**attempt  # Exponential backoff
                        print(
                            f"Request failed: {e}. Retrying in {wait_time} seconds..."
                        )
                        time.sleep(wait_time)
                    else:
                        print(
                            f"Failed to retrieve batch {i//batch_size + 1} after {max_retries} attempts: {e}"
                        )
                        failed_count += batch_size_actual
                        failed_accessions.update(batch_set)

            # Brief pause to avoid overloading the server
            time.sleep(0.5)

    # Report results
    elapsed_time = time.time() - start_time
    print(f"\nDownload completed in {elapsed_time:.1f} seconds")
    print(f"Successfully retrieved: {success_count} sequences")
    print(f"Failed to retrieve: {failed_count} sequences")

    # Calculate download rate
    if elapsed_time > 0:
        rate = success_count / elapsed_time
        print(f"Download rate: {rate:.1f} sequences/second")

    # Display first few lines of the FASTA file for verification
    if (
        show_preview
        and os.path.exists(output_file)
        and os.path.getsize(output_file) > 0
    ):
        print("\nFirst 5 lines of the FASTA file:")
        with open(output_file, "r") as f:
            for i, line in enumerate(f):
                if i < 5:
                    print(line.strip())
                else:
                    break

    # Return the set of failed accessions for potential retry
    if failed_count > 0:
        print("\nFailed accessions:")
        # Print only first 10 if there are many
        if len(failed_accessions) > 10:
            print(
                f"{list(failed_accessions)[:10]} ... and {len(failed_accessions)-10} more"
            )
        else:
            print(failed_accessions)

    return success_count, failed_count, os.path.abspath(output_file), failed_accessions
