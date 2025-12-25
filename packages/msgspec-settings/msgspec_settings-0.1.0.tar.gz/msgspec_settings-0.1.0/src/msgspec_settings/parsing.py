"""Parse settings class annotations into schema."""

import logging

import msgspec

from .exceptions import RecursionLimitError, UnsupportedFieldTypeError
from .models import LoaderConfig
from .types import AnnotationSchema, FieldPath, NestedDict, ParseResult, is_struct


def parse_annotations(*, settings_cls: type, config: LoaderConfig, logger: logging.Logger) -> ParseResult:
    """Parse settings class annotations into flat list and skeleton dict.

    Returns:
        Tuple of (annotations dict, skeletons dict) where:
        - annotations: {collection: [(path, type, is_required), ...]}
        - skeletons: {collection: nested empty dict structure}
    """
    result = {}
    skeletons = {}
    for field_name, field_type in settings_cls.__annotations__.items():
        if not is_struct(field_type):
            raise UnsupportedFieldTypeError(field_type=field_type, path=[field_name])
        items, skeleton = parse_struct(field_type, path=[], config=config)
        result[field_name] = items
        skeletons[field_name] = skeleton
    return result, skeletons


def parse_struct(
    cls: type[msgspec.Struct],
    *,
    path: FieldPath,
    config: LoaderConfig,
    depth: int = 0,
) -> tuple[AnnotationSchema, NestedDict]:
    """Recursively parse msgspec.Struct into flat list and skeleton.

    Returns:
        Tuple of (items list, skeleton dict) where:
        - items: [(path, type, is_required), ...] for leaf fields
        - skeleton: nested empty dict structure for struct fields
    """
    depth += 1
    if depth > config.max_recursion_depth:
        raise RecursionLimitError(path=path, max_depth=config.max_recursion_depth)

    schema: AnnotationSchema = []
    skeleton: NestedDict = {}
    for field in msgspec.structs.fields(cls):
        new_path = make_path(path, field.name)
        if is_struct(field.type):
            items, subskeleton = parse_struct(field.type, path=new_path, config=config, depth=depth)
            schema += items
            skeleton[field.name] = subskeleton
        else:
            schema.append((new_path, field.type, check_is_required(field)))
    return schema, skeleton


def check_is_required(field: msgspec.structs.FieldInfo) -> bool:
    """Check if field is required (no default value)."""
    return field.default is msgspec.NODEFAULT and field.default_factory is msgspec.NODEFAULT


def make_path(base_path: FieldPath, field_name: str) -> FieldPath:
    """Build new path by appending field name."""
    return base_path + [field_name]
