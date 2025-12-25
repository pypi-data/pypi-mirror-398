#!/usr/bin/env python3
"""Convert a table with chrom, pos, refer, alt columns to VCF format.

This script converts a simple table format to VCF (Variant Call Format) file.
The input table should contain at least four columns: chrom, pos, refer, alt.
Uses pandas with chunked reading to handle large files efficiently.
"""

import sys
from collections.abc import Iterable
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, TextIO

import pandas as pd
import typer
from tqdm import tqdm


class DedupeMode(str, Enum):
    chunk = "chunk"
    adjacent = "adjacent"
    global_ = "global"


app = typer.Typer(help="Convert table to VCF format")


REQUIRED_INPUT_COLUMNS = ("chrom", "pos", "refer", "alt")


def _normalize_columns(columns: pd.Index) -> list[str]:
    return [str(col).strip().lower() for col in columns]


def _validate_required_columns(
    *, normalized_columns: list[str], original_columns: list[str]
) -> None:
    duplicates = sorted({c for c in normalized_columns if normalized_columns.count(c) > 1})
    if duplicates:
        typer.echo(
            "Error: Duplicate column names after normalization: " + ", ".join(duplicates),
            err=True,
        )
        typer.echo("Available columns: " + ", ".join(original_columns), err=True)
        raise typer.Exit(1)

    required: set[str] = set(REQUIRED_INPUT_COLUMNS)
    missing = sorted(required - set(normalized_columns))
    if missing:
        typer.echo(
            "Error: Missing required columns: " + ", ".join(missing),
            err=True,
        )
        typer.echo("Available columns: " + ", ".join(original_columns), err=True)
        raise typer.Exit(1)


def write_vcf_header(
    output: TextIO,
    reference: str = "unknown",
    source: str = "table2vcf",
    contigs: Iterable[str] | None = None,
) -> None:
    """Write VCF header.

    Args:
        output: Output file handle
        reference: Reference genome name
        source: Source of the variants
    """
    today = datetime.now().strftime("%Y%m%d")
    output.write("##fileformat=VCFv4.2\n")
    output.write(f"##fileDate={today}\n")
    output.write(f"##source={source}\n")
    output.write(f"##reference={reference}\n")
    if contigs is not None:
        for contig in contigs:
            if contig:
                output.write(f"##contig=<ID={contig}>\n")
    output.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n")


def _collect_contigs(
    *, input_file: Path, delimiter: str, chunksize: int, progress: bool
) -> list[str]:
    contigs: set[str] = set()

    # Read only the chrom column in chunks (case/whitespace-insensitive column match)
    chunks = pd.read_csv(
        input_file,
        sep=delimiter,
        header=0,
        chunksize=chunksize,
        dtype=str,
        keep_default_na=False,
        usecols=lambda c: str(c).strip().lower() == "chrom",
    )

    disable_progress = (not progress) or (not sys.stderr.isatty())
    for chunk in tqdm(
        chunks,
        desc="Collecting contigs",
        unit="chunk",
        disable=disable_progress,
    ):
        if chunk.empty:
            continue
        chrom_series = chunk.iloc[:, 0].astype(str).str.strip()
        for value in chrom_series:
            if value:
                contigs.add(value)

    return sorted(contigs)


