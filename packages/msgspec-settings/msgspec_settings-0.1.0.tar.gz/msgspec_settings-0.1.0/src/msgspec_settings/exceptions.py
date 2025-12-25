"""Exception classes for msgspec_settings."""


class MsgspecSettingsException(Exception):
    """Base exception for all msgspec_settings errors."""


class ValueLoadingError(MsgspecSettingsException):
    """Base class for errors loading specific values from env or secrets."""

    def __init__(self, message: str, *args, collection: str, path: list[str], **kwargs):
        self.message = message
        self.path = path
        self.collection = collection
        super().__init__(message, *args, **kwargs)

    def __repr__(self):
        message = f"{self.__class__.__name__}: {self.collection}.{'.'.join(self.path)}"
        message += f" - {self.message}"
        return message


class ValueRequiredError(ValueLoadingError):
    """Required value not found in env or secrets."""

    def __init__(self, *args, collection: str, path: list[str], **kwargs):
        super().__init__("Required value not found", *args, collection=collection, path=path, **kwargs)


class ValueCastError(ValueLoadingError):
    """Value cannot be cast to target type."""

    def __init__(self, *args, collection: str, path: list[str], target_type: type | None = None, **kwargs):
        msg = "Cannot cast to target type"
        if target_type:
            msg += f" {target_type.__name__}"
        super().__init__(msg, *args, collection=collection, path=path, **kwargs)


class ValueEmptyError(ValueLoadingError):
    """Value found but is empty string."""

    def __init__(self, *args, collection: str, path: list[str], **kwargs):
        super().__init__("Value is empty", *args, collection=collection, path=path, **kwargs)


class SecretFileReadError(ValueLoadingError):
    """Secret file exists but cannot be read."""

    def __init__(self, *args, collection: str, path: list[str], file_path: str, **kwargs):
        super().__init__(f"Cannot read secret file {file_path}", *args, collection=collection, path=path, **kwargs)


class SchemaError(MsgspecSettingsException):
    """Base class for errors parsing settings schema."""

    def __init__(self, message: str, *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class UnsupportedFieldTypeError(SchemaError):
    """Field type is not supported (must be msgspec.Struct)."""

    def __init__(self, *args, field_type: type, path: list[str], **kwargs):
        message = f"Unsupported field type {field_type} at {'.'.join(path)} (must be msgspec.Struct)"
        super().__init__(message, *args, **kwargs)


class UnsupportedValueTypeError(SchemaError):
    """Value type is not supported (must be str/int/float/bool)."""

    def __init__(self, *args, field_type: type, path: list[str], **kwargs):
        message = f"Unsupported value type {field_type} at {'.'.join(path)} (must be str/int/float/bool)"
        super().__init__(message, *args, **kwargs)


class RecursionLimitError(SchemaError):
    """Maximum recursion depth exceeded during parsing."""

    def __init__(self, *args, path: list[str], max_depth: int, **kwargs):
        message = f"Recursion limit exceeded ({max_depth}) at {'.'.join(path)}"
        super().__init__(message, *args, **kwargs)


class NoAnnotationsError(SchemaError):
    """Settings class has no annotations."""

    def __init__(self, *args, settings_cls: type, **kwargs):
        message = f"Settings class {settings_cls.__name__} has no annotations"
        super().__init__(message, *args, **kwargs)


class SettingsBuildError(MsgspecSettingsException):
    """Error building settings from loaded values."""

    def __init__(self, message: str, *args, errors: list[ValueLoadingError] | None = None, **kwargs):
        self.errors = errors or []
        super().__init__(message, *args, **kwargs)


class ConfigError(MsgspecSettingsException):
    """Error in loader configuration parameters."""


__all__ = [
    "MsgspecSettingsException",
    "ValueLoadingError",
    "ValueRequiredError",
    "ValueCastError",
    "SchemaError",
    "UnsupportedFieldTypeError",
    "UnsupportedValueTypeError",
    "RecursionLimitError",
    "NoAnnotationsError",
    "SettingsBuildError",
]
