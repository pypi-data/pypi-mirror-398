import logging
import os
import time
from typing import Dict, List, Literal, Optional, Tuple, cast

import h5py
import numpy as np
import pandas as pd
import torch
import torch.utils.data
from dayhoff_tools.deployment.processors import Processor
from dayhoff_tools.fasta import (
    clean_noncanonical_fasta,
    clean_noncanonical_fasta_to_dict,
)
from esm import FastaBatchedDataset, pretrained
from transformers import T5EncoderModel, T5Tokenizer

logger = logging.getLogger(__name__)


class ESMEmbedder(Processor):
    """A processor that calculates ESM embeddings for a file of protein sequences.
    Embeddings come from the last layer, and can be per-protein or per-residue."""

    def __init__(
        self,
        # PyTorch model file OR name of pretrained model to download
        # https://github.com/facebookresearch/esm?tab=readme-ov-file#available
        model_name: Literal[
            "esm2_t33_650M_UR50D",  # ESM2 version of the size used in CLEAN
            "esm2_t6_8M_UR50D",  # Smallest
            "esm1b_t33_650M_UR50S",  # Same as CLEAN
            "esm2_t36_3B_UR50D",  # 2nd largest
            "esm2_t48_15B_UR50D",  # Largest
        ],
        # Whether to return per-protein or per-residue embeddings.
        embedding_level: Literal["protein", "residue"],
        # Maximum batch size
        toks_per_batch: int = 4096,
        # Truncate sequences longer than the given value
        truncation_seq_length: int = 1022,
    ):
        super().__init__()
        self.model_name = model_name
        self.toks_per_batch = toks_per_batch
        self.embedding_level = embedding_level
        self.truncation_seq_length = truncation_seq_length

        # Instance variables set by other methods below:
        # self.model, self.alphabet, self.len_batches, self.data_loader, self.dataset_base_name

    def _load_model(self):
        """Download pre-trained model and load onto device"""
        self.model, self.alphabet = pretrained.load_model_and_alphabet(self.model_name)
        self.model.eval()
        if torch.cuda.is_available():
            self.model.cuda()
            logger.info("Transferred model to GPU.")
        else:
            logger.info("GPU not available. Running model on CPU.")

    def _load_dataset(self, fasta_file: str) -> None:
        """Load FASTA file into batched dataset and dataloader"""
        if not fasta_file.endswith(".fasta"):
            raise ValueError("Input file must have .fasta extension.")

        self.dataset_base_name = fasta_file.replace(".fasta", "")
        clean_fasta_file = fasta_file.replace(".fasta", "_clean.fasta")
        clean_noncanonical_fasta(input_path=fasta_file, output_path=clean_fasta_file)

        dataset = FastaBatchedDataset.from_file(clean_fasta_file)
        logger.info("Read %s and loaded %s sequences.", fasta_file, len(dataset))

        batches = dataset.get_batch_indices(self.toks_per_batch, extra_toks_per_seq=1)
        self.len_batches = len(batches)
        self.data_loader = torch.utils.data.DataLoader(
            dataset,  # type: ignore
            collate_fn=self.alphabet.get_batch_converter(self.truncation_seq_length),
            batch_sampler=batches,
        )
        os.remove(clean_fasta_file)

    def embed_fasta(self) -> str:
        """Calculate embeddings from the FASTA file, return the path to the .h5 file of results
        Write the H5 file with one dataset per protein (id plus embedding vector, where the vector
        is 2D if it was calculated per-residue).
        """
        output_path = self.dataset_base_name + ".h5"
        with h5py.File(output_path, "w") as h5_file, torch.no_grad():
            start_time = time.time()
            logger.info(
                f"Calculating per-{self.embedding_level} embeddings. This dataset contains {self.len_batches} batches."
            )
            total_batches = self.len_batches

            for batch_idx, (labels, sequences, toks) in enumerate(
                self.data_loader, start=1
            ):
                if batch_idx % 10 == 0:
                    elapsed_time = time.time() - start_time
                    time_left = elapsed_time * (total_batches - batch_idx) / batch_idx
                    logger.info(
                        f"{self.dataset_base_name} | Batch {batch_idx}/{total_batches} | Elapsed time {elapsed_time / 60:.0f} min | Time left {time_left / 60:.0f} min, or {time_left / 3_600:.2f} hours"
                    )

                if torch.cuda.is_available():
                    toks = toks.to(device="cuda", non_blocking=True)
                out = self.model(
                    toks,
                    repr_layers=[
                        cast(int, self.model.num_layers)
                    ],  # Get the last layer
                    return_contacts=False,
                )
                out["logits"].to(device="cpu")
                representations = {
                    layer: t.to(device="cpu")
                    for layer, t in out["representations"].items()
                }
                for label_idx, label_full in enumerate(labels):
                    label = label_full.split()[
                        0
                    ]  # Shorten the label to only the first word
                    truncate_len = min(
                        self.truncation_seq_length, len(sequences[label_idx])
                    )

                    full_embeds = list(representations.items())[0][1]
                    if self.embedding_level == "protein":
                        protein_embeds = (
                            full_embeds[label_idx, 1 : truncate_len + 1].mean(0).clone()
                        )
                        h5_file.create_dataset(label, data=protein_embeds)
                    elif self.embedding_level == "residue":
                        residue_embeds = full_embeds[
                            label_idx, 1 : truncate_len + 1
                        ].clone()
                        h5_file.create_dataset(label, data=residue_embeds)
                    else:
                        raise NotImplementedError(
                            f"Embedding level {self.embedding_level} not implemented."
                        )

        logger.info(f"Saved embeddings to {output_path}")
        return output_path

    def run(self, input_file: str, output_file: Optional[str] = None) -> str:
        self._load_model()
        self._load_dataset(input_file)
        embedding_file = self.embed_fasta()

        # If embedding per-protein, reformat the H5 file.
        # By default, write to the same filename; otherwise to output_file.
        reformatted_embedding_file = output_file or embedding_file
        if self.embedding_level == "protein":
            print("Reformatting H5 file...")
            formatter = H5Reformatter()
            formatter.run2(
                input_file=embedding_file,
                output_file=reformatted_embedding_file,
            )

        return reformatted_embedding_file


