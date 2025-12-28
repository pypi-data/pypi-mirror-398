# exit-stack-container

Async lifecycle management with declarative dependency injection for Python 3.13+.

Automatically initialize and cleanup resources (database, cache, clients) using async context managers.

## Installation

```bash
pip install exit-stack-container
```

## Quick Start

```python
from msgspec import Struct
from msgspec_settings import BaseSettings

from exit_stack_container import AsyncExitStackContainer, BaseResources, Dependency, on_exit

class Database:
    def __init__(self, host: str, port: int):
        print(f"Database connected to {host}:{port}")

    async def close(self):
        print("Database connection closed")

    async def query(self, query: str):
        print(f"Executing query: {query}")

class Usecase:
    def __init__(self, database: Database):
        self.database = database
        print(f"Usecase created with database at {database}")

    async def __call__(self):
        await self.database.query("SELECT * FROM table")

@on_exit(lambda db: db.close)
async def create_database(*, host: str, port: int) -> Database:
    return Database(host=host, port=port)

def create_usecase(*, database: Database) -> Usecase:
    return Usecase(database=database)

class DatabaseSettings(Struct, frozen=True):
    host: str = "localhost"
    port: int = 5432

class AppSettings(BaseSettings):
    database: DatabaseSettings

class AppResources(BaseResources[AppSettings]):
    usecase: Usecase

class AppContainer(AsyncExitStackContainer[AppSettings, AppResources]):
    _settings: AppSettings = AppSettings()

    database: Dependency = Dependency(
        create_database,
        host=_settings.database.host,
        port=_settings.database.port,
    )

    usecase: Dependency = Dependency(
        create_usecase,
        database=database,
    )

async def main():
    async with AppContainer() as resources:
        await resources.usecase()

await main()
```

**Output:**
```
Database connected to localhost:5432
Usecase created with database at <__main__.Database object at 0x7f4669422120>
Executing query: SELECT * FROM table
Database connection closed
```

## Features

- **Declarative DI** — Type-safe dependency descriptors
- **Async lifecycle** — Automatic init and cleanup via context managers
- **Topological sorting** — Correct dependency resolution order
- **Circular detection** — Prevents circular dependency issues
- **Single active context** — Cannot re-enter before exit

## License

MIT
