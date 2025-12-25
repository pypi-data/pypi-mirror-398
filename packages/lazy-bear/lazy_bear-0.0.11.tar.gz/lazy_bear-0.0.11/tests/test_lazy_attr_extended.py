from __future__ import annotations

from collections import OrderedDict as RealOrderedDict
import pickle
import string
from typing import TYPE_CHECKING

import pytest

from lazy_bear.lazy_attribute import NOT_FOUND, LazyAttr
from lazy_bear.lazy_imports import LazyLoader, lazy


def test_not_found_repr() -> None:
    assert repr(NOT_FOUND) == "<NOT_FOUND>"


def test_missing_attribute_raises_attributeerror() -> None:
    missing = LazyLoader("math").to("does_not_exist_xyz")
    with pytest.raises(AttributeError):
        _ = missing.value


def test_metaclass_cache_shared_between_wrappers() -> None:
    LazyAttr._cached.clear()

    sqrt1 = LazyLoader("math").to("sqrt")
    assert LazyAttr.check_cache("sqrt", "math") is NOT_FOUND
    assert sqrt1(16) == 4.0
    import math

    assert LazyAttr.check_cache("sqrt", "math") is math.sqrt
    sqrt2 = LazyLoader("math").to("sqrt")
    assert sqrt2.value is math.sqrt


def test_metaclass_cache_with_builtin_class() -> None:
    LazyAttr._cached.clear()
    list1 = LazyLoader("builtins").to("list")
    assert LazyAttr.check_cache("list", "builtins") is NOT_FOUND
    assert list1() == []
    assert LazyAttr.check_cache("list", "builtins") is list
    list2 = LazyLoader("builtins").to("list")
    assert list2.value is list


def test_metaclass_cache_with_constant() -> None:
    LazyAttr._cached.clear()
    letters1 = LazyLoader("string").to("ascii_lowercase")
    assert LazyAttr.check_cache("ascii_lowercase", "string") is NOT_FOUND
    const = letters1.value
    assert const is string.ascii_lowercase
    assert LazyAttr.check_cache("ascii_lowercase", "string") is const
    letters2 = LazyLoader("string").to("ascii_lowercase")
    assert letters2.value is const


def test_metaclass_cache_with_module_instance() -> None:
    LazyAttr._cached.clear()
    mutable1 = LazyLoader("tests.fixture_lazy_attr").to("mutable")
    assert LazyAttr.check_cache("mutable", "tests.fixture_lazy_attr") is NOT_FOUND
    obj = mutable1.value
    assert LazyAttr.check_cache("mutable", "tests.fixture_lazy_attr") is obj
    mutable2 = LazyLoader("tests.fixture_lazy_attr").to("mutable")
    assert mutable2.value is obj


def test_metaclass_cache_with_enum_member_instance() -> None:
    LazyAttr._cached.clear()
    if TYPE_CHECKING:
        from tests.fixture_lazy_attr import color_red as red1
    else:
        red1 = LazyLoader("tests.fixture_lazy_attr").to("color_red")
    assert LazyAttr.check_cache("color_red", "tests.fixture_lazy_attr") is NOT_FOUND
    enum_member = red1.value
    from tests.fixture_lazy_attr import color_red as real_red

    assert enum_member is real_red
    assert LazyAttr.check_cache("color_red", "tests.fixture_lazy_attr") is enum_member
    red2 = LazyLoader("tests.fixture_lazy_attr").to("color_red")
    assert red2.value is enum_member


def test_numeric_operations_and_comparisons() -> None:
    if TYPE_CHECKING:
        from math import pi
    else:
        pi = LazyLoader("math").to("pi")
    assert pi > 3
    assert pi >= 3
    assert pi < 4
    assert pi <= 4
    assert pi != 0
    import math

    assert pi + 1 == math.pi + 1
    assert 1 + pi == 1 + math.pi
    assert pi - 1 == math.pi - 1
    assert 1 - pi == 1 - math.pi
    assert pi * 2 == math.pi * 2
    assert 2 * pi == 2 * math.pi


def test_unsupported_add_raises() -> None:
    modules_dict = LazyLoader("sys").to("modules")
    with pytest.raises(TypeError):
        _ = modules_dict + 1
    with pytest.raises(TypeError):
        _ = 1 + modules_dict


def test_isinstance_and_issubclass_with_lazyattr_wrapper() -> None:
    if TYPE_CHECKING:
        from collections import OrderedDict as OrderedDictAttr
    else:
        OrderedDictAttr = LazyLoader("collections").to("OrderedDict")  # noqa: N806

    od = RealOrderedDict()
    assert isinstance(od, OrderedDictAttr)
    assert issubclass(RealOrderedDict, OrderedDictAttr)
    od2 = OrderedDictAttr()
    assert isinstance(od2, OrderedDictAttr)


def test_descriptor_protocol_delegates_to_wrapped_value() -> None:
    if TYPE_CHECKING:
        from tests.fixture_lazy_attr import descriptor as desc_attr
    else:
        desc_attr = LazyLoader("tests.fixture_lazy_attr").to("descriptor")

    class Holder:
        descriptor = desc_attr

    holder = Holder()
    assert Holder.descriptor == "class-access"
    assert holder.descriptor == "instance-access"


def test_setattr_guard_and_forwarding() -> None:
    mutable_attr = LazyLoader("tests.fixture_lazy_attr").to("mutable")
    with pytest.raises(AttributeError):
        mutable_attr.new_value = 1
    obj = mutable_attr.value
    mutable_attr.new_value = 1
    assert obj.new_value == 1


def test_parent_globals_replaced_after_load() -> None:
    LazyAttr._cached.clear()
    loader = LazyLoader("math")
    loader2 = lazy("math")
    sqrt_attr = loader.to("sqrt")

    g = globals()
    old = g.get("sqrt", None)
    g["sqrt"] = sqrt_attr
    try:
        _ = sqrt_attr(9)
        import math

        assert g["sqrt"] is math.sqrt
    finally:
        if old is None:
            g.pop("sqrt", None)
        else:
            g["sqrt"] = old


def test_pickle_non_class_works() -> None:
    sqrt_attr = LazyLoader("math").to("sqrt")
    pickled = pickle.dumps(sqrt_attr)
    unpickled = pickle.loads(pickled)  # noqa: S301 # This is sqrt itself at this point since it was loaded
    assert callable(unpickled)
    assert unpickled(25) == 5.0


def test_class_property_and_setter_behavior() -> None:
    sqrt_attr = LazyLoader("math").to("sqrt")
    assert sqrt_attr.__class__ is LazyAttr
    with pytest.raises(TypeError):
        sqrt_attr.__class__ = int  # type: ignore[misc]
    _ = sqrt_attr(4)
    import math

    assert sqrt_attr.__class__ is type(math.sqrt)


def test_getattr_proxy_and_missing_attribute() -> None:
    sqrt_attr = LazyLoader("math").to("sqrt")
    assert sqrt_attr.__name__ == "sqrt"
    with pytest.raises(AttributeError):
        _ = sqrt_attr.no_such_attr


def test_unwrap_alias_returns_underlying_value() -> None:
    letters = LazyLoader("string").to("ascii_letters")
    assert letters.unwrap() == string.ascii_letters


# ruff: noqa: PLC0415
