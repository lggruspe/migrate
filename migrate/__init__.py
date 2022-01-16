"""Library for running SQLite migration scripts.

Idea: Migrations are applied incrementally.
There should be an initial schema (version 1) and a series of migration
scripts.
Migration scripts can be written in SQL or Python.

Each migration script should set PRAGMA user_version.

Usage:

migrate db.sqlite3 migrations/

Writing a migration script using python (example):

```python
def main(db):
    db.execute("ALTER TABLE Users ADD COLUMN email")
```
"""

from pathlib import Path
import sqlite3
import typing as t

from .checks import check
from .runner import Runner
from .scripts import find_scripts


def migrate(db: str, migrations: Path, version: t.Optional[int] = None) -> int:
    """Migrate to specified version.

    If version is None, migrate to latest version instead.
    """
    scripts = find_scripts(migrations)
    up_scripts, down_scripts = check(scripts)

    if version is None:
        version = up_scripts[-1].file_version
    runner = Runner(up_scripts, down_scripts)

    con = sqlite3.connect(db)
    result = runner.migrate(con, version)
    con.close()

    return result


__all__ = ["migrate"]
