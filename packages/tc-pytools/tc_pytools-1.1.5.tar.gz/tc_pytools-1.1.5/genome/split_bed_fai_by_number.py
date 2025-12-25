"""Split BED and FAI files into multiple files by a specified number of parts."""

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pandas as pd
import typer
from loguru import logger
from typing_extensions import Annotated

# Constants
OUT_COLUMNS = ["chrom", "start", "end"]
DEFAULT_SPLIT_NUMBER = 400
STEP_DIVISOR = 10

# Create Typer app instance
app = typer.Typer(help="Split BED and FAI files into multiple parts by number.")


@dataclass
class BedRegion:
    """Represents a genomic region in BED format."""

    chrom: str
    start: int
    end: int

    @property
    def length(self) -> int:
        """Calculate the length of the region."""
        return self.end - self.start

    def __str__(self) -> str:
        """Return a string representation of the region."""
        return f"{self.chrom}:{self.start}-{self.end}"


def _calculate_padding_width(max_value: int) -> int:
    """Calculate the number of digits needed for zero-padding.

    Args:
        max_value: The maximum value to be padded

    Returns:
        The number of digits needed for zero-padding
    """
    return math.ceil(math.log10(max_value + 1)) if max_value > 0 else 1


def _generate_output_filename(regions: List[BedRegion], prefix: str) -> str:
    """Generate output filename based on start and end regions.

    Args:
        regions: List of BedRegion objects
        prefix: Prefix for the filename

    Returns:
        Generated filename
    """
    start_region = regions[0]
    end_region = regions[-1]

    start_pos = f"{start_region.chrom}_{start_region.start}"
    end_pos = str(end_region.end)

    if start_region.chrom != end_region.chrom:
        end_pos = f"{end_region.chrom}_{end_region.end}"

    return f"{prefix}_{start_pos}_{end_pos}.bed"


def _save_bed_regions(regions: List[BedRegion], out_dir: Path, prefix: str) -> None:
    """Save a list of BedRegion objects to a BED file.

    Args:
        regions: List of BedRegion objects to save
        out_dir: Output directory
        prefix: Prefix for the output filename
    """
    if not regions:
        logger.warning("No regions to save")
        return

    filename = _generate_output_filename(regions, prefix)
    out_file = out_dir / filename

    df = pd.DataFrame(regions)
    df.to_csv(out_file, sep="\t", index=False, header=False, columns=OUT_COLUMNS)
    logger.debug(f"Saved {len(regions)} regions to {out_file}")


def split_bed(bed_file: Path, out_dir: Path, split_number: int) -> None:
    """Split a BED file into multiple files by total length.

    Args:
        bed_file: Path to the input BED file
        out_dir: Output directory
        split_number: Number of files to split into

    Raises:
        ValueError: If output directory already exists
        FileNotFoundError: If input BED file does not exist
    """
    if not bed_file.exists():
        raise FileNotFoundError(f"BED file not found: {bed_file}")

    split_out_dir = out_dir / bed_file.stem
    if split_out_dir.exists():
        raise ValueError(f"Output directory already exists: {split_out_dir}")

    split_out_dir.mkdir(parents=True)

    # Special case: no splitting needed
    if split_number == 1:
        os.symlink(bed_file.absolute(), split_out_dir / bed_file.name)
        logger.info(f"Created symlink for single split: {split_out_dir / bed_file.name}")
        return

    # Read and process BED file
    bed_df = pd.read_table(bed_file, header=None, names=["chrom", "start", "end"])
    bed_df["region_length"] = bed_df["end"] - bed_df["start"]

    total_length = bed_df["region_length"].sum()
    length_per_file = total_length // split_number

    # Calculate padding for output filenames
    prefix_padding = _calculate_padding_width(split_number)

    # Split regions into files
    current_regions: List[BedRegion] = []
    current_length = 0
    file_index = 0

    for row in bed_df.itertuples(index=False):
        if current_length > length_per_file and current_regions:
            file_index += 1
            prefix = str(file_index).zfill(prefix_padding)
            _save_bed_regions(current_regions, split_out_dir, prefix)
            current_regions = []
            current_length = 0

        current_length += row.region_length
        current_regions.append(BedRegion(chrom=str(row.chrom), start=row.start, end=row.end))

    # Save remaining regions
    if current_regions:
        file_index += 1
        prefix = str(file_index).zfill(prefix_padding)
        _save_bed_regions(current_regions, split_out_dir, prefix)

    logger.info(f"Split BED file into {file_index} files in {split_out_dir}")


