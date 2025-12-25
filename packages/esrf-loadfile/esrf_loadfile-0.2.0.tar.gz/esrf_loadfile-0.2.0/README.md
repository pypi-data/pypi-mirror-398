# esrf-loadfile

Standalone re-usable loader utilities for ESRF DCT and tomography data formats.  
These helpers were extracted from the StatusGUI code base so that other tools can
inspect `.h5`, `.mat`, `.cif`, and reflection files without depending on the GUI.

## Installation

```bash
pip install esrf-loadfile
```

For local development inside the StatusGUI monorepo you can install it in editable
mode:

```bash
pip install -e loadfile
```

## Usage

```python
from esrf_loadfile import loadFile

handler = loadFile("/path/to/parameters.h5")
print(handler.get_keys("entry/detector"))

# Nested keys work end-to-end:
dataset = handler.get_value("entry/detector/data")
print(handler.get_size("entry/detector/data"))
print(handler.get_description("entry/detector/data"))
```

## Development

Install the project in editable mode together with its test dependencies and run the
test-suite:

```bash
pip install -e .[test]
PYTHONPATH=src pytest
```

To run the code-coherency checks (imports/formatting/linting) install the dev extras
and run Ruff on the sources:

```bash
pip install -e .[dev]
ruff check src tests
```
