"""Tests for split_bed_fai_by_number module."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from genome.split_bed_fai_by_number import (
    BedRegion,
    _calculate_padding_width,
    _calculate_split_length,
    _generate_output_filename,
    _save_bed_regions,
    split_bed,
    split_fai,
)


class TestBedRegion(unittest.TestCase):
    """Test BedRegion dataclass."""

    def test_bed_region_creation(self):
        """Test creating a BedRegion."""
        region = BedRegion(chrom="chr1", start=100, end=200)
        self.assertEqual(region.chrom, "chr1")
        self.assertEqual(region.start, 100)
        self.assertEqual(region.end, 200)

    def test_bed_region_length(self):
        """Test BedRegion length property."""
        region = BedRegion(chrom="chr1", start=100, end=250)
        self.assertEqual(region.length, 150)

    def test_bed_region_str(self):
        """Test BedRegion string representation."""
        region = BedRegion(chrom="chr2", start=500, end=1000)
        self.assertEqual(str(region), "chr2:500-1000")


class TestCalculatePaddingWidth(unittest.TestCase):
    """Test _calculate_padding_width function."""

    def test_padding_for_single_digit(self):
        """Test padding calculation for single digit numbers."""
        self.assertEqual(_calculate_padding_width(9), 1)

    def test_padding_for_two_digits(self):
        """Test padding calculation for two digit numbers."""
        self.assertEqual(_calculate_padding_width(10), 2)
        self.assertEqual(_calculate_padding_width(99), 2)

    def test_padding_for_three_digits(self):
        """Test padding calculation for three digit numbers."""
        self.assertEqual(_calculate_padding_width(100), 3)
        self.assertEqual(_calculate_padding_width(999), 3)

    def test_padding_for_zero(self):
        """Test padding calculation for zero."""
        self.assertEqual(_calculate_padding_width(0), 1)


class TestGenerateOutputFilename(unittest.TestCase):
    """Test _generate_output_filename function."""

    def test_single_chromosome_filename(self):
        """Test filename generation for regions on same chromosome."""
        regions = [
            BedRegion(chrom="chr1", start=100, end=200),
            BedRegion(chrom="chr1", start=200, end=300),
        ]
        filename = _generate_output_filename(regions, "01")
        self.assertEqual(filename, "01_chr1_100_300.bed")

    def test_multiple_chromosomes_filename(self):
        """Test filename generation for regions across different chromosomes."""
        regions = [
            BedRegion(chrom="chr1", start=100, end=200),
            BedRegion(chrom="chr2", start=0, end=100),
        ]
        filename = _generate_output_filename(regions, "02")
        self.assertEqual(filename, "02_chr1_100_chr2_100.bed")


class TestCalculateSplitLength(unittest.TestCase):
    """Test _calculate_split_length function."""

    def test_split_length_calculation(self):
        """Test split length calculation rounds to nice numbers."""
        # 1000000 / 10 = 100000 -> should return 100000
        result = _calculate_split_length(1000000, 10)
        self.assertEqual(result, 100000)

    def test_split_length_with_rounding(self):
        """Test split length with rounding down."""
        # 123456 / 5 = 24691 -> magnitude is 10000, multiplier is 2
        result = _calculate_split_length(123456, 5)
        self.assertEqual(result, 20000)

    def test_split_length_large_numbers(self):
        """Test split length with large numbers."""
        # 10000000 / 4 = 2500000 -> should return 2000000
        result = _calculate_split_length(10000000, 4)
        self.assertEqual(result, 2000000)


class TestSaveBedRegions(unittest.TestCase):
    """Test _save_bed_regions function."""

    def test_save_bed_regions(self):
        """Test saving BED regions to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            regions = [
                BedRegion(chrom="chr1", start=0, end=100),
                BedRegion(chrom="chr1", start=100, end=200),
            ]

            _save_bed_regions(regions, out_dir, "01")

            # Check file was created
            expected_file = out_dir / "01_chr1_0_200.bed"
            self.assertTrue(expected_file.exists())

            # Check file content
            df = pd.read_table(expected_file, header=None)
            self.assertEqual(len(df), 2)
            self.assertEqual(df.iloc[0, 0], "chr1")
            self.assertEqual(df.iloc[0, 1], 0)
            self.assertEqual(df.iloc[0, 2], 100)

    @patch("genome.split_bed_fai_by_number.logger")
    def test_save_empty_regions(self, mock_logger):
        """Test saving empty regions list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            _save_bed_regions([], out_dir, "01")

            # Check warning was logged
            mock_logger.warning.assert_called_once()


class TestSplitBed(unittest.TestCase):
    """Test split_bed function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_split_bed_file_not_found(self):
        """Test split_bed with non-existent file."""
        non_existent = self.test_dir / "non_existent.bed"
        with self.assertRaises(FileNotFoundError):
            split_bed(non_existent, self.test_dir, 2)

    def test_split_bed_output_exists(self):
        """Test split_bed when output directory exists."""
        # Create input file
        bed_file = self.test_dir / "test.bed"
        bed_file.write_text("chr1\t0\t100\n")

        # Create output directory
        out_dir = self.test_dir / "test"
        out_dir.mkdir()

        with self.assertRaises(ValueError):
            split_bed(bed_file, self.test_dir, 2)

    def test_split_bed_single_split(self):
        """Test split_bed with split_number=1 creates symlink."""
        bed_file = self.test_dir / "test.bed"
        bed_file.write_text("chr1\t0\t100\n")

        out_dir = self.test_dir / "output"
        split_bed(bed_file, out_dir, 1)

        symlink = out_dir / "test" / "test.bed"
        self.assertTrue(symlink.exists())
        self.assertTrue(symlink.is_symlink())

    def test_split_bed_multiple_splits(self):
        """Test split_bed with multiple splits."""
        bed_file = self.test_dir / "test.bed"
        bed_content = "\n".join(
            [
                "chr1\t0\t1000",
                "chr1\t1000\t2000",
                "chr1\t2000\t3000",
                "chr1\t3000\t4000",
            ]
        )
        bed_file.write_text(bed_content)

        out_dir = self.test_dir / "output"
        split_bed(bed_file, out_dir, 2)

        # Check output directory exists
        split_dir = out_dir / "test"
        self.assertTrue(split_dir.exists())

        # Check that some files were created
        bed_files = list(split_dir.glob("*.bed"))
        self.assertGreater(len(bed_files), 0)