class H5Reformatter(Processor):
    """A processor that reformats per-protein T5 embeddings
    Old format (input): 1 dataset per protein, with the ID as key and the embedding as value.
    New format (output): 2 datasets for the whole file, one of all protein IDs and one of all
                            the embeddings together."""

    def __init__(self):
        super().__init__()
        # Set the device to GPU if available, otherwise CPU
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        logger.info("Device is: %s", self.device)

    def embedding_file_to_df(self, file_name: str) -> pd.DataFrame:
        with h5py.File(file_name, "r") as f:
            gene_names = list(f.keys())
            Xg = [f[key][()] for key in gene_names]  # type:ignore
        return pd.DataFrame(np.asmatrix(Xg), index=gene_names)  # type:ignore

    def write_df_to_h5(self, df: pd.DataFrame, filename: str, description: str) -> None:
        """
        Write a DataFrame to an HDF5 file, separating row IDs and vectors.

        Parameters:
        - df: pandas DataFrame, where the index contains the IDs and
                the columns contain the vector components.
        - filename: String, the path to the output HDF5 file.
        """
        df.index = df.index.astype(
            str
        )  # Ensure the index is of a string type for the row IDs
        vectors = df.values
        ids = df.index.to_numpy(dtype=str)

        with h5py.File(filename, "w") as h5f:
            h5f.create_dataset("vectors", data=vectors)
            dt = h5py.special_dtype(
                vlen=str
            )  # Use variable-length strings to accommodate any ID size
            h5f.create_dataset("ids", data=ids.astype("S"), dtype=dt)

            # add the attributes
            h5f.attrs["description"] = description
            h5f.attrs["num_vecs"] = vectors.shape[0]
            h5f.attrs["vec_dim"] = vectors.shape[1]

    def run(self, input_file: str) -> str:
        """Load an H5 file as a DataFrame, delete the file, and then export
        the dataframe as an H5 file in the new format."""
        df = self.embedding_file_to_df(input_file)
        os.remove(input_file)
        new_file_description = "Embeddings formatted for global ID and Vector tables."
        self.write_df_to_h5(df, input_file, new_file_description)

        return input_file

    def run2(self, input_file: str, output_file: str):
        """Load an H5 file as a DataFrame, delete the file, and then export
        the dataframe as an H5 file in the new format."""
        df = self.embedding_file_to_df(input_file)
        new_file_description = "Embeddings formatted for global ID and Vector tables."
        self.write_df_to_h5(df, output_file, new_file_description)


