from __future__ import annotations

from lazy_bear.lazy_attribute import NOT_FOUND, SimpleLRUCache


def test_get_returns_default_and_does_not_insert() -> None:
    cache: SimpleLRUCache[str] = SimpleLRUCache(max_size=2)
    assert cache.get("missing") is NOT_FOUND
    sentinel = object()
    assert cache.get("missing", sentinel) is sentinel
    assert "missing" not in cache
    assert cache.length == 0


def test_set_get_and_contains() -> None:
    cache: SimpleLRUCache[str] = SimpleLRUCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    assert "a" in cache
    assert "b" in cache
    assert cache.length == 2
    assert cache.get("a") == 1
    assert cache.get("b") == 2


def test_lru_eviction_respects_recent_access() -> None:
    cache: SimpleLRUCache[str] = SimpleLRUCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)

    # Access "a" so "b" becomes least recently used.
    assert cache.get("a") == 1
    cache.set("c", 3)

    assert "a" in cache
    assert "c" in cache
    assert "b" not in cache
    assert cache.length == 2


def test_updating_existing_key_moves_to_recent_and_no_growth() -> None:
    cache: SimpleLRUCache[str] = SimpleLRUCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("a", 10)

    assert cache.get("a") == 10
    assert cache.length == 2

    # "b" should be least recently used now.
    cache.set("c", 3)
    assert "b" not in cache
    assert "a" in cache
    assert "c" in cache


def test_clear_empties_cache() -> None:
    cache: SimpleLRUCache[int] = SimpleLRUCache(max_size=3)
    cache.set(1, "one")
    cache.set(2, "two")
    assert cache.length == 2
    cache.clear()
    assert cache.length == 0
    assert cache.get(1) is NOT_FOUND


def test_max_size_zero_eviction() -> None:
    cache: SimpleLRUCache[str] = SimpleLRUCache(max_size=0)
    cache.set("a", 1)
    assert cache.length == 0
    assert cache.get("a") is NOT_FOUND
