from sqlalchemy import inspect

from connection import engine
from models import metadata


def create_tables():
    """Create and verify all database tables."""

    metadata.create_all(engine)

    inspector = inspect(engine)

    print("Database tables created successfully.")

    print("\nTables:")
    for table_name in inspector.get_table_names():
        print(f" - {table_name}")


if __name__ == "__main__":
    create_tables()