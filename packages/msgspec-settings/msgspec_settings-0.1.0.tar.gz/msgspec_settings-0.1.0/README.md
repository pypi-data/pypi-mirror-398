# msgspec-settings

Type-safe settings from environment variables and Docker secrets using msgspec.

## Description

msgspec-settings is a lightweight library for loading application settings from environment variables and Docker secrets with automatic type validation using msgspec.Struct. It provides a schema-first approach where you define your configuration structure using msgspec's typed structs, and the library handles parsing, type conversion, and validation.

The library supports nested structures of arbitrary depth, automatic type casting for common Python types (str, int, float, bool), and follows a predictable environment variable naming convention with customizable prefixes. Values are loaded with priority: environment variables override Docker secrets.

## Installation

```bash
uv add msgspec-settings
```

or with pip:

```bash
pip install msgspec-settings
```

## Quick Start

```python
import msgspec
from msgspec_settings import BaseSettings

class PostgresConfig(msgspec.Struct, frozen=True):
    host: str
    port: int = 5432
    password: str
    
class DatabaseConfig(msgspec.Struct, frozen=True):
    postgres: PostgresConfig
    pool_size: int = 10
    
class AppSettings(BaseSettings):
    database: DatabaseConfig
    debug: bool = False

# Environment variables:
# APP__DATABASE__POSTGRES__HOST=localhost
# APP__DATABASE__POSTGRES__PORT=3306
# APP__DATABASE__POOL_SIZE=20

# Docker secret file:
# /run/secrets/app__database__postgres__password
# Contents: "super_secret_password"

settings = AppSettings(env_prefix="app", secrets_dir="/run/secrets")
print(settings.database.postgres.host)      # localhost
print(settings.database.postgres.port)      # 3306
print(settings.database.postgres.password)  # super_secret_password (from secret file)
print(settings.database.pool_size)          # 20
```

## License

MIT License - see LICENSE file for details.
