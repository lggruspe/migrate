# pylint: disable=redefined-outer-name,no-self-use
"""Test migrate package."""

from pathlib import Path

import pytest

from migrate import migrate
from migrate.exceptions import MigrationScriptError


@pytest.fixture
def database(tmp_path: Path) -> Path:
    """Prepare sqlite3 database."""
    return tmp_path/"test.db"


@pytest.fixture
def migrations(tmp_path: Path) -> Path:
    """Prepare migrations directory."""
    root = tmp_path/"migrations"
    root.mkdir(exist_ok=True)
    return root


def up(user_version: int) -> str:
    """Return minimal up script SQL for testing."""
    return f"""
        BEGIN TRANSACTION;
        PRAGMA user_version = {user_version};
        CREATE TABLE Test (key PRIMARY KEY);
        COMMIT;
    """


def down(user_version: int) -> str:
    """Return down script for self.up."""
    return f"""
        BEGIN TRANSACTION;
        PRAGMA user_version = {user_version};
        DROP TABLE Test;
        COMMIT;
    """


class TestVersionNumber:
    """Tests for stuff related to file version numbers."""

    def test_version_zero(self, database: Path, migrations: Path) -> None:
        """Version 0 is not allowed."""
        (migrations/"0_test.up.sql").write_text(up(0))
        (migrations/"0_test.down.sql").write_text(down(0))
        with pytest.raises(MigrationScriptError):
            migrate(str(database), migrations)

    def test_version_nonzero(self, database: Path, migrations: Path) -> None:
        """Any nonzero version is fine."""
        (migrations/"1_test.up.sql").write_text(up(1))
        (migrations/"1_test.down.sql").write_text(down(0))
        version = migrate(str(database), migrations)
        assert version == 1


def test_sql_not_in_transaction(database: Path, migrations: Path) -> None:
    """SQL scripts should be wrapped in transaction."""
    (migrations/"1_test.up.sql").write_text(
        """
        PRAGMA user_version = 1;
        CREATE TABLE Test (key);
        """
    )
    (migrations/"1_test.down.sql").write_text(
        """
        PRAGMA user_version = 0;
        DROP TABLE Test;
        """
    )
    with pytest.raises(MigrationScriptError):
        migrate(str(database), migrations)


def test_with_mismatched_versions(database: Path, migrations: Path) -> None:
    """It should raise error."""
    (migrations/"1_test.up.sql").write_text(up(2))
    (migrations/"1_test.down.sql").write_text(down(0))
    with pytest.raises(MigrationScriptError):
        migrate(str(database), migrations)


def test_python_script(database: Path, migrations: Path) -> None:
    """It should run without errors."""
    (migrations/"1_test.up.py").write_text("""
USER_VERSION = 1

def main(db):
    db.execute("CREATE TABLE Test (key)")
    """)
    (migrations/"1_test.down.py").write_text("""
USER_VERSION = 0

def main(db):
    db.execute("DROP TABLE Test")
    """)

    assert migrate(str(database), migrations, version=1) == 1
    assert migrate(str(database), migrations, version=0) == 0
