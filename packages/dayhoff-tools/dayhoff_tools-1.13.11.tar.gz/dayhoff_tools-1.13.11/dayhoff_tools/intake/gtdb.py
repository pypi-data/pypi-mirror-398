import collections.abc
import csv
import gzip
import pathlib
import re

from tqdm import tqdm

_ACCESSION_REGEX = re.compile(r"(GC[AF]_[0-9]+\.[0-9]+)")


def _extract_accession_from_filename(filename_str: str) -> str:
    """
    Extracts the genome assembly accession (e.g., GCA_XXXXXXXXX.X or GCF_XXXXXXXXX.X)
    from a filename.

    Args:
        filename_str (str): The filename string.

    Returns:
        str: The extracted accession or "UNKNOWN_ACCESSION" if not found.
    """
    match = _ACCESSION_REGEX.search(filename_str)
    if match:
        return match.group(1)
    return "UNKNOWN_ACCESSION"


def process_gtdb_files_to_fasta(
    gtdb_top_folder: str,
    output_fasta_path: str,
    chunk_size: int = 10000,
) -> None:
    """
    Processes a top-level GTDB folder containing gzipped FASTA files (.faa.gz)
    and combines all protein sequences into a single FASTA file.

    Output is written in chunks for efficiency with large datasets.
    A progress bar is displayed during processing.

    Args:
        gtdb_top_folder (str): Path to the top-level GTDB directory.
        output_fasta_path (str): Path to write the combined FASTA file.
        chunk_size (int, optional): Number of sequences to process before
            writing a chunk to the output file. Defaults to 10000.
    """
    gtdb_path = pathlib.Path(gtdb_top_folder)
    faa_files = list(gtdb_path.rglob("*.faa.gz"))

    if not faa_files:
        print(f"No .faa.gz files found in {gtdb_top_folder}")
        return

    fasta_entries_chunk = []
    sequences_in_current_chunk = 0

    with open(output_fasta_path, "w") as fasta_out_file:
        current_header_id = None
        current_sequence_lines = []

        for faa_file_path in tqdm(faa_files, desc="Processing GTDB files to FASTA"):
            try:
                with gzip.open(faa_file_path, "rt") as gz_file:
                    for line_content in gz_file:
                        line = line_content.strip()
                        if not line:  # Skip empty lines
                            continue
                        if line.startswith(">"):
                            if current_header_id and current_sequence_lines:
                                sequence_string = "".join(current_sequence_lines)
                                fasta_entries_chunk.append(
                                    f">{current_header_id}\n{sequence_string}\n"
                                )
                                sequences_in_current_chunk += 1

                            # Parse new header
                            header_content = line[1:]
                            parts = header_content.split(None, 1)
                            current_header_id = parts[0]
                            current_sequence_lines = []

                            if sequences_in_current_chunk >= chunk_size:
                                if fasta_entries_chunk:
                                    fasta_out_file.write("".join(fasta_entries_chunk))
                                fasta_entries_chunk = []
                                sequences_in_current_chunk = 0
                        else:
                            if current_header_id:
                                current_sequence_lines.append(line)

                    if current_header_id and current_sequence_lines:
                        sequence_string = "".join(current_sequence_lines)
                        fasta_entries_chunk.append(
                            f">{current_header_id}\n{sequence_string}\n"
                        )
                        sequences_in_current_chunk += 1

                # Reset state for the next file to ensure clean parsing start for that file
                current_header_id = None
                current_sequence_lines = []

            except gzip.BadGzipFile:
                tqdm.write(
                    f"Warning: Skipping corrupted or non-gzipped file: {faa_file_path}"
                )
                current_header_id = None
                current_sequence_lines = []
            except Exception as e:
                tqdm.write(f"Warning: Error processing file {faa_file_path}: {e}")
                current_header_id = None
                current_sequence_lines = []

        if fasta_entries_chunk:
            fasta_out_file.write("".join(fasta_entries_chunk))

    print(f"Processing complete. Output FASTA file created: {output_fasta_path}")


