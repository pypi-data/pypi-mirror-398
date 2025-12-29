import json
import logging
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class Processor(ABC):
    """Processes data locally.  Abstract class for specific calculations.
    Takes in a single file and produces a single file or folder of outputs."""

    @abstractmethod
    def run(self, input_file: str) -> str:
        """Do the calculation, including reading from input_file
        and writing to output_file"""
        output_path = "output_file"

        return output_path


class InterProScanProcessor(Processor):
    """Processes a single FASTA file using InterProScan and extracts target domains.

    This processor handles the analysis of protein sequences using InterProScan,
    and extracts specific domains based on their InterPro accession IDs.
    It maps sequence identifiers correctly using MD5 hashes from the TSV output
    to handle differences in sequence ID representation between input FASTA and
    InterProScan JSON output.
    """

    def __init__(
        self,
        interproscan_install_dir: str,  # Path to the InterProScan installation
        interproscan_temp_dir_mount: str,  # Path to temporary directory for InterProScan
        num_threads: int,  # Number of CPU threads for InterProScan to use
        output_formats: list[
            str
        ],  # List of desired output formats (e.g., ["JSON", "TSV"])
        target_iprs: set[str],  # Set of InterPro IDs to extract domains for
        other_interproscan_options: (
            str | None
        ) = None,  # Additional command-line options
    ):
        """Initialize the InterProScanProcessor.

        Args:
            interproscan_install_dir: Path to the InterProScan installation directory.
            interproscan_temp_dir_mount: Path to the temporary directory for InterProScan.
            num_threads: Number of CPU threads for InterProScan to use.
            output_formats: List of desired output formats (e.g., ["JSON", "TSV"]).
            target_iprs: A set of InterPro accession IDs to extract domain sequences for.
            other_interproscan_options: Additional command-line options for interproscan.sh.
        """
        self.interproscan_sh_path = Path(interproscan_install_dir) / "interproscan.sh"
        if not self.interproscan_sh_path.is_file():
            raise FileNotFoundError(
                f"interproscan.sh not found at {self.interproscan_sh_path}"
            )

        self.interproscan_temp_dir_mount = Path(interproscan_temp_dir_mount)
        # Ensure the temp directory exists
        self.interproscan_temp_dir_mount.mkdir(parents=True, exist_ok=True)

        self.num_threads = num_threads
        self.output_formats = output_formats

        # Ensure both JSON and TSV formats are included for domain extraction
        if "JSON" not in self.output_formats:
            self.output_formats.append("JSON")
        if "TSV" not in self.output_formats:
            self.output_formats.append("TSV")

        self.target_iprs = target_iprs
        self.other_options = (
            other_interproscan_options if other_interproscan_options else ""
        )

        logger.info(
            f"InterProScanProcessor initialized with script: {self.interproscan_sh_path}"
        )
        logger.info(
            f"Temp dir mount for InterProScan: {self.interproscan_temp_dir_mount}"
        )
        logger.info(f"Target IPRs: {self.target_iprs}")

    def run(self, input_file: str) -> str:
        """Run InterProScan on the input FASTA file and extract domain sequences.

        This method processes a FASTA file through InterProScan, extracts domains
        of interest based on the target_iprs list, and writes the extracted domains
        to a separate FASTA file. Domain sequences are correctly mapped using MD5 hashes
        from the TSV output to handle differences in sequence ID representation.

        Args:
            input_file: Path to the input FASTA file.

        Returns:
            Path to the output directory containing extracted domain sequences and raw results.
        """
        from Bio import SeqIO
        from Bio.Seq import Seq

        input_file_path = Path(input_file).resolve()
        input_file_stem = input_file_path.stem

        # Create output directory structure
        chunk_output_dir = Path(f"results_{input_file_stem}").resolve()
        chunk_output_dir.mkdir(parents=True, exist_ok=True)

        raw_ipr_output_dir = chunk_output_dir / "raw_ipr_output"
        raw_ipr_output_dir.mkdir(parents=True, exist_ok=True)

        # --- Clean input FASTA file to remove stop codons ---
        cleaned_input_file_path = (
            raw_ipr_output_dir / f"{input_file_stem}_cleaned.fasta"
        )
        logger.info(
            f"Cleaning input FASTA file: {input_file_path} to remove '*' characters."
        )
        cleaned_records = []
        has_asterisks = False

        for record in SeqIO.parse(input_file_path, "fasta"):
            original_seq_str = str(record.seq)
            if "*" in original_seq_str:
                has_asterisks = True
                cleaned_seq_str = original_seq_str.replace("*", "")
                record.seq = Seq(cleaned_seq_str)
                logger.debug(f"Removed '*' from sequence {record.id}")
            cleaned_records.append(record)

        if has_asterisks:
            SeqIO.write(cleaned_records, cleaned_input_file_path, "fasta")
            logger.info(f"Cleaned FASTA written to {cleaned_input_file_path}")
            ipr_input_file_to_use = cleaned_input_file_path
        else:
            logger.info(
                f"No '*' characters found in {input_file_path}. Using original."
            )
            ipr_input_file_to_use = input_file_path
        # --- End of cleaning ---

        # Set up InterProScan output base path
        ipr_output_base = raw_ipr_output_dir / input_file_stem

        # Build the InterProScan command
        cmd = [
            str(self.interproscan_sh_path),
            "-i",
            str(ipr_input_file_to_use),
            "-b",
            str(ipr_output_base),
            "-f",
            ",".join(self.output_formats),
            "--cpu",
            str(self.num_threads),
            "--tempdir",
            str(self.interproscan_temp_dir_mount),
            "--disable-precalc",
        ]

        # Add additional options if provided
        if self.other_options:
            cmd.extend(self.other_options.split())

        # Run InterProScan
        logger.info(f"Running InterProScan command: {' '.join(cmd)}")
        try:
            process = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"InterProScan STDOUT: {process.stdout}")
            if process.stderr:
                logger.info(f"InterProScan STDERR: {process.stderr}")
        except subprocess.CalledProcessError as e:
            logger.error(f"InterProScan failed for {input_file_path}")
            logger.error(f"Return code: {e.returncode}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            # Create a failure marker file
            Path(chunk_output_dir / "INTERPROSCAN_FAILED.txt").touch()
            return str(chunk_output_dir)

        # Define paths for output files
        extracted_domains_fasta_path = (
            chunk_output_dir / f"{input_file_stem}_extracted_domains.fasta"
        )
        json_output_path = ipr_output_base.with_suffix(".json")
        tsv_output_path = ipr_output_base.with_suffix(".tsv")

        # Check for required output formats
        if "JSON" not in self.output_formats or not json_output_path.is_file():
            logger.warning(
                f"JSON output format not requested or file not found: {json_output_path}. Cannot extract domains."
            )
            return str(chunk_output_dir)

        if "TSV" not in self.output_formats or not tsv_output_path.is_file():
            logger.warning(
                f"TSV output format not found: {tsv_output_path}. This is needed to map sequence IDs."
            )
            return str(chunk_output_dir)

        # Extract domains using the JSON and TSV outputs
        try:
            # Create MD5 to sequence ID mapping from TSV
            md5_to_id = {}
            with open(tsv_output_path, "r") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) >= 3:  # Ensure there are enough columns
                        seq_id = parts[0]
                        md5 = parts[1]
                        md5_to_id[md5] = seq_id

            logger.debug(f"Created MD5 to ID mapping with {len(md5_to_id)} entries")

            # Load protein sequences for coordinate mapping
            protein_sequences = SeqIO.to_dict(
                SeqIO.parse(ipr_input_file_to_use, "fasta")
            )

            # Process JSON for domain extraction
            extracted_count = 0
            with (
                open(extracted_domains_fasta_path, "w") as f_out,
                open(json_output_path, "r") as f_json,
            ):
                data = json.load(f_json)
                if "results" not in data:
                    logger.info(f"No 'results' key in JSON output {json_output_path}")
                    return str(chunk_output_dir)

                for result in data.get("results", []):
                    # Map sequence via MD5 hash
                    md5 = result.get("md5")
                    if not md5 or md5 not in md5_to_id:
                        logger.debug(f"MD5 hash not found in mapping: {md5}")
                        continue

                    protein_acc = md5_to_id[md5]
                    if protein_acc not in protein_sequences:
                        logger.debug(f"Sequence ID not found in FASTA: {protein_acc}")
                        continue

                    original_seq_record = protein_sequences[protein_acc]
                    for match in result.get("matches", []):
                        # Extract the InterPro domain entry
                        signature = match.get("signature", {})
                        entry = signature.get("entry")
                        if not entry or entry.get("accession") not in self.target_iprs:
                            continue

                        ipr_id = entry.get("accession")
                        ipr_desc = entry.get("description", "N/A").replace(" ", "_")
                        logger.info(
                            f"Found target domain {ipr_id} ({ipr_desc}) in sequence {protein_acc}"
                        )

                        for location in match.get("locations", []):
                            start = location.get("start")
                            end = location.get("end")
                            if start is not None and end is not None:
                                domain_seq_str = str(
                                    original_seq_record.seq[start - 1 : end]
                                )
                                domain_fasta_header = f">{original_seq_record.id}|{ipr_id}|{start}-{end}|{ipr_desc}"
                                f_out.write(f"{domain_fasta_header}\n")
                                f_out.write(f"{domain_seq_str}\n")
                                extracted_count += 1
                                logger.debug(
                                    f"Extracted domain {ipr_id} ({start}-{end}) from {protein_acc}"
                                )

            logger.info(
                f"Extracted {extracted_count} domain sequences to {extracted_domains_fasta_path}"
            )

        except FileNotFoundError:
            logger.error(
                f"Input FASTA file {ipr_input_file_to_use} not found during domain extraction."
            )
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {json_output_path}.")
        except Exception as e:
            logger.error(f"Error during domain extraction: {e}", exc_info=True)

        # Clean up if the input file was a temporary one
        if has_asterisks and cleaned_input_file_path != input_file_path:
            if cleaned_input_file_path.exists():
                cleaned_input_file_path.unlink()

        return str(chunk_output_dir)