class Embedder(Processor):
    """Base class for protein sequence embedders with optimized memory management.

    This class provides the core functionality for embedding protein sequences using
    transformer models, with built-in memory management and batch processing capabilities.
    It handles sequences of different sizes appropriately, processing large sequences
    individually and smaller sequences in batches for efficiency.

    Memory Management Features:
    - Periodic cleanup of GPU memory to prevent fragmentation
    - Separate handling of large and small sequences to optimize memory usage
    - Batch size limits based on total residues to prevent OOM errors
    - Configurable cleanup frequency to balance performance and memory usage
    - Empirically tested sequence length limits (5000-5500 residues depending on model)

    Memory Fragmentation Prevention:
    - Large sequences (>2500 residues) are processed individually to maintain contiguous memory blocks
    - Small sequences are batched to efficiently use memory fragments
    - Forced cleanup after processing large proteins
    - Memory cleanup after every N sequences (configurable)
    - Aggressive garbage collection settings for CUDA memory allocator

    Memory Usage Patterns:
    - Base memory: 2.4-4.8GB (model dependent)
    - Peak memory: 12-15GB during large sequence processing
    - Fragmentation ratio maintained above 0.92 for efficient memory use
    - Maximum sequence length determined by model:
        * T5: ~5000 residues
        * ProstT5: ~5500 residues

    Implementation Details:
    - Uses PyTorch's CUDA memory allocator with optimized settings
    - Configurable thresholds for large protein handling
    - Automatic batch size adjustment based on sequence lengths
    - Optional chunking for sequences exceeding maximum length
    - Detailed memory statistics logging for monitoring

    Note:
        Memory limits are hardware-dependent. The above values are based on testing
        with a 16GB GPU (such as NVIDIA T4). Adjust parameters based on available GPU memory.
    """

    def __init__(
        self,
        model,
        tokenizer,
        max_seq_length: int = 5000,
        large_protein_threshold: int = 2500,
        batch_residue_limit: int = 5000,
        cleanup_frequency: int = 100,
        skip_long_proteins: bool = False,
    ):
        """Initialize the Embedder with model and memory management parameters.

        Args:
            model: The transformer model to use for embeddings
            tokenizer: The tokenizer matching the model
            max_seq_length: Maximum sequence length before chunking or skipping.
                          Also used as chunk size when processing long sequences.
            large_protein_threshold: Sequences longer than this are processed individually
            batch_residue_limit: Maximum total residues allowed in a batch
            cleanup_frequency: Number of sequences to process before performing memory cleanup
            skip_long_proteins: If True, skip proteins longer than max_seq_length.
                              If False, process them in chunks of max_seq_length size.

        Note:
            The class automatically configures CUDA memory allocation if GPU is available.
        """
        # Configure memory allocator for CUDA
        if torch.cuda.is_available():
            os.environ["PYTORCH_CUDA_ALLOC_CONF"] = (
                "max_split_size_mb:128,"  # Smaller allocation chunks
                "garbage_collection_threshold:0.8"  # More aggressive GC
            )

        self.max_seq_length = max_seq_length
        self.large_protein_threshold = large_protein_threshold
        self.batch_residue_limit = batch_residue_limit
        self.cleanup_frequency = cleanup_frequency
        self.skip_long_proteins = skip_long_proteins
        self.processed_count = 0

        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = model
        self.tokenizer = tokenizer

        self.model.to(self.device)
        self.model.eval()

    def get_embeddings(self, seqs: Dict[str, str]) -> Dict[str, np.ndarray]:
        """Process sequences and generate embeddings with memory management.

        This method handles the core embedding logic, including:
        - Handling sequences that exceed maximum length (skip or chunk)
        - Splitting sequences into large and small batches
        - Periodic memory cleanup
        - Batch processing for efficiency

        Args:
            seqs: Dictionary mapping sequence IDs to their amino acid sequences

        Returns:
            Dictionary mapping sequence IDs to their embedding vectors

        Note:
            Long sequences are either skipped or processed in chunks based on skip_long_proteins
        """
        results: Dict[str, np.ndarray] = {}
        try:
            # Initialize progress tracking
            total_sequences = len(seqs)
            processed_sequences = 0
            start_time = time.time()

            logger.info(f"Starting embedding of {total_sequences} sequences")

            # Handle sequences based on length
            long_seqs = {
                id: seq for id, seq in seqs.items() if len(seq) > self.max_seq_length
            }
            valid_seqs = {
                id: seq for id, seq in seqs.items() if len(seq) <= self.max_seq_length
            }

            if long_seqs:
                if self.skip_long_proteins:
                    logger.warning(
                        f"Skipping {len(long_seqs)} sequences exceeding max length {self.max_seq_length}: {', '.join(long_seqs.keys())}"
                    )
                else:
                    logger.info(
                        f"Processing {len(long_seqs)} long sequences in chunks: {', '.join(long_seqs.keys())}"
                    )
                    for i, (seq_id, seq) in enumerate(long_seqs.items(), 1):
                        logger.info(
                            f"Embedding long sequence {i}/{len(long_seqs)}: {seq_id}"
                        )
                        results[seq_id] = self.embed_big_prot(seq_id, seq)
                        self.cleanup_memory()

                        # Update progress
                        processed_sequences += 1
                        elapsed_time = time.time() - start_time
                        remaining_sequences = total_sequences - processed_sequences
                        avg_time_per_seq = (
                            elapsed_time / processed_sequences
                            if processed_sequences > 0
                            else 0
                        )
                        estimated_time_left = avg_time_per_seq * remaining_sequences

                        logger.info(
                            f"Progress: {processed_sequences}/{total_sequences} sequences ({processed_sequences/total_sequences*100:.1f}%) | "
                            f"Elapsed: {elapsed_time/60:.1f} min | "
                            f"Est. remaining: {estimated_time_left/60:.1f} min"
                        )

            # Split remaining sequences based on size
            large_seqs = {
                id: seq
                for id, seq in valid_seqs.items()
                if len(seq) > self.large_protein_threshold
            }
            small_seqs = {
                id: seq
                for id, seq in valid_seqs.items()
                if len(seq) <= self.large_protein_threshold
            }

            logger.info(
                f"Split into {len(large_seqs)} large and {len(small_seqs)} small sequences"
            )

            # Process large sequences individually
            for i, (seq_id, seq) in enumerate(large_seqs.items(), 1):
                logger.info(
                    f"Processing large sequence {i}/{len(large_seqs)}: {seq_id}"
                )
                batch = [(seq_id, seq, len(seq))]
                results.update(self.embed_batch(batch))
                self.cleanup_memory()  # Cleanup after each large sequence

                # Update progress
                processed_sequences += 1
                elapsed_time = time.time() - start_time
                remaining_sequences = total_sequences - processed_sequences
                avg_time_per_seq = (
                    elapsed_time / processed_sequences if processed_sequences > 0 else 0
                )
                estimated_time_left = avg_time_per_seq * remaining_sequences

                logger.info(
                    f"Progress: {processed_sequences}/{total_sequences} sequences ({processed_sequences/total_sequences*100:.1f}%) | "
                    f"Elapsed: {elapsed_time/60:.1f} min | "
                    f"Est. remaining: {estimated_time_left/60:.1f} min"
                )

            # Process small sequences in batches
            current_batch: List[Tuple[str, str, int]] = []
            current_size = 0
            small_batch_count = 0
            total_small_batches = (
                sum(len(seq) for seq in small_seqs.values())
                + self.batch_residue_limit
                - 1
            ) // self.batch_residue_limit

            # Sort sequences by length in descending order (reduces unnecessary padding --> speeds up embedding)
            small_seqs_sorted = sorted(
                small_seqs.items(), key=lambda x: len(x[1]), reverse=True
            )

            for seq_id, seq in small_seqs_sorted:
                seq_len = len(seq)

                # Check if adding this sequence would exceed the limit
                if current_batch and current_size + seq_len > self.batch_residue_limit:
                    # Process current batch before adding the new sequence
                    small_batch_count += 1
                    logger.info(
                        f"Processing small batch {small_batch_count}/{total_small_batches} with {len(current_batch)} sequences"
                    )
                    batch_results = self.embed_batch(current_batch)
                    results.update(batch_results)
                    self.cleanup_memory()

                    # Update progress
                    processed_sequences += len(current_batch)
                    elapsed_time = time.time() - start_time
                    remaining_sequences = total_sequences - processed_sequences
                    avg_time_per_seq = (
                        elapsed_time / processed_sequences
                        if processed_sequences > 0
                        else 0
                    )
                    estimated_time_left = avg_time_per_seq * remaining_sequences

                    logger.info(
                        f"Progress: {processed_sequences}/{total_sequences} sequences ({processed_sequences/total_sequences*100:.1f}%) | "
                        f"Elapsed: {elapsed_time/60:.1f} min | "
                        f"Est. remaining: {estimated_time_left/60:.1f} min"
                    )
                    # Start new batch
                    current_batch = []
                    current_size = 0

                # Add the current sequence to the batch
                current_batch.append((seq_id, seq, seq_len))
                current_size += seq_len

            # Process remaining batch
            if current_batch:
                small_batch_count += 1
                logger.info(
                    f"Processing final small batch {small_batch_count}/{total_small_batches} with {len(current_batch)} sequences"
                )
                batch_results = self.embed_batch(current_batch)
                results.update(batch_results)

                # Update final progress
                processed_sequences += len(current_batch)
                elapsed_time = time.time() - start_time

                logger.info(
                    f"Completed embedding {processed_sequences}/{total_sequences} sequences in {elapsed_time/60:.1f} minutes"
                )

            return results

        finally:
            self.cleanup_memory(deep=True)

    def cleanup_memory(self, deep: bool = False):
        """Perform memory cleanup operations.

        Args:
            deep: If True, performs aggressive cleanup including model transfer
                 and garbage collection. Takes longer but frees more memory.

        Note:
            Regular cleanup is performed based on cleanup_frequency.
            Deep cleanup is more thorough but takes longer.
        """
        self.processed_count += 1

        if deep or self.processed_count % self.cleanup_frequency == 0:
            logger.info(
                f"Performing memory cleanup after {self.processed_count} sequences"
            )
            if torch.cuda.is_available():
                before_mem = torch.cuda.memory_allocated() / 1e9

                torch.cuda.empty_cache()
                if deep:
                    self.model = self.model.cpu()
                    torch.cuda.empty_cache()
                    self.model = self.model.to(self.device)

                after_mem = torch.cuda.memory_allocated() / 1e9
                logger.info(
                    f"Memory cleaned up: {before_mem:.2f}GB -> {after_mem:.2f}GB"
                )

            if deep:
                import gc

                gc.collect()

    def run(self, input_file, output_file=None):
        """
        Run the embedding process on the input file.

        Args:
            input_file (str): Path to the input FASTA file.
            output_file (str, optional): Path to the output H5 file. If not provided,
                                         it will be generated from the input file name.

        Returns:
            str: Path to the output H5 file containing the embeddings.
        """
        logger.info(f"Loading sequences from {input_file}")
        start_time = time.time()
        sequences = clean_noncanonical_fasta_to_dict(input_file)
        load_time = time.time() - start_time
        logger.info(
            f"Loaded {len(sequences)} sequences from {input_file} in {load_time:.2f} seconds"
        )

        logger.info(f"Starting embedding process for {len(sequences)} sequences")
        embed_start_time = time.time()
        embeddings = self.get_embeddings(sequences)
        embed_time = time.time() - embed_start_time
        logger.info(
            f"Completed embedding {len(embeddings)} sequences in {embed_time/60:.2f} minutes"
        )

        if output_file is None:
            output_file = input_file.replace(".fasta", ".h5")

        logger.info(f"Saving embeddings to {output_file}")
        save_start_time = time.time()
        self.save_to_h5(output_file, embeddings)
        save_time = time.time() - save_start_time
        logger.info(
            f"Saved {len(embeddings)} embeddings to {output_file} in {save_time:.2f} seconds"
        )

        total_time = time.time() - start_time
        logger.info(f"Total processing time: {total_time/60:.2f} minutes")

        return output_file

    def save_to_h5(self, output_file: str, embeddings: Dict[str, np.ndarray]) -> None:
        """
        Save protein embeddings to an HDF5 file.

        Args:
            output_file (str): Path to save the embeddings.
            embeddings (Dict[str, np.ndarray]): Dictionary of embeddings.

        The method creates an H5 file with two datasets:
        - 'ids': contains protein IDs as variable-length strings
        - 'vectors': contains embedding vectors as float32 arrays
        """
        # Convert the embeddings dictionary to lists for ids and vectors
        ids = list(embeddings.keys())
        vectors = np.array(list(embeddings.values()), dtype=np.float32)

        # Create the HDF5 file, with datasets for vectors and IDs
        with h5py.File(output_file, "w") as h5f:
            # Create the 'vectors' dataset
            h5f.create_dataset("vectors", data=vectors)

            # Create the 'ids' dataset with variable-length strings
            dt = h5py.special_dtype(vlen=str)
            h5f.create_dataset("ids", data=ids, dtype=dt)

            # Add the attributes
            h5f.attrs["num_vecs"] = len(embeddings)
            h5f.attrs["vec_dim"] = vectors.shape[1] if vectors.size > 0 else 0

    def embed_big_prot(self, seq_id: str, sequence: str) -> np.ndarray:
        """Embed a large protein sequence by chunking it and averaging the embeddings.

        Args:
            seq_id: The identifier for the protein sequence
            sequence: The protein sequence to embed

        Returns:
            np.ndarray: The averaged embedding for the entire sequence

        Note:
            This method processes the sequence in chunks of size max_seq_length
            and averages the resulting embeddings.
        """
        if not isinstance(sequence, str):
            raise TypeError("Sequence must be a string.")

        if not sequence:
            raise ValueError("Sequence cannot be empty.")

        if self.max_seq_length <= 0:
            raise ValueError("max_seq_length must be greater than 0.")

        # Create chunks of the sequence using max_seq_length
        chunks: List[Tuple[str, str, int]] = [
            (
                seq_id,
                sequence[i : i + self.max_seq_length],
                min(self.max_seq_length, len(sequence) - i),
            )
            for i in range(0, len(sequence), self.max_seq_length)
        ]

        logger.info(
            f"Processing {seq_id} in {len(chunks)} chunks (total length: {len(sequence)})"
        )

        # Embed each chunk
        chunk_embeddings = []
        for i, chunk in enumerate(chunks, 1):
            logger.info(
                f"Processing chunk {i}/{len(chunks)} for {seq_id} (length: {chunk[2]})"
            )
            chunk_start_time = time.time()
            result = self.embed_batch([chunk])
            chunk_embeddings.append(result[seq_id])
            chunk_time = time.time() - chunk_start_time
            logger.info(
                f"Processed chunk {i}/{len(chunks)} for {seq_id} in {chunk_time:.2f} seconds"
            )

        # Average the embeddings
        average_embedding = np.mean(chunk_embeddings, axis=0)
        logger.info(f"Completed processing {seq_id} (averaged {len(chunks)} chunks)")

        return average_embedding

    def embed_batch(self, batch: List[Tuple[str, str, int]]) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for a batch of sequences.

        Args:
            batch: A list of tuples, each containing (sequence_id, sequence, sequence_length)

        Returns:
            A dictionary mapping sequence IDs to their embeddings as numpy arrays
        """
        if not batch:
            raise ValueError(
                "Cannot embed an empty batch. Please provide at least one sequence."
            )

        sequence_ids, sequences, sequence_lengths = zip(*batch)

        # Prepare sequences for tokenization
        tokenizer_input = self.prepare_tokenizer_input(list(sequences))

        # Tokenize sequences
        encoded_input = self.tokenizer.batch_encode_plus(
            tokenizer_input,
            add_special_tokens=True,
            padding="longest",
            return_tensors="pt",
        )

        # Move tensors to the appropriate device
        input_ids = encoded_input["input_ids"].to(self.device)
        attention_mask = encoded_input["attention_mask"].to(self.device)

        # Generate embeddings
        with torch.no_grad():
            embedding_output = self.model(
                input_ids, attention_mask=attention_mask
            ).last_hidden_state

        # Process embeddings for each sequence
        embeddings = {}
        for idx, (seq_id, seq_len) in enumerate(zip(sequence_ids, sequence_lengths)):
            # Extract embedding for the sequence
            seq_embedding = self.extract_sequence_embedding(
                embedding_output[idx], seq_len
            )

            # Calculate mean embedding and convert to numpy array
            mean_embedding = seq_embedding.mean(dim=0).detach().cpu().numpy().squeeze()

            embeddings[seq_id] = mean_embedding

        return embeddings

    def prepare_tokenizer_input(self, sequences: List[str]) -> List[str]:
        """Prepare sequences for tokenization."""
        raise NotImplementedError

    def extract_sequence_embedding(
        self, embedding: torch.Tensor, seq_len: int
    ) -> torch.Tensor:
        """Extract the relevant part of the embedding for a sequence."""
        raise NotImplementedError


class ProstT5Embedder(Embedder):
    """Protein sequence embedder using the ProstT5 model.

    This class implements protein sequence embedding using the ProstT5 model,
    which is specifically trained for protein structure prediction tasks.
    It includes memory-efficient processing and automatic precision selection
    based on available hardware.

    Memory management features are inherited from the base Embedder class:
    - Periodic cleanup of GPU memory
    - Separate handling of large and small sequences
    - Batch size limits based on total residues
    - Configurable cleanup frequency
    """

    def __init__(
        self,
        max_seq_length: int = 5000,
        large_protein_threshold: int = 2500,
        batch_residue_limit: int = 5000,
        cleanup_frequency: int = 100,
        skip_long_proteins: bool = False,
    ):
        """Initialize ProstT5Embedder with memory management parameters.

        Args:
            max_seq_length: Maximum sequence length before chunking or skipping.
                          Also used as chunk size when processing long sequences.
            large_protein_threshold: Sequences longer than this are processed individually
            batch_residue_limit: Maximum total residues in a batch
            cleanup_frequency: Frequency of memory cleanup operations
            skip_long_proteins: If True, skip proteins longer than max_seq_length

        Note:
            The model automatically selects half precision (float16) when running on GPU
            and full precision (float32) when running on CPU.
        """
        tokenizer = T5Tokenizer.from_pretrained(
            "Rostlab/ProstT5", do_lower_case=False, legacy=True
        )
        model = T5EncoderModel.from_pretrained("Rostlab/ProstT5")

        super().__init__(
            model,
            tokenizer,
            max_seq_length,
            large_protein_threshold,
            batch_residue_limit,
            cleanup_frequency,
            skip_long_proteins,
        )

        # Set precision based on device
        self.model = (
            self.model.half() if torch.cuda.is_available() else self.model.float()
        )

    def prepare_tokenizer_input(self, sequences: List[str]) -> List[str]:
        """Prepare sequences for ProstT5 tokenization.

        Args:
            sequences: List of amino acid sequences

        Returns:
            List of sequences with ProstT5-specific formatting, including the
            <AA2fold> prefix and space-separated residues.
        """
        return [f"<AA2fold> {' '.join(seq)}" for seq in sequences]

    def extract_sequence_embedding(
        self, embedding: torch.Tensor, seq_len: int
    ) -> torch.Tensor:
        """Extract relevant embeddings for a sequence.

        Args:
            embedding: Raw embedding tensor from the model
            seq_len: Length of the original sequence

        Returns:
            Tensor containing only the relevant sequence embeddings,
            excluding special tokens. For ProstT5, we skip the first token
            (corresponding to <AA2fold>) and take the next seq_len tokens.
        """
        return embedding[1 : seq_len + 1]


class T5Embedder(Embedder):
    """Protein sequence embedder using the T5 transformer model.

    This class implements protein sequence embedding using the T5 model from Rostlab,
    specifically designed for protein sequences. It includes memory-efficient processing
    of both large and small sequences.

    The model used is 'Rostlab/prot_t5_xl_half_uniref50-enc', which was trained on
    UniRef50 sequences and provides state-of-the-art protein embeddings.

    Memory management features are inherited from the base Embedder class:
    - Periodic cleanup of GPU memory
    - Separate handling of large and small sequences
    - Batch size limits based on total residues
    - Configurable cleanup frequency
    """

    def __init__(
        self,
        max_seq_length: int = 5000,
        large_protein_threshold: int = 2500,
        batch_residue_limit: int = 5000,
        cleanup_frequency: int = 100,
        skip_long_proteins: bool = False,
    ):
        """Initialize T5Embedder with memory management parameters.

        Args:
            max_seq_length: Maximum sequence length before chunking or skipping.
                          Also used as chunk size when processing long sequences.
            large_protein_threshold: Sequences longer than this are processed individually
            batch_residue_limit: Maximum total residues in a batch
            cleanup_frequency: Frequency of memory cleanup operations
            skip_long_proteins: If True, skip proteins longer than max_seq_length

        Note:
            The model automatically handles memory management and batch processing
            based on sequence sizes and available resources.
        """
        tokenizer = T5Tokenizer.from_pretrained(
            "Rostlab/prot_t5_xl_half_uniref50-enc", do_lower_case=False
        )
        model = T5EncoderModel.from_pretrained("Rostlab/prot_t5_xl_half_uniref50-enc")

        super().__init__(
            model,
            tokenizer,
            max_seq_length,
            large_protein_threshold,
            batch_residue_limit,
            cleanup_frequency,
            skip_long_proteins,
        )

    def prepare_tokenizer_input(self, sequences: List[str]) -> List[str]:
        """Prepare sequences for T5 tokenization.

        Args:
            sequences: List of amino acid sequences

        Returns:
            List of space-separated sequences ready for tokenization
        """
        return [" ".join(seq) for seq in sequences]

    def extract_sequence_embedding(
        self, embedding: torch.Tensor, seq_len: int
    ) -> torch.Tensor:
        """Extract relevant embeddings for a sequence.

        Args:
            embedding: Raw embedding tensor from the model
            seq_len: Length of the original sequence

        Returns:
            Tensor containing only the relevant sequence embeddings
        """
        return embedding[:seq_len]
