from pathlib import Path

import pandas as pd

from connection import engine


# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# --------------------------------------------------
# TABLE LOAD ORDER
# --------------------------------------------------
# Order matters because of foreign key relationships.
#
# patients
#     ↓
# admissions
#     ↓
# readmissions / costs
#
# staffing is independent.

TABLE_FILES = {
    "patients": "patients.csv",
    "admissions": "admissions.csv",
    "readmissions": "readmissions.csv",
    "costs": "costs.csv",
    "staffing": "staffing.csv",
}


# --------------------------------------------------
# LOAD ONE TABLE
# --------------------------------------------------

def load_table(table_name: str, filename: str) -> None:
    """
    Load a processed CSV file into an existing MySQL table.

    The database tables must already exist because this function
    appends data to the schema defined in models.py.
    """

    file_path = PROCESSED_DIR / filename

    # Check whether CSV exists
    if not file_path.exists():
        raise FileNotFoundError(
            f"Processed file not found: {file_path}"
        )

    # Read processed CSV
    df = pd.read_csv(file_path)

    print(
        f"\nLoading '{table_name}' "
        f"({len(df):,} rows)..."
    )

    # Append data to the existing MySQL table
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )

    print(
        f"Successfully loaded '{table_name}'."
    )


# --------------------------------------------------
# LOAD ALL TABLES
# --------------------------------------------------

def load_database() -> None:
    """
    Load all processed datasets into MySQL
    in foreign-key-safe order.
    """

    print("=" * 60)
    print("STARTING DATABASE LOAD")
    print("=" * 60)

    for table_name, filename in TABLE_FILES.items():
        load_table(
            table_name=table_name,
            filename=filename,
        )

    print("\n" + "=" * 60)
    print("DATABASE LOAD COMPLETED SUCCESSFULLY")
    print("=" * 60)


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    load_database()