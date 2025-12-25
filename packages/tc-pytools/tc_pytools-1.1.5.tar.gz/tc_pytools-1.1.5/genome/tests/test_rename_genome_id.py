import tempfile
import unittest
from pathlib import Path

from genome.rename_genome_id import (
    build_id_mapping,
    load_id_mapping,
    parse_fasta_header,
    rename_fasta,
    rename_gff,
)


class TestParseFastaHeader(unittest.TestCase):
    """Test parsing of FASTA header to extract old and new IDs."""

    def test_standard_ngdc_format(self):
        header = ">GWHGECT00000001.1      Chromosome 1A   Complete=T      Circular=F      OriSeqID=Chr1A  Len=600907804"
        old_id, new_id = parse_fasta_header(header)
        self.assertEqual(old_id, "GWHGECT00000001.1")
        self.assertEqual(new_id, "Chr1A")

    def test_another_example(self):
        header = ">GWHGECT00000010.1      Chromosome 5B   Complete=T      Circular=F      OriSeqID=Chr5B  Len=742642744"
        old_id, new_id = parse_fasta_header(header)
        self.assertEqual(old_id, "GWHGECT00000010.1")
        self.assertEqual(new_id, "Chr5B")

    def test_header_without_oriseqid(self):
        header = ">GWHGECT00000001.1      Chromosome 1A"
        old_id, new_id = parse_fasta_header(header)
        self.assertIsNone(old_id)
        self.assertIsNone(new_id)

    def test_empty_header(self):
        header = ">"
        old_id, new_id = parse_fasta_header(header)
        self.assertIsNone(old_id)
        self.assertIsNone(new_id)


