"""Defines exception classes used by migrate."""


class MigrateError(Exception):
    """Parent class of all exceptions raised by migrate."""


class MigrationScriptError(MigrateError):
    """Raised when there's something wrong with a migration script."""


class MigrationRuntimeError(MigrateError):
    """Raised when something goes wrong with running a migration script."""
