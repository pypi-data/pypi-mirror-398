# Lazy Bear

[![pypi version](https://img.shields.io/pypi/v/lazy-bear.svg)](https://pypi.org/project/lazy-bear/)
[![python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)

Lazy Bear is a lightweight toolkit for deferring Python imports until the first time you actually need them. Keep startup fast, trim optional dependencies, and expose a clean API without fighting `import` order.

## Highlights

- Drop-in `lazy("package.module")` helper that mirrors a regular module object once touched.
- `LazyLoader.to()` and `LazyLoader.to_many()` for lazily binding one or more attributes without importing the whole module up front.
- `LazyAttr.value` for grabbing the underlying attribute (dicts, constants, classes) without changing call semantics.
- Ideally the attribute would just be extracted but there are some issues when the item is defined within a local scope.
- Thread-safe module caching that updates `sys.modules` and the caller's globals exactly once.
- Debug-friendly repr and `dir()` support so interactive sessions stay intuitive even before loading.
- Batteries-included CLI with version info, environment diagnostics, and release bump helpers.

## Installation

Requires Python 3.13 or newer.

```bash
pip install lazy-bear
```

With [`uv`](https://docs.astral.sh/uv/):

```bash
uv tool install lazy-bear
```

## Quick Start

```python
from lazy_bear import lazy

json = lazy("json")  # nothing imported yet

payload = {"hello": "lazy bear"}
print(json.dumps(payload, sort_keys=True))
# Module is imported the first time .dumps is accessed.
```

Under the hood `lazy()` returns a `LazyLoader` (a `types.ModuleType` subclass). Once you touch an attribute it:

1. Imports the target module.
2. Registers it in both `sys.modules` and the globals of the caller.
3. Proxies the module so future access is indistinguishable from a normal import.

## Lazily Accessing Attributes

Sometimes you only need a specific callable or attribute, not the whole module namespace:

```python
from lazy_bear import LazyAttr, lazy

console = lazy("rich.console")
Console: LazyAttr = console.to("Console")

if __name__ == "__main__":
    rich_console = Console(width=100)  # `rich.console` is imported here
    rich_console.print("[bold green]Hello from Lazy Bear![/]")
```

Need multiple attributes or callables? Use `to_many`:

```python
math = lazy("math")
sqrt_attr, pow_attr = math.to_many("sqrt", "pow")

print(sqrt_attr(25))             # LazyAttr stays callable
pow_func = pow_attr.value        # or pow_attr.unwrap()
print(pow_func(2, 3))
```

`LazyAttr` proxies most dunder methods (`__call__`, `__iter__`, `__getitem__`, etc.), so lazily loaded attributes behave just like the originals.

When you need the underlying object—say a dictionary of settings—forgo calling and reach for `.value` (or its alias `.unwrap()`):

```python
env = lazy("os").to("environ").value                   # returns the real os._Environ mapping
letters = lazy("string").to("ascii_letters").unwrap()  # works for constants too
```

## __class__ Override

There is a __class__ override in the LazyAttr class in order to get things like `isinstance()` support to work as expected. It isn't
100% ideal but allows the wrapper to act as the wrapped object during the moments before the wrapper is destroyed.