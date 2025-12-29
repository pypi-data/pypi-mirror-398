import gzip
import io
import multiprocessing
import os
import re
from dataclasses import dataclass
from functools import partial
from typing import Iterator

import h5py
import numpy as np
from Bio import PDB, SeqIO
from tqdm import tqdm


@dataclass
class PDBData:
    """Stores parsed PDB file data."""

    atom_coords: np.ndarray
    uncertainty: np.ndarray
    id: str
    aa_sequence: str

    @property
    def atom_count(self) -> int:
        return len(self.atom_coords)


class PDBParser:
    """Parses PDB files and extracts relevant information."""

    def __init__(self):
        self.parser = PDB.PDBParser(QUIET=True)  # type: ignore

    def parse(self, pdb_file: str, backbone_only: bool = False) -> PDBData:
        """
        Parse a PDB file and extract data for a single-chain protein.

        Args:
            pdb_file: Path to the PDB file.
            backbone_only: If True, only extract coordinates for alpha carbons (CA).

        Returns:
            PDBData containing parsed PDB data.

        Raises:
            ValueError: If the PDB file is invalid or doesn't meet criteria.
        """
        with self._open_pdb_file(pdb_file) as file:
            try:
                structure = self.parser.get_structure("protein", file)
                model = next(structure.get_models())  # type: ignore
            except StopIteration:
                raise ValueError("Invalid PDB file: No models found.")

        chains = list(model.get_chains())

        if len(chains) != 1:
            raise ValueError(
                f"Expected a single chain, but found {len(chains)} chains."
            )

        chain = chains[0]

        atom_coords, uncertainty = self._extract_coords_and_uncertainty(
            chain, backbone_only
        )

        id = self._extract_id(pdb_file)
        aa_sequence = self._extract_aa_sequence(pdb_file)

        return PDBData(
            atom_coords=atom_coords,
            uncertainty=uncertainty,
            id=id,
            aa_sequence=aa_sequence,
        )

    def _extract_coords_and_uncertainty(
        self, chain: PDB.Chain.Chain, backbone_only: bool = False
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Extract atom coordinates and uncertainty values from a chain.

        Args:
            chain: A Bio.PDB.Chain object.
            backbone_only: If True, only extract coordinates for alpha carbons (CA).

        Returns:
            A tuple containing two NumPy arrays:
            - atom_coords: Array of atom coordinates with shape (n_atoms, 3).
            - uncertainty: Array of uncertainty values (B-factors) with shape (n_atoms,).
        """
        atoms = self._get_atoms(chain, backbone_only)

        atom_coords = []
        uncertainty = []
        for atom in atoms:
            atom_coords.append(atom.coord)
            uncertainty.append(atom.bfactor if atom.bfactor is not None else 0.0)

        return np.array(atom_coords), np.array(uncertainty)

    @staticmethod
    def _get_atoms(
        chain: PDB.Chain.Chain, backbone_only: bool
    ) -> Iterator[PDB.Atom.Atom]:
        """Get atoms from the chain based on the backbone_only flag."""
        if backbone_only:
            return (residue["CA"] for residue in chain if "CA" in residue)
        return (atom for residue in chain for atom in residue)

    def _extract_id(self, file_path: str) -> str:
        """
        Extract UniProt ID from PDB file TITLE lines.

        Args:
            file_path: Path to the PDB file.

        Returns:
            UniProt ID extracted from the PDB file.

        Raises:
            ValueError: If UniProt ID is not found.
        """
        with self._open_pdb_file(file_path) as file:
            title = ""
            for line in file:
                if line.startswith("TITLE"):  # type: ignore
                    title += line[10:].strip()  # type: ignore
                elif not line.startswith("TITLE") and title:  # type: ignore
                    break

        match = re.search(r"\(([A-Z0-9]+)\)$", title)
        if match:
            return match.group(1)
        raise ValueError("UniProt ID not found in the PDB file.")

    def _extract_aa_sequence(self, file_path: str) -> str:
        """
        Extract amino acid sequence from PDB file SEQRES records.

        Args:
            file_path: Path to the PDB file.

        Returns:
            Amino acid sequence extracted from the PDB file.

        Raises:
            ValueError: If sequence is not found.
        """
        with self._open_pdb_file(file_path) as file:
            for record in SeqIO.parse(file, "pdb-seqres"):
                return str(record.seq)
        raise ValueError("Amino acid sequence not found in the PDB file.")

    @staticmethod
    def _open_pdb_file(file_path: str) -> io.TextIOWrapper | gzip.GzipFile:
        """
        Open a PDB file, handling both .pdb and .pdb.gz formats.

        Args:
            file_path: Path to the PDB file.

        Returns:
            File-like object containing the PDB data.
        """
        if file_path.endswith(".gz"):
            return gzip.open(file_path, "rt")  # type: ignore
        return open(file_path, "r")


class HDF5Writer:
    """Writes protein data to an HDF5 file."""

    def __init__(self, output_file: str, total_proteins: int):
        """
        Initialize the HDF5Writer.

        Args:
            output_file: Path to the output HDF5 file.
            total_proteins: Total number of proteins to be processed.
        """
        self.output_file = output_file
        self.total_proteins = total_proteins
        self.file = None

    def create_datasets(self):
        """
        Create resizable datasets in the HDF5 file.

        Creates the following datasets:
        - ids: UniProt IDs of the proteins (string)
        - aa_sequences: Amino acid sequences of the proteins (string)
        - atom_counts: Number of atoms in each protein (integer)
        - prot_start_idx: Starting index of each protein's atoms in the atom_coords and uncertainty datasets (integer)
        - atom_coords: 3D coordinates of atoms for all proteins (float)
        - uncertainty: B-factors or uncertainty values for each atom (float)
        """
        compression = "gzip"
        compression_opts = 4  # Compression level (1-9)
        chunk_size = min(1000, self.total_proteins)

        self._create_string_dataset("ids", chunk_size, compression, compression_opts)
        self._create_string_dataset(
            "aa_sequences", chunk_size, compression, compression_opts
        )
        self._create_int_dataset(
            "atom_counts", chunk_size, compression, compression_opts
        )
        self._create_int_dataset(
            "prot_start_idx", chunk_size, compression, compression_opts
        )
        self._create_float_dataset(
            "atom_coords", (1000, 3), compression, compression_opts
        )
        self._create_float_dataset(
            "uncertainty", (1000,), compression, compression_opts
        )

    def _create_string_dataset(
        self, name: str, chunk_size: int, compression: str, compression_opts: int
    ):
        self.file.create_dataset(
            name,
            (0,),
            maxshape=(None,),
            dtype=h5py.string_dtype(encoding="utf-8"),
            chunks=(chunk_size,),
            compression=compression,
            compression_opts=compression_opts,
        )

    def _create_int_dataset(
        self, name: str, chunk_size: int, compression: str, compression_opts: int
    ):
        self.file.create_dataset(
            name,
            (0,),
            maxshape=(None,),
            dtype=int,
            chunks=(chunk_size,),
            compression=compression,
            compression_opts=compression_opts,
        )

    def _create_float_dataset(
        self, name: str, chunk: tuple, compression: str, compression_opts: int
    ):
        self.file.create_dataset(
            name,
            (0, *chunk[1:]),
            maxshape=(None, *chunk[1:]),
            dtype=float,
            chunks=chunk,
            compression=compression,
            compression_opts=compression_opts,
        )

    def update_datasets(self, start_idx: int, end_idx: int, data: list[PDBData]):
        """
        Update datasets in the HDF5 file with new data, resizing as necessary.

        Args:
            start_idx: Starting index for updating the datasets.
            end_idx: Ending index for updating the datasets.
            data: List of PDBData objects containing the new data to be added.

        This method updates all datasets, including prot_start_idx, which stores
        the starting index of each protein's atoms in the atom_coords and uncertainty datasets.
        """
        if not data:
            raise ValueError("No data provided to update_datasets")

        if any(pdb is None for pdb in data):
            raise ValueError("Invalid data: None values are not allowed")

        current_size = self.file["ids"].shape[0]
        new_size = max(current_size, end_idx)

        # Resize datasets if necessary
        if new_size > current_size:
            self.file["ids"].resize((new_size,))
            self.file["aa_sequences"].resize((new_size,))
            self.file["atom_counts"].resize((new_size,))
            self.file["prot_start_idx"].resize((new_size,))

        # Update datasets
        self.file["ids"][start_idx:end_idx] = [pdb.id for pdb in data]
        self.file["aa_sequences"][start_idx:end_idx] = [pdb.aa_sequence for pdb in data]

        atom_counts = [pdb.atom_count for pdb in data]
        self.file["atom_counts"][start_idx:end_idx] = atom_counts

        # Update prot_start_idx
        if start_idx == 0:
            self.file["prot_start_idx"][0] = 0
        else:
            previous_start = self.file["prot_start_idx"][start_idx - 1]
            previous_count = self.file["atom_counts"][start_idx - 1]
            self.file["prot_start_idx"][start_idx] = previous_start + previous_count

        cumulative_counts = np.cumsum([0] + atom_counts[:-1])
        self.file["prot_start_idx"][start_idx + 1 : end_idx] = (
            self.file["prot_start_idx"][start_idx] + cumulative_counts[1:]
        )

        # Calculate total atoms for the current chunk
        total_atoms = sum(atom_counts)

        # Resize atom_coords and uncertainty datasets
        current_atoms = self.file["atom_coords"].shape[0]
        new_atoms = current_atoms + total_atoms
        self.file["atom_coords"].resize((new_atoms, 3))
        self.file["uncertainty"].resize((new_atoms,))

        # Update atom_coords and uncertainty datasets
        atom_index = current_atoms
        for pdb in data:
            self.file["atom_coords"][
                atom_index : atom_index + pdb.atom_count
            ] = pdb.atom_coords
            self.file["uncertainty"][
                atom_index : atom_index + pdb.atom_count
            ] = pdb.uncertainty
            atom_index += pdb.atom_count

    def __enter__(self):
        self.file = h5py.File(self.output_file, "w")
        self.create_datasets()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()


class PDBFolderProcessor:
    """Processes multiple PDB files and writes data to an HDF5 file."""

    def __init__(
        self,
        pdb_dir: str,
        output_file: str,
        chunk_size: int = 1000,
        id_set: set[str] | None = None,
        backbone_only: bool = False,
    ):
        """
        Initialize the PDBFolderProcessor.

        Args:
            pdb_dir: Path to the directory containing PDB files.
            output_file: Path to the output HDF5 file.
            chunk_size: Number of PDB files to process in each chunk.
            id_set: Optional set of IDs to filter PDB files.
            backbone_only: If True, only extract coordinates for alpha carbons (CA).
        """
        self.pdb_dir = pdb_dir
        self.output_file = output_file
        self.chunk_size = chunk_size
        self.parser = PDBParser()
        self.id_set = id_set
        self.backbone_only = backbone_only

    def process(self):
        """
        Process PDB files and write data to HDF5 file.
        """
        print(f"Starting to process PDB files from {self.pdb_dir}")
        pdb_files = self._get_pdb_files()
        total_proteins = len(pdb_files)
        print(f"Found {total_proteins} PDB files to process")

        with HDF5Writer(self.output_file, total_proteins) as writer:
            with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
                process_single_pdb_partial = partial(self._process_single_pdb)
                processed_proteins = 0
                for start_idx in tqdm(
                    range(0, total_proteins, self.chunk_size),
                    desc="Processing PDB files",
                    unit="chunk",
                ):
                    end_idx = min(start_idx + self.chunk_size, total_proteins)
                    chunk = pdb_files[start_idx:end_idx]

                    print(f"\nProcessing chunk {start_idx // self.chunk_size + 1}")
                    data = pool.map(process_single_pdb_partial, chunk)
                    valid_data = [item for item in data if item is not None]

                    if valid_data:
                        writer.update_datasets(
                            processed_proteins,
                            processed_proteins + len(valid_data),
                            valid_data,
                        )
                        processed_proteins += len(valid_data)

                    print(
                        f"Processed {processed_proteins} valid proteins out of {end_idx} total files"
                    )

        print(
            f"\nFinished processing all PDB files. Output saved to {self.output_file}"
        )
        print(f"Total valid proteins processed: {processed_proteins}")

    def _get_pdb_files(self) -> list[str]:
        """
        Get a list of PDB files in the specified directory, optionally filtered by ID set.
        Files are sorted by creation time to ensure consistent processing order.

        Returns:
            List of PDB file names sorted by creation time.
        """
        print("Scanning directory for PDB files...")
        pdb_files = [
            f for f in os.listdir(self.pdb_dir) if f.endswith((".pdb", ".pdb.gz"))
        ]

        if self.id_set:
            pdb_files = [
                f for f in pdb_files if self._extract_id_from_filename(f) in self.id_set
            ]

        # Sort files by creation time
        pdb_files.sort(key=lambda f: os.path.getctime(os.path.join(self.pdb_dir, f)))

        print(f"Found {len(pdb_files)} PDB files")
        return pdb_files

    @staticmethod
    def _extract_id_from_filename(filename: str) -> str:
        """
        Extract the ID from a PDB filename.

        Args:
            filename: The filename of the PDB file (e.g., "AF-A3DBM5-F1-model_v4.pdb.gz").

        Returns:
            The extracted ID (e.g., "A3DBM5").

        Raises:
            ValueError: If the filename doesn't match the expected format.
        """
        match = re.match(r"AF-([A-Z0-9]+)-F", filename)
        if match:
            return match.group(1)
        raise ValueError(f"Invalid filename format: {filename}")

    def _process_single_pdb(self, pdb_file: str) -> PDBData | None:
        """
        Process a single PDB file.

        Args:
            pdb_file: PDB file name to process.

        Returns:
            PDBData object containing parsed PDB data, or None if processing fails.
        """
        try:
            file_path = os.path.join(self.pdb_dir, pdb_file)
            parsed_data = self.parser.parse(file_path, backbone_only=self.backbone_only)
            return parsed_data
        except Exception as e:
            return None


def parse_pdb_folder_to_h5(
    pdb_dir: str,
    output_file: str,
    chunk_size: int = 1000,
    id_set: set[str] | None = None,
    backbone_only: bool = False,
):
    """
    Create an HDF5 file containing data from multiple PDB files.

    This function processes a folder of PDB files and stores their structural
    information in an efficient HDF5 format. The resulting file is optimized
    for fast access by machine learning dataloaders.

    Args:
        pdb_dir: Path to the directory containing PDB files.
        output_file: Path to the output HDF5 file.
        chunk_size: Number of PDB files to process in each chunk.
        id_set: Optional set of IDs to filter PDB files.
        backbone_only: If True, only extract coordinates for alpha carbons (CA).

    H5 File Structure:
    The output HDF5 file contains the following datasets:
    - ids: UniProt IDs of the proteins (string) [n_proteins]
    - aa_sequences: Amino acid sequences of the proteins (string) [n_proteins]
    - atom_counts: Number of atoms in each protein (integer) [n_proteins]
    - prot_start_idx: Starting index of each protein's atoms (integer) [n_proteins]
    - atom_coords: 3D coordinates of atoms for all proteins (float) [total_atoms, 3]
    - uncertainty: B-factors or uncertainty values for each atom (float) [total_atoms]

    Benefits for ML Dataloaders:
    1. Efficient Storage: Atom coordinates are stored sequentially in a single
       contiguous array, allowing for efficient disk I/O and memory usage.
    2. Fast Retrieval: Using atom_counts and prot_start_idx, dataloaders
       can quickly locate and extract coordinates for specific proteins without
       loading the entire dataset.
    3. Vectorized Operations: The sequential storage of atom coordinates enables
       efficient vectorized operations on entire proteins or batches of proteins.
    4. Memory Mapping: The contiguous storage allows for easy memory mapping,
       enabling access to large datasets without loading them entirely into RAM.
    5. Batch Processing: Dataloaders can efficiently create batches of proteins
       with varying numbers of atoms, using the atom count information to slice
       the coordinate array.

    Retrieving Atom Coordinates:
    To get the atom coordinates for the i-th protein:
    1. start_idx = prot_start_idx[i]
    2. end_idx = start_idx + atom_counts[i]
    3. coords = atom_coords[start_idx:end_idx]

    This approach allows for quick access to protein data without loading or
    processing unnecessary information, making it ideal for ML tasks involving
    protein structural data, such as structure prediction or function analysis.
    """
    print(f"Starting PDB folder processing")
    print(f"Input directory: {pdb_dir}")
    print(f"Output file: {output_file}")
    print(f"Chunk size: {chunk_size}")
    print(f"Backbone only: {backbone_only}")
    if id_set:
        print(f"Filtering PDB files using {len(id_set)} provided IDs")

    processor = PDBFolderProcessor(
        pdb_dir, output_file, chunk_size, id_set, backbone_only
    )
    processor.process()

    print("PDB folder processing completed successfully")


def filter_structural_h5(
    input_file: str, output_file: str, id_set: set[str], chunk_size: int = 1000000
) -> set[str]:
    """
    WARNING: This function takes forever on files of just 3gb or so.  Problem unclear.
    I'll leave it here because it works on small data, so it's a good starting point for future work.

    Filter an H5 file generated by parse_pdb_folder_to_h5 to include only specified IDs.

    Args:
        input_file: Path to the input H5 file.
        output_file: Path to the output H5 file.
        id_set: Set of IDs to include in the output file.
        chunk_size: Number of atoms to process in each chunk.

    Returns:
        Set of IDs that were not found in the input file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        FileExistsError: If the output file already exists.
        ValueError: If the input file is missing required datasets or contains unexpected datasets.
        OSError: If there's an error reading from or writing to the H5 files.

    Note:
        The function expects the input H5 file to have the following datasets:
        - ids
        - aa_sequences
        - atom_counts
        - prot_start_idx
        - atom_coords
        - uncertainty

        If any of these datasets are missing or if there are additional unexpected
        datasets, a ValueError will be raised.

    The output file will have the same structure as the input file, but only
    containing data for the specified IDs. The prot_start_idx dataset will be
    recalculated to reflect the new positions of proteins in the filtered file.
    """
    print(f"\nStarting H5 filtering process:")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Number of IDs to filter: {len(id_set)}")
    print(f"Chunk size: {chunk_size} atoms")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if os.path.exists(output_file):
        raise FileExistsError(f"Output file already exists: {output_file}")

    expected_datasets = [
        "ids",
        "aa_sequences",
        "atom_counts",
        "prot_start_idx",
        "atom_coords",
        "uncertainty",
    ]

    with h5py.File(input_file, "r") as input_h5:
        # Validate datasets
        missing_datasets = set(expected_datasets) - set(input_h5.keys())
        if missing_datasets:
            raise ValueError(
                f"Missing required datasets: {', '.join(missing_datasets)}"
            )

        unexpected_datasets = set(input_h5.keys()) - set(expected_datasets)
        if unexpected_datasets:
            raise ValueError(
                f"Unexpected datasets found: {', '.join(unexpected_datasets)}"
            )

        # Find matching indices
        ids = input_h5["ids"][:]
        id_list = [id.decode() for id in ids]
        indices = [i for i, id in enumerate(id_list) if id in id_set]

        if not indices:
            return id_set

        print(f"Found {len(indices)} matching IDs")

        with h5py.File(output_file, "w") as output_h5:
            # Copy basic datasets
            output_h5.create_dataset("ids", data=input_h5["ids"][indices])
            output_h5.create_dataset(
                "aa_sequences", data=input_h5["aa_sequences"][indices]
            )
            output_h5.create_dataset(
                "atom_counts", data=input_h5["atom_counts"][indices]
            )

            # Calculate new prot_start_idx
            atom_counts = input_h5["atom_counts"][indices]
            prot_start_idx = np.zeros(len(indices), dtype=int)
            np.cumsum(atom_counts[:-1], out=prot_start_idx[1:])
            output_h5.create_dataset("prot_start_idx", data=prot_start_idx)

            # Create output datasets for coordinates and uncertainty
            total_atoms = prot_start_idx[-1] + atom_counts[-1]
            output_h5.create_dataset("atom_coords", shape=(total_atoms, 3), dtype=float)
            output_h5.create_dataset("uncertainty", shape=(total_atoms,), dtype=float)

            # Copy atom data in chunks
            output_idx = 0
            for i, protein_idx in enumerate(tqdm(indices, desc="Filtering proteins")):
                start_idx = input_h5["prot_start_idx"][protein_idx]
                n_atoms = atom_counts[i]
                end_idx = start_idx + n_atoms

                # Process this protein's atoms in chunks if needed
                for chunk_start in range(start_idx, end_idx, chunk_size):
                    chunk_end = min(chunk_start + chunk_size, end_idx)
                    chunk_size_actual = chunk_end - chunk_start

                    output_h5["atom_coords"][
                        output_idx : output_idx + chunk_size_actual
                    ] = input_h5["atom_coords"][chunk_start:chunk_end]
                    output_h5["uncertainty"][
                        output_idx : output_idx + chunk_size_actual
                    ] = input_h5["uncertainty"][chunk_start:chunk_end]

                    output_idx += chunk_size_actual

    not_found = id_set - set(id_list)
    return not_found


def update_cumulative_to_start_idx(input_file: str, output_file: str):
    """
    Update an H5 file that uses cumulative_atom_counts to use prot_start_idx instead.

    This function reads the existing cumulative_atom_counts dataset, calculates the
    corresponding prot_start_idx, and writes a new H5 file with the updated structure.

    Args:
        input_file: Path to the input H5 file with cumulative_atom_counts.
        output_file: Path to the output H5 file that will use prot_start_idx.

    Raises:
        FileNotFoundError: If the input file does not exist.
        FileExistsError: If the output file already exists.
        ValueError: If the input file is missing required datasets or contains unexpected datasets.
        OSError: If there's an error reading from or writing to the H5 files.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if os.path.exists(output_file):
        raise FileExistsError(f"Output file already exists: {output_file}")

    expected_datasets = [
        "ids",
        "aa_sequences",
        "atom_counts",
        "cumulative_atom_counts",
        "atom_coords",
        "uncertainty",
    ]

    with (
        h5py.File(input_file, "r") as input_h5,
        h5py.File(output_file, "w") as output_h5,
    ):
        # Check if the input file has the expected structure
        missing_datasets = set(expected_datasets) - set(input_h5.keys())
        if missing_datasets:
            raise ValueError(
                f"Missing required datasets: {', '.join(missing_datasets)}"
            )

        unexpected_datasets = set(input_h5.keys()) - set(expected_datasets)
        if unexpected_datasets:
            raise ValueError(
                f"Unexpected datasets found: {', '.join(unexpected_datasets)}"
            )

        # Copy datasets with original compression and chunking if available
        for dataset in [
            "ids",
            "aa_sequences",
            "atom_counts",
            "atom_coords",
            "uncertainty",
        ]:
            input_dataset = input_h5[dataset]
            kwargs = {}
            if input_dataset.compression is not None:
                kwargs["compression"] = input_dataset.compression
                kwargs["compression_opts"] = input_dataset.compression_opts
            if input_dataset.chunks is not None:
                kwargs["chunks"] = input_dataset.chunks
            output_h5.create_dataset(dataset, data=input_dataset, **kwargs)

        # Calculate prot_start_idx from cumulative_atom_counts
        cumulative_atom_counts = input_h5["cumulative_atom_counts"][:]
        prot_start_idx = cumulative_atom_counts[:-1]

        # Create prot_start_idx dataset with compression and chunking similar to cumulative_atom_counts
        cumulative_dataset = input_h5["cumulative_atom_counts"]
        kwargs = {}
        if cumulative_dataset.compression is not None:
            kwargs["compression"] = cumulative_dataset.compression
            kwargs["compression_opts"] = cumulative_dataset.compression_opts
        if cumulative_dataset.chunks is not None:
            kwargs["chunks"] = cumulative_dataset.chunks
        output_h5.create_dataset("prot_start_idx", data=prot_start_idx, **kwargs)

    print(f"Updated H5 file saved to {output_file}")
