"""Performs additional checks on migration scripts."""

import typing as t

from .exceptions import MigrationScriptError
from .scripts import Script


def check_not_empty(up_scripts: list[Script],
                    down_scripts: list[Script]) -> None:
    """Make sure migrations folder is not empty."""
    if not up_scripts or not down_scripts:
        raise MigrationScriptError("no migration scripts found")


def check_unique_file_versions(up_scripts: list[Script],
                               down_scripts: list[Script]) -> None:
    """Make sure there are no duplicate file versions."""
    for i, s in enumerate(up_scripts[:-1]):
        if s.file_version == up_scripts[i+1].file_version:
            raise MigrationScriptError("duplicate file version:",
                                       s.file_version)
    for i, s in enumerate(down_scripts[:-1]):
        if s.file_version == down_scripts[i+1].file_version:
            raise MigrationScriptError("duplicate file version:",
                                       s.file_version)


def check_matching_file_versions(up_scripts: list[Script],
                                 down_scripts: list[Script]) -> None:
    """Make sure each up script has a down script and vice versa.

    Assumes both lists are sorted.
    """
    for up, down in zip(up_scripts, down_scripts):
        if up.file_version != down.file_version:
            script = min(up, down, key=lambda s: s.file_version)
            raise MigrationScriptError("missing up or down script:", script)


def check_no_version_zero(up_scripts: list[Script], _: list[Script]) -> None:
    """File version number shouldn't exist.

    USER_VERSION is for empty database.
    """
    if up_scripts and up_scripts[0].file_version == 0:
        raise MigrationScriptError("0 as file version number is not allowed")


def check_user_versions(up_scripts: list[Script],
                        down_scripts: list[Script]) -> None:
    """Make sure file versions and user versions are consistent."""
    for up in up_scripts:
        if up.file_version != up.user_version:
            raise MigrationScriptError("inconsistent version numbers:", up)

    if down_scripts and down_scripts[0].user_version != 0:
        raise MigrationScriptError(
            "incorrect user_version number in script: "
            + str(down_scripts[0].path)
            + " (should be 0)"
        )
    for i, s in enumerate(down_scripts[:-1]):
        succ = down_scripts[i + 1]
        if s.file_version != succ.user_version:
            raise MigrationScriptError(
                "incorrect user_version number in script: "
                + str(succ.path) + f" (should be {s.file_version})"
            )


def check(scripts: t.Iterable[Script]) -> tuple[list[Script], list[Script]]:
    """Performs additional checks on migration scripts.

    Raises error if there are any problems.
    """
    up_scripts = []
    down_scripts = []
    for script in sorted(scripts, key=lambda s: s.file_version):
        if script.direction == "up":
            up_scripts.append(script)
        else:
            down_scripts.append(script)

    checks = [
        check_not_empty,
        check_no_version_zero,
        check_unique_file_versions,
        check_matching_file_versions,
        check_user_versions,
    ]
    for fn in checks:
        fn(up_scripts, down_scripts)
    return up_scripts, down_scripts


__all__ = ["check"]