class TestBuildIdMapping(unittest.TestCase):
    """Test building ID mapping from FASTA file."""

    def test_build_mapping(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            fasta_content = """>GWHGECT00000001.1      Chromosome 1A   Complete=T      Circular=F      OriSeqID=Chr1A  Len=600907804
ATCGATCGATCG
>GWHGECT00000002.1      Chromosome 1B   Complete=T      Circular=F      OriSeqID=Chr1B  Len=731628012
GCTAGCTAGCTA
>GWHGECT00000003.1      Chromosome 2A   Complete=T      Circular=F      OriSeqID=Chr2A  Len=801619444
TTAATTAATTAA
"""
            fasta_file = Path(tmp_dir) / "test.fasta"
            fasta_file.write_text(fasta_content)

            id_map = build_id_mapping(fasta_file)

            self.assertEqual(len(id_map), 3)
            self.assertEqual(id_map["GWHGECT00000001.1"], "Chr1A")
            self.assertEqual(id_map["GWHGECT00000002.1"], "Chr1B")
            self.assertEqual(id_map["GWHGECT00000003.1"], "Chr2A")


class TestRenameFasta(unittest.TestCase):
    """Test renaming chromosome IDs in FASTA file."""

    def test_rename_fasta(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_content = """>GWHGECT00000001.1      Chromosome 1A   Complete=T      Circular=F      OriSeqID=Chr1A  Len=600907804
ATCGATCGATCG
GCTAGCTAGCTA
>GWHGECT00000002.1      Chromosome 1B   Complete=T      Circular=F      OriSeqID=Chr1B  Len=731628012
TTAATTAATTAA
CCGGCCGGCCGG
"""
            input_file = Path(tmp_dir) / "input.fasta"
            output_file = Path(tmp_dir) / "output.fasta"
            input_file.write_text(input_content)

            id_map = {"GWHGECT00000001.1": "Chr1A", "GWHGECT00000002.1": "Chr1B"}

            rename_fasta(input_file, output_file, id_map)

            output_content = output_file.read_text()
            expected = """>Chr1A
ATCGATCGATCG
GCTAGCTAGCTA
>Chr1B
TTAATTAATTAA
CCGGCCGGCCGG
"""
            self.assertEqual(output_content, expected)

    def test_rename_fasta_no_mapping(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_content = """>GWHGECT00000001.1      Chromosome 1A   Complete=T      Circular=F      OriSeqID=Chr1A  Len=600907804
ATCG
>UnknownSeq
GCTA
"""
            input_file = Path(tmp_dir) / "input.fasta"
            output_file = Path(tmp_dir) / "output.fasta"
            input_file.write_text(input_content)

            id_map = {"GWHGECT00000001.1": "Chr1A"}

            rename_fasta(input_file, output_file, id_map)

            output_content = output_file.read_text()
            expected = """>Chr1A
ATCG
>UnknownSeq
GCTA
"""
            self.assertEqual(output_content, expected)


class TestRenameGff(unittest.TestCase):
    """Test renaming chromosome IDs in GFF file."""

    def test_rename_gff(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_content = """##gff-version 3
##sequence-region GWHGECT00000001.1 1 600907804
GWHGECT00000001.1\tRefSeq\tgene\t100\t200\t.\t+\t.\tID=gene1;Name=GENE1
GWHGECT00000001.1\tRefSeq\tmRNA\t100\t200\t.\t+\t.\tID=transcript1;Parent=gene1
GWHGECT00000002.1\tRefSeq\tgene\t300\t400\t.\t-\t.\tID=gene2;Name=GENE2
"""
            input_file = Path(tmp_dir) / "input.gff"
            output_file = Path(tmp_dir) / "output.gff"
            input_file.write_text(input_content)

            id_map = {"GWHGECT00000001.1": "Chr1A", "GWHGECT00000002.1": "Chr1B"}

            rename_gff(input_file, output_file, id_map)

            output_content = output_file.read_text()
            expected = """##gff-version 3
##sequence-region GWHGECT00000001.1 1 600907804
Chr1A\tRefSeq\tgene\t100\t200\t.\t+\t.\tID=gene1;Name=GENE1
Chr1A\tRefSeq\tmRNA\t100\t200\t.\t+\t.\tID=transcript1;Parent=gene1
Chr1B\tRefSeq\tgene\t300\t400\t.\t-\t.\tID=gene2;Name=GENE2
"""
            self.assertEqual(output_content, expected)

    def test_rename_gff_with_unmapped_chromosomes(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_content = """GWHGECT00000001.1\tRefSeq\tgene\t100\t200\t.\t+\t.\tID=gene1
UnknownChr\tRefSeq\tgene\t300\t400\t.\t-\t.\tID=gene2
GWHGECT00000002.1\tRefSeq\tgene\t500\t600\t.\t+\t.\tID=gene3
"""
            input_file = Path(tmp_dir) / "input.gff"
            output_file = Path(tmp_dir) / "output.gff"
            input_file.write_text(input_content)

            id_map = {"GWHGECT00000001.1": "Chr1A", "GWHGECT00000002.1": "Chr1B"}

            rename_gff(input_file, output_file, id_map)

            output_content = output_file.read_text()
            expected = """Chr1A\tRefSeq\tgene\t100\t200\t.\t+\t.\tID=gene1
UnknownChr\tRefSeq\tgene\t300\t400\t.\t-\t.\tID=gene2
Chr1B\tRefSeq\tgene\t500\t600\t.\t+\t.\tID=gene3
"""
            self.assertEqual(output_content, expected)

    def test_rename_gff_empty_lines(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_content = """##gff-version 3

GWHGECT00000001.1\tRefSeq\tgene\t100\t200\t.\t+\t.\tID=gene1

# This is a comment
GWHGECT00000002.1\tRefSeq\tgene\t300\t400\t.\t-\t.\tID=gene2
"""
            input_file = Path(tmp_dir) / "input.gff"
            output_file = Path(tmp_dir) / "output.gff"
            input_file.write_text(input_content)

            id_map = {"GWHGECT00000001.1": "Chr1A", "GWHGECT00000002.1": "Chr1B"}

            rename_gff(input_file, output_file, id_map)

            output_content = output_file.read_text()
            expected = """##gff-version 3

Chr1A\tRefSeq\tgene\t100\t200\t.\t+\t.\tID=gene1

# This is a comment
Chr1B\tRefSeq\tgene\t300\t400\t.\t-\t.\tID=gene2
"""
            self.assertEqual(output_content, expected)


class TestLoadIdMapping(unittest.TestCase):
    """Test loading ID mapping from file."""

    def test_load_mapping_basic(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            map_content = """GWHGECT00000001.1\tChr1A
GWHGECT00000002.1\tChr1B
GWHGECT00000003.1\tChr2A
"""
            map_file = Path(tmp_dir) / "id_map.txt"
            map_file.write_text(map_content)

            id_map = load_id_mapping(map_file)

            self.assertEqual(len(id_map), 3)
            self.assertEqual(id_map["GWHGECT00000001.1"], "Chr1A")
            self.assertEqual(id_map["GWHGECT00000002.1"], "Chr1B")
            self.assertEqual(id_map["GWHGECT00000003.1"], "Chr2A")

    def test_load_mapping_with_comments(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            map_content = """# This is a comment
GWHGECT00000001.1\tChr1A
# Another comment
GWHGECT00000002.1\tChr1B
"""
            map_file = Path(tmp_dir) / "id_map.txt"
            map_file.write_text(map_content)

            id_map = load_id_mapping(map_file)

            self.assertEqual(len(id_map), 2)
            self.assertEqual(id_map["GWHGECT00000001.1"], "Chr1A")
            self.assertEqual(id_map["GWHGECT00000002.1"], "Chr1B")

    def test_load_mapping_with_empty_lines(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            map_content = """GWHGECT00000001.1\tChr1A

GWHGECT00000002.1\tChr1B

"""
            map_file = Path(tmp_dir) / "id_map.txt"
            map_file.write_text(map_content)

            id_map = load_id_mapping(map_file)

            self.assertEqual(len(id_map), 2)
            self.assertEqual(id_map["GWHGECT00000001.1"], "Chr1A")
            self.assertEqual(id_map["GWHGECT00000002.1"], "Chr1B")

    def test_load_mapping_simple_ids(self):
        """Test loading mapping for non-NGDC genomes with simple IDs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            map_content = """scaffold_1\tChr1
scaffold_2\tChr2
scaffold_3\tChr3
"""
            map_file = Path(tmp_dir) / "id_map.txt"
            map_file.write_text(map_content)

            id_map = load_id_mapping(map_file)

            self.assertEqual(len(id_map), 3)
            self.assertEqual(id_map["scaffold_1"], "Chr1")
            self.assertEqual(id_map["scaffold_2"], "Chr2")
            self.assertEqual(id_map["scaffold_3"], "Chr3")


class TestRenameFastaWithMapping(unittest.TestCase):
    """Test renaming FASTA with custom ID mapping (non-NGDC genomes)."""

    def test_rename_simple_fasta(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_content = """>scaffold_1
ATCGATCGATCG
GCTAGCTAGCTA
>scaffold_2
TTAATTAATTAA
CCGGCCGGCCGG
"""
            input_file = Path(tmp_dir) / "input.fasta"
            output_file = Path(tmp_dir) / "output.fasta"
            input_file.write_text(input_content)

            id_map = {"scaffold_1": "Chr1", "scaffold_2": "Chr2"}

            rename_fasta(input_file, output_file, id_map)

            output_content = output_file.read_text()
            expected = """>Chr1
ATCGATCGATCG
GCTAGCTAGCTA
>Chr2
TTAATTAATTAA
CCGGCCGGCCGG
"""
            self.assertEqual(output_content, expected)

    def test_rename_fasta_with_descriptions(self):
        """Test that FASTA headers with descriptions are handled correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_content = """>scaffold_1 length=1000 GC=45.2
ATCGATCGATCG
>scaffold_2 length=2000 GC=50.1
GCTAGCTAGCTA
"""
            input_file = Path(tmp_dir) / "input.fasta"
            output_file = Path(tmp_dir) / "output.fasta"
            input_file.write_text(input_content)

            id_map = {"scaffold_1": "Chr1", "scaffold_2": "Chr2"}

            rename_fasta(input_file, output_file, id_map)

            output_content = output_file.read_text()
            expected = """>Chr1
ATCGATCGATCG
>Chr2
GCTAGCTAGCTA
"""
            self.assertEqual(output_content, expected)


if __name__ == "__main__":
    unittest.main()
