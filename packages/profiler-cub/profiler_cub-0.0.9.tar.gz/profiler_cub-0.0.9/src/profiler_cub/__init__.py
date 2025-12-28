"""Profiler Cub package.

A beautiful profiler for Python projects with various options
"""

from profiler_cub._internal._info import METADATA
from profiler_cub._internal.cli import main

__version__: str = METADATA.version

__all__: list[str] = ["METADATA", "__version__", "main"]
