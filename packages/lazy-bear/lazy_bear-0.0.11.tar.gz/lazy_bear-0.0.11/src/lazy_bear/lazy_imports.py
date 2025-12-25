"""A set of helper functions for dynamic module loading."""

from __future__ import annotations

import importlib
import inspect
import sys
from threading import RLock
from types import FrameType, ModuleType
from typing import TYPE_CHECKING, Any, ClassVar, final, overload

from lazy_bear.lazy_attribute import LazyAttr

from ._logger import get_logger

if TYPE_CHECKING:
    from logging import Logger

_lock: RLock = RLock()
logger: Logger = get_logger("LazyImports")


def get_calling_file(d: int = 2) -> str:
    """Get the filename of the calling frame.

    Args:
        d (int): The depth of the frame to inspect. Default is 2.
    """
    return sys._getframe(d).f_code.co_filename  # type: ignore[attr-defined]


def get_calling_globals(d: int = 2) -> dict[str, Any]:
    """Get the globals of the calling frame.

    Args:
        d (int): The depth of the frame to inspect. Default is 2.
    """
    return sys._getframe(d).f_globals  # type: ignore[attr-defined]


DEFAULT_FRAME = 1
"""The default frame offset for when getting the calling file/globals.

We will add 1 to this when using it from within the lazy() function.
"""


@final
class LazyLoader(ModuleType):
    """Class for module lazy loading."""

    __slots__: tuple = ("_module", "_name", "_parent_globals")

    _module: ModuleType | None
    _name: str
    _parent_globals: dict[str, Any]
    _globals_modules: ClassVar[dict[str, dict[str, Any]]] = {}

    def __init__(self, name: str, f_offset: int = 0, local_frame: FrameType | None = None) -> None:
        """Initialize the LazyLoader.

        Args:
            name (str): The full name of the module to load, must be the full path.
            f_offset (int): The frame offset to determine the calling file. Default is 0.
            frame (FrameType | None): The frame to use for caching globals. If None, it will be determined from the calling frame.
        """
        logger.debug(f"[LAZY LOADER INIT] Initializing LazyLoader for module '{name}'")
        self._name = name
        self._module = None

        with _lock:
            frame: FrameType = sys._getframe(DEFAULT_FRAME + f_offset)
            f: str = frame.f_code.co_filename
            if local_frame is not None and f != local_frame.f_code.co_filename:
                logger.warning(
                    "[LAZY LOADER INIT] Filename mismatch: expected '%s', got '%s'. Using provided filename for globals caching.",
                    local_frame.f_code.co_filename if local_frame is not None else None,
                    f,
                )
            if f not in self._globals_modules:
                logger.debug(f"[LAZY LOADER INIT] Caching globals for file '{f}'")
                self._globals_modules[f] = frame.f_globals
            self._parent_globals: dict[str, Any] = self._globals_modules[f]
        super().__init__(str(name))

    @classmethod
    def clear_globals(cls) -> None:
        """Clear the stored globals modules mapping."""
        with _lock:
            cls._globals_modules.clear()

    def _load(self) -> ModuleType:
        """Load the module and insert it into the parent's globals."""
        if self._module:
            return self._module

        with _lock:
            logger.debug(f"[LAZY LOADER LOAD] Loading module '{self._name}'")
            if self._module:
                logger.debug(f"[LAZY LOADER LOAD] Module '{self._name}' already loaded by another thread")
                return self._module
            module: ModuleType = importlib.import_module(self.__name__)
            self._parent_globals[self._name] = module
            sys.modules[self._name] = module
            self.__dict__.update(module.__dict__)
            self._module = module
            logger.debug(f"[LAZY LOADER LOAD] Module '{self._name}' loaded successfully")
            return module

    @overload
    def to(self, n: str) -> LazyAttr: ...
    @overload
    def to(self, *n: str) -> tuple[LazyAttr, ...]: ...
    def to(self, n: str, *rest: str) -> LazyAttr | tuple[LazyAttr, ...]:
        """Get a lazy attribute from the module.

        Args:
            n (str): The name of the attribute to get.
            *rest (str): Additional attribute names to get.

        Returns:
            Any: The attribute from the module, or a tuple of attributes.
        """
        if rest:
            return tuple(LazyAttr(name, self) for name in (n, *rest))

        return LazyAttr(n, self)

    def to_many(self, *names: str) -> tuple[LazyAttr, ...]:
        """Get multiple lazy attributes from the module.

        Args:
            *names (str): The names of the attributes to get.

        Returns:
            tuple[LazyAttr, ...]: The attributes from the module.
        """
        return tuple(LazyAttr(n, self) for n in names)

    def __getattr__(self, item: str) -> Any:
        module: ModuleType = self._load()
        return getattr(module, item)

    def __dir__(self) -> list[str]:
        module: ModuleType = self._load()
        return dir(module)

    def __repr__(self) -> str:
        if not self._module:
            return f"<module '{self.__name__} (Not loaded yet)'>"
        return repr(self._module)


@overload
def lazy(n: str) -> LazyLoader: ...
@overload
def lazy(n: str, attr: str, *rest: None) -> LazyAttr: ...
@overload
def lazy(n: str, attr: str, *rest: str) -> tuple[LazyAttr, ...]: ...
def lazy(n: str, attr: str | None = None, *rest: Any) -> LazyLoader | tuple[LazyAttr, ...] | LazyAttr:
    """Lazily load a module by its full name.

    Args:
        n (str): The full name of the module to load.
        attr (str | None): The attribute name to load lazily from the module. Default is None.
        *rest (str | None): Additional attribute names to load lazily from the module. Default is None.

    Returns:
        LazyLoader | tuple[LazyAttr, ...] | LazyAttr: The loaded module, a tuple of lazy attributes, or a single lazy attribute.

    Raises:
        ImportError: If the module cannot be found or loaded.
    """
    frame: FrameType | None = inspect.currentframe()
    logger.debug("[LAZY IMPORT] Creating LazyLoader for module '%s'", n)
    loader: LazyLoader = LazyLoader(n, 1, frame)
    if attr is None:
        return loader
    if not rest:
        return loader.to(attr)
    return loader.to_many(attr, *rest)


__all__ = ["LazyLoader", "lazy"]
