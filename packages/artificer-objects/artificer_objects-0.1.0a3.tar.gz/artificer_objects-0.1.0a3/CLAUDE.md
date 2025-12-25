# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Artificer Objects is an object store framework exposed to agents as an MCP (Model Context Protocol) server. It provides a base `Object` class that can be subclassed to create custom object stores with CRUD operations.

## Development Commands

This project uses `uv` for dependency management and Python 3.13+.

```bash
# Install dependencies
uv sync

# Run all checks (lint, format, typecheck, tests)
./scripts/check.sh

# Individual checks
./scripts/lint.sh      # ruff check
./scripts/format.sh    # ruff format
./scripts/typecheck.sh # mypy
./scripts/test.sh      # pytest
```

## Architecture

```
artificer/
  objects/
    __init__.py      # Exports Object
    base.py          # Object ABC with registry and MCP registration
    features.py      # ObjectsFeature for artificer-cli integration
tests/
  test_object.py     # Unit tests
scripts/
  check.sh           # Run all checks
  format.sh          # Run ruff format
  lint.sh            # Run ruff check
  test.sh            # Run pytest
  typecheck.sh       # Run mypy
```

### Object Base Class (`base.py`)

- `Object` - Abstract base class for object stores
  - Subclasses must define `model` class attribute (Pydantic model or builtin: str, bytes, int, float, bool)
  - Subclasses must implement:
    - `read(name: str) -> Model`
    - `write(name: str, data: Model) -> None`
    - `delete(name: str) -> None`
    - `exists(name: str) -> bool`
    - `list_objects() -> list[str]`
  - Optionally override `metadata(name: str) -> dict[str, Any]` for additional context (e.g., file paths)
  - `Object.register(mcp, instance, default=False)` registers MCP tools
  - Use `default=True` to make a type the default when `object_type` is omitted

### MCP Tools (auto-registered)

When `Object.register(mcp)` is called, these shared tools are registered:
- `object_types()` - List registered object types
- `object_read(name, object_type?)` - Read object by name
- `object_write(name, data, object_type?)` - Write object to store
- `object_delete(name, object_type?)` - Delete object from store
- `object_exists(name, object_type?)` - Check if object exists
- `object_list(object_type?)` - List all objects in store
- `object_schema(object_type?)` - Get JSON schema for object type
- `object_metadata(name, object_type?)` - Get metadata for object (file paths, etc.)

The `object_type` parameter uses the default type if set, or the only registered type.

### CLI Integration (`features.py`)

`ObjectsFeature` integrates with `artificer-cli`:
- `artificer objects types` - List registered object types
- `artificer objects list [TYPE]` - List objects (with questionary selector)
- `artificer objects read [NAME] --type TYPE` - Read object
- `artificer objects write NAME DATA --type TYPE --file FILE` - Write object
- `artificer objects delete [NAME] --type TYPE` - Delete object
- `artificer objects exists NAME --type TYPE` - Check if object exists

Configure in `pyproject.toml`:
```toml
[tool.artificer]
features = ["artificer.objects.features.ObjectsFeature"]

[tool.artificer.objects]
modules = ["myapp.objects"]  # modules to import to register objects
```

## Example Usage

```python
from pydantic import BaseModel
from fastmcp import FastMCP
from artificer.objects import Object

class MyModel(BaseModel):
    name: str
    value: int

class MyObject(Object):
    model = MyModel

    def __init__(self, storage_path: str):
        self.path = storage_path

    def read(self, name: str) -> MyModel:
        # implementation
        ...

    def write(self, name: str, data: MyModel) -> None:
        # implementation
        ...

    def delete(self, name: str) -> None:
        # implementation
        ...

    def exists(self, name: str) -> bool:
        # implementation
        ...

    def list_objects(self) -> list[str]:
        # implementation
        ...

mcp = FastMCP()
MyObject.register(mcp, MyObject("/path/to/storage"), default=True)
mcp.run()
```
