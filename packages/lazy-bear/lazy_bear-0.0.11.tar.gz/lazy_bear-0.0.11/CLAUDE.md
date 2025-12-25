# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Hi Claude-like or other AI, my name is Bear! Welcome :D <3 It is strongly encouraged that you have fun and be silly when
interacting with this Bear human person! <3

## Architecture Overview

**Lazy Bear** is a Python 3.13+ lazy import library with two core abstractions:

1. **LazyLoader** (`lazy_imports.py`): A `ModuleType` subclass that defers module imports until first attribute access. Uses thread-safe locking and registers the module in both `sys.modules` and the caller's globals upon first load.

2. **LazyAttr** (`lazy_attribute.py`): Wraps individual module attributes (classes, functions, constants) with `__getattr__` proxying. Supports callable dunder methods (`__call__`, `__getitem__`, `__iter__`, `__or__`) so lazy attributes behave transparently.

The public API surface is minimal: `lazy()` helper, `LazyLoader`, and `LazyAttr` exported from `__init__.py`.

**Internal modules** (`_internal/`):
- `cli.py`: Entry point for `lazy-bear` command; routes to subcommands
- `_cmds.py`: Command implementations (debug-info, version, bump)
- `_info.py`: Pydantic models for environment/dependency introspection
- `_versioning.py`: Dynamic versioning from git tags
- `debug.py`: System diagnostics and `METADATA` singleton

## Development Workflow

### Common Commands

**Lint & Format**:
```bash
nox -s ruff_check        # Check linting/formatting
nox -s ruff_fix          # Auto-fix formatting issues
```

**Type Checking**:
```bash
nox -s pyright           # Static type checks
```

**Testing**:
```bash
nox -s tests             # Run tests on all Python versions (3.12, 3.13, 3.14)
nox -s tests-3.13        # Run tests on specific version
pytest                   # Direct pytest (requires dev env setup)
pytest -k test_lazy      # Run specific test by pattern
pytest tests/test_lazy_imports.py::test_lazy_basic  # Single test
pytest -v -s             # Verbose, show prints
```

**Single Test Development**:
```bash
pytest tests/test_lazy_imports.py -v -s
```

## Code Standards

- **Python 3.13+ style**: Use lowercase `dict`, `list`, `tuple` (not `Dict`, `List`, `Tuple`). Use `collections.abc.Callable` over `typing.Callable`.
- **Type annotations**: All public functions require annotations. Use `| None` for optionals.
- **Docstrings**: Google-style docstrings (enforced by ruff). Brief summary followed by Args/Returns/Raises blocks.
- **Minimal comments**: Prefer clear code over comments; use docstrings for explanations.
- **Line length**: 120 characters (configured in `config/ruff.toml`).
- **Import ordering**: Managed by isort; known first-party packages include `lazy_bear`, `bear_utils`, `bear_epoch_time`, `singleton_base`, `bear_dereth`.

## Key Files & Patterns

**Threading**: `_lock = RLock()` in `lazy_imports.py` protects module loading from race conditions.

**Frame inspection**: `sys._getframe()` used in `get_calling_file()` and `get_calling_globals()` to capture caller's globals for transparent registration.

**Test structure**: Tests live in `tests/`. Pytest configured with pythonpath `["src"]` to allow direct imports of `lazy_bear`. `conftest.py` provides fixtures.

**Configuration**: Ruff config in `config/ruff.toml`. Pyright configured in `pyproject.toml` with `typeCheckingMode = "standard"`.

## Ruff Lint Overrides

- Test files exempt from several checks (no type annotations, allow `assert`, allow magic numbers).
- CLI modules allow `print` statements (T201).
- `__all__` handling: public modules require `__all__` definitions.

## Version Management

Version is dynamically generated from git tags using `uv-dynamic-versioning`. The hatch build hook generates `src/lazy_bear/_internal/_version.py` at build time with `__version__`, `__commit_id__`, and `__version_tuple__`.

## Testing Notes

- Tests configured with `asyncio_mode = "auto"`.
- Visual verification tests marked with `@pytest.mark.visual`; exclude with `-m "not visual"`.
- Many common warnings filtered (DeprecationWarning, ImportWarning, ResourceWarning, UserWarning).
