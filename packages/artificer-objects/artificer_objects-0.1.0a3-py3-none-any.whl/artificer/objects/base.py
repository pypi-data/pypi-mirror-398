"""Base Object class for object stores."""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar, Union

from pydantic import BaseModel

if TYPE_CHECKING:
    from fastmcp import FastMCP

# Supported builtin types for Object.model
BuiltinType = Union[str, bytes, int, float, bool]
BUILTIN_TYPES: tuple[type, ...] = (str, bytes, int, float, bool)

# Type alias for all supported model types
ObjectModel = Union[
    type[BaseModel], type[str], type[bytes], type[int], type[float], type[bool]
]


def _is_builtin_model(model: type) -> bool:
    """Check if a model type is a builtin type."""
    return model in BUILTIN_TYPES


def _serialize_value(value: Any, model: type) -> Any:
    """Serialize a value for JSON/MCP transport."""
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    # str, int, float, bool pass through directly
    return value


def _deserialize_value(data: Any, model: type) -> Any:
    """Deserialize a value from JSON/MCP transport to the model type."""
    if issubclass(model, BaseModel):
        return model.model_validate(data)
    if model is bytes:
        return base64.b64decode(data)
    if model is bool:
        # Handle string booleans from JSON
        if isinstance(data, str):
            return data.lower() in ("true", "1", "yes")
        return bool(data)
    # str, int, float - cast directly
    return model(data)  # type: ignore[call-arg]


def _get_builtin_schema(model: type) -> dict[str, Any]:
    """Get JSON schema for a builtin type."""
    if model is str:
        return {"type": "string"}
    if model is bytes:
        return {"type": "string", "contentEncoding": "base64"}
    if model is int:
        return {"type": "integer"}
    if model is float:
        return {"type": "number"}
    if model is bool:
        return {"type": "boolean"}
    raise ValueError(f"Unknown builtin type: {model}")


class Object(ABC):
    """Base class for object stores.

    Subclass this to create a custom object store. You must:
    1. Define a `model` class attribute with your Pydantic model or builtin type
       (str, bytes, int, float, bool)
    2. Implement `read(name)` to return an instance of your model
    3. Implement `write(name, data)` to persist an instance of your model
    4. Implement `delete(name)` to remove an object
    5. Implement `exists(name)` to check if an object exists
    6. Implement `list_objects()` to return names of all stored objects

    Optionally override `metadata(name)` to provide additional context about objects
    (e.g., file paths, timestamps).

    Example with Pydantic model:
        class FileSystemObject(Object):
            model = MyModel

            def __init__(self, path: str):
                self.path = Path(path)

            def read(self, name: str) -> MyModel:
                file_path = self.path / f"{name}.json"
                with open(file_path) as f:
                    return MyModel.model_validate_json(f.read())

            def write(self, name: str, data: MyModel) -> None:
                with open(self.path / f"{name}.json", 'w') as f:
                    f.write(data.model_dump_json())

            def metadata(self, name: str) -> dict[str, Any]:
                return {"path": str(self.path / f"{name}.json")}

            ...

    Example with builtin type:
        class StringStore(Object):
            model = str

            def read(self, name: str) -> str:
                return self._data[name]

            def write(self, name: str, data: str) -> None:
                self._data[name] = data
    """

    model: ClassVar[ObjectModel]
    _registry: ClassVar[dict[str, "Object"]] = {}
    _default_type: ClassVar[str | None] = None
    _mcp_tools_registered: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Ensure subclasses define a model
        if not hasattr(cls, "model"):
            raise TypeError(f"{cls.__name__} must define a 'model' class attribute")

    @abstractmethod
    def read(self, name: str) -> BaseModel | BuiltinType:
        """Read an object by name and return it as a model instance."""
        raise NotImplementedError

    @abstractmethod
    def write(self, name: str, data: BaseModel | BuiltinType) -> None:
        """Write a model instance to the store."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, name: str) -> None:
        """Delete an object by name."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check if an object exists by name."""
        raise NotImplementedError

    @abstractmethod
    def list_objects(self) -> list[str]:
        """List all object names in the store."""
        raise NotImplementedError

    def metadata(self, name: str) -> dict[str, Any]:
        """Return metadata for an object.

        Override this method to provide additional context about objects,
        such as file paths, timestamps, or other useful information.

        Args:
            name: The name/identifier of the object

        Returns:
            A dict of metadata. Default implementation returns empty dict.
        """
        return {}

    @classmethod
    def register(
        cls,
        mcp: "FastMCP",
        instance: "Object | None" = None,
        *,
        default: bool = False,
    ) -> None:
        """Register this object type with a FastMCP instance.

        Args:
            mcp: The FastMCP instance to register with
            instance: An instance of the Object subclass. If not provided,
                     the class will be instantiated with no arguments.
            default: If True, this type becomes the default when object_type
                    is not specified. Only one type can be default.
        """
        if instance is None:
            instance = cls()

        type_name = cls.__name__
        Object._registry[type_name] = instance

        if default:
            Object._default_type = type_name

        # Register shared tools on first registration
        if not Object._mcp_tools_registered:
            _register_shared_tools(mcp)
            Object._mcp_tools_registered = True

    @classmethod
    def get_registered_types(cls) -> list[str]:
        """Get list of registered object type names."""
        return list(cls._registry.keys())

    @classmethod
    def get_default_type(cls) -> str | None:
        """Get the default object type name, if set."""
        return cls._default_type

    @classmethod
    def get_instance(cls, type_name: str) -> "Object":
        """Get a registered object instance by type name."""
        if type_name not in cls._registry:
            raise KeyError(f"Object type '{type_name}' is not registered")
        return cls._registry[type_name]


