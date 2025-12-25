"""Base settings class."""

import logging
import re
from pathlib import Path

import msgspec

from .exceptions import ConfigError
from .loading import build_nested_dict
from .models import LoaderConfig
from .parsing import parse_annotations
from .types import is_struct

ENV_PREFIX_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
ENV_DELIMITER = "__"


def setup_logger(name: str = __name__, *, level=logging.INFO) -> logging.Logger:
    logging.basicConfig(level=level)
    logger = logging.getLogger(name)
    return logger


class BaseSettings:
    """Base settings class with env/secrets loading.

    Automatically loads values from environment variables and Docker secrets
    on instance creation using a schema-first approach.

    Uses msgspec.structs.fields() for lazy loading and comprehensive validation
    before loading.

    Args:
        env_prefix: Prefix for environment variables. Defaults to "app".
        secrets_path: Directory for Docker secrets. Defaults to "/run/secrets".
        max_recursion_depth: Maximum recursion depth for parsing annotations. Defaults to 10.
        logger: Optional logger instance. If not provided, a default logger is created.
    """

    def __init__(
        self,
        *,
        env_prefix: str = "app",
        secrets_dir: str | None = "/run/secrets",
        max_recursion_depth: int = 10,
        logger: logging.Logger | None = None,
    ) -> None:
        self.logger = logger or setup_logger(__name__)
        config = LoaderConfig(
            env_prefix=self._prepare_env_prefix(env_prefix),
            secrets_path=self._prepare_path(secrets_dir),
            env_delimiter=ENV_DELIMITER,
            max_recursion_depth=max_recursion_depth,
        )
        annotations, skeletons = parse_annotations(settings_cls=self.__class__, config=config, logger=self.logger)
        nested_dict = build_nested_dict(annotations=annotations, skeletons=skeletons, config=config, logger=self.logger)

        for field_name, field_type in self.__class__.__annotations__.items():
            if not is_struct(field_type):
                continue
            result = msgspec.convert(nested_dict[field_name], type=field_type)
            setattr(self, field_name, result)

    def _prepare_env_prefix(self, value: str) -> str:
        """Validate env prefix."""
        prefix = value.strip().lower()
        if not ENV_PREFIX_PATTERN.match(prefix):
            self.logger.error(f"Invalid env prefix: '{value}'")
            raise ConfigError(f"Invalid env prefix: '{value}' (must match pattern: [a-zA-Z_][a-zA-Z0-9_]*)")
        return prefix

    def _prepare_path(self, secrets_path: str | None) -> Path | None:
        """Prepare secrets directory path."""
        if secrets_path is None:
            return None

        path = Path(secrets_path)
        if not path.exists() or not path.is_dir():
            self.logger.warning(f"Secrets directory does not exist or is not a directory: '{secrets_path}'")
            return None

        return path
