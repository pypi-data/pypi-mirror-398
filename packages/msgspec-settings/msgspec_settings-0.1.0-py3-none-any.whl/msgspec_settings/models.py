"""Models for msgspec-settings."""

from pathlib import Path

import msgspec


class LoaderConfig(msgspec.Struct, frozen=True):
    """Configuration for environment variable and secrets loading."""

    env_prefix: str
    env_delimiter: str
    secrets_path: Path | None
    max_recursion_depth: int
