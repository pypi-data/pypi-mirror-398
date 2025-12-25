# Changelog

All notable changes to `esrf-loadfile` will be documented here. This project follows
the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format and uses
semver-style versioning through `setuptools-scm`.

## [Unreleased]

### Added
- Placeholder for ongoing development. Document your changes under the appropriate
  section before tagging the next release.

### Changed
- _None yet._

### Fixed
- _None yet._

## [0.2.0] - 2025-12-23

### Added
- Getting ready for pypi.

## [0.1.0] - 2025-11-13

### Added
- Initial extraction of the StatusGUI loader utilities for `.h5`, `.mat`, `.cif`,
  and reflection (`.csv`/`.dat`) files.
- CONTRIBUTING guide describing local setup, code style, and review expectations.
- Development extra (`pip install -e .[dev]`) that installs Ruff alongside pytest.
- Ruff configuration plus documentation of the lint/test workflow in `README.md`.
- Regression test covering HDF5 nested access, metadata handling, and size helpers.

### Changed
- Package now uses a `src/` layout; `loadFile.py` exposes safer navigation helpers
  and standardized numpy/attribute handling.
- README usage example now highlights nested key lookups and metadata accessors.

### Fixed
- Column-vector handling, byte-string decoding, and attribute traversal in the
  generic/HDF5 loaders now behave consistently across datasets.

<!-- Release links -->
[Unreleased]: https://gitlab.esrf.fr/graintracking/loadfile.git/-/compare/v0.1.0...main
[0.1.0]: https://gitlab.esrf.fr/graintracking/loadfile.git/-/releases/v0.1.0