def process_gtdb_files_to_csv(
    gtdb_top_folder: str,
    output_csv_path: str,
    chunk_size: int = 10000,
) -> None:
    """
    Processes a top-level GTDB folder containing gzipped FASTA files (.faa.gz)
    and creates a CSV file with detailed information for each sequence entry.

    The CSV includes the genome assembly accession, original FASTA header ID,
    and header description for each entry. Output is written in chunks for
    efficiency with large datasets. A progress bar is displayed during processing.

    Args:
        gtdb_top_folder (str): Path to the top-level GTDB directory.
        output_csv_path (str): Path to write the CSV file.
        chunk_size (int, optional): Number of sequences to process before
            writing a chunk to the output file. Defaults to 10000.
    """
    gtdb_path = pathlib.Path(gtdb_top_folder)
    faa_files = list(gtdb_path.rglob("*.faa.gz"))

    if not faa_files:
        print(f"No .faa.gz files found in {gtdb_top_folder}")
        return

    def _serial_iter(paths):
        """Yield the same structure as the parallel branch but serially."""
        for p in paths:
            row_generator_for_file, file_warnings = _csv_rows_from_single_faa(str(p))
            yield row_generator_for_file, file_warnings

    # Open output CSV for streaming writes.
    with open(output_csv_path, "w", newline="") as csv_out_file:
        csv_writer = csv.writer(csv_out_file)
        csv_writer.writerow(
            [
                "genome_assembly_accession",
                "original_fasta_header_id",
                "original_fasta_header_description",
            ]
        )

        rows_buffer: list[list[str]] = []

        # Choose the iterator depending on workers.
        result_iter = _serial_iter(faa_files)
        progress_iter = tqdm(
            result_iter, total=len(faa_files), desc="Processing GTDB files to CSV"
        )

        # Consume iterator and stream rows to disk in chunks.
        for row_generator_for_file, file_warnings in progress_iter:
            # Add rows to buffer and flush in chunk-size batches.
            # This will consume the generator, and in doing so, populate file_warnings if errors occur.
            for r in row_generator_for_file:
                rows_buffer.append(r)
                if len(rows_buffer) >= chunk_size:
                    csv_writer.writerows(rows_buffer)
                    rows_buffer.clear()

            # Now that the generator for the file has been processed (or attempted),
            # emit any warnings that were collected for this specific file.
            for w in file_warnings:
                tqdm.write(w)

        # Flush remaining rows.
        if rows_buffer:
            csv_writer.writerows(rows_buffer)

    print(f"Processing complete. Output CSV file created: {output_csv_path}")


# ---------------------------------------------------------------------------
# Helper functions (private)
# ---------------------------------------------------------------------------


def _csv_rows_from_single_faa(
    faa_file_path: str,
) -> tuple[collections.abc.Iterable[list[str]], list[str]]:
    """Parse a single gzipped FASTA (`.faa.gz`) file into CSV rows.

    Parameters
    ----------
    faa_file_path
        Path (as ``str``) to the ``.faa.gz`` file.

    Returns
    -------
    tuple[collections.abc.Iterable[list[str]], list[str]]
        * First element – an iterable (generator) of CSV rows ``[accession, header_id, description]``.
        * Second element – list of warning strings produced while processing
          the file.  The caller is responsible for emitting them.
    """
    warnings: list[str] = []  # Outer scope warnings list
    faa_path = pathlib.Path(faa_file_path)
    current_file_accession = _extract_accession_from_filename(faa_path.name)

    def _generate_rows_iter_inner() -> (
        collections.abc.Iterable[list[str]]
    ):  # Renamed for clarity
        # Local parsing state for the generator
        current_header_id_gen = None
        current_header_desc_gen = ""
        has_sequence_lines_gen = False

        try:
            with gzip.open(faa_file_path, "rt") as gz_file:
                for line_content in gz_file:
                    line = line_content.strip()
                    if not line:
                        continue
                    if line.startswith(">"):
                        if current_header_id_gen and has_sequence_lines_gen:
                            yield [
                                current_file_accession,
                                current_header_id_gen,
                                current_header_desc_gen,
                            ]

                        header_content = line[1:]
                        parts = header_content.split(None, 1)
                        current_header_id_gen = parts[0]
                        current_header_desc_gen = parts[1] if len(parts) > 1 else ""
                        has_sequence_lines_gen = False
                    else:
                        if current_header_id_gen:
                            has_sequence_lines_gen = True

            # Add final entry if the file ended after sequence lines.
            if current_header_id_gen and has_sequence_lines_gen:
                yield [
                    current_file_accession,
                    current_header_id_gen,
                    current_header_desc_gen,
                ]
        except gzip.BadGzipFile:
            # Exception handled inside the generator.
            # Append to the outer warnings list and terminate generator.
            warnings.append(
                f"Warning: Skipping corrupted or non-gzipped file: {faa_file_path}"
            )
            return  # Stop generation
        except Exception as exc:
            warnings.append(f"Warning: Error processing file {faa_file_path}: {exc}")
            return  # Stop generation

    # Directly return the generator instance and the warnings list.
    # The warnings list will be populated by the generator if errors occur during its execution.
    return _generate_rows_iter_inner(), warnings
