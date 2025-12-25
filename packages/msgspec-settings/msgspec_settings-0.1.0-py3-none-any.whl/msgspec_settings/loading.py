"""Load values from environment variables and secrets."""

import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from .exceptions import (
    SettingsBuildError,
    UnsupportedValueTypeError,
    ValueCastError,
    ValueLoadingError,
    ValueRequiredError,
)
from .models import LoaderConfig
from .types import AnnotationsDict, FieldPath, NestedDict, SkeletonsDict

INT_PATTERN = re.compile(r"^-?\d+$")
FLOAT_PATTERN = re.compile(r"^[+-]?\d+\.?\d*([eE][+-]?\d+)?$")


@lru_cache(maxsize=128)
def cast_int(value: str) -> int:
    """Cast string to int."""
    value = value.strip()
    if not _is_valid_int_string(value):
        raise ValueError("Cannot be casted to int")
    return int(value)


def _is_valid_int_string(value: str) -> bool:
    """Check if string is a valid integer."""
    return bool(INT_PATTERN.match(value))


@lru_cache(maxsize=128)
def cast_float(value: str) -> float:
    """Cast string to float."""
    value = value.strip()
    if not _is_valid_float_string(value):
        raise ValueError("Cannot be casted to float")
    return float(value)


def _is_valid_float_string(value: str) -> bool:
    """Check if string is a valid float."""
    return bool(FLOAT_PATTERN.match(value))


@lru_cache(maxsize=128)
def cast_bool(value: str) -> bool:
    """Cast string to bool. Accepts: true/false, 1/0, yes/no, on/off."""
    value = value.strip().lower()
    match value:
        case "true" | "1" | "yes" | "on":
            return True
        case "false" | "0" | "no" | "off":
            return False
        case _:
            raise ValueError("Cannot be casted to bool")


@lru_cache(maxsize=128)
def cast_str(value: str) -> str:
    """Cast string to str (identity)."""
    return value


def cast(value: str, field_type: type, *, collection: str, path: FieldPath) -> Any:
    """Cast string value to target type."""
    try:
        if field_type is int:
            return cast_int(value)
        elif field_type is float:
            return cast_float(value)
        elif field_type is bool:
            return cast_bool(value)
        elif field_type is str:
            return cast_str(value)
        else:
            raise UnsupportedValueTypeError(collection=collection, path=path, field_type=field_type)
    except Exception as e:
        raise ValueCastError(collection=collection, path=path) from e


def make_key(collection: str, path: FieldPath, config: LoaderConfig) -> str:
    """Build key from collection and path."""
    return config.env_delimiter.join(([config.env_prefix, collection] + path))


def make_secret_file_path(collection: str, path: FieldPath, config: LoaderConfig) -> Path | None:
    """Build path to secret file."""
    if not config.secrets_path:
        return None
    return config.secrets_path / make_key(collection, path, config).lower()


def make_env_name(collection: str, path: FieldPath, config: LoaderConfig) -> str:
    """Build environment variable name."""
    return make_key(collection, path, config).upper()


def get_value(collection: str, path: FieldPath, field_type: type, config: LoaderConfig, required: bool = False) -> Any | None:
    """Get value from environment variable or secret file.

    Priority: env var > secret file > None (if optional) / raise (if required)
    """
    env_name = make_env_name(collection, path, config)

    if env_name in os.environ:
        return cast(os.environ[env_name], field_type, collection=collection, path=path)

    secret_file_path = make_secret_file_path(collection, path, config)
    if secret_file_path and secret_file_path.exists() and secret_file_path.is_file():
        return cast(secret_file_path.read_text(encoding="utf-8").strip(), field_type, collection=collection, path=path)

    if required:
        raise ValueRequiredError(collection=collection, path=path)

    return None


def build_nested_dict(
    *,
    annotations: AnnotationsDict,
    skeletons: SkeletonsDict,
    config: LoaderConfig,
    logger: logging.Logger,
) -> NestedDict:
    """Build nested dict from annotations, loading values from env/secrets.

    Uses skeleton as base structure to ensure all nested dicts exist.
    """
    result: NestedDict = {}
    errors: list[ValueLoadingError] = []

    for collection, items in annotations.items():
        collection_dict = skeletons[collection].copy() if collection in skeletons else {}

        for path, field_type, required in items:
            try:
                value = get_value(collection, path, field_type, config, required=required)
            except ValueLoadingError as e:
                errors.append(e)
            else:
                if value is None:
                    continue
                _current = collection_dict
                for key in path[:-1]:
                    if key not in _current:
                        _current[key] = {}
                    _current = _current[key]

                _current[path[-1]] = value

        result[collection] = collection_dict

    if errors:
        raise SettingsBuildError(
            "Errors occurred while loading settings:\n" + "\n".join([repr(e) for e in errors]),
            errors=errors,
        )
    return result
