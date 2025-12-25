"""Lazy Bear package.

A lazy import package for both modules and items within modules.
"""

from lazy_bear._internal.cli import main
from lazy_bear._internal.debug import METADATA
from lazy_bear.lazy_attribute import LazyAttr
from lazy_bear.lazy_imports import LazyLoader, lazy

__version__: str = METADATA.version

__all__: list[str] = ["METADATA", "LazyAttr", "LazyLoader", "__version__", "lazy", "main"]