def _register_shared_tools(mcp: "FastMCP") -> None:
    """Register the shared object_* tools with MCP."""

    @mcp.tool()
    def object_types() -> list[str]:
        """List all registered object types."""
        return Object.get_registered_types()

    @mcp.tool()
    def object_read(name: str, object_type: str | None = None) -> Any:
        """Read an object by name.

        Args:
            name: The name/identifier of the object to read
            object_type: The object type. Uses default if not specified.

        Returns:
            For Pydantic models: a dict representation
            For builtin types: the value (bytes are base64 encoded)
        """
        type_name = _resolve_type(object_type)
        instance = Object.get_instance(type_name)
        result = instance.read(name)
        return _serialize_value(result, instance.model)

    @mcp.tool()
    def object_write(name: str, data: Any, object_type: str | None = None) -> str:
        """Write an object to the store.

        Args:
            name: The name/identifier for the object
            data: The object data matching the type's schema
                  For Pydantic models: a dict
                  For builtin types: the value (bytes should be base64 encoded)
            object_type: The object type. Uses default if not specified.
        """
        type_name = _resolve_type(object_type)
        instance = Object.get_instance(type_name)
        model_instance = _deserialize_value(data, instance.model)
        instance.write(name, model_instance)
        return f"Successfully wrote '{name}' to {type_name}"

    @mcp.tool()
    def object_delete(name: str, object_type: str | None = None) -> str:
        """Delete an object from the store.

        Args:
            name: The name/identifier of the object to delete
            object_type: The object type. Uses default if not specified.
        """
        type_name = _resolve_type(object_type)
        instance = Object.get_instance(type_name)
        instance.delete(name)
        return f"Successfully deleted '{name}' from {type_name}"

    @mcp.tool()
    def object_exists(name: str, object_type: str | None = None) -> bool:
        """Check if an object exists in the store.

        Args:
            name: The name/identifier of the object to check
            object_type: The object type. Uses default if not specified.
        """
        type_name = _resolve_type(object_type)
        instance = Object.get_instance(type_name)
        return instance.exists(name)

    @mcp.tool()
    def object_list(object_type: str | None = None) -> list[str]:
        """List all objects in the store.

        Args:
            object_type: The object type. Uses default if not specified.
        """
        type_name = _resolve_type(object_type)
        instance = Object.get_instance(type_name)
        return instance.list_objects()

    @mcp.tool()
    def object_schema(object_type: str | None = None) -> dict[str, Any]:
        """Get the JSON schema for an object type.

        Args:
            object_type: The object type. Uses default if not specified.
        """
        type_name = _resolve_type(object_type)
        instance = Object.get_instance(type_name)
        if _is_builtin_model(instance.model):
            return _get_builtin_schema(instance.model)
        return instance.model.model_json_schema()  # type: ignore[union-attr]

    @mcp.tool()
    def object_metadata(name: str, object_type: str | None = None) -> dict[str, Any]:
        """Get metadata for an object.

        Returns additional context about the object such as file paths,
        timestamps, or other implementation-specific information.

        Args:
            name: The name/identifier of the object
            object_type: The object type. Uses default if not specified.
        """
        type_name = _resolve_type(object_type)
        instance = Object.get_instance(type_name)
        return instance.metadata(name)


def _resolve_type(type_name: str | None) -> str:
    """Resolve the object type, using default if available."""
    registered = Object.get_registered_types()

    if not registered:
        raise RuntimeError("No object types are registered")

    if type_name is not None:
        if type_name not in registered:
            raise ValueError(
                f"Unknown object type '{type_name}'. "
                f"Available types: {', '.join(registered)}"
            )
        return type_name

    # Use default if set
    default = Object.get_default_type()
    if default is not None:
        return default

    # Fall back to single registered type
    if len(registered) == 1:
        return registered[0]

    raise ValueError(
        f"Multiple object types registered ({', '.join(registered)}). "
        "Please specify 'object_type' or register one with default=True."
    )
