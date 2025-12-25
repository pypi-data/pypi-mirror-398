"""Genomic flank analysis tool for mapping probe sequences to reference genomes."""

import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import pandas as pd
import typer
from loguru import logger

# ============================================================================
# Constants & Configuration
# ============================================================================

FLANK_SIZE_DEFAULT = 60
ALLELE_PATTERN = re.compile(r"\[([ACGT\-]+)/([ACGT\-]+)\]")
CIGAR_PATTERN = re.compile(r"(\d+)([MIDNSHPX=])")
CIGAR_TAG_PATTERN = re.compile(r"cg:Z:([0-9MIDNSHPX=]+)")
NM_TAG_PATTERN = re.compile(r"NM:i:([0-9]+)")

# PAF file column specifications
PAF_COLUMNS = {
    "names": [
        "id",
        "probe_length",
        "probe_start",
        "strand",
        "chrom",
        "match_start",
        "match_length",
        "mapq",
    ],
    "usecols": [0, 1, 2, 4, 5, 7, 9, 11],
}

app = typer.Typer(help="Genomic flank analysis tool.")


# ============================================================================
# Data Classes & Enums
# ============================================================================


class TargetType(str, Enum):
    """Supported input target file types."""

    BED = "bed"
    VCF = "vcf"


@dataclass(frozen=True)
class CigarOperation:
    """Represents a single CIGAR operation."""

    count: int
    operation: str


@dataclass(frozen=True)
class AlignmentOffset:
    """Stores offset information for alignment calculations."""

    start: int
    end: int


# ============================================================================
# Sequence & CIGAR Processing
# ============================================================================


def extract_alleles(variant_string: str) -> str:
    """
    Extract REF/ALT alleles from formatted string.

    Args:
        variant_string: String containing alleles like 'AAA[C/T]GGG'

    Returns:
        Alleles in format 'REF/ALT', or '-/-' if not found

    Example:
        >>> extract_alleles('AAA[C/T]GGG')
        'C/T'
    """
    match = ALLELE_PATTERN.search(variant_string)
    return f"{match.group(1)}/{match.group(2)}" if match else "-/-"


def parse_cigar(cigar: str) -> list[CigarOperation]:
    """
    Parse CIGAR string into structured operations.

    Args:
        cigar: CIGAR string (e.g., '10M2I5M')

    Returns:
        List of CigarOperation objects

    Raises:
        ValueError: If CIGAR string is empty or invalid
    """
    if not cigar:
        raise ValueError("CIGAR string is empty")

    operations = [CigarOperation(int(count), op) for count, op in CIGAR_PATTERN.findall(cigar)]

    if not operations:
        raise ValueError(f"Invalid CIGAR string: {cigar}")

    return operations


def calculate_indel_bias(cigar: str, offset_limit: int) -> Optional[int]:
    """
    Calculate deletion - insertion bias up to specified offset.

    Args:
        cigar: CIGAR string
        offset_limit: Maximum match offset to consider

    Returns:
        Indel bias (deletions - insertions), or None if offset not reached
    """
    operations = parse_cigar(cigar)
    match_count = 0
    ins_count = 0
    del_count = 0

    for op in operations:
        if op.operation == "M":
            match_count += op.count
        elif op.operation == "I":
            ins_count += op.count
        elif op.operation == "D":
            if match_count == offset_limit:
                return None
            del_count += op.count

        if match_count > offset_limit:
            break

    return (del_count - ins_count) if match_count >= offset_limit else None


def calculate_genomic_position(
    match_start: int, offset_target: int, probe_start: int, indel_bias: int
) -> int:
    """
    Calculate final genomic position accounting for alignment details.

    Args:
        match_start: Start position of match in genome
        offset_target: Target offset from alignment
        probe_start: Start position in probe sequence
        indel_bias: Calculated indel bias

    Returns:
        1-based genomic coordinate
    """
    return match_start + offset_target + 1 - probe_start + indel_bias


