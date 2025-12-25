from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from lazy_bear.lazy_imports import LazyAttr, LazyLoader, lazy


def get_module(n: str) -> LazyLoader:
    sys.modules.pop(n, None)
    LazyLoader.clear_globals()
    return LazyLoader(n)


def test_lazy_func() -> None:
    test_module = "random"
    sys.modules.pop(test_module, None)
    if TYPE_CHECKING:
        import random  # noqa: PLC0415
    else:
        random: LazyLoader = lazy(test_module)
    assert test_module not in sys.modules
    value: int = random.randint(1, 10)
    assert 1 <= value <= 10
    assert test_module in sys.modules
    assert "Not loaded yet" not in repr(random)


def test_lazy_import() -> None:
    test_module = "json"
    json: LazyLoader = get_module(test_module)
    assert test_module not in sys.modules
    value: str = json.dumps({"key": "value"})
    assert test_module in sys.modules
    assert value == '{"key": "value"}'
    assert "Not loaded yet" not in repr(json)
    assert "dumps" in dir(json)


def test_lazy_import_repr() -> None:
    test_module = "math"
    math: LazyLoader = get_module(test_module)
    repr_before = repr(math)
    assert "Not loaded yet" in repr_before
    _ = math.sqrt(16)
    repr_after = repr(math)
    assert "Not loaded yet" not in repr_after


def test_dir() -> None:
    test_module = "collections"
    collections: LazyLoader = get_module(test_module)
    assert test_module not in sys.modules
    dir_test = dir(collections)  # calling this loads the module
    assert "Not loaded yet" not in repr(collections)
    assert "deque" in dir_test


def test_actually_lazy() -> None:
    test_module = "email.mime.text"
    loader: LazyLoader = get_module(test_module)
    assert test_module not in sys.modules
    _ = loader.MIMEText
    assert test_module in sys.modules


def test_fake_import() -> None:
    test_module = "non_existent_module_abcxyz"
    fake_module: LazyLoader = get_module(test_module)
    with pytest.raises(ModuleNotFoundError):
        _ = fake_module.some_attribute


def test_attr_access() -> None:
    test_module = "collections"

    if TYPE_CHECKING:
        from collections import defaultdict  # noqa: PLC0415

        collections: LazyLoader = get_module(test_module)
    else:
        collections: LazyLoader = get_module(test_module)
        defaultdict: LazyAttr = collections.to("defaultdict")  # lazy attribute

    # assert test_module not in sys.modules

    assert "Not loaded yet" in repr(collections)
    assert "Not loaded yet" in repr(defaultdict)

    console_instance = defaultdict(int)
    assert "Not loaded yet" not in repr(collections)
    assert "Not loaded yet" not in repr(defaultdict)
    assert test_module in sys.modules
    assert isinstance(console_instance, collections.defaultdict)


def test_multiple_attr_access() -> None:
    test_module = "math"
    math_loader: LazyLoader = get_module(test_module)
    if TYPE_CHECKING:
        from math import pow, sqrt  # noqa: A004, PLC0415

    sqrt, pow = math_loader.to_many("sqrt", "pow")

    assert test_module not in sys.modules
    assert "Not loaded yet" in repr(math_loader)
    assert "Not loaded yet" in repr(sqrt)
    assert "Not loaded yet" in repr(pow)

    sqrt_result = sqrt(25)
    pow_result = pow(2, 3)

    assert test_module in sys.modules
    assert sqrt_result == 5.0
    assert pow_result == 8
    assert "Not loaded yet" not in repr(math_loader)
    assert "Not loaded yet" not in repr(sqrt)
    assert "Not loaded yet" not in repr(pow)


def test_speeds():
    import subprocess  # noqa: PLC0415
    import timeit  # noqa: PLC0415

    python = sys.executable
    runs = 5
    mult = 2

    def null_run() -> None:
        null_code = """pass"""
        subprocess.run([python, "-c", null_code], capture_output=True, check=True)

    null_time: float = timeit.timeit(null_run, number=runs) / runs
    # print(f"Null run time over {runs} runs: {null_time * 1000:.4f} ms")

    def import_os_run() -> None:
        import_os_code = """import os"""
        subprocess.run([python, "-c", import_os_code], capture_output=True, check=True)

    import_os_time: float = timeit.timeit(import_os_run, number=runs) / runs

    # print(f"Import os run time over {runs} runs: {import_os_time * 1000:.4f} ms")

    def lazy_os_run() -> None:
        lazy_os_code = """from lazy_bear import LazyLoader\nos = LazyLoader("os")"""
        subprocess.run([python, "-c", lazy_os_code], capture_output=True, check=True)

    lazy_os_time: float = timeit.timeit(lazy_os_run, number=runs) / runs
    assert lazy_os_time > 0, "Lazy os import time should be greater than zero"
    assert import_os_time > 0, "Normal os import time should be greater than zero"
    # To be clear, this is here to demonstrate that you shouldn't always use lazy imports for everything.
    # Stdlib is one of those cases where lazy imports are often slower.
    assert import_os_time < lazy_os_time, "Lazy os import is slower than normal import, this is expected."

    def lazy_run() -> None:
        lazy_code = """from lazy_bear import LazyLoader\npd = LazyLoader("pandas")"""
        subprocess.run([python, "-c", lazy_code], capture_output=True, check=True)

    def normal_run() -> None:
        normal_code = """import pandas as pd"""
        subprocess.run([python, "-c", normal_code], capture_output=True, check=True)

    lazy_time: float = (timeit.timeit(lazy_run, number=runs) / runs) - null_time
    normal_time: float = (timeit.timeit(normal_run, number=runs) / runs) - null_time

    # print(f"Lazy import time over {runs} runs: {lazy_time * 1000:.4f} ms")
    # print(f"Normal import time over {runs} runs: {normal_time * 1000:.4f} ms")
    assert lazy_time > 0, "Lazy import time should be greater than zero"
    assert normal_time > 0, "Normal import time should be greater than zero"
    assert (normal_time * mult) > lazy_time, "Lazy import is slower than normal import"
    # print(f"Actual difference: {(normal_time - lazy_time) * 1000:.4f} ms")

    def lazy_attr_run() -> None:
        lazy_attr_code = """from lazy_bear import LazyLoader\nDataFrame, Series = LazyLoader("pandas").to_many("DataFrame", "Series")"""
        subprocess.run([python, "-c", lazy_attr_code], capture_output=True, check=True)

    def normal_attr_run() -> None:
        normal_attr_code = """from pandas import DataFrame, Series"""
        subprocess.run([python, "-c", normal_attr_code], capture_output=True, check=True)

    lazy_attr_time: float = (timeit.timeit(lazy_attr_run, number=runs) / runs) - null_time
    normal_attr_time: float = (timeit.timeit(normal_attr_run, number=runs) / runs) - null_time

    # print(f"Lazy attribute import time over {runs} runs: {lazy_attr_time * 1000:.4f} ms")
    # print(f"Normal attribute import time over {runs} runs: {normal_attr_time * 1000:.4f} ms")
    assert lazy_attr_time > 0, "Lazy attribute import time should be greater than zero"
    assert normal_attr_time > 0, "Normal attribute import time should be greater than zero"
    assert (normal_attr_time * mult) > lazy_attr_time, (
        "Lazy attribute import is not significantly faster than normal import"
    )
    # print(f"Actual difference: {(normal_attr_time - lazy_attr_time) * 1000:.4f} ms")


# ruff: noqa: S603