def _calculate_split_length(genome_length: int, split_number: int) -> int:
    """Calculate the length for each split based on genome length.

    Round down to a nice round number based on the magnitude of the split length.

    Args:
        genome_length: Total length of the genome
        split_number: Number of splits

    Returns:
        Calculated split length rounded to a nice number
    """
    raw_length = genome_length // split_number
    magnitude = 10 ** math.floor(math.log10(raw_length))
    multiplier = raw_length // magnitude
    return int(multiplier * magnitude)


def split_fai(fai_file: Path, out_dir: Path, split_number: int) -> None:
    """Split genome based on FAI file into BED regions.

    Args:
        fai_file: Path to the FAI (FASTA index) file
        out_dir: Output directory
        split_number: Number of files to split into

    Raises:
        ValueError: If output directory already exists
        FileNotFoundError: If input FAI file does not exist
    """
    if not fai_file.exists():
        raise FileNotFoundError(f"FAI file not found: {fai_file}")

    split_out_dir = out_dir / "genome"
    if split_out_dir.exists():
        raise ValueError(f"Output directory already exists: {split_out_dir}")

    split_out_dir.mkdir(parents=True)

    # Read FAI file
    fai_df = pd.read_table(fai_file, header=None, names=["chrom", "chrom_length"], usecols=[0, 1])

    genome_length = fai_df["chrom_length"].sum()
    split_length = _calculate_split_length(genome_length, split_number)
    step = split_length // STEP_DIVISOR

    # Calculate padding for output filenames
    prefix_padding = _calculate_padding_width(split_number)

    # Generate BED regions from FAI
    regions: List[BedRegion] = []
    current_length = 0
    file_index = 0

    for row in fai_df.itertuples(index=False):
        for pos in range(0, row.chrom_length, step):
            if current_length >= split_length and regions:
                file_index += 1
                prefix = str(file_index).zfill(prefix_padding)
                _save_bed_regions(regions, split_out_dir, prefix)
                regions = []
                current_length = 0

            end = min(pos + step, row.chrom_length)
            region_length = end - pos
            current_length += region_length

            # Merge consecutive regions on the same chromosome
            if regions and regions[-1].chrom == str(row.chrom):
                regions[-1].end = end
            else:
                regions.append(BedRegion(chrom=str(row.chrom), start=pos, end=end))

    # Save remaining regions
    if regions:
        file_index += 1
        prefix = str(file_index).zfill(prefix_padding)
        _save_bed_regions(regions, split_out_dir, prefix)

    logger.info(f"Split genome into {file_index} files in {split_out_dir}")


@app.command()
def split(
    bed_fai: Annotated[
        Path, typer.Argument(..., exists=True, help="Input BED or FAI file to split")
    ],
    out_path: Annotated[Path, typer.Argument(..., help="Output directory for split files")],
    split_number: Annotated[
        int, typer.Option("--split-number", "-n", help="Number of files to split into")
    ] = DEFAULT_SPLIT_NUMBER,
    is_bed: Annotated[
        bool, typer.Option("--bed/--fai", help="Input file type: BED (default) or FAI")
    ] = True,
) -> None:
    """Split BED or FAI files into multiple files by total length.

    This tool splits genomic files into multiple parts of approximately equal size.
    For BED files, it splits by total region length. For FAI files, it generates
    BED regions from the genome sequence lengths.

    Examples:

        # Split a BED file into 400 parts
        tc-split-bed-fai-by-number input.bed output_dir

        # Split an FAI file into 200 parts
        tc-split-bed-fai-by-number genome.fai output_dir --fai --split-number 200
    """
    try:
        if is_bed:
            logger.info(f"Splitting BED file: {bed_fai}")
            split_bed(bed_file=bed_fai, out_dir=out_path, split_number=split_number)
        else:
            logger.info(f"Splitting FAI file: {bed_fai}")
            split_fai(fai_file=bed_fai, out_dir=out_path, split_number=split_number)
        logger.success("Split completed successfully")
    except Exception as e:
        logger.error(f"Error during split: {e}")
        raise


def main() -> None:
    """Entry point for console script."""
    app()


if __name__ == "__main__":
    main()
