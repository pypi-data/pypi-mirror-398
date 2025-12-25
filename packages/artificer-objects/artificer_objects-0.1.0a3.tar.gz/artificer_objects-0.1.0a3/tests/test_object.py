"""Tests for the Object base class."""

import tempfile
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from artificer.objects import Object


class SampleModel(BaseModel):
    """Sample model for object store tests."""

    name: str
    value: int


class FileSystemObject(Object):
    """Test implementation of Object using filesystem."""

    model = SampleModel

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)

    def read(self, name: str) -> SampleModel:
        file_path = self.path / f"{name}.json"
        with open(file_path) as f:
            return SampleModel.model_validate_json(f.read())

    def write(self, name: str, data: SampleModel) -> None:
        file_path = self.path / f"{name}.json"
        with open(file_path, "w") as f:
            f.write(data.model_dump_json())

    def delete(self, name: str) -> None:
        file_path = self.path / f"{name}.json"
        file_path.unlink()

    def exists(self, name: str) -> bool:
        file_path = self.path / f"{name}.json"
        return file_path.exists()

    def list_objects(self) -> list[str]:
        return [f.stem for f in self.path.glob("*.json")]

    def metadata(self, name: str) -> dict[str, Any]:
        return {"path": str(self.path / f"{name}.json")}


class TestObjectSubclass:
    """Test that Object subclasses work correctly."""

    def test_subclass_requires_model(self):
        """Subclass must define a model attribute."""
        with pytest.raises(TypeError, match="must define a 'model' class attribute"):

            class BadObject(Object):
                pass

    def test_subclass_with_model_succeeds(self):
        """Subclass with model attribute succeeds."""

        class GoodObject(Object):
            model = SampleModel

            def read(self, name: str) -> SampleModel:
                raise NotImplementedError

            def write(self, name: str, data: SampleModel) -> None:
                raise NotImplementedError

            def delete(self, name: str) -> None:
                raise NotImplementedError

            def exists(self, name: str) -> bool:
                raise NotImplementedError

            def list_objects(self) -> list[str]:
                raise NotImplementedError

        assert GoodObject.model is SampleModel


class TestObjectCRUD:
    """Test CRUD operations on Object implementations."""

    def test_write_and_read(self):
        """Write an object and read it back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemObject(tmpdir)
            data = SampleModel(name="test", value=42)

            store.write("myobj", data)
            result = store.read("myobj")

            assert result.name == "test"
            assert result.value == 42

    def test_metadata(self):
        """Test metadata method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemObject(tmpdir)
            data = SampleModel(name="test", value=42)

            store.write("myobj", data)
            meta = store.metadata("myobj")

            assert "path" in meta
            assert "myobj.json" in meta["path"]

    def test_exists(self):
        """Test exists method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemObject(tmpdir)
            data = SampleModel(name="test", value=42)

            assert not store.exists("myobj")
            store.write("myobj", data)
            assert store.exists("myobj")

    def test_delete(self):
        """Test delete method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemObject(tmpdir)
            data = SampleModel(name="test", value=42)

            store.write("myobj", data)
            assert store.exists("myobj")

            store.delete("myobj")
            assert not store.exists("myobj")

    def test_list_objects(self):
        """Test list_objects method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSystemObject(tmpdir)

            assert store.list_objects() == []

            store.write("obj1", SampleModel(name="a", value=1))
            store.write("obj2", SampleModel(name="b", value=2))

            objects = store.list_objects()
            assert len(objects) == 2
            assert "obj1" in objects
            assert "obj2" in objects


class TestObjectRegistry:
    """Test Object registry functionality."""

    def test_get_registered_types_empty(self):
        """Empty registry returns empty list."""
        assert Object.get_registered_types() == []

    def test_get_registered_types_after_register(self):
        """Registry contains registered types."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        with tempfile.TemporaryDirectory() as tmpdir:
            instance = FileSystemObject(tmpdir)
            FileSystemObject.register(mcp, instance)

            types = Object.get_registered_types()
            assert "FileSystemObject" in types

    def test_get_instance(self):
        """Get instance by type name."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        with tempfile.TemporaryDirectory() as tmpdir:
            instance = FileSystemObject(tmpdir)
            FileSystemObject.register(mcp, instance)

            retrieved = Object.get_instance("FileSystemObject")
            assert retrieved is instance

    def test_get_instance_unknown_type(self):
        """Get instance for unknown type raises KeyError."""
        with pytest.raises(KeyError, match="not registered"):
            Object.get_instance("UnknownType")

    def test_default_type(self):
        """Test default type registration."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        with tempfile.TemporaryDirectory() as tmpdir:
            instance = FileSystemObject(tmpdir)
            FileSystemObject.register(mcp, instance, default=True)

            assert Object.get_default_type() == "FileSystemObject"

    def test_no_default_type(self):
        """No default type when not set."""
        assert Object.get_default_type() is None