def probe_sequence_from_flank(flank_str: str) -> str:
    """
    Convert flank notation to probe sequence using reference allele.

    Args:
        flank_str: Flank string like 'AAA[C/T]GGG'

    Returns:
        Probe sequence using first allele: 'AAACGGG'

    Raises:
        ValueError: If flank format is invalid
    """
    try:
        left, remainder = flank_str.split("[", 1)
        alleles, right = remainder.split("]", 1)
        ref_allele = alleles.split("/")[0]
        return f"{left}{ref_allele}{right}"
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid flank sequence format: {flank_str}") from e


# ============================================================================
# External Tool Integration
# ============================================================================


class CommandRunner:
    """Handles execution of external bioinformatics tools."""

    @staticmethod
    def run(command: list[str], output_file: Optional[Path] = None) -> None:
        """
        Execute external command with proper error handling.

        Args:
            command: Command and arguments as list
            output_file: Optional file to redirect stdout

        Raises:
            RuntimeError: If command execution fails
        """
        cmd_str = " ".join(str(c) for c in command)
        logger.debug(f"Running: {cmd_str}")

        stdout_dest = None
        try:
            if output_file:
                stdout_dest = output_file.open("w", encoding="utf-8")

            subprocess.run(
                command,
                stdout=stdout_dest,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {cmd_str}")
            logger.error(f"Stderr: {e.stderr.strip()}")
            raise RuntimeError(f"External command failed: {cmd_str}") from e
        except FileNotFoundError as e:
            logger.error(f"Tool not found: {command[0]}")
            raise RuntimeError(f"Required tool '{command[0]}' not found in PATH") from e
        finally:
            if stdout_dest:
                stdout_dest.close()


class BedtoolsWrapper:
    """Wrapper for bedtools operations."""

    def __init__(self, runner: CommandRunner):
        self.runner = runner

    def slop(self, input_bed: Path, output_bed: Path, flank_size: int, genome_fai: Path) -> None:
        """Extend regions in BED file."""
        self.runner.run(
            [
                "bedtools",
                "slop",
                "-b",
                str(flank_size),
                "-i",
                str(input_bed),
                "-g",
                str(genome_fai),
            ],
            output_file=output_bed,
        )

    def getfasta(self, genome: Path, bed: Path, output_fa: Path) -> None:
        """Extract sequences from genome."""
        self.runner.run(
            [
                "bedtools",
                "getfasta",
                "-fi",
                str(genome),
                "-fo",
                str(output_fa),
                "-bed",
                str(bed),
                "-nameOnly",
            ]
        )


class Minimap2Wrapper:
    """Wrapper for minimap2 alignment."""

    def __init__(self, runner: CommandRunner):
        self.runner = runner

    def align(self, index: Path, query: Path, output_paf: Path, threads: int = 16) -> None:
        """Align sequences to indexed genome."""
        self.runner.run(
            [
                "minimap2",
                "-t",
                str(threads),
                "--secondary=yes",
                "-N",
                "10",
                "-cx",
                "sr",
                str(index),
                str(query),
            ],
            output_file=output_paf,
        )


# ============================================================================
# PAF File Processing
# ============================================================================


def extract_tag_value(line: str, pattern: re.Pattern) -> str:
    """Extract tag value from PAF line using regex pattern."""
    match = pattern.search(line)
    if not match:
        raise ValueError(f"Pattern {pattern.pattern} not found in line")
    return match.group(1)


def parse_paf_tags(paf_path: Path) -> pd.DataFrame:
    """
    Extract CIGAR and NM tags from PAF file.

    Args:
        paf_path: Path to PAF alignment file

    Returns:
        DataFrame with 'cigar' and 'n_mismatch' columns
    """
    records = []

    with paf_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                records.append(
                    {
                        "cigar": extract_tag_value(line, CIGAR_TAG_PATTERN),
                        "n_mismatch": int(extract_tag_value(line, NM_TAG_PATTERN)),
                    }
                )
            except ValueError as e:
                logger.warning(f"Skipping line due to parse error: {e}")

    return pd.DataFrame(records)


# ============================================================================
# Alignment Processing Pipeline
# ============================================================================


class AlignmentProcessor:
    """Processes PAF alignments to generate position mappings."""

    @staticmethod
    def filter_best_alignments(df: pd.DataFrame, keep_duplicates: bool = False) -> pd.DataFrame:
        """
        Filter alignments to keep only best matches per probe.

        Best matches are determined by:
        1. Maximum match length
        2. Minimum number of mismatches
        """
        # Keep longest matches
        df = df[df["match_length"] == df.groupby("id")["match_length"].transform("max")]

        # Among equal-length matches, keep those with fewest mismatches
        df = df[df["n_mismatch"] == df.groupby("id")["n_mismatch"].transform("min")]

        # Remove duplicates unless explicitly kept
        if not keep_duplicates:
            df = df.drop_duplicates(subset=["id"])

        return df

    @staticmethod
    def filter_by_match_quality(df: pd.DataFrame, cutoff: float) -> pd.DataFrame:
        """Filter alignments by match ratio threshold."""
        match_ratio = df["match_length"] / df["probe_length"]
        return df[match_ratio > cutoff].copy()

    @staticmethod
    def calculate_positions(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate genomic positions from alignment data."""

        def get_position(row: pd.Series) -> Optional[int]:  # type: ignore[type-arg]
            target_offset = row["offset_start"] if row["strand"] == "+" else row["offset_end"]

            indel_bias = calculate_indel_bias(row["cigar"], target_offset)
            if indel_bias is None:
                return None

            return calculate_genomic_position(
                match_start=row["match_start"],
                offset_target=target_offset,
                probe_start=row["probe_start"],
                indel_bias=indel_bias,
            )

        df["pos"] = df.apply(get_position, axis=1)  # type: ignore[arg-type]
        return df.dropna(subset=["pos"]).copy()

    @staticmethod
    def add_identifiers(df: pd.DataFrame) -> pd.DataFrame:
        """Add new identifiers and 0-based position."""
        df["pos"] = df["pos"].astype(int)
        df["new_id"] = df["chrom"].astype(str) + "_" + df["pos"].astype(str)
        df["pos_0"] = df["pos"] - 1
        return df

    def process(
        self,
        paf_df: pd.DataFrame,
        offset_df: pd.DataFrame,
        match_cutoff: float,
        keep_duplicates: bool = False,
    ) -> pd.DataFrame:
        """
        Complete processing pipeline for PAF alignments.

        Args:
            paf_df: DataFrame with PAF alignment data
            offset_df: DataFrame with offset information
            match_cutoff: Minimum match ratio threshold
            keep_duplicates: Whether to keep duplicate alignments

        Returns:
            DataFrame with ID mapping (id -> new_id)
        """
        # Filter pipeline
        df = self.filter_best_alignments(paf_df, keep_duplicates)
        df = self.filter_by_match_quality(df, match_cutoff)

        # Merge with offset information
        df = df.merge(offset_df, on="id")

        # Calculate positions
        df = self.calculate_positions(df)
        df = self.add_identifiers(df)

        return df


# ============================================================================
# File Output Management
# ============================================================================


class OutputManager:
    """Manages output file generation."""

    @staticmethod
    def save_idmap(df: pd.DataFrame, output_path: Path) -> None:
        """Save ID mapping file."""
        df[["id", "new_id"]].to_csv(output_path, sep="\t", index=False, header=False)
        logger.info(f"Saved ID map: {output_path}")

    @staticmethod
    def save_target_bed(df: pd.DataFrame, output_path: Path) -> None:
        """Save target positions as BED file."""
        columns = ["chrom", "pos_0", "pos", "id", "mapq", "strand"]
        df.sort_values(["chrom", "pos"])[columns].to_csv(
            output_path, sep="\t", index=False, header=False
        )
        logger.info(f"Saved target BED: {output_path}")

    @staticmethod
    def save_position_table(df: pd.DataFrame, output_path: Path) -> None:
        """Save position table with allele information."""
        if "alleles" not in df.columns:
            df["alleles"] = "-/-"

        df[["chrom", "pos", "alleles", "id"]].to_csv(output_path, sep="\t", index=False)
        logger.info(f"Saved position table: {output_path}")

    def save_all(self, df: pd.DataFrame, prefix: Path) -> None:
        """Save all output file formats."""
        self.save_idmap(df, prefix.with_suffix(".idmap.tsv"))
        self.save_target_bed(df, prefix.with_suffix(".target.bed"))
        self.save_position_table(df, prefix.with_suffix(".pos.tsv"))


# ============================================================================
# VCF/BED Conversion
# ============================================================================


def convert_vcf_to_bed(vcf_path: Path, output_bed: Path) -> None:
    """
    Convert VCF file to BED format.

    Args:
        vcf_path: Input VCF file path
        output_bed: Output BED file path
    """
    logger.info("Converting VCF to BED...")

    df = pd.read_table(vcf_path, comment="#", header=None, usecols=[0, 1], names=["chrom", "end"])

    df["start"] = df["end"] - 1
    df["id"] = df["chrom"].astype(str) + "_" + df["end"].astype(str)

    df[["chrom", "start", "end", "id"]].to_csv(output_bed, sep="\t", index=False, header=False)


# ============================================================================
# Offset Calculation
# ============================================================================


def calculate_offsets(target_bed: Path, flank_bed: Path) -> pd.DataFrame:
    """
    Calculate offset positions for alignment.

    Args:
        target_bed: Original target BED file
        flank_bed: Extended flank BED file

    Returns:
        DataFrame with offset_start and offset_end columns
    """
    target_df = pd.read_table(target_bed, header=None, usecols=[1, 3], names=["t_start", "id"])

    flank_df = pd.read_table(
        flank_bed, header=None, usecols=[1, 2, 3], names=["f_start", "f_end", "id"]
    )

    merged = target_df.merge(flank_df, on="id")
    merged["offset_start"] = merged["t_start"] - merged["f_start"]
    merged["offset_end"] = merged["f_end"] - merged["t_start"] - 1

    return merged[["id", "offset_start", "offset_end"]]


# ============================================================================
# Main Command Functions
# ============================================================================


@app.command()
def site(
    target_file: Annotated[Path, typer.Argument(..., exists=True, help="Input BED or VCF file")],
    genome: Annotated[Path, typer.Argument(..., exists=True, help="Reference genome FASTA")],
    genome_sr_idx: Annotated[Path, typer.Argument(..., exists=True, help="Minimap2 SR index")],
    threads: Annotated[int, typer.Option("-t", "--threads", help="Number of threads")] = 16,
    cut_off: Annotated[float, typer.Option(help="Match ratio cutoff")] = 0.9,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing files")] = (False),
    target_type: Annotated[TargetType, typer.Option(case_sensitive=False)] = TargetType.BED,
):
    """
    Process genomic sites to generate mapping positions.

    Takes a BED or VCF file of target positions, extracts flanking sequences,
    aligns them to the genome, and generates position mappings.
    """
    # Initialize tools
    runner = CommandRunner()
    bedtools = BedtoolsWrapper(runner)
    minimap2 = Minimap2Wrapper(runner)
    processor = AlignmentProcessor()
    output_mgr = OutputManager()

    # Find genome index
    genome_fai = genome.with_suffix(genome.suffix + ".fai")
    if not genome_fai.exists():
        genome_fai = genome.parent / f"{genome.name}.fai"

    # Convert VCF to BED if needed
    if target_type == TargetType.VCF:
        target_bed = target_file.with_suffix(".bed")
        if force or not target_bed.exists():
            convert_vcf_to_bed(target_file, target_bed)
    else:
        target_bed = target_file

    # Generate flank regions
    logger.info(f"Generating {FLANK_SIZE_DEFAULT}bp flank regions...")
    flank_bed = target_bed.with_suffix(f".flank{FLANK_SIZE_DEFAULT}.bed")
    if force or not flank_bed.exists():
        bedtools.slop(target_bed, flank_bed, FLANK_SIZE_DEFAULT, genome_fai)

    # Extract sequences
    flank_fa = flank_bed.with_suffix(".fa")
    if force or not flank_fa.exists():
        bedtools.getfasta(genome, flank_bed, flank_fa)

    # Align to genome
    logger.info("Mapping flanks to genome...")
    flank_paf = flank_fa.with_suffix(".paf")
    if force or not flank_paf.exists():
        minimap2.align(genome_sr_idx, flank_fa, flank_paf, threads)

    # Process alignments
    logger.info("Processing alignments...")
    offset_df = calculate_offsets(target_bed, flank_bed)

    paf_df = pd.read_table(
        flank_paf,
        header=None,
        usecols=PAF_COLUMNS["usecols"],
        names=PAF_COLUMNS["names"],
    )

    tags_df = parse_paf_tags(flank_paf)
    full_df = pd.concat([paf_df, tags_df], axis=1)

    result_df = processor.process(full_df, offset_df, cut_off)
    output_mgr.save_all(result_df, flank_paf)

    logger.success("Site analysis complete!")


@app.command()
def flank(
    probe_table: Annotated[
        Path, typer.Argument(..., exists=True, help="Probe table with flank sequences")
    ],
    genome_sr_idx: Annotated[Path, typer.Argument(..., exists=True, help="Minimap2 SR index")],
    threads: Annotated[int, typer.Option("-t", "--threads", help="Number of threads")] = 16,
    cut_off: Annotated[float, typer.Option(help="Match ratio cutoff")] = 0.9,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing files")] = (False),
    keep_duplicates: Annotated[bool, typer.Option(help="Keep duplicate alignments")] = False,
):
    """
    Map probe sequences from table to genome.

    Takes a table with probe flanking sequences and maps them to the reference
    genome to determine genomic positions.
    """
    # Initialize tools
    runner = CommandRunner()
    minimap2 = Minimap2Wrapper(runner)
    processor = AlignmentProcessor()
    output_mgr = OutputManager()

    # Load and process probe table
    logger.info("Processing probe table...")
    probe_df = pd.read_table(probe_table)

    # Generate probe sequences
    probe_df["sequence"] = probe_df["Flank"].apply(probe_sequence_from_flank)

    # Write FASTA
    probe_fasta = probe_table.with_suffix(".fa")
    with probe_fasta.open("w") as f:
        for _, row in probe_df.iterrows():
            f.write(f">{row['id']}\n{row['sequence']}\n")

    # Calculate metadata
    probe_df["seq_length"] = probe_df["sequence"].str.len()
    probe_df["offset_start"] = probe_df["Flank"].str.find("[")
    probe_df["offset_end"] = probe_df["seq_length"] - probe_df["offset_start"] - 1
    probe_df["alleles"] = probe_df["Flank"].apply(extract_alleles)

    offset_df = probe_df[["id", "offset_start", "offset_end", "alleles"]]

    # Align to genome
    logger.info("Mapping to genome...")
    flank_paf = probe_fasta.with_suffix(".paf")
    if force or not flank_paf.exists():
        minimap2.align(genome_sr_idx, probe_fasta, flank_paf, threads)

    # Process alignments
    logger.info("Processing alignments...")
    paf_df = pd.read_table(
        flank_paf,
        header=None,
        usecols=PAF_COLUMNS["usecols"],
        names=PAF_COLUMNS["names"],
    )

    tags_df = parse_paf_tags(flank_paf)
    full_df = pd.concat([paf_df, tags_df], axis=1)

    result_df = processor.process(full_df, offset_df, cut_off, keep_duplicates)
    output_mgr.save_all(result_df, flank_paf)

    logger.success("Flank analysis complete!")


if __name__ == "__main__":
    app()


def main() -> None:
    """Entry point for console script."""
    app()
