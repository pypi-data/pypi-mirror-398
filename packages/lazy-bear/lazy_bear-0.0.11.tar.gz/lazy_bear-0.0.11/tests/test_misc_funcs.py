from lazy_bear.lazy_imports import get_calling_file, get_calling_globals

STACK_OFFSET = 1


def test_calling_file() -> None:
    """Test get_calling_file function."""
    calling_file: str = get_calling_file(STACK_OFFSET)
    assert isinstance(calling_file, str)
    assert __file__ in calling_file


def test_calling_file_offset() -> None:
    """Test get_calling_file function with different stack offsets."""

    def inner_function() -> str:
        return get_calling_file(STACK_OFFSET + 1)

    calling_file: str = inner_function()
    assert isinstance(calling_file, str)
    assert __file__ in calling_file


def test_calling_file_deeper_offset() -> None:
    """Test get_calling_file function with deeper stack offsets."""

    def level_one() -> str:
        return level_two()

    def level_two() -> str:
        return get_calling_file(STACK_OFFSET + 2)

    calling_file: str = level_one()
    assert isinstance(calling_file, str)
    assert __file__ in calling_file


def test_get_globals() -> None:
    """Test get_calling_globals function."""
    calling_globals: dict[str, object] = get_calling_globals(STACK_OFFSET)
    assert isinstance(calling_globals, dict)
    assert "__file__" in calling_globals
    assert calling_globals["__file__"] == __file__
    assert globals() == calling_globals


def test_get_globals_offset() -> None:
    """Test get_calling_globals function with different stack offsets."""

    def inner_function() -> dict[str, object]:
        return get_calling_globals(STACK_OFFSET + 1)

    calling_globals: dict[str, object] = inner_function()
    assert isinstance(calling_globals, dict)
    assert "__file__" in calling_globals
    assert calling_globals["__file__"] == __file__
    assert globals() == calling_globals