class TestMCPTools:
    """Test MCP tool registration."""

    def test_tools_registered(self):
        """MCP tools are registered on first Object registration."""
        from fastmcp import FastMCP

        mcp = FastMCP()
        with tempfile.TemporaryDirectory() as tmpdir:
            instance = FileSystemObject(tmpdir)
            FileSystemObject.register(mcp, instance)

            # Check that tools were registered
            tool_names = [t.name for t in mcp._tool_manager._tools.values()]
            assert "object_types" in tool_names
            assert "object_read" in tool_names
            assert "object_write" in tool_names
            assert "object_delete" in tool_names
            assert "object_exists" in tool_names
            assert "object_list" in tool_names
            assert "object_schema" in tool_names
            assert "object_metadata" in tool_names

    def test_tools_registered_once(self):
        """MCP tools are only registered once."""
        from fastmcp import FastMCP

        mcp = FastMCP()

        # Create two different Object subclasses
        class Object1(Object):
            model = SampleModel

            def read(self, name: str) -> SampleModel:
                raise NotImplementedError

            def write(self, name: str, data: SampleModel) -> None:
                raise NotImplementedError

            def delete(self, name: str) -> None:
                raise NotImplementedError

            def exists(self, name: str) -> bool:
                raise NotImplementedError

            def list_objects(self) -> list[str]:
                raise NotImplementedError

        class Object2(Object):
            model = SampleModel

            def read(self, name: str) -> SampleModel:
                raise NotImplementedError

            def write(self, name: str, data: SampleModel) -> None:
                raise NotImplementedError

            def delete(self, name: str) -> None:
                raise NotImplementedError

            def exists(self, name: str) -> bool:
                raise NotImplementedError

            def list_objects(self) -> list[str]:
                raise NotImplementedError

        Object1.register(mcp, Object1())
        Object2.register(mcp, Object2())

        # Count how many times each tool appears
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert tool_names.count("object_types") == 1


class StringObject(Object):
    """Test implementation of Object using string builtin."""

    model = str

    def __init__(self):
        self._data: dict[str, str] = {}

    def read(self, name: str) -> str:
        return self._data[name]

    def write(self, name: str, data: str) -> None:
        self._data[name] = data

    def delete(self, name: str) -> None:
        del self._data[name]

    def exists(self, name: str) -> bool:
        return name in self._data

    def list_objects(self) -> list[str]:
        return list(self._data.keys())


class IntObject(Object):
    """Test implementation of Object using int builtin."""

    model = int

    def __init__(self):
        self._data: dict[str, int] = {}

    def read(self, name: str) -> int:
        return self._data[name]

    def write(self, name: str, data: int) -> None:
        self._data[name] = data

    def delete(self, name: str) -> None:
        del self._data[name]

    def exists(self, name: str) -> bool:
        return name in self._data

    def list_objects(self) -> list[str]:
        return list(self._data.keys())


class BytesObject(Object):
    """Test implementation of Object using bytes builtin."""

    model = bytes

    def __init__(self):
        self._data: dict[str, bytes] = {}

    def read(self, name: str) -> bytes:
        return self._data[name]

    def write(self, name: str, data: bytes) -> None:
        self._data[name] = data

    def delete(self, name: str) -> None:
        del self._data[name]

    def exists(self, name: str) -> bool:
        return name in self._data

    def list_objects(self) -> list[str]:
        return list(self._data.keys())


