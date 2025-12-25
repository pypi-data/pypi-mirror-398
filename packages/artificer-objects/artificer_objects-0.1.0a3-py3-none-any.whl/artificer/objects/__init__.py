"""Objects module - base class and registry for object stores."""

from artificer.objects.base import (
    BUILTIN_TYPES,
    BuiltinType,
    Object,
    ObjectModel,
)

__all__ = ["Object", "ObjectModel", "BuiltinType", "BUILTIN_TYPES"]
