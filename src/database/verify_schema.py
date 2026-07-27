from sqlalchemy import inspect

from connection import engine


def verify_schema():
    """Inspect tables, primary keys, and foreign keys."""

    inspector = inspect(engine)

    for table_name in inspector.get_table_names():

        print(f"\n{'=' * 60}")
        print(f"TABLE: {table_name.upper()}")
        print("=" * 60)

        print("\nColumns:")

        for column in inspector.get_columns(table_name):
            print(
                f"{column['name']:<30}"
                f"{str(column['type']):<20}"
                f"nullable={column['nullable']}"
            )

        print("\nPrimary Key:")

        primary_key = inspector.get_pk_constraint(table_name)

        print(primary_key["constrained_columns"])

        print("\nForeign Keys:")

        foreign_keys = inspector.get_foreign_keys(table_name)

        if not foreign_keys:
            print("None")

        for fk in foreign_keys:
            print(
                f"{fk['constrained_columns']} "
                f"-> {fk['referred_table']}."
                f"{fk['referred_columns']}"
            )


if __name__ == "__main__":
    verify_schema()