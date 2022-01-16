"""Migrations runner."""

from sqlite3 import Connection
import typing as t

from .scripts import Script


Direction = t.Literal["down", "up"]
MigrationTable = dict[tuple[int, Direction], Script]


def get_current_user_version(con: Connection) -> int:
    """Get current user_version from sqlite3 database."""
    cur = con.cursor()
    row = cur.execute("PRAGMA user_version")
    return t.cast(int, row.fetchone()[0])


class Runner:
    """Runs migrations."""
    def __init__(self, up_scripts: list[Script], down_scripts: list[Script]):
        """Assumes up_scripts and down_scripts have been checked and sorted."""
        self.table: MigrationTable = {}

        if up_scripts:
            self.table[(0, "up")] = up_scripts[0]
            for i in range(1, len(up_scripts)):
                before = up_scripts[i - 1]
                after = up_scripts[i]
                self.table[(before.file_version, "up")] = after
        if down_scripts:
            for script in down_scripts:
                self.table[(script.file_version, "down")] = script

    def migrate_up(self, con: Connection, version: int) -> int:
        """Migrate up to specified version."""
        while True:
            current_version = get_current_user_version(con)
            if current_version >= version:
                break
            script = self.table[(current_version, "up")]
            if script.user_version > version:
                break
            script.apply(con)
        return get_current_user_version(con)

    def migrate_down(self, con: Connection, version: int) -> int:
        """Migrate down to specificed version."""
        while True:
            current_version = get_current_user_version(con)
            if current_version <= version:
                break
            script = self.table[(current_version, "down")]
            if script.user_version < version:
                break
            script.apply(con)
        return get_current_user_version(con)

    def migrate(self, con: Connection, version: int) -> int:
        """Migrate to specified version."""
        current_version = get_current_user_version(con)
        if current_version == version:
            return version
        if current_version < version:
            return self.migrate_up(con, version)
        return self.migrate_down(con, version)


__all__ = ["Runner"]
