import pandas as pd
import pytest

from liftover.liftover_flank_and_site import (
    CIGAR_TAG_PATTERN,
    NM_TAG_PATTERN,
    AlignmentProcessor,
    CigarOperation,
    calculate_genomic_position,
    calculate_indel_bias,
    calculate_offsets,
    convert_vcf_to_bed,
    extract_alleles,
    extract_tag_value,
    parse_cigar,
    parse_paf_tags,
    probe_sequence_from_flank,
)


def test_extract_alleles() -> None:
    assert extract_alleles("AAA[C/T]CCC") == "C/T"
    assert extract_alleles("no allele info") == "-/-"


def test_parse_cigar_valid_and_invalid() -> None:
    assert parse_cigar("3M1I4M2D5M") == [
        CigarOperation(3, "M"),
        CigarOperation(1, "I"),
        CigarOperation(4, "M"),
        CigarOperation(2, "D"),
        CigarOperation(5, "M"),
    ]
    with pytest.raises(ValueError):
        parse_cigar("")
    with pytest.raises(ValueError):
        parse_cigar("3Z")


def test_calculate_indel_bias_handles_bias_and_short_reads() -> None:
    assert calculate_indel_bias("2M1D4M", offset_limit=4) == 1
    assert calculate_indel_bias("2M1D4M", offset_limit=2) is None


def test_calculate_genomic_position_applies_indel_bias() -> None:
    assert calculate_genomic_position(100, offset_target=3, probe_start=10, indel_bias=-1) == 93


def test_probe_sequence_from_flank() -> None:
    assert probe_sequence_from_flank("AAA[C/T]GGG") == "AAACGGG"
    with pytest.raises(ValueError):
        probe_sequence_from_flank("invalid")


def test_extract_tag_value_and_parse_paf_tags(tmp_path) -> None:
    line = "q1\t0\t0\t0\t+\tt1\t0\t0\t0\t0\t0\t0\tNM:i:2\tcg:Z:3M1I2M"
    assert extract_tag_value(line, NM_TAG_PATTERN) == "2"
    assert extract_tag_value(line, CIGAR_TAG_PATTERN) == "3M1I2M"

    paf_path = tmp_path / "example.paf"
    paf_path.write_text(
        "\n".join(
            [
                line,
                "q2\t0\t0\t0\t+\tt1\t0\t0\t0\t0\t0\t0\tNM:i:1\tcg:Z:5M",
                "bad line without tags",
                "",
            ]
        ),
        encoding="utf-8",
    )
    tags_df = parse_paf_tags(paf_path)
    assert list(tags_df["cigar"]) == ["3M1I2M", "5M"]
    assert list(tags_df["n_mismatch"]) == [2, 1]


def test_filter_best_alignments_respects_match_length_and_mismatches() -> None:
    df = pd.DataFrame(
        {
            "id": ["a", "a", "a"],
            "match_length": [10, 10, 8],
            "n_mismatch": [2, 1, 1],
        }
    )
    processor = AlignmentProcessor()
    filtered = processor.filter_best_alignments(df)
    assert list(filtered["id"]) == ["a"]
    assert list(filtered["n_mismatch"]) == [1]

    duplicate_df = pd.DataFrame({"id": ["a", "a"], "match_length": [10, 10], "n_mismatch": [1, 1]})
    kept = processor.filter_best_alignments(duplicate_df, keep_duplicates=True)
    assert len(kept) == 2


def test_filter_by_match_quality() -> None:
    df = pd.DataFrame({"match_length": [9, 7], "probe_length": [10, 10]})
    processor = AlignmentProcessor()
    filtered = processor.filter_by_match_quality(df, cutoff=0.8)
    assert list(filtered["match_length"]) == [9]


def test_calculate_positions_and_add_identifiers() -> None:
    processor = AlignmentProcessor()
    df = pd.DataFrame(
        [
            {
                "cigar": "2M1D4M",
                "offset_start": 4,
                "offset_end": 0,
                "strand": "+",
                "match_start": 100,
                "probe_start": 0,
                "chrom": "chr1",
            },
            {
                "cigar": "2M1D4M",
                "offset_start": 2,
                "offset_end": 0,
                "strand": "+",
                "match_start": 100,
                "probe_start": 0,
                "chrom": "chr1",
            },
        ]
    )
    positions = processor.calculate_positions(df)
    assert list(positions["pos"]) == [106]

    identifiers = processor.add_identifiers(positions)
    assert identifiers.iloc[0]["new_id"] == "chr1_106"
    assert identifiers.iloc[0]["pos_0"] == 105


def test_full_process_pipeline_respects_cutoff() -> None:
    processor = AlignmentProcessor()
    paf_df = pd.DataFrame(
        {
            "id": ["probe1", "probe2"],
            "probe_length": [10, 10],
            "probe_start": [0, 0],
            "strand": ["+", "-"],
            "chrom": ["chr1", "chr2"],
            "match_start": [100, 200],
            "match_length": [10, 8],
            "mapq": [60, 60],
        }
    )
    tags_df = pd.DataFrame({"cigar": ["10M", "8M"], "n_mismatch": [0, 1]})
    full_df = pd.concat([paf_df, tags_df], axis=1)

    offset_df = pd.DataFrame(
        {
            "id": ["probe1", "probe2"],
            "offset_start": [3, 2],
            "offset_end": [6, 3],
        }
    )

    result = processor.process(full_df, offset_df, match_cutoff=0.9)
    assert list(result["id"]) == ["probe1"]
    assert list(result["new_id"]) == ["chr1_104"]


def test_convert_vcf_to_bed(tmp_path) -> None:
    vcf_path = tmp_path / "input.vcf"
    vcf_path.write_text("##header\nchr1\t10\nchr2\t20\n", encoding="utf-8")
    output_bed = tmp_path / "output.bed"

    convert_vcf_to_bed(vcf_path, output_bed)

    lines = output_bed.read_text(encoding="utf-8").splitlines()
    assert lines == ["chr1\t9\t10\tchr1_10", "chr2\t19\t20\tchr2_20"]


def test_calculate_offsets(tmp_path) -> None:
    target_bed = tmp_path / "target.bed"
    flank_bed = tmp_path / "flank.bed"

    target_bed.write_text("chr1\t9\t10\tid1\n", encoding="utf-8")
    flank_bed.write_text("chr1\t4\t14\tid1\n", encoding="utf-8")

    offsets = calculate_offsets(target_bed, flank_bed)
    assert offsets.to_dict(orient="list") == {
        "id": ["id1"],
        "offset_start": [5],
        "offset_end": [4],
    }
