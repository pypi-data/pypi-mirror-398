"""Configuration for the pytest test suite."""

from __future__ import annotations

import os
from os import environ
from typing import TYPE_CHECKING

import pytest

from lazy_bear import METADATA

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

environ[f"{METADATA.env_variable}"] = "test"


@pytest.fixture
def devnull_print() -> Generator[Callable[[str], None]]:
    """Print to devnull to trigger evaluation without cluttering output."""
    with open(os.devnull, "w") as devnull:
        yield lambda *args, **kwargs: print(*args, **kwargs, file=devnull)
