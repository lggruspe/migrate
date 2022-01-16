"""migrate command-line program."""

from argparse import ArgumentParser
from pathlib import Path

from . import migrate


def main() -> None:
    """Run CLI."""
    cli = ArgumentParser("migrate", description="Run SQLite migration scripts")
    cli.add_argument("database", help="SQLite database file")
    cli.add_argument("migrations", type=Path, help="migrations directory")
    cli.add_argument("--version", type=int,
                     help="version to migrate to (default: latest version)")
    args = cli.parse_args()
    migrate(args.database, args.migrations, args.version)


if __name__ == "__main__":
    main()
