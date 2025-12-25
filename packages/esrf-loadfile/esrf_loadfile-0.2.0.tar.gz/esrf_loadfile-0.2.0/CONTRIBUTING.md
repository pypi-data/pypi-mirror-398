# Contributing

Thanks for helping improve `esrf-loadfile`. This document describes the workflow we
follow for changes, testing, and reviews.

## Getting Started

1. Fork/clone the repository.
2. Install the project in editable mode together with the development extras:

   ```bash
   pip install -e .[dev]
   ```

3. We rely on Python 3.9+ for development. If you need to test against other Python
   versions, please use a virtual environment per interpreter.

## Development Workflow

1. Create a feature branch (`feature/nice-improvement`, `bugfix/some-bug`, etc.).
2. Make focused commits. Try to keep unrelated changes out of the same MR.
3. Update or add tests that cover the new behaviour.
4. Run the validation suite before opening a merge request:

   ```bash
   # Style / imports / static checks
   ruff check src tests

   # Unit tests
   PYTHONPATH=src python3 -m pytest
   ```

5. Update `README.md` or `CHANGELOG.md` whenever you add a user-facing feature or
   behaviour change.

## Coding Guidelines

- **Style**: Ruff enforces basic formatting and import ordering. Run `ruff check` (or
  `ruff check --fix`) frequently.
- **Type hints**: Prefer explicit type hints in public functions and whenever the
  signature is not obvious. This keeps the API clearer for downstream projects.
- **Logging**: Use the module-level `logger` and avoid `print`.
- **Error handling**: Wrap external file access in informative exceptions or log
  messages. When swallowing an exception, leave a short comment explaining why.

## Tests

- Place tests in `tests/` and name files `test_*.py`.
- When adding a loader feature, add at least one regression test that reproduces the
  target behaviour (even if it requires creating a synthetic file during the test).
- Tests should be fast and not rely on network access.

## Documentation

- Keep `README.md` up to date with notable CLI/API changes.
- Include short code snippets demonstrating new public APIs.
- Cross-reference `CHANGELOG.md` if the change is visible to users.

## Submitting Changes

1. Rebase onto `main` to avoid merge conflicts.
2. Double-check that tests and Ruff pass.
3. Push your branch and open a merge request with:
   - A concise title.
   - A description of the change and any follow-up work.
   - Notes about testing performed and/or missing coverage.
4. Review feedback promptly; small follow-up commits are fine.

Thanks again for contributing!
