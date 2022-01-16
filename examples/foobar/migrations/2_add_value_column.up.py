from uuid import uuid4

USER_VERSION = 2


def main(m):
    """Add value column to Data table."""
    m.create_function("uuid", 0, lambda: str(uuid4()))
    m.execute("ALTER TABLE Data ADD COLUMN value")
    m.execute("UPDATE Data SET value = uuid() WHERE value IS NULL")
