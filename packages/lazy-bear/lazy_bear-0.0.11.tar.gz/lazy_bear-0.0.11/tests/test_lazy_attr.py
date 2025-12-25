import inspect
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import FunctionType

import pytest

from lazy_bear.lazy_imports import LazyAttr, LazyLoader


def get_module(name: str) -> LazyLoader:
    """Helper function to get a LazyLoader for a module."""
    return LazyLoader(name)


def test_wrapped_magic_attr() -> None:
    """Test LazyAttr __wrapped__ functionality."""
    sqrt: LazyAttr = LazyLoader("math").to("sqrt")
    unwrapped: FunctionType = inspect.unwrap(sqrt)
    assert unwrapped is sqrt._attr
    assert not isinstance(unwrapped, LazyAttr)
    assert unwrapped(16) == 4.0


def test_lazy_attr_dir() -> None:
    """Test LazyAttr __dir__ functionality."""
    sqrt = LazyLoader("math").to("sqrt")
    dir_result: list[str] = dir(sqrt)
    assert isinstance(dir_result, list)
    assert "Not loaded yet" not in dir_result

    repr_result: str = repr(sqrt)
    assert isinstance(repr_result, str)
    sqrt_result = sqrt(25)
    assert sqrt_result == 5.0
    pi = LazyLoader("math").to("pi")
    with pytest.raises(TypeError):
        pi()


def test_lazy_attr() -> None:
    """Test LazyAttr __contains__ functionality."""
    environ = LazyLoader("os").to("environ")
    assert isinstance(environ, LazyAttr)
    assert "<class 'os._Environ'>" in str(type(environ.value))
    assert environ.__setitem__("TEST_KEY", "TEST_VALUE") is None
    assert environ.__contains__("TEST_KEY")
    assert environ.__getitem__("TEST_KEY") == "TEST_VALUE"
    assert environ.__len__() > 0
    assert environ.__iter__() is not None
    assert len(environ) > 0
    assert "TEST_KEY" in environ
    assert "NON_EXISTENT_KEY" not in environ


def test_lazy_attr_ordered_dict_class() -> None:
    """Ensure LazyAttr can provide a stdlib class and allow instantiation."""
    OrderedDict = LazyLoader("collections").to("OrderedDict")
    ordered = OrderedDict([("a", 1), ("b", 2)])
    assert list(ordered.items()) == [("a", 1), ("b", 2)]


def test_lazy_attr_keyword_list_constant() -> None:
    """Ensure LazyAttr exposes a list-like constant."""
    loader: LazyLoader = get_module("keyword")
    kwlist_attr = LazyAttr("kwlist", loader)

    assert "def" in kwlist_attr
    assert kwlist_attr[0] in ("False", "True", "None")  # type: ignore[index]
    assert kwlist_attr.__len__() >= 30


def test_lazy_attr_this_module_dict_constant() -> None:
    """Ensure LazyAttr can expose a dictionary constant."""
    loader: LazyLoader = get_module("this")
    cipher_dict_attr = LazyAttr("d", loader)

    assert cipher_dict_attr["a"] == "n"
    assert "b" in cipher_dict_attr
    assert len(cipher_dict_attr) == 52


def test_lazy_attr_operator_function() -> None:
    """Ensure LazyAttr works with callable functions."""
    loader: LazyLoader = get_module("operator")
    itemgetter_attr = LazyAttr("itemgetter", loader)

    getter = itemgetter_attr(1)
    assert getter(["zero", "one", "two"]) == "one"


def test_lazy_attr_pathlib_class_usage() -> None:
    """Ensure LazyAttr can expose pathlib.Path class."""
    pathlib: LazyLoader = get_module("pathlib")
    path_attr = LazyAttr("Path", pathlib)

    cwd_path = path_attr(".")
    assert cwd_path.name in (".", "")
    assert cwd_path.exists()


def test_collections_ordered_dict_methods() -> None:
    """Test that LazyAttr for collections.OrderedDict exposes its methods."""
    loader: LazyLoader = get_module("collections")
    ordered_dict_attr = LazyAttr("OrderedDict", loader)

    ordered = ordered_dict_attr()
    ordered["x"] = 10
    ordered["y"] = 20

    assert list(ordered.keys()) == ["x", "y"]
    assert list(ordered.values()) == [10, 20]
    assert list(ordered.items()) == [("x", 10), ("y", 20)]


def test_logger_module_lazy_attr() -> None:
    """Test that LazyAttr for logging.Logger exposes its methods."""
    DEBUG = LazyLoader("logging").to("DEBUG")

    assert DEBUG == 10
    assert str(DEBUG) == "10"
    assert int(DEBUG) == 10
    assert float(DEBUG) == 10.0
    assert hash(DEBUG) == hash(10)
    assert isinstance(repr(DEBUG), str)
    assert isinstance(dir(DEBUG), list)

    assert isinstance(DEBUG, int)
    assert DEBUG | 5 == 15
    assert 5 | DEBUG == 15
    with pytest.raises(TypeError):
        len(DEBUG)


def test_if_globals_set() -> None:
    """Test that LazyLoader sets the module in globals upon loading."""
    import subprocess  # noqa: PLC0415
    from subprocess import CompletedProcess  # noqa: PLC0415

    python: str = sys.executable
    path = "tests/_meta_test.py"

    result: CompletedProcess[str] = subprocess.run(  # noqa: S603
        [python, path], check=False, capture_output=True, text=True
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "0"


# ruff: noqa: N806
