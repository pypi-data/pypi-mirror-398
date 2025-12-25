from __future__ import annotations

from pathlib import Path

import pytest
import typer

from vcf.table2vcf import DedupeMode, parse_and_convert


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def test_missing_required_columns_raises(tmp_path: Path) -> None:
    input_path = tmp_path / "in.tsv"
    output_path = tmp_path / "out.vcf"

    _write_text(
        input_path,
        "chrom\tpos\trefer\nchr1\t1\tA\n",
    )

    with pytest.raises(typer.Exit):
        parse_and_convert(input_file=input_path, output_file=output_path)


def test_header_normalization_case_whitespace(tmp_path: Path) -> None:
    input_path = tmp_path / "in.tsv"
    output_path = tmp_path / "out.vcf"

    _write_text(
        input_path,
        " Chrom \t POS\t Refer\tALT \nchr1\t1\tA\tT\n",
    )

    parse_and_convert(input_file=input_path, output_file=output_path, chunksize=1)

    lines = _read_lines(output_path)
    assert lines[0].startswith("##fileformat=VCFv4.2")
    assert "##contig=<ID=chr1>" in lines
    assert lines[-2].startswith("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO")
    assert lines[-1].split("\t")[:5] == ["chr1", "1", ".", "A", "T"]


def test_convert_skips_invalid_pos_and_writes_variants(tmp_path: Path) -> None:
    input_path = tmp_path / "in.tsv"
    output_path = tmp_path / "out.vcf"

    _write_text(
        input_path,
        "chrom\tpos\trefer\talt\nchr1\t1\tA\tT\nchr1\tabc\tC\tG\n chr2 \t 2 \t G \t A \n",
    )

    parse_and_convert(input_file=input_path, output_file=output_path, chunksize=2)

    lines = _read_lines(output_path)

    assert "##contig=<ID=chr1>" in lines
    assert "##contig=<ID=chr2>" in lines

    header_idx = lines.index("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO")
    variants = lines[header_idx + 1 :]

    # invalid POS dropped
    assert len(variants) == 2

    variant1 = variants[0].split("\t")
    variant2 = variants[1].split("\t")

    assert variant1 == ["chr1", "1", ".", "A", "T", ".", ".", "."]
    assert variant2 == ["chr2", "2", ".", "G", "A", ".", ".", "."]


def test_chunksize_one_processes_multiple_chunks(tmp_path: Path) -> None:
    input_path = tmp_path / "in.tsv"
    output_path = tmp_path / "out.vcf"

    _write_text(
        input_path,
        "chrom\tpos\trefer\talt\nchr1\t1\tA\tT\nchr1\t2\tC\tG\nchr2\t3\tG\tA\n",
    )

    parse_and_convert(input_file=input_path, output_file=output_path, chunksize=1)

    lines = _read_lines(output_path)
    assert "##contig=<ID=chr1>" in lines
    assert "##contig=<ID=chr2>" in lines

    header_idx = lines.index("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO")
    variants = lines[header_idx + 1 :]

    assert len(variants) == 3
    assert variants[0].split("\t")[:5] == ["chr1", "1", ".", "A", "T"]
    assert variants[1].split("\t")[:5] == ["chr1", "2", ".", "C", "G"]
    assert variants[2].split("\t")[:5] == ["chr2", "3", ".", "G", "A"]


def test_contig_header_includes_nonstandard_ids(tmp_path: Path) -> None:
    input_path = tmp_path / "in.tsv"
    output_path = tmp_path / "out.vcf"

    _write_text(
        input_path,
        "chrom\tpos\trefer\talt\n1A\t10\tA\tT\n",
    )

    parse_and_convert(input_file=input_path, output_file=output_path, chunksize=1)

    lines = _read_lines(output_path)
    assert "##contig=<ID=1A>" in lines


def test_dedupe_chunk_removes_duplicates_within_chunk(tmp_path: Path) -> None:
    input_path = tmp_path / "in.tsv"
    output_path = tmp_path / "out.vcf"

    _write_text(
        input_path,
        "chrom\tpos\trefer\talt\nchr1\t1\tA\tT\nchr1\t1\tA\tT\nchr1\t2\tC\tG\n",
    )

    parse_and_convert(
        input_file=input_path,
        output_file=output_path,
        chunksize=10,
        progress=False,
        dedupe=True,
        dedupe_mode=DedupeMode.chunk,
    )

    lines = _read_lines(output_path)
    header_idx = lines.index("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO")
    variants = lines[header_idx + 1 :]
    assert len(variants) == 2


def test_dedupe_adjacent_only_removes_consecutive_duplicates(tmp_path: Path) -> None:
    input_path = tmp_path / "in.tsv"
    output_path = tmp_path / "out.vcf"

    _write_text(
        input_path,
        "chrom\tpos\trefer\talt\nchr1\t1\tA\tT\nchr1\t1\tA\tT\nchr1\t2\tC\tG\nchr1\t1\tA\tT\n",
    )

    parse_and_convert(
        input_file=input_path,
        output_file=output_path,
        chunksize=2,
        progress=False,
        dedupe=True,
        dedupe_mode=DedupeMode.adjacent,
    )

    lines = _read_lines(output_path)
    header_idx = lines.index("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO")
    variants = lines[header_idx + 1 :]

    # Only the second consecutive duplicate is removed; later same variant remains.
    assert len(variants) == 3
