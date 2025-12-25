#!/usr/bin/env python3
"""
Rename chromosome IDs in genome FASTA and GFF files.

Supports three modes:
- NGDC: Extracts OriSeqID from NGDC FASTA headers
- NCBI: Auto-downloads assembly_report.txt from FASTA filename and extracts ID mapping
- Custom: Uses user-provided ID mapping file

Usage:
    # NGDC genome with OriSeqID
    tc-rename-genome-id ngdc -f genome.fasta -o output.fasta [-g input.gff -og output.gff]

    # NCBI genome (auto-download assembly report from FASTA filename)
    tc-rename-genome-id ncbi -f /path/to/GCF_016699485.2_bGalGal1.mat.broiler.GRCg7b_genomic.fna -o output.fasta

    # NCBI genome (with local assembly report)
    tc-rename-genome-id ncbi -f genome.fasta -o output.fasta -r assembly_report.txt

    # Custom ID mapping file
    tc-rename-genome-id custom -f genome.fasta -o output.fasta -m id_map.txt [-g input.gff -og output.gff]
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional

import requests
import typer
from typing_extensions import Annotated


def parse_fasta_header(header):
    """
    Parse FASTA header to extract ID and OriSeqID.

    Example header:
    >GWHGECT00000001.1      Chromosome 1A   Complete=T      Circular=F      OriSeqID=Chr1A  Len=600907804

    Returns:
        tuple: (old_id, new_id) or (None, None) if OriSeqID not found
    """
    # Extract the first field (ID)
    parts = header.strip().split()
    if not parts:
        return None, None

    old_id = parts[0].lstrip(">")

    # Extract OriSeqID
    match = re.search(r"OriSeqID=(\S+)", header)
    if match:
        new_id = match.group(1)
        return old_id, new_id

    return None, None


def build_id_mapping(fasta_file):
    """
    Build a mapping dictionary from FASTA file (for NGDC genomes).

    Args:
        fasta_file: Path to input FASTA file

    Returns:
        dict: Mapping from old IDs to new IDs
    """
    id_map = {}

    with open(fasta_file) as f:
        for line in f:
            if line.startswith(">"):
                old_id, new_id = parse_fasta_header(line)
                if old_id and new_id:
                    id_map[old_id] = new_id

    return id_map


def load_id_mapping(map_file):
    """
    Load ID mapping from a tab-separated file.

    Args:
        map_file: Path to mapping file (format: old_id\\tnew_id)

    Returns:
        dict: Mapping from old IDs to new IDs
    """
    id_map = {}

    with open(map_file) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) != 2:
                print(
                    f"Warning: Skipping invalid line {line_num} in mapping file: {line}",
                    file=sys.stderr,
                )
                continue

            old_id, new_id = parts[0].strip(), parts[1].strip()
            if old_id and new_id:
                id_map[old_id] = new_id

    return id_map


def download_assembly_report(genome_filename: str, output_path: Optional[Path] = None) -> Path:
    """
    Download NCBI assembly_report.txt file by genome filename or accession.

    Args:
        genome_filename: Full genome filename (e.g., GCF_016699485.2_bGalGal1.mat.broiler.GRCg7b_genomic.fna.gz)
                        or just accession with assembly name (e.g., GCF_016699485.2_bGalGal1.mat.broiler.GRCg7b)
        output_path: Optional output file path. If not provided, saves to current directory.

    Returns:
        Path: Path to the downloaded assembly report file

    Raises:
        ValueError: If filename format is invalid
        requests.HTTPError: If download fails
    """
    typer.echo(f"Parsing genome filename: {genome_filename}", err=True)

    # Parse filename to extract the prefix before "_genomic"
    if "_genomic" in genome_filename:
        prefix_end = genome_filename.index("_genomic")
        full_prefix = genome_filename[:prefix_end]
    else:
        # Assume user provided the prefix directly (without _genomic suffix)
        full_prefix = genome_filename

    # Extract Assembly ID and Assembly Name
    parts = full_prefix.split("_", 2)
    if len(parts) < 3:
        raise ValueError(
            f"Invalid filename format. Expected format: GCF_XXXXXX.X_AssemblyName\n"
            f"Got: {genome_filename}"
        )

    assembly_prefix = parts[0]  # GCF or GCA
    assembly_number = parts[1]  # 016699485.2
    assembly_name_suffix = parts[2]  # bGalGal1.mat.broiler.GRCg7b

    # Build NCBI FTP directory path
    # NCBI structure: /genomes/all/GCF/016/699/485/GCF_016699485.2_xxx/
    number_base = assembly_number.split(".")[0]  # Remove version: 016699485

    if len(number_base) < 9:
        raise ValueError(f"Invalid assembly number format: {assembly_number}")

    # Split into three-digit groups
    dir1 = number_base[:3]  # 016
    dir2 = number_base[3:6]  # 699
    dir3 = number_base[6:9]  # 485

    # Construct full URL
    base_url = "https://ftp.ncbi.nlm.nih.gov/genomes/all"
    report_filename = f"{full_prefix}_assembly_report.txt"
    download_url = (
        f"{base_url}/{assembly_prefix}/{dir1}/{dir2}/{dir3}/{full_prefix}/{report_filename}"
    )

    typer.echo(f"Assembly: {assembly_prefix}_{assembly_number} ({assembly_name_suffix})", err=True)
    typer.echo(f"Downloading from: {download_url}", err=True)

    try:
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()

        # Determine output path
        if output_path is None:
            output_path = Path(report_filename)

        # Save file
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        file_size = os.path.getsize(output_path) / 1024
        typer.echo(f"✓ Downloaded {output_path} ({file_size:.2f} KB)", err=True)
        return output_path

    except requests.exceptions.HTTPError as e:
        typer.echo(
            f"✗ Failed to download (HTTP {e.response.status_code})",
            err=True,
        )
        typer.echo(f"  URL: {download_url}", err=True)
        typer.echo(
            "  Tip: Verify the filename format. Expected: GCF_XXXXXX.X_AssemblyName", err=True
        )
        raise


def extract_fasta_ids(fasta_file: Path) -> set:
    """
    Extract all sequence IDs from FASTA file.

    Args:
        fasta_file: Path to FASTA file

    Returns:
        set: Set of sequence IDs found in FASTA headers
    """
    ids = set()
    with open(fasta_file) as f:
        for line in f:
            if line.startswith(">"):
                # Extract first field as sequence ID
                parts = line.strip().split()
                if parts:
                    seq_id = parts[0].lstrip(">")
                    ids.add(seq_id)
    return ids


def auto_detect_old_col(report_file: Path, fasta_ids: set, new_id_col: int = 1) -> int:
    """
    Auto-detect which column in assembly report matches FASTA IDs.

    Args:
        report_file: Path to assembly_report.txt file
        fasta_ids: Set of sequence IDs from FASTA file
        new_id_col: Column index for new ID (1-indexed, to exclude from detection)

    Returns:
        int: Best matching column index (1-indexed), or 7 as default if no good match
    """
    # Columns to check (excluding the new_id_col)
    # Typical columns: 1=Sequence-Name, 5=GenBank-Accn, 7=RefSeq-Accn, 9=UCSC-style-name
    candidate_cols = [1, 5, 7, 9, 10]
    if new_id_col in candidate_cols:
        candidate_cols.remove(new_id_col)

    match_scores: dict[int, int] = {}

    # Read assembly report and count matches for each column
    with open(report_file) as f:
        for line in f:
            if line.startswith("#"):
                continue
            line = line.strip()
            if not line:
                continue

            fields = line.split("\t")

            for col in candidate_cols:
                if col > len(fields):
                    continue

                col_idx = col - 1
                value = fields[col_idx].strip()

                # Skip empty or 'na' values
                if not value or value == "na":
                    continue

                # Check if this value matches any FASTA ID
                if value in fasta_ids:
                    match_scores[col] = match_scores.get(col, 0) + 1

    # Find column with highest match count
    if match_scores:
        best_col = max(match_scores, key=lambda x: match_scores[x])
        best_score = match_scores[best_col]
        typer.echo(f"Auto-detected old_col={best_col} with {best_score} matches", err=True)
        typer.echo(f"Match scores: {match_scores}", err=True)
        return best_col

    # Default to RefSeq-Accn (column 7) if no matches found
    typer.echo("Warning: No column auto-detected, using default old_col=7 (RefSeq-Accn)", err=True)
    return 7


def parse_assembly_report(report_file: Path, old_id_col: int = 7, new_id_col: int = 1) -> dict:
    """
    Parse NCBI assembly_report.txt to extract ID mapping.

    Args:
        report_file: Path to assembly_report.txt file
        old_id_col: Column index for old ID (1-indexed, default 7 for RefSeq-Accn)
        new_id_col: Column index for new ID (1-indexed, default 1 for Sequence-Name)

    Returns:
        dict: Mapping from old IDs to new IDs
    """
    id_map = {}

    # Convert to 0-indexed
    old_idx = old_id_col - 1
    new_idx = new_id_col - 1

    with open(report_file) as f:
        for line in f:
            # Skip comments and headers
            if line.startswith("#"):
                continue

            line = line.strip()
            if not line:
                continue

            fields = line.split("\t")

            # Validate column indices
            max_idx = max(old_idx, new_idx)
            if len(fields) <= max_idx:
                continue

            old_id = fields[old_idx].strip()
            new_id = fields[new_idx].strip()

            # Skip empty or 'na' values
            if old_id and new_id and old_id != "na" and new_id != "na":
                id_map[old_id] = new_id

    return id_map


def rename_fasta(input_fasta, output_fasta, id_map):
    """
    Rename chromosome IDs in FASTA file.

    Args:
        input_fasta: Path to input FASTA file
        output_fasta: Path to output FASTA file
        id_map: Dictionary mapping old IDs to new IDs
    """
    with open(input_fasta) as infile, open(output_fasta, "w") as outfile:
        for line in infile:
            if line.startswith(">"):
                # Try to extract the first field as the sequence ID
                parts = line.strip().split()
                if parts:
                    seq_id = parts[0].lstrip(">")
                    if seq_id in id_map:
                        # Write simplified header with just the new ID
                        outfile.write(f">{id_map[seq_id]}\n")
                    else:
                        # If no mapping, try parsing as NGDC format
                        old_id, new_id = parse_fasta_header(line)
                        if old_id and new_id and old_id in id_map:
                            outfile.write(f">{new_id}\n")
                        else:
                            # Keep original header if no mapping found
                            outfile.write(line)
                else:
                    # Keep original header if parsing fails
                    outfile.write(line)
            else:
                outfile.write(line)


def rename_gff(input_gff, output_gff, id_map):
    """
    Rename chromosome IDs in GFF file.

    Args:
        input_gff: Path to input GFF file
        output_gff: Path to output GFF file
        id_map: Dictionary mapping old IDs to new IDs
    """
    with open(input_gff) as infile, open(output_gff, "w") as outfile:
        for line in infile:
            # Skip comment lines
            if line.startswith("#"):
                outfile.write(line)
                continue

            # Skip empty lines
            if not line.strip():
                outfile.write(line)
                continue

            # Process GFF lines
            fields = line.split("\t")
            if len(fields) >= 1:
                chrom = fields[0]
                if chrom in id_map:
                    fields[0] = id_map[chrom]
                outfile.write("\t".join(fields))
            else:
                outfile.write(line)


def main():
    app()


app = typer.Typer(help="Rename chromosome IDs in genome FASTA and GFF files")


@app.command()
def ngdc(
    fasta: Annotated[Path, typer.Option("-f", "--fasta", help="Input FASTA file")],
    output: Annotated[Path, typer.Option("-o", "--output", help="Output FASTA file")],
    gff: Annotated[
        Optional[Path], typer.Option("-g", "--gff", help="Input GFF file (optional)")
    ] = None,
    output_gff: Annotated[
        Optional[Path],
        typer.Option("-og", "--output-gff", help="Output GFF file (optional)"),
    ] = None,
):
    """
    Rename chromosome IDs using NGDC OriSeqID from FASTA headers.

    This command extracts OriSeqID values from NGDC FASTA headers and uses them
    to rename chromosome IDs in both FASTA and GFF files.
    """
    # Check GFF arguments consistency
    if gff and not output_gff:
        typer.echo("Error: --output-gff is required when --gff is specified", err=True)
        raise typer.Exit(1)
    if output_gff and not gff:
        typer.echo("Error: --gff is required when --output-gff is specified", err=True)
        raise typer.Exit(1)

    # Build ID mapping from FASTA
    typer.echo(f"Building ID mapping from {fasta} (OriSeqID)...", err=True)
    id_map = build_id_mapping(fasta)
    typer.echo(f"Found {len(id_map)} chromosome mappings", err=True)

    for old_id, new_id in sorted(id_map.items()):
        typer.echo(f"  {old_id} -> {new_id}", err=True)

    # Rename FASTA
    typer.echo(f"Renaming FASTA file to {output}...", err=True)
    rename_fasta(fasta, output, id_map)

    # Rename GFF if specified
    if gff:
        typer.echo(f"Renaming GFF file to {output_gff}...", err=True)
        rename_gff(gff, output_gff, id_map)

    typer.echo("Done!", err=True)


@app.command()
def ncbi(
    fasta: Annotated[
        Path,
        typer.Option(
            "-f",
            "--fasta",
            help="Input FASTA file (e.g., GCF_016699485.2_bGalGal1.mat.broiler.GRCg7b_genomic.fna)",
        ),
    ],
    output: Annotated[Path, typer.Option("-o", "--output", help="Output FASTA file")],
    report: Annotated[
        Optional[Path],
        typer.Option(
            "-r",
            "--report",
            help="Local assembly_report.txt file (optional, will auto-download from FASTA filename if not provided)",
        ),
    ] = None,
    old_col: Annotated[
        Optional[int],
        typer.Option(
            "--old-col",
            help="Column index for old ID (1-indexed). If not specified, auto-detects by matching FASTA IDs with assembly report columns",
        ),
    ] = None,
    new_col: Annotated[
        int,
        typer.Option(
            "--new-col",
            help="Column index for new ID (1-indexed, default: 1 for Sequence-Name)",
        ),
    ] = 1,
    gff: Annotated[
        Optional[Path], typer.Option("-g", "--gff", help="Input GFF file (optional)")
    ] = None,
    output_gff: Annotated[
        Optional[Path],
        typer.Option("-og", "--output-gff", help="Output GFF file (optional)"),
    ] = None,
):
    """
    Rename chromosome IDs using NCBI assembly_report.txt.

    The assembly report will be auto-downloaded based on the FASTA filename.
    FASTA filename should follow NCBI format: GCF_XXXXXX.X_AssemblyName_genomic.fna[.gz]

    Example: GCF_016699485.2_bGalGal1.mat.broiler.GRCg7b_genomic.fna

    Alternatively, provide --report to use a local assembly_report.txt file.

    By default, the tool auto-detects which column in the assembly report matches
    the FASTA IDs. You can override this with --old-col.

    Column indices (1-indexed):
      1 = Sequence-Name (e.g., 1, 2, X, MT)
      5 = GenBank-Accn (e.g., CM028482.1)
      7 = RefSeq-Accn (e.g., NC_052532.1)
      9 = UCSC-style-name
    """
    # Check GFF arguments consistency
    if gff and not output_gff:
        typer.echo("Error: --output-gff is required when --gff is specified", err=True)
        raise typer.Exit(1)
    if output_gff and not gff:
        typer.echo("Error: --gff is required when --output-gff is specified", err=True)
        raise typer.Exit(1)

    # Get assembly report file
    if report:
        report_file = report
        typer.echo(f"Using local assembly report: {report_file}", err=True)
    else:
        # Extract genome name from FASTA filename and download assembly report
        genome_filename = fasta.name
        typer.echo(f"Extracting genome name from: {genome_filename}", err=True)

        try:
            report_file = download_assembly_report(genome_filename)
        except Exception as e:
            typer.echo(f"Error downloading assembly report: {e}", err=True)
            typer.echo(
                "Tip: Ensure FASTA filename follows NCBI format (GCF_XXXXXX.X_AssemblyName_genomic.fna)",
                err=True,
            )
            typer.echo(
                "     Or provide a local assembly report with --report",
                err=True,
            )
            raise typer.Exit(1) from e

    # Auto-detect old_col if not specified
    if old_col is None:
        typer.echo("Auto-detecting old_col by matching FASTA IDs...", err=True)
        fasta_ids = extract_fasta_ids(fasta)
        typer.echo(f"Found {len(fasta_ids)} sequences in FASTA file", err=True)
        old_col = auto_detect_old_col(report_file, fasta_ids, new_col)

    # Parse assembly report
    typer.echo(f"Parsing assembly report (old_col={old_col}, new_col={new_col})...", err=True)
    id_map = parse_assembly_report(report_file, old_col, new_col)
    typer.echo(f"Found {len(id_map)} chromosome mappings", err=True)

    for old_id, new_id in sorted(id_map.items()):
        typer.echo(f"  {old_id} -> {new_id}", err=True)

    # Rename FASTA
    typer.echo(f"Renaming FASTA file to {output}...", err=True)
    rename_fasta(fasta, output, id_map)

    # Rename GFF if specified
    if gff:
        typer.echo(f"Renaming GFF file to {output_gff}...", err=True)
        rename_gff(gff, output_gff, id_map)

    typer.echo("Done!", err=True)


@app.command()
def custom(
    fasta: Annotated[Path, typer.Option("-f", "--fasta", help="Input FASTA file")],
    output: Annotated[Path, typer.Option("-o", "--output", help="Output FASTA file")],
    id_map: Annotated[
        Path,
        typer.Option("-m", "--map", help="ID mapping file (tab-separated: old_id\\tnew_id)"),
    ],
    gff: Annotated[
        Optional[Path], typer.Option("-g", "--gff", help="Input GFF file (optional)")
    ] = None,
    output_gff: Annotated[
        Optional[Path],
        typer.Option("-og", "--output-gff", help="Output GFF file (optional)"),
    ] = None,
):
    """
    Rename chromosome IDs using a custom ID mapping file.

    The mapping file should be tab-separated with format: old_id\\tnew_id
    Lines starting with # are treated as comments and empty lines are ignored.
    """
    # Check GFF arguments consistency
    if gff and not output_gff:
        typer.echo("Error: --output-gff is required when --gff is specified", err=True)
        raise typer.Exit(1)
    if output_gff and not gff:
        typer.echo("Error: --gff is required when --output-gff is specified", err=True)
        raise typer.Exit(1)

    # Load ID mapping from file
    typer.echo(f"Loading ID mapping from {id_map}...", err=True)
    mapping = load_id_mapping(id_map)
    typer.echo(f"Loaded {len(mapping)} chromosome mappings", err=True)

    for old_id, new_id in sorted(mapping.items()):
        typer.echo(f"  {old_id} -> {new_id}", err=True)

    # Rename FASTA
    typer.echo(f"Renaming FASTA file to {output}...", err=True)
    rename_fasta(fasta, output, mapping)

    # Rename GFF if specified
    if gff:
        typer.echo(f"Renaming GFF file to {output_gff}...", err=True)
        rename_gff(gff, output_gff, mapping)

    typer.echo("Done!", err=True)


if __name__ == "__main__":
    main()
