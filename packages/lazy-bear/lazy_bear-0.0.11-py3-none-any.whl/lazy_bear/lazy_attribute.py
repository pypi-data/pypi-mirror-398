"""Module providing a lazy-loaded attribute wrapper."""

from __future__ import annotations

from collections import OrderedDict
from threading import RLock
from typing import TYPE_CHECKING, Any, ClassVar, NamedTuple, NoReturn, final

from ._logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger

    from lazy_bear.lazy_imports import LazyLoader

_lock: RLock = RLock()

logger: Logger = get_logger("LazyAttr")


@final
class NotFoundType:
    """Sentinel type for not found attributes."""

    def __repr__(self) -> str:  # pragma: no cover
        return "<NOT_FOUND>"


@final
class NotSetType:
    """Sentinel type for not set attributes."""

    def __repr__(self) -> str:  # pragma: no cover
        return "<NOT_SET>"


NOT_FOUND: NotFoundType = NotFoundType()
NOT_SET: NotSetType = NotSetType()


class LazyAttrKey(NamedTuple):
    """Key for caching lazy attributes."""

    module_name: str  # loader._name
    attr_name: str


class CacheCheckResult(NamedTuple):
    """Result of checking the LazyAttr cache."""

    key: LazyAttrKey
    value: Any

    @property
    def found(self) -> bool:  # pragma: no cover
        return self.value != NOT_FOUND


class SimpleLRUCache[T]:
    """A simple LRU cache implementation."""

    def __init__(self, max_size: int = 128) -> None:
        self.max_size: int = max_size
        self._cache: OrderedDict[T, Any] = OrderedDict()

    def get(self, key: T, d: Any = NOT_FOUND) -> Any | NotFoundType:  # pragma: no cover
        """Get a value from the cache or return default if not found."""
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return d

    def set(self, key: T, value: Any) -> None:  # pragma: no cover
        self._cache[key] = value
        self._cache.move_to_end(key)
        if self.length > self.max_size:
            self._cache.popitem(last=False)

    def __contains__(self, key: T) -> bool:  # pragma: no cover
        return key in self._cache

    @property
    def length(self) -> int:  # pragma: no cover
        return len(self._cache)

    def clear(self) -> None:  # pragma: no cover
        self._cache.clear()


class LazyAttrMeta(type):
    _cached: ClassVar[SimpleLRUCache[LazyAttrKey]] = SimpleLRUCache()

    @classmethod
    def check_cache(cls, name: str, module_name: str) -> Any:  # pragma: no cover
        key: LazyAttrKey = LazyAttrKey(module_name, attr_name=name)
        return cls._cached.get(key)

    @classmethod
    def get_cache(cls, name: str, module_name: str) -> CacheCheckResult:  # pragma: no cover
        key: LazyAttrKey = LazyAttrKey(module_name, attr_name=name)
        return CacheCheckResult(key, cls._cached.get(key, NOT_FOUND))

    @classmethod
    def __attr_cache__(
        cls,
        name: str,
        module_name: str,
        loaded: Any | None = None,
        key: LazyAttrKey | None = None,
    ) -> Any:  # pragma: no cover
        """A cache for loaded attributes stored by (module_name, name).

        If you end up calling this, make sure you wrap it in a lock!
        """
        key = key if key is not None else LazyAttrKey(module_name, name)
        if key not in cls._cached:
            if loaded is None:
                from lazy_bear.lazy_imports import LazyLoader  # noqa: PLC0415

                loader: LazyLoader = LazyLoader(module_name)
                loaded = getattr(loader._load(), name)
            cls._cached.set(key, loaded)
        return cls._cached.get(key)


