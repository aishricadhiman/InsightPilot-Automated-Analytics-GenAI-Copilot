from pathlib import Path

import pandas as pd
from sqlalchemy import inspect, text

from connection import engine


# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# --------------------------------------------------
# TABLE / FILE CONFIGURATION
# --------------------------------------------------

TABLE_FILES = {
    "patients": "patients.csv",
    "admissions": "admissions.csv",
    "readmissions": "readmissions.csv",
    "costs": "costs.csv",
    "staffing": "staffing.csv",
}


# --------------------------------------------------
# VERIFY TABLE EXISTENCE
# --------------------------------------------------

def verify_tables_exist() -> None:
    """Check that all expected tables exist in MySQL."""

    inspector = inspect(engine)

    existing_tables = set(inspector.get_table_names())
    expected_tables = set(TABLE_FILES.keys())

    missing_tables = expected_tables - existing_tables

    if missing_tables:
        raise RuntimeError(
            f"Missing MySQL tables: {sorted(missing_tables)}"
        )

    print("PASS | All expected MySQL tables exist.")


# --------------------------------------------------
# GET CSV ROW COUNT
# --------------------------------------------------

def get_csv_row_count(filename: str) -> int:
    """Return the number of rows in a processed CSV."""

    file_path = PROCESSED_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Processed file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    return len(df)


# --------------------------------------------------
# GET DATABASE ROW COUNT
# --------------------------------------------------

def get_database_row_count(table_name: str) -> int:
    """Return the number of rows stored in a MySQL table."""

    query = text(
        f"SELECT COUNT(*) FROM `{table_name}`"
    )

    with engine.connect() as connection:
        result = connection.execute(query)

        return result.scalar_one()


# --------------------------------------------------
# VERIFY ROW COUNTS
# --------------------------------------------------

def verify_row_counts() -> pd.DataFrame:
    """
    Compare processed CSV row counts against
    corresponding MySQL table row counts.
    """

    results = []

    for table_name, filename in TABLE_FILES.items():

        csv_rows = get_csv_row_count(filename)

        database_rows = get_database_row_count(
            table_name
        )

        difference = database_rows - csv_rows

        status = (
            "PASS"
            if csv_rows == database_rows
            else "FAIL"
        )

        results.append(
            {
                "table": table_name,
                "csv_rows": csv_rows,
                "database_rows": database_rows,
                "difference": difference,
                "status": status,
            }
        )

    return pd.DataFrame(results)


# --------------------------------------------------
# VERIFY FOREIGN KEY INTEGRITY
# --------------------------------------------------

def verify_foreign_keys() -> dict:
    """
    Check for orphan records in relational tables.
    """

    queries = {
        "admissions_without_patient": """
            SELECT COUNT(*)
            FROM admissions a
            LEFT JOIN patients p
                ON a.patient_id = p.patient_id
            WHERE p.patient_id IS NULL
        """,

        "readmissions_without_admission": """
            SELECT COUNT(*)
            FROM readmissions r
            LEFT JOIN admissions a
                ON r.original_admission_id = a.admission_id
            WHERE a.admission_id IS NULL
        """,

        "costs_without_admission": """
            SELECT COUNT(*)
            FROM costs c
            LEFT JOIN admissions a
                ON c.admission_id = a.admission_id
            WHERE a.admission_id IS NULL
        """,
    }

    results = {}

    with engine.connect() as connection:

        for check_name, query in queries.items():

            count = connection.execute(
                text(query)
            ).scalar_one()

            results[check_name] = count

    return results


# --------------------------------------------------
# MAIN VERIFICATION
# --------------------------------------------------

def verify_database() -> None:
    """Run database integrity checks."""

    print("=" * 70)
    print("DATABASE VERIFICATION")
    print("=" * 70)

    # 1. Verify tables
    verify_tables_exist()

    # 2. Verify row counts
    print("\nROW COUNT VERIFICATION")
    print("-" * 70)

    row_report = verify_row_counts()

    print(
        row_report.to_string(
            index=False
        )
    )

    # 3. Verify foreign keys
    print("\nFOREIGN KEY VERIFICATION")
    print("-" * 70)

    fk_results = verify_foreign_keys()

    for check_name, count in fk_results.items():

        status = (
            "PASS"
            if count == 0
            else "FAIL"
        )

        print(
            f"{status:<5} | "
            f"{check_name:<35} | "
            f"{count:,}"
        )

    # 4. Overall status

    row_counts_passed = (
        row_report["status"] == "PASS"
    ).all()

    foreign_keys_passed = all(
        count == 0
        for count in fk_results.values()
    )

    print("\n" + "=" * 70)

    if row_counts_passed and foreign_keys_passed:

        print(
            "DATABASE VERIFICATION PASSED"
        )

    else:

        print(
            "DATABASE VERIFICATION FAILED"
        )

    print("=" * 70)


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    verify_database()