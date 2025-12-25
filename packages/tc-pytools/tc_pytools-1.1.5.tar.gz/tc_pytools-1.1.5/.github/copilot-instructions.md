# TC PyTools - GitHub Copilot Instructions

This is a Python genomic data processing toolkit built with modern Python tooling (uv, hatchling). The package provides command-line tools for renaming chromosome IDs in genome files (FASTA/GFF) from various sources (NGDC, NCBI).

## Project Structure

- `genome/`: Main package containing the core CLI application
  - `rename_genome_id.py`: Primary tool with three subcommands (ngdc, ncbi, custom)
  - `tests/`: Test suite with pytest
- `pyproject.toml`: Project configuration and dependencies
- `ci.sh`: Local CI validation script
- `Makefile`: Common development tasks
- `.github/workflows/`: CI/CD pipelines

## Development Workflow

### Required Before Each Commit

1. **Format code**: `uv run ruff format .`
2. **Check linting**: `uv run ruff check .`
3. **Type checking**: `uv run mypy genome --ignore-missing-imports`
4. **Run tests**: `uv run pytest`
5. **Full CI check**: `./ci.sh` (includes all above steps plus coverage)

### Build and Test Commands

- Build: `uv build`
- Test with coverage: `uv run pytest --cov=genome --cov-report=html --cov-report=term`
- Clean build artifacts: `make clean`
- Install in editable mode: `uv pip install -e .`

## Code Standards

1. **Python Version**: Python 3.8+
2. **Type Hints**: Use type hints for all function signatures
3. **Code Style**: Follow ruff formatting and linting rules (configured in `ruff.toml`)
4. **Error Handling**: Use proper exception chaining (e.g., `raise SomeError() from e`)
5. **Testing**: Write unit tests for new functionality; prefer table-driven tests
6. **Documentation**: Update docstrings for public functions; maintain README and CHANGELOG

## Key Guidelines

1. **CLI Design**: Use Typer for command-line interfaces; maintain consistent help messages
2. **File Handling**: Use pathlib.Path for all file operations
3. **External Dependencies**:
   - Minimize dependencies; currently using: typer, requests, typing-extensions
   - Add type stubs when needed (e.g., types-requests)
4. **NCBI Integration**: Assembly reports are downloaded from NCBI FTP using genome name extracted from FASTA filename
5. **ID Mapping**: Support configurable column mapping via --old-col and --new-col parameters

## Documentation Requirements

### After Each Commit: Update Documentation

**IMPORTANT**: After any code changes are committed, Copilot should automatically:

1. **Update README.md**:
   - Add new features to the "Features" section
   - Update usage examples if CLI changed
   - Add new installation requirements if dependencies changed
   - Update command names or parameters in examples
   - Keep the Chinese language style consistent

2. **Update CHANGELOG.md**:
   - Add entries to the `[Unreleased]` section following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
   - Categorize changes under appropriate sections:
     - `### Added` - new features
     - `### Changed` - changes in existing functionality
     - `### Deprecated` - soon-to-be removed features
     - `### Removed` - removed features
     - `### Fixed` - bug fixes
     - `### Security` - security improvements
   - Use concise, descriptive bullet points
   - Reference issue/PR numbers if applicable

3. **Keep Format Consistent**:
   - README should be in Chinese (中文)
   - CHANGELOG should be in English
   - Follow existing structure and formatting

### Example Changelog Entry Pattern

```markdown
## [Unreleased]

### Added
- NCBI genome renaming support with automatic assembly_report.txt download
- Configurable column mapping (--old-col, --new-col) for flexible ID extraction
- Auto-detection of genome name from FASTA filename

### Changed
- Renamed package from `gtf` to `genome` for broader scope
- Command renamed from `rename-ngdc-genome-id` to `tc-rename-genome-id`
- Simplified NCBI workflow by removing -n parameter

### Fixed
- CI/CD: Fixed mypy path to check genome directory instead of gtf
- Linting: Added proper exception chaining (B904) in error handlers
```

## Testing Strategy

- **Unit Tests**: Cover core functions (parsing, mapping, renaming)
- **Integration Tests**: Test full command workflows
- **Fixtures**: Use pytest fixtures for test data (FASTA/GFF samples)
- **Coverage**: Aim for >70% code coverage
- **CI**: All tests must pass before merging

## Dependencies Management

- **Runtime Dependencies**: Listed in `pyproject.toml` under `dependencies`
- **Dev Dependencies**: Listed under `dependency-groups.dev`
- **Type Stubs**: Add to dev dependencies when needed (e.g., `types-requests`)
- **Version Pinning**: Use minimum version specifiers (e.g., `requests>=2.0.0`)

## Release Process

1. Update version in `genome/__init__.py`
2. Move `[Unreleased]` changes to new version section in CHANGELOG.md
3. Create git tag: `git tag v1.x.x`
4. Build: `uv build`
5. Publish to PyPI: `twine upload dist/*` (use twine, not `uv publish`)

## Repository-Specific Conventions

- **Command Naming**: All commands use `tc-` prefix to avoid naming conflicts
- **Backward Compatibility**: Maintain old command aliases (e.g., `tc-rename-ngdc-genome-id`)
- **Error Messages**: Provide clear, actionable error messages for users
- **Progress Indicators**: Use Typer's echo for user feedback during long operations
- **File Validation**: Check file existence and format before processing