class TestBuiltinTypes:
    """Test Object with builtin types instead of Pydantic models."""

    def test_string_object_crud(self):
        """Test CRUD with string model."""
        store = StringObject()
        store.write("key1", "hello world")

        assert store.exists("key1")
        assert store.read("key1") == "hello world"

        store.delete("key1")
        assert not store.exists("key1")

    def test_int_object_crud(self):
        """Test CRUD with int model."""
        store = IntObject()
        store.write("counter", 42)

        assert store.exists("counter")
        assert store.read("counter") == 42

        store.delete("counter")
        assert not store.exists("counter")

    def test_bytes_object_crud(self):
        """Test CRUD with bytes model."""
        store = BytesObject()
        store.write("binary", b"\x00\x01\x02\x03")

        assert store.exists("binary")
        assert store.read("binary") == b"\x00\x01\x02\x03"

        store.delete("binary")
        assert not store.exists("binary")

    def test_string_object_list(self):
        """Test list_objects with string model."""
        store = StringObject()
        store.write("a", "value a")
        store.write("b", "value b")

        objects = store.list_objects()
        assert len(objects) == 2
        assert "a" in objects
        assert "b" in objects

    def test_default_metadata_empty(self):
        """Test default metadata returns empty dict."""
        store = StringObject()
        store.write("key1", "value")
        assert store.metadata("key1") == {}


class TestBuiltinSerialization:
    """Test serialization of builtin types for MCP transport."""

    def test_serialize_string(self):
        """String values pass through unchanged."""
        from artificer.objects.base import _serialize_value

        assert _serialize_value("hello", str) == "hello"

    def test_serialize_int(self):
        """Int values pass through unchanged."""
        from artificer.objects.base import _serialize_value

        assert _serialize_value(42, int) == 42

    def test_serialize_float(self):
        """Float values pass through unchanged."""
        from artificer.objects.base import _serialize_value

        assert _serialize_value(3.14, float) == 3.14

    def test_serialize_bool(self):
        """Bool values pass through unchanged."""
        from artificer.objects.base import _serialize_value

        assert _serialize_value(True, bool) is True
        assert _serialize_value(False, bool) is False

    def test_serialize_bytes(self):
        """Bytes are base64 encoded."""
        from artificer.objects.base import _serialize_value

        result = _serialize_value(b"\x00\x01\x02", bytes)
        assert result == "AAEC"  # base64 of \x00\x01\x02

    def test_deserialize_string(self):
        """String values pass through unchanged."""
        from artificer.objects.base import _deserialize_value

        assert _deserialize_value("hello", str) == "hello"

    def test_deserialize_int(self):
        """Int values are cast from input."""
        from artificer.objects.base import _deserialize_value

        assert _deserialize_value(42, int) == 42
        assert _deserialize_value("42", int) == 42

    def test_deserialize_float(self):
        """Float values are cast from input."""
        from artificer.objects.base import _deserialize_value

        assert _deserialize_value(3.14, float) == 3.14
        assert _deserialize_value("3.14", float) == 3.14

    def test_deserialize_bool(self):
        """Bool values handle various inputs."""
        from artificer.objects.base import _deserialize_value

        assert _deserialize_value(True, bool) is True
        assert _deserialize_value(False, bool) is False
        assert _deserialize_value("true", bool) is True
        assert _deserialize_value("false", bool) is False
        assert _deserialize_value("TRUE", bool) is True
        assert _deserialize_value("1", bool) is True
        assert _deserialize_value("yes", bool) is True

    def test_deserialize_bytes(self):
        """Bytes are base64 decoded."""
        from artificer.objects.base import _deserialize_value

        result = _deserialize_value("AAEC", bytes)
        assert result == b"\x00\x01\x02"


class TestBuiltinSchema:
    """Test JSON schema generation for builtin types."""

    def test_string_schema(self):
        """String schema is correct."""
        from artificer.objects.base import _get_builtin_schema

        assert _get_builtin_schema(str) == {"type": "string"}

    def test_int_schema(self):
        """Int schema is correct."""
        from artificer.objects.base import _get_builtin_schema

        assert _get_builtin_schema(int) == {"type": "integer"}

    def test_float_schema(self):
        """Float schema is correct."""
        from artificer.objects.base import _get_builtin_schema

        assert _get_builtin_schema(float) == {"type": "number"}

    def test_bool_schema(self):
        """Bool schema is correct."""
        from artificer.objects.base import _get_builtin_schema

        assert _get_builtin_schema(bool) == {"type": "boolean"}

    def test_bytes_schema(self):
        """Bytes schema is correct with encoding."""
        from artificer.objects.base import _get_builtin_schema

        assert _get_builtin_schema(bytes) == {
            "type": "string",
            "contentEncoding": "base64",
        }
