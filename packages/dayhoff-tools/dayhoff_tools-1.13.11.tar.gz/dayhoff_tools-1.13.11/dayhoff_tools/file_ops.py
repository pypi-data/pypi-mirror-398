import gzip
import inspect
import logging
import os
import re
import shutil
import tarfile
from pathlib import Path
from typing import Any, Set

from tqdm import tqdm

logger = logging.getLogger(__name__)


def compress_gz(input_path: str, output_path: str):
    """Compress the input file using gzip, keep the original."""
    with open(input_path, "rb") as f_in:
        with gzip.open(output_path, "wb") as f_out:
            f_out.writelines(f_in)


def decompress_gz(file_path: str) -> str:
    """
    Decompress a .gz file and return the path to the decompressed file.

    Args:
        file_path (str): Path to the .gz file.

    Returns:
        str: Path to the decompressed file.
    """
    input_path = Path(file_path)
    if input_path.suffix != ".gz":
        raise ValueError(f"File {file_path} does not have a .gz extension")

    output_path = input_path.with_suffix("")  # Remove the .gz suffix

    with gzip.open(input_path, "rb") as f_in:
        with open(output_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    return str(output_path)


def compress_folder_into_tar_gz(folder_path: str) -> str:
    """
    Compress a folder into a tar.gz file of the same name.

    :param folder_path: The path to the folder to compress.
    """
    output_path = folder_path + ".tar.gz"
    with tarfile.open(output_path, "w:gz") as tarf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                tarf.add(file_path, os.path.relpath(file_path, folder_path))

    return output_path


def decompress_tar(compressed_folder: str):
    """Decompress a .tar.gz or .tar.bz2 folder to the same location
    and return the path of the decompressed folder.

    Args:
        compressed_folder (str): Path to a .tar.gz or .tar.bz2 file, which
                itself is a compression of a multi-level folder.

    Returns:
        str: the path to the decompressed folder
    """
    # Get the directory of the compressed file
    directory = os.path.dirname(compressed_folder)

    # Determine the compression type
    if compressed_folder.endswith(".tar.gz"):
        mode = "r:gz"
        decompressed_folder = compressed_folder.replace(".tar.gz", "")
    elif compressed_folder.endswith(".tar.bz2"):
        mode = "r:bz2"
        decompressed_folder = compressed_folder.replace(".tar.bz2", "")
    else:
        raise ValueError(
            "Unsupported compression type. Only .tar.gz and .tar.bz2 are supported."
        )

    # Open the compressed file
    with tarfile.open(compressed_folder, mode) as tar:
        # Check if the decompressed folder already exists
        if os.path.exists(decompressed_folder):
            # Remove the existing decompressed folder
            shutil.rmtree(decompressed_folder)

        # Extract the contents to the decompressed folder
        tar.extractall(path=directory)

        return decompressed_folder


def natural_sort_key(s):
    """
    A sorting key function for natural (human) sorting of strings containing numbers.
    Args:
    s (str): The string to be split into parts for sorting.

    Returns:
    list: A list of strings and integers derived from the input string.
    """
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split("([0-9]+)", s)
    ]


def list_files_in_directory_to_txt(directory_path: str, output_txt_file: str):
    """
    Lists all files in the specified directory in natural sorted order and writes their names to a .txt file.

    Args:
    directory_path (str): Path to the directory whose files should be listed.
    output_txt_file (str): Path to the .txt file where the list of file names will be written.
    """
    # Ensure the directory exists
    if not os.path.isdir(directory_path):
        print(f"The directory {directory_path} does not exist.")
        return

    # Collect all file names in the directory
    file_names = [
        filename
        for filename in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, filename))
    ]

    # Sort the list of file names using the natural sort key
    sorted_file_names = sorted(file_names, key=natural_sort_key)

    # Open the output file in write mode
    with open(output_txt_file, "w") as file_out:
        # Iterate through the sorted list of file names
        for filename in sorted_file_names:
            # Write each file name to the output .txt file
            file_out.write(f"{filename}\n")

    print(f"File names have been written to {output_txt_file}")


def list_files_in_directory(directory_path: str) -> list[str]:
    """
    Make a list of the names for all the files in a specified directory, in natural sorted order.

    Args:
    directory_path (str): Path to the directory whose files should be listed.
    """
    # Collect all file names in the directory
    file_names = [
        filename
        for filename in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, filename))
    ]

    # Sort the list of file names using the natural sort key
    return sorted(file_names, key=natural_sort_key)


def write_set_to_file(set_data: Set[Any], filename: str) -> None:
    """
    Write the contents of a set to a text file, one item per line.

    Args:
        set_data (Set[Any]): The set containing items to write to the file.
        filename (str): The name of the file to create or overwrite.

    Returns:
        None
    """
    with open(filename, "w") as file:
        for item in tqdm(set_data, desc="Writing to file", unit="item"):
            file.write(str(item) + "\n")


def read_file_to_set(filename: str) -> Set[str]:
    """
    Read all lines from a text file and return them as a set.

    Args:
        filename (str): The name of the file to read from.

    Returns:
        Set[str]: A set containing all unique lines from the file.
    """
    result_set = set()
    with open(filename, "r") as file:
        for line in file:
            result_set.add(line.strip())

    print(f"Item count: {len(result_set)}")
    return result_set


def compare_sets(
    set1: set, set2: set, set1_name: str | None = None, set2_name: str | None = None
) -> None:
    """
    Compare two sets and return a string representation of the comparison.

    This function performs set operations to find the intersection and differences
    between the two input sets. It then generates a text-based Venn diagram and
    detailed statistics about the comparison.

    Args:
        set1 (set): The first set to compare.
        set2 (set): The second set to compare.
        set1_name (str, optional): The name of the first set. If None, attempts to extract from variable name.
        set2_name (str, optional): The name of the second set. If None, attempts to extract from variable name.

    Returns:
        str: A string containing the text-based Venn diagram and detailed statistics.

    Example:
        >>> set1 = {1, 2, 3, 4}
        >>> set2 = {3, 4, 5, 6}
        >>> print(compare_sets(set1, set2))
    """
    # Try to extract variable names if not provided
    if set1_name is None or set2_name is None:
        frame = inspect.currentframe().f_back
        local_vars = frame.f_locals
        if set1_name is None:
            set1_name = next(
                (var for var, val in local_vars.items() if val is set1), "Set 1"
            )
        if set2_name is None:
            set2_name = next(
                (var for var, val in local_vars.items() if val is set2), "Set 2"
            )

    # Perform set operations
    in_both = set1.intersection(set2)
    only_in_set1 = set1.difference(set2)
    only_in_set2 = set2.difference(set1)

    # Calculate totals and percentages
    total = len(set1.union(set2))
    in_both_percent = len(in_both) / total * 100
    only_in_set1_percent = len(only_in_set1) / total * 100
    only_in_set2_percent = len(only_in_set2) / total * 100

    # Create the output string
    output = [
        f"Set Comparison: {set1_name} vs {set2_name}",
        "---------------------------------------",
        f"Total unique elements: {total:,}",
        "",
        f"Only in {set1_name}:  {len(only_in_set1):,} ({only_in_set1_percent:.2f}%)",
        f"In both sets:       {len(in_both):,} ({in_both_percent:.2f}%)",
        f"Only in {set2_name}:  {len(only_in_set2):,} ({only_in_set2_percent:.2f}%)",
    ]

    print("\n".join(output))
