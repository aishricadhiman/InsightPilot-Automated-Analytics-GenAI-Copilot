import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text


# --------------------------------------------------
# PROJECT IMPORT SETUP
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.database.connection import engine
from src.agent.sql_validator import (
    SQLValidationError,
    validate_sql,
)


# --------------------------------------------------
# DATABASE QUERY ERROR
# --------------------------------------------------

class DatabaseQueryError(RuntimeError):
    """
    Raised when an approved SQL query fails during
    database execution.
    """

    pass


# --------------------------------------------------
# QUERY EXECUTION
# --------------------------------------------------

def execute_analytical_query(
    sql: str,
) -> pd.DataFrame:
    """
    Validate and execute a read-only analytical SQL query.

    The SQL must pass sql_validator.py before it can
    reach MySQL.

    Returns:
        pandas DataFrame containing query results.
    """

    # ----------------------------------------------
    # SAFETY VALIDATION
    # ----------------------------------------------

    validated_sql = validate_sql(sql)

    # ----------------------------------------------
    # DATABASE EXECUTION
    # ----------------------------------------------

    try:

        with engine.connect() as connection:

            result_df = pd.read_sql_query(
                text(validated_sql),
                connection,
            )

    except Exception as error:

        raise DatabaseQueryError(
            f"Database query execution failed: {error}"
        ) from error

    return result_df


# --------------------------------------------------
# RESULT SERIALISATION
# --------------------------------------------------

def dataframe_to_records(
    df: pd.DataFrame,
    max_rows: int = 50,
) -> list[dict]:
    """
    Convert query results into records that can later
    be supplied to the LLM.

    Limits the number of rows passed to the model.
    """

    if max_rows <= 0:
        raise ValueError(
            "max_rows must be greater than zero."
        )

    limited_df = df.head(max_rows)

    # Convert NaN values to None so the result is
    # easier to serialise later.
    limited_df = limited_df.astype(object).where(
        pd.notnull(limited_df),
        None,
    )

    return limited_df.to_dict(
        orient="records"
    )


# --------------------------------------------------
# TEST SAFE QUERY
# --------------------------------------------------

def test_safe_query() -> None:

    sql = """
    SELECT
        department,
        COUNT(DISTINCT admission_id) AS total_admissions
    FROM vw_admission_metrics
    GROUP BY department
    ORDER BY total_admissions DESC
    LIMIT 5;
    """

    print("=" * 70)
    print("TEST 1: SAFE QUERY")
    print("=" * 70)

    result = execute_analytical_query(
        sql
    )

    print(result.to_string(index=False))

    print(
        f"\nReturned rows: {len(result)}"
    )


# --------------------------------------------------
# TEST BLOCKED QUERY
# --------------------------------------------------

def test_unsafe_query() -> None:

    sql = """
    DELETE FROM admissions;
    """

    print("\n" + "=" * 70)
    print("TEST 2: UNSAFE QUERY")
    print("=" * 70)

    try:

        execute_analytical_query(
            sql
        )

        print(
            "FAIL - Unsafe SQL reached execution."
        )

    except SQLValidationError as error:

        print(
            "PASS - Unsafe SQL blocked before MySQL."
        )

        print(
            f"Reason: {error}"
        )


# --------------------------------------------------
# TEST CTE QUERY
# --------------------------------------------------

def test_cte_query() -> None:

    sql = """
    WITH department_workload AS (

        SELECT
            department,

            SUM(patient_count)
            /
            NULLIF(
                SUM(staff_count),
                0
            ) AS patient_to_staff_ratio

        FROM vw_staffing_metrics

        GROUP BY department
    )

    SELECT
        department,
        ROUND(
            patient_to_staff_ratio,
            2
        ) AS patient_to_staff_ratio

    FROM department_workload

    ORDER BY patient_to_staff_ratio DESC

    LIMIT 5;
    """

    print("\n" + "=" * 70)
    print("TEST 3: SAFE CTE QUERY")
    print("=" * 70)

    result = execute_analytical_query(
        sql
    )

    print(result.to_string(index=False))


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    test_safe_query()

    test_unsafe_query()

    test_cte_query()

    print("\n" + "=" * 70)
    print("DATABASE TOOL TESTS COMPLETED")
    print("=" * 70)