def parse_and_convert(
    input_file: Path,
    output_file: Path,
    delimiter: str = "\t",
    reference: str = "unknown",
    chunksize: int = 10000,
    progress: bool = True,
    dedupe: bool = False,
    dedupe_mode: DedupeMode = DedupeMode.chunk,
) -> None:
    """Parse table and convert to VCF using pandas with chunked reading.

    Args:
        input_file: Input table file
        output_file: Output VCF file
        delimiter: Column delimiter
        reference: Reference genome name
        chunksize: Number of rows to read at a time

    Raises:
        typer.Exit: If required columns are missing
    """
    # Validate headers (read only header row)
    try:
        header_df = pd.read_csv(
            input_file,
            sep=delimiter,
            header=0,
            nrows=0,
            dtype=str,
            keep_default_na=False,
        )
        normalized_columns = _normalize_columns(header_df.columns)
        _validate_required_columns(
            normalized_columns=normalized_columns,
            original_columns=[str(c) for c in header_df.columns],
        )
    except pd.errors.EmptyDataError:
        typer.echo("Error: Input file is empty", err=True)
        raise typer.Exit(1) from None
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error reading file: {e}", err=True)
        raise typer.Exit(1) from e

    contigs = _collect_contigs(
        input_file=input_file,
        delimiter=delimiter,
        chunksize=chunksize,
        progress=progress,
    )

    with open(output_file, "w") as outfile:
        write_vcf_header(outfile, reference=reference, contigs=contigs)

        total_variants = 0
        skipped_variants = 0
        deduped_variants = 0

        last_key: tuple[str, int, str, str] | None = None
        seen_keys: set[tuple[str, int, str, str]] | None = (
            set() if dedupe and dedupe_mode == DedupeMode.global_ else None
        )

        # Read file in chunks
        try:
            chunks = pd.read_csv(
                input_file,
                sep=delimiter,
                header=0,
                chunksize=chunksize,
                dtype=str,
                keep_default_na=False,
            )

            disable_progress = (not progress) or (not sys.stderr.isatty())
            for chunk_num, chunk in enumerate(
                tqdm(chunks, desc="Converting", unit="chunk", disable=disable_progress),
                1,
            ):
                # Normalize column names
                chunk.columns = _normalize_columns(chunk.columns)

                # Select required columns and rename for VCF
                chunk_data = chunk[list(REQUIRED_INPUT_COLUMNS)].copy()
                chunk_data.columns = ["CHROM", "POS", "REF", "ALT"]

                # Strip whitespace
                for col in ["CHROM", "POS", "REF", "ALT"]:
                    chunk_data[col] = chunk_data[col].astype(str).str.strip()

                # Validate position is numeric
                chunk_data["POS"] = pd.to_numeric(chunk_data["POS"], errors="coerce")

                # Drop rows with invalid positions
                invalid_rows = chunk_data["POS"].isna().sum()
                if invalid_rows > 0:
                    skipped_variants += invalid_rows
                    typer.echo(
                        f"Warning: Chunk {chunk_num} has {invalid_rows} invalid positions, skipping",
                        err=True,
                    )

                chunk_data = chunk_data.dropna(subset=["POS"])

                # Convert POS to integer
                chunk_data["POS"] = chunk_data["POS"].astype(int)

                if dedupe:
                    before = len(chunk_data)
                    if dedupe_mode == DedupeMode.chunk:
                        chunk_data = chunk_data.drop_duplicates(
                            subset=["CHROM", "POS", "REF", "ALT"], keep="first"
                        )
                    elif dedupe_mode == DedupeMode.adjacent:
                        keys = list(
                            zip(
                                chunk_data["CHROM"].astype(str),
                                chunk_data["POS"].astype(int),
                                chunk_data["REF"].astype(str),
                                chunk_data["ALT"].astype(str),
                            )
                        )
                        if keys:
                            keep_mask = [True] * len(keys)
                            prev = last_key
                            for i, k in enumerate(keys):
                                if prev is not None and k == prev:
                                    keep_mask[i] = False
                                prev = k
                            last_key = keys[-1]
                            chunk_data = chunk_data.loc[keep_mask]
                    else:  # global
                        assert seen_keys is not None
                        keys = list(
                            zip(
                                chunk_data["CHROM"].astype(str),
                                chunk_data["POS"].astype(int),
                                chunk_data["REF"].astype(str),
                                chunk_data["ALT"].astype(str),
                            )
                        )
                        keep_mask = [True] * len(keys)
                        for i, k in enumerate(keys):
                            if k in seen_keys:
                                keep_mask[i] = False
                            else:
                                seen_keys.add(k)
                        chunk_data = chunk_data.loc[keep_mask]

                    deduped_variants += before - len(chunk_data)

                # Add missing VCF columns
                chunk_data["ID"] = "."
                chunk_data["QUAL"] = "."
                chunk_data["FILTER"] = "."
                chunk_data["INFO"] = "."

                # Reorder columns for VCF format
                chunk_data = chunk_data[
                    ["CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO"]
                ]

                # Write to file
                chunk_data.to_csv(outfile, sep="\t", header=False, index=False)

                total_variants += len(chunk_data)
                if disable_progress:
                    typer.echo(
                        f"Processed chunk {chunk_num}: {len(chunk_data)} variants",
                        err=False,
                    )

        except Exception as e:
            typer.echo(f"Error reading file: {e}", err=True)
            raise typer.Exit(1) from e

        typer.echo(
            f"Total variants written: {total_variants}, skipped: {skipped_variants}, deduped: {deduped_variants}",
            err=False,
        )


@app.command()
def main(
    input_file: Path = typer.Argument(
        ...,
        help="Input table file with chrom, pos, refer, alt columns (header required)",
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output VCF file (default: <input>.vcf)"
    ),
    delimiter: str = typer.Option("\t", "--delimiter", "-d", help="Column delimiter"),
    reference: str = typer.Option("unknown", "--reference", "-r", help="Reference genome name"),
    chunksize: int = typer.Option(
        10000, "--chunksize", "-c", help="Number of rows to read at a time"
    ),
    progress: bool = typer.Option(
        True,
        "--progress/--no-progress",
        help="Show tqdm progress (auto-disabled when not a TTY)",
    ),
    dedupe: bool = typer.Option(
        False,
        "--dedupe/--no-dedupe",
        help="Remove duplicate variants (see --dedupe-mode)",
    ),
    dedupe_mode: DedupeMode = typer.Option(
        DedupeMode.chunk,
        "--dedupe-mode",
        help="Dedupe strategy: chunk (within-chunk), adjacent (consecutive duplicates), global (all seen; uses RAM)",
    ),
) -> None:
    """Convert table with chrom, pos, refer, alt columns to VCF format.

    The input file must have a header line with the following columns:
    - chrom: chromosome name
    - pos: position (integer)
    - refer: reference allele
    - alt: alternate allele

    Column names are matched case-insensitively and with surrounding whitespace ignored.
    """
    if not input_file.exists():
        typer.echo(f"Error: Input file '{input_file}' not found", err=True)
        raise typer.Exit(1)

    if output_file is None:
        output_file = input_file.with_suffix(".vcf")

    typer.echo(f"Converting {input_file} to {output_file}")
    typer.echo(f"Using chunksize: {chunksize}")

    parse_and_convert(
        input_file=input_file,
        output_file=output_file,
        delimiter=delimiter,
        reference=reference,
        chunksize=chunksize,
        progress=progress,
        dedupe=dedupe,
        dedupe_mode=dedupe_mode,
    )


if __name__ == "__main__":
    app()
