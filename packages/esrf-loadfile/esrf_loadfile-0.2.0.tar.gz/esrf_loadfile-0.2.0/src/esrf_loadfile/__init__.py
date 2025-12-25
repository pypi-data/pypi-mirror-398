"""Standalone accessors for ESRF tomography data files."""

from importlib import metadata

try:  # pragma: no cover - importlib.metadata varies with install
    __version__ = metadata.version("esrf-loadfile")
except metadata.PackageNotFoundError:  # pragma: no cover - local editable install
    __version__ = "0.2.0"

from .loadFile import (  # noqa: F401
    FileType,
    FilterH5Dataset,
    FilterMATDataset,
    LoadCIFFile,
    LoadH5File,
    LoadMatFile,
    LoadReflexionFile,
    genericFile,
    loadFile,
)

__all__ = [
    "FileType",
    "FilterH5Dataset",
    "FilterMATDataset",
    "LoadCIFFile",
    "LoadH5File",
    "LoadMatFile",
    "LoadReflexionFile",
    "genericFile",
    "loadFile",
    "__version__",
]
