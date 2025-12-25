"""Fixture module for LazyAttr tests.

This module is imported via LazyLoader in tests to exercise behaviors that are
hard to hit with stdlib-only objects (descriptor protocol, setattr forwarding).
"""

from __future__ import annotations

from enum import Enum
from typing import Literal


class DemoDescriptor:
    """Simple descriptor that returns different values for class/instance access."""

    def __get__(self, instance: object | None, owner: type | None = None) -> str:
        return "class-access" if instance is None else "instance-access"


descriptor = DemoDescriptor()


class Mutable:
    """Object that supports arbitrary attribute setting."""

    def __init__(self) -> None:  # noqa: D107
        self.initial = "ok"


mutable = Mutable()


class Color(Enum):
    RED = "red"
    BLUE = "blue"


color_red: Literal[Color.RED] = Color.RED

constant_number = 42
constant_text = "hello"