class TestSplitFai(unittest.TestCase):
    """Test split_fai function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_split_fai_file_not_found(self):
        """Test split_fai with non-existent file."""
        non_existent = self.test_dir / "non_existent.fai"
        with self.assertRaises(FileNotFoundError):
            split_fai(non_existent, self.test_dir, 2)

    def test_split_fai_output_exists(self):
        """Test split_fai when output directory exists."""
        # Create input file
        fai_file = self.test_dir / "test.fai"
        fai_file.write_text("chr1\t10000\t52\t60\t61\n")

        # Create output directory
        out_dir = self.test_dir / "genome"
        out_dir.mkdir()

        with self.assertRaises(ValueError):
            split_fai(fai_file, self.test_dir, 2)

    def test_split_fai_basic(self):
        """Test basic split_fai functionality."""
        fai_file = self.test_dir / "test.fai"
        fai_content = "\n".join(
            [
                "chr1\t100000\t52\t60\t61",
                "chr2\t200000\t52\t60\t61",
            ]
        )
        fai_file.write_text(fai_content)

        out_dir = self.test_dir / "output"
        split_fai(fai_file, out_dir, 3)

        # Check output directory exists
        genome_dir = out_dir / "genome"
        self.assertTrue(genome_dir.exists())

        # Check that some files were created
        bed_files = list(genome_dir.glob("*.bed"))
        self.assertGreater(len(bed_files), 0)

        # Verify BED file format
        first_bed = bed_files[0]
        df = pd.read_table(first_bed, header=None)
        self.assertEqual(df.shape[1], 3)  # Should have 3 columns


if __name__ == "__main__":
    unittest.main()
