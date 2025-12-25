from typing import TYPE_CHECKING  # pragma: no cover

from lazy_bear import LazyAttr, LazyLoader  # pragma: no cover

environ = LazyLoader("os").to("environ")  # pragma: no cover
if TYPE_CHECKING:  # pragma: no cover
    from os import environ  # noqa: TC004


def test_if_real_object() -> int:  # pragma: no cover
    try:
        assert isinstance(environ, LazyAttr)
        environ["TEST_KEY"] = "TEST_VALUE"
        assert "<class 'os._Environ'>" in str(type(environ))
        assert environ.__setitem__("TEST_KEY", "TEST_VALUE") is None
        assert environ.__contains__("TEST_KEY")
        assert environ.__getitem__("TEST_KEY") == "TEST_VALUE"
        assert environ.__len__() > 0
        assert environ.__iter__() is not None
        assert len(environ) > 0
        assert "TEST_KEY" in environ
        assert "NON_EXISTENT_KEY" not in environ
        assert "<class 'os._Environ'>" in str(type(environ))
    except Exception:  # pragma: no cover  # Intentionally suppressing to return 1 on failure, this is a boolean test, it passes or fails.
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    print(test_if_real_object())
