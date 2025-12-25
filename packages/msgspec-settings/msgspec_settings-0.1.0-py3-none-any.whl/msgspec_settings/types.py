"""Type definitions and guards."""

from inspect import isclass
from typing import Any, TypeGuard

import msgspec

# Path to a field as list of keys
FieldPath = list[str]

# Single field schema: (path, type, is_required)
FieldSchema = tuple[FieldPath, type, bool]

# List of field schemas for a collection
AnnotationSchema = list[FieldSchema]

# Collection name -> field schemas
AnnotationsDict = dict[str, AnnotationSchema]

# Nested dict structure (can contain dicts or values)
NestedDict = dict[str, Any]

# Collection name -> skeleton dict
SkeletonsDict = dict[str, NestedDict]

# Parsed result: annotations and skeletons
ParseResult = tuple[AnnotationsDict, SkeletonsDict]


def is_struct(field_type: type) -> TypeGuard[type[msgspec.Struct]]:
    """Check if type is a msgspec.Struct subclass."""
    return isclass(field_type) and issubclass(field_type, msgspec.Struct)
