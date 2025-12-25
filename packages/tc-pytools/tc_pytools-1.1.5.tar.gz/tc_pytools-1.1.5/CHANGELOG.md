# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.5] - 2025-12-22

### Added
- `tc-table2vcf` tool for converting simple table format to VCF format
- Support for customizable column mapping (--chrom-col, --pos-col, --ref-col, --alt-col)
- Support for different delimiters (tab, comma, etc.)
- Optional header skipping functionality
- Automatic VCF header generation with metadata

## [1.1.0] - 2024-11-24

### Added
- Initial release of tc-pytools
- `rename-ngdc-genome-id` tool for renaming chromosome IDs in NGDC genome files
- Support for processing FASTA files
- Support for processing GFF files
- Comprehensive test suite with pytest
- CI/CD configuration with GitHub Actions
- Local CI scripts and pre-commit hooks
- Complete documentation (README, INSTALL, QUICKREF, PUBLISH guides)
- UV package manager integration
- Makefile for common tasks

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- N/A (initial release)

## Release Notes

### [1.1.0] - Initial Release

This is the first public release of TC PyTools, a toolkit for processing genomic data files.

**Key Features:**
- Fast and efficient chromosome ID renaming for NGDC genome files
- Simple command-line interface
- Python API for programmatic use
- Comprehensive test coverage (67%)
- Modern Python packaging with uv

**Installation:**
```bash
pip install tc-pytools
```

**Usage:**
```bash
rename-ngdc-genome-id -f genome.fasta -o output.fasta
```

For more information, see the [README](README.md) and [documentation](gtf/docs/README.md).

---

[Unreleased]: https://github.com/yourusername/tc-pytools/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/yourusername/tc-pytools/releases/tag/v1.1.0
