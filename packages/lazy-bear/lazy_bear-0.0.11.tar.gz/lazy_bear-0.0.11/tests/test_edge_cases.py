from __future__ import annotations

from copy import copy, deepcopy
import pickle
from typing import TYPE_CHECKING, Any

from lazy_bear import lazy

if TYPE_CHECKING:
    from collections.abc import Callable


def test_lazy_attr_pickle() -> None:
    if TYPE_CHECKING:
        from collections import OrderedDict  # noqa: PLC0415
    else:
        OrderedDict = lazy("collections").to("OrderedDict")  # noqa: N806

    pickled: bytes = pickle.dumps(OrderedDict)
    unpickled: Any = pickle.loads(pickled)  # noqa: S301
    from collections import OrderedDict as RealOrderedDict  # noqa: PLC0415

    assert unpickled is RealOrderedDict
    instance = unpickled(name="test")
    assert isinstance(instance, RealOrderedDict)


def test_lazy_attr_copy() -> None:
    if TYPE_CHECKING:
        from builtins import list as lazy_list  # noqa: PLC0415
    else:
        lazy_list = lazy("builtins").to("list")
    # Shallow copy
    copied = copy(lazy_list)
    assert copied is list
    assert isinstance([], copied)
    deep_copied = deepcopy(lazy_list)
    assert deep_copied is list
    assert isinstance([], deep_copied)


def test_lazy_instances(devnull_print: Callable[[str], None]) -> None:
    if TYPE_CHECKING:
        from tests.fixture_lazy_attr import mutable  # noqa: PLC0415
    else:
        mutable = lazy("tests.fixture_lazy_attr").to("mutable")

    assert mutable.initial == "ok"


def test_functions() -> None:
    if TYPE_CHECKING:
        from os.path import join  # noqa: PLC0415
    else:
        join = lazy("os.path").to("join")

    result: str = join("a", "b")
    assert result in {"a/b", "a\\b"}