@final
class LazyAttr(metaclass=LazyAttrMeta):
    """A lazy-loaded attribute from a LazyLoader module."""

    __slots__: tuple = ("_attr_name", "_cached_attr", "_loader")

    _loader: LazyLoader
    _attr_name: str
    _cached_attr: Any

    def __init__(self, n: str, loader: LazyLoader) -> None:  # pragma: no cover
        """Initialize a lazy-loaded attribute."""
        object.__setattr__(self, "_loader", loader)
        object.__setattr__(self, "_attr_name", n)
        object.__setattr__(self, "_cached_attr", NOT_SET)
        logger.debug("[INIT] Created LazyAttr for attribute '%s' from module '%s'", n, loader._name)

    def _load_attr(self) -> Any:
        """Get the lazy-loaded attribute.

        This will load the attribute from the module if it hasn't been loaded yet.
        It will also replace the reference in the parent's globals to point to the
        loaded attribute for future accesses, basically getting rid of the LazyAttr wrapper.

        We want to get rid of the wrapper to avoid overhead on future accesses.

        Pytest will make this tricky to test since it frontloads modules and will
        trip this method early.
        """
        logger.debug("[LOAD] Loading attribute '%s' from module '%s'", self._attr_name, self._loader._name)
        cached: Any = self._cached_attr
        logger.debug("[CACHE CHECK] Cached value for '%s': %s", self._attr_name, cached)
        if cached is not NOT_SET:
            logger.debug("[CACHE HIT] Returning cached value for '%s'", self._attr_name)
            return cached
        logger.debug("[CACHE MISS] No cached value for '%s', loading...", self._attr_name)

        with _lock:
            if self._cached_attr is NOT_SET:
                cached_item: CacheCheckResult = LazyAttr.get_cache(self._attr_name, self._loader._name)
                if cached_item.found:
                    logger.debug("[CACHE HIT] Found cached value for '%s' in global cache", self._attr_name)
                    self._cached_attr = cached_item.value
                    return self._cached_attr
                self._cached_attr = getattr(self._loader._load(), self._attr_name, NOT_FOUND)
                parent_globals: dict[str, Any] = self._loader._parent_globals
                global_attr: Any | NotFoundType = parent_globals.get(self._attr_name, NOT_FOUND)
                logger.debug("[GLOBAL CHECK] Global attr for '%s': %s", self._attr_name, global_attr)
                if global_attr is not NOT_FOUND and global_attr is self:
                    logger.debug("[GLOBAL UPDATE] Updating parent globals for '%s'", self._attr_name)
                    parent_globals[self._attr_name] = self._cached_attr
                LazyAttr.__attr_cache__(self._attr_name, self._loader._name, self._cached_attr, key=cached_item.key)
            if self._cached_attr is NOT_SET or self._cached_attr is NOT_FOUND:
                raise AttributeError(f"Attribute '{self._attr_name}' not found in module '{self._loader._name}'")
            logger.debug("[LOAD COMPLETE] Loaded attribute '%s': %s", self._attr_name, self._cached_attr)
            return self._cached_attr

    def _ensure_loaded(self) -> Any:
        """Ensure the attribute is loaded and return it.

        Returns:
            Any: Load the attribute if not already loaded, otherwise return the cached value.
        """
        return self._cached_attr if self._cached_attr is not NOT_SET else self._load_attr()

    @property
    def value(self) -> Any:  # pragma: no cover
        """Get the lazy-loaded attribute value."""
        return self._ensure_loaded()

    def unwrap(self) -> Any:  # pragma: no cover
        """Alias for value to get the lazy-loaded attribute."""
        return self._ensure_loaded()

    @property
    def __class__(self) -> type:  # pragma: no cover
        """Return the class of the wrapped value for transparent type checking.

        We use metaclass magic in order to make picking just work seamlessly.
        """
        if self._cached_attr is not NOT_SET:
            return self._cached_attr.__class__
        return type(self)

    @__class__.setter
    def __class__(self, value: type) -> NoReturn:  # pragma: no cover
        raise TypeError("Cannot set __class__ on LazyAttr")

    def __reduce__(self) -> tuple[Callable[[str, str], Any], tuple[str, str]]:  # pragma: no cover
        """Allow pickling by returning reconstruction info."""
        self._ensure_loaded()
        if self._cached_attr is NOT_FOUND or self._cached_attr is NOT_SET:
            logger.error("[PICKLE ERROR] Cannot pickle LazyAttr with unloaded value: %s", self._cached_attr)
            raise TypeError(f"Cannot pickle LazyAttr with {self._cached_attr} value")
        return (LazyAttr.__attr_cache__, (self._attr_name, self._loader._name))

    @property
    def __wrapped__(self) -> Any:  # pragma: no cover
        """PEP 8 standard attribute for accessing wrapped object.

        This will trigger the loading of the attribute if it hasn't been loaded yet.
        """
        return self._ensure_loaded()

    def __call__(self, *args, **kwargs) -> Any:  # pragma: no cover
        """Call the lazy-loaded attribute if it is callable."""
        target: Callable[..., Any] = self._ensure_loaded()
        if not callable(target):
            logger.error("[CALL ERROR] Attempted to call non-callable attribute '%s'", self._attr_name)
            raise TypeError(f"Attribute '{self._attr_name}' is not callable.")
        return target(*args, **kwargs)

    def __get__(self, instance: Any, owner: type | None = None) -> Any:  # pragma: no cover
        """Support descriptor protocol to allow LazyAttr to be used as a descriptor."""
        logger.debug("[DESCRIPTOR GET] Getting descriptor for '%s'", self._attr_name)
        self._ensure_loaded()
        if hasattr(self._cached_attr, "__get__"):
            return self._cached_attr.__get__(instance, owner)
        if self._cached_attr is NOT_FOUND or self._cached_attr is NOT_SET:
            logger.error(
                "[DESCRIPTOR ERROR] Attribute '%s' not found in module '%s'", self._attr_name, self._loader._name
            )
            raise AttributeError(f"Attribute '{self._attr_name}' not found in module '{self._loader._name}'")
        return self._cached_attr

    def __subclasscheck__(self, subclass: type) -> bool:  # pragma: no cover
        return issubclass(subclass, self._ensure_loaded())

    def __instancecheck__(self, instance: Any) -> bool:  # pragma: no cover
        logger.debug("[INSTANCE CHECK] Checking instance for '%s'", self._attr_name)
        return isinstance(instance, self._ensure_loaded())

    def __getattr__(self, name: str) -> Any:  # pragma: no cover
        logger.debug("[GETATTR] Getting attribute '%s' from LazyAttr '%s'", name, self._attr_name)
        if name in self.__slots__:
            return super().__getattribute__(name)
        self._ensure_loaded()
        if name == "_attr":
            if self._cached_attr is NOT_FOUND or self._cached_attr is NOT_SET:
                logger.error(
                    "[GETATTR ATTRIBUTE ERROR] '%s' not found in module '%s'", self._attr_name, self._loader._name
                )
                raise AttributeError(f"Attribute '{self._attr_name}' not found in module '{self._loader._name}'")
            return self._cached_attr
        if not hasattr(self._cached_attr, name):
            logger.error("[GETATTR ATTRIBUTE ERROR] '%s' has no attribute '%s'", self._attr_name, name)
            raise AttributeError(f"Attribute '{name}' not found in '{type(self._cached_attr).__name__}'")
        logger.debug("[GETATTR SUCCESS] Found attribute '%s' in '%s'", name, self._attr_name)
        return getattr(self._cached_attr, name)

    def __setattr__(self, name: str, value: Any) -> None:  # pragma: no cover
        logger.debug("[SETATTR] Setting attribute '%s' on LazyAttr '%s' to '%s'", name, self._attr_name, value)
        if name in self.__slots__:
            super().__setattr__(name, value)
            return
        if name == "__class__":
            logger.error("[SETATTR CLASS ERROR] Attempt to set __class__ on LazyAttr '%s'", self._attr_name)
            raise TypeError("Cannot set __class__ on LazyAttr")
        if self._cached_attr is NOT_SET:
            logger.error("[SETATTR LOAD ERROR] Cannot set attribute '%s' before '%s' is loaded", name, self._attr_name)
            raise AttributeError(f"Cannot set attribute '{name}' before '{self._attr_name}' is loaded.")
        self._ensure_loaded()
        logger.debug("[SETATTR SUCCESS] Setting attribute '%s' on loaded attribute '%s'", name, self._attr_name)
        setattr(self._cached_attr, name, value)

    def __dir__(self) -> list[str]:  # pragma: no cover
        """List the attributes of the lazy-loaded attribute.

        This will trigger the loading of the attribute if it hasn't been loaded yet.
        """
        return dir(self._ensure_loaded())

    def __getitem__(self, key: str) -> Any:  # pragma: no cover
        return self._ensure_loaded()[key]

    def _error(self, op: str, other: Any) -> NoReturn:  # pragma: no cover
        raise TypeError(
            f"Unsupported operand type(s) for {op}: '{type(self._cached_attr).__name__}' and '{type(other).__name__}'"
        )

    def __setitem__(self, key: str, value: Any) -> None:  # pragma: no cover
        self._ensure_loaded()[key] = value

    def __iter__(self) -> Any:  # pragma: no cover
        if not hasattr(self._ensure_loaded(), "__iter__"):
            self._error("iter()", self._cached_attr)
        return iter(self._cached_attr)

    def __contains__(self, item: object) -> bool:  # pragma: no cover
        if not hasattr(self._ensure_loaded(), "__contains__"):
            self._error("in", item)
        return item in self._cached_attr

    def __or__(self, other: Any) -> Any:  # pragma: no cover
        if not hasattr(self._ensure_loaded(), "__or__"):
            self._error("|", other)
        return self._cached_attr | other

    def __ror__(self, other: Any) -> Any:  # pragma: no cover
        if not hasattr(self._ensure_loaded(), "__ror__"):
            self._error("|", other)
        return other | self._cached_attr

    def __eq__(self, other: object) -> bool:  # pragma: no cover
        if not hasattr(self._ensure_loaded(), "__eq__"):
            self._error("==", other)
        return self._cached_attr == other

    def __ne__(self, other: object) -> bool:  # pragma: no cover
        if not hasattr(self._ensure_loaded(), "__ne__"):
            self._error("!=", other)
        return self._cached_attr != other

    def __lt__(self, other: object) -> bool:  # pragma: no cover
        if not hasattr(self._ensure_loaded(), "__lt__"):
            self._error("<", other)
        return self._cached_attr < other

    def __le__(self, other: object) -> bool:  # pragma: no cover
        if not hasattr(self._ensure_loaded(), "__le__"):
            self._error("<=", other)
        return self._cached_attr <= other

    def __gt__(self, other: object) -> bool:  # pragma: no cover
        if not hasattr(self._ensure_loaded(), "__gt__"):
            self._error(">", other)
        return self._cached_attr > other

    def __ge__(self, other: object) -> bool:  # pragma: no cover
        if not hasattr(self._ensure_loaded(), "__ge__"):
            self._error(">=", other)
        return self._cached_attr >= other

    def __len__(self) -> int:  # pragma: no cover
        self._ensure_loaded()
        try:
            return len(self._cached_attr)
        except TypeError:
            self._error("len()", self._cached_attr)

    def __bool__(self) -> bool:  # pragma: no cover
        return (self._cached_attr is not NOT_FOUND and self._cached_attr is not NOT_SET) and bool(self._ensure_loaded())

    def __add__(self, other: Any) -> Any:  # pragma: no cover
        self._ensure_loaded()
        if not hasattr(self._cached_attr, "__add__"):
            self._error("+", other)
        return self._cached_attr + other

    def __radd__(self, other: Any) -> Any:  # pragma: no cover
        self._ensure_loaded()
        if not hasattr(self._cached_attr, "__radd__"):
            self._error("+", other)
        return other + self._cached_attr

    def __sub__(self, other: Any) -> Any:  # pragma: no cover
        self._ensure_loaded()
        if not hasattr(self._cached_attr, "__sub__"):
            self._error("-", other)
        return self._cached_attr - other

    def __rsub__(self, other: Any) -> Any:  # pragma: no cover
        self._ensure_loaded()
        if not hasattr(self._cached_attr, "__rsub__"):
            self._error("-", other)
        return other - self._cached_attr

    def __mul__(self, other: Any) -> Any:  # pragma: no cover
        self._ensure_loaded()
        if not hasattr(self._cached_attr, "__mul__"):
            self._error("*", other)
        return self._cached_attr * other

    def __rmul__(self, other: Any) -> Any:  # pragma: no cover
        self._ensure_loaded()
        if not hasattr(self._cached_attr, "__rmul__"):
            self._error("*", other)
        return other * self._cached_attr

    def __truediv__(self, other: Any) -> Any:  # pragma: no cover
        self._ensure_loaded()
        if not hasattr(self._cached_attr, "__truediv__"):
            self._error("/", other)
        return self._cached_attr / other

    def __rtruediv__(self, other: Any) -> Any:  # pragma: no cover
        self._ensure_loaded()
        if not hasattr(self._cached_attr, "__rtruediv__"):
            self._error("/", other)
        return other / self._cached_attr

    def __hash__(self) -> int:  # pragma: no cover
        return hash(self._ensure_loaded())

    def __int__(self) -> int:  # pragma: no cover
        return int(self._ensure_loaded())

    def __float__(self) -> float:  # pragma: no cover
        return float(self._ensure_loaded())

    def __repr__(self) -> str:  # pragma: no cover
        if self._cached_attr is NOT_SET:
            return f"<lazy attribute '{self._attr_name}' from module '{self._loader._name}' (Not loaded yet)>"  # pyright: ignore[reportPrivateUsage]
        return repr(self._cached_attr)

    def __str__(self) -> str:  # pragma: no cover
        return str(self._ensure_loaded())


__all__ = ["LazyAttr"]
