"""Classes that represent migration scripts."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from importlib.util import module_from_spec, spec_from_file_location
from locale import getpreferredencoding
from pathlib import Path
import re
from sqlite3 import Connection
import typing as t

from .exceptions import MigrationScriptError


Direction = t.Literal["down", "up"]


@dataclass(frozen=True)  # type: ignore
class Script(ABC):
    """Migration script."""
    path: Path
    file_version: int
    direction: Direction

    @property
    @abstractmethod
    def user_version(self) -> int:
        """USER_VERSION inside script."""

    @abstractmethod
    def apply(self, con: Connection) -> None:
        """Apply migration script to database.

        Note: applies script regardless of current database version.
        """


def import_python_script(name: str, path: Path) -> t.Any:
    """Import python script and return module."""
    assert path.suffix == ".py"
    spec = spec_from_file_location(name, path)
    assert spec
    module = module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class SafeConnection:  # pylint: disable=too-few-public-methods
    """Wrapper around sqlite3 connection that only exposes safe functions."""
    def __init__(self, con: Connection):
        self._con = con
        self.create_function = con.create_function
        self.execute = con.execute


MigrationFunction = t.Callable[[SafeConnection], None]


@dataclass(frozen=True)
class PythonScript(Script):
    """Python migration scripts."""
    main: MigrationFunction = field(init=False)
    _user_version: int = field(init=False)

    def __post_init__(self) -> None:
        module = import_python_script("migration", self.path)

        try:
            user_version = getattr(module, "USER_VERSION")
        except AttributeError as exc:
            raise MigrationScriptError("missing USER_VERSION") from exc
        try:
            main = getattr(module, "main")
        except AttributeError as exc:
            raise MigrationScriptError("missing 'main' in .py script") from exc

        object.__setattr__(self, "_user_version", user_version)
        object.__setattr__(self, "main", main)

    @property
    def user_version(self) -> int:
        """Get user_version from module variable."""
        return self._user_version

    def apply(self, con: Connection) -> None:
        """Apply Python script to sqlite3 database."""
        con.commit()
        con.execute("BEGIN TRANSACTION")
        con.execute(f"PRAGMA user_version={self.user_version}")
        self.main(SafeConnection(con))  # type: ignore
        con.execute("COMMIT")


def remove_comments(sql: str) -> str:
    """Remove comments from SQL script."""
    # NOTE Does not strip multi-line comments.
    lines = map(str.strip, sql.split("\n"))
    return "\n".join(line for line in lines if not line.startswith("--"))


def unwrap_transaction(sql: str) -> str:
    """Return block inside transaction."""
    pattern = r"^begin\s+transaction\s*;(.*)commit\s*;$"
    result = re.match(pattern, sql.strip(), re.IGNORECASE | re.DOTALL)
    if not result:
        raise MigrationScriptError("SQL not wrapped in transaction")
    return result.groups()[0]


def parse_sql(sql: str) -> int:
    """Parse SQL script and return USER_VERSION.

    Raises error if the script is not wrapped in a transaction or if it does
    not set USER_VERSION.
    """
    block = unwrap_transaction(remove_comments(sql)).strip()
    pattern = r"pragma\s+user_version\s*=\s*(\d+)\s*;"

    # NOTE Assume USER_VERSION is set in first or last line of transaction.
    result = re.match(f"^{pattern}", block, re.IGNORECASE | re.DOTALL)
    if result is not None:
        return int(result.groups()[0])

    result = re.match(f"{pattern}$", block, re.IGNORECASE | re.DOTALL)
    if result is not None:
        return int(result.groups()[0])

    raise MigrationScriptError("missing USER_VERSION")


@dataclass(frozen=True)
class SQLScript(Script):
    """SQL migration scripts."""
    text: str = field(init=False)
    _user_version: int = field(init=False)

    def __post_init__(self) -> None:
        encoding = getpreferredencoding(False)
        object.__setattr__(self, "text", self.path.read_text(encoding))
        object.__setattr__(self, "_user_version", parse_sql(self.text))

    @property
    def user_version(self) -> int:
        return self._user_version

    def apply(self, con: Connection) -> None:
        """Apply SQL script to sqlite3 database."""
        con.executescript(self.text)


def find_scripts(root: Path) -> t.Iterable[Script]:
    """Find all migration scripts in root."""
    pattern = re.compile(r"^(\d+).*\.(up|down)(\.py|\.sql)$")
    for path in root.iterdir():
        result = pattern.match(path.name)
        if result:
            groups = result.groups()
            args = (path, int(groups[0]), t.cast(Direction, groups[1]))
            if groups[2] == ".py":
                yield PythonScript(*args)
            else:
                yield SQLScript(*args)


__all__ = ["Script", "PythonScript", "SQLScript", "find_scripts"]
