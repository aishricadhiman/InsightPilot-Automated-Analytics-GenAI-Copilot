from sqlglot import parse
from sqlglot import expressions as exp
from sqlglot.errors import ParseError


# ============================================================
# ALLOWED DATABASE OBJECTS
# ============================================================

ALLOWED_VIEWS = {
    "vw_admission_metrics",
    "vw_readmission_metrics",
    "vw_staffing_metrics",
    "vw_cost_metrics",
}


# ============================================================
# FORBIDDEN SQL OPERATIONS
# ============================================================

FORBIDDEN_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
    exp.Command,
    exp.Merge,
)


# ============================================================
# VALIDATION ERROR
# ============================================================

class SQLValidationError(ValueError):
    """
    Raised when generated SQL violates the agent's
    database safety rules.
    """

    pass


# ============================================================
# SQL VALIDATOR
# ============================================================

def validate_sql(sql: str) -> str:
    """
    Validate LLM-generated SQL before database execution.

    Rules:
        1. SQL cannot be empty.
        2. Only one SQL statement is allowed.
        3. Query must be read-only.
        4. Query must ultimately be SELECT-based.
        5. Only approved analytical views may be accessed.

    Returns:
        The validated SQL string.

    Raises:
        SQLValidationError
    """

    if not sql or not sql.strip():
        raise SQLValidationError(
            "SQL query cannot be empty."
        )

    sql = sql.strip()

    # --------------------------------------------------------
    # PARSE SQL
    # --------------------------------------------------------

    try:
        statements = parse(
            sql,
            read="mysql",
        )

    except ParseError as error:
        raise SQLValidationError(
            f"Invalid MySQL syntax: {error}"
        ) from error

    # --------------------------------------------------------
    # ONLY ONE STATEMENT
    # --------------------------------------------------------

    if len(statements) != 1:
        raise SQLValidationError(
            "Multiple SQL statements are not allowed."
        )

    statement = statements[0]

    # --------------------------------------------------------
    # BLOCK WRITE / DDL OPERATIONS
    # --------------------------------------------------------

    for expression_type in FORBIDDEN_EXPRESSIONS:

        if (
            isinstance(statement, expression_type)
            or statement.find(expression_type)
        ):
            raise SQLValidationError(
                "Only read-only analytical queries "
                "are allowed."
            )

    # --------------------------------------------------------
    # REQUIRE SELECT
    #
    # Allows:
    # SELECT ...
    #
    # and:
    # WITH x AS (...)
    # SELECT ...
    # --------------------------------------------------------

    if statement.find(exp.Select) is None:
        raise SQLValidationError(
            "Query must contain a SELECT statement."
        )

    # --------------------------------------------------------
    # FIND CTE NAMES
    #
    # Example:
    #
    # WITH department_metrics AS (...)
    # SELECT *
    # FROM department_metrics
    #
    # department_metrics is temporary query logic,
    # not a physical database view.
    # --------------------------------------------------------

    cte_names = {
        cte.alias_or_name.lower()
        for cte in statement.find_all(exp.CTE)
        if cte.alias_or_name
    }

    # --------------------------------------------------------
    # CHECK DATABASE OBJECTS
    # --------------------------------------------------------

    referenced_tables = set()

    for table in statement.find_all(exp.Table):

        table_name = table.name

        if not table_name:
            continue

        table_name = table_name.lower()

        # CTE references are allowed.
        if table_name in cte_names:
            continue

        referenced_tables.add(
            table_name
        )

    # A useful analytical query should access
    # at least one approved database view.

    if not referenced_tables:
        raise SQLValidationError(
            "Query does not reference an approved "
            "analytical view."
        )

    unauthorized_tables = (
        referenced_tables
        - ALLOWED_VIEWS
    )

    if unauthorized_tables:

        raise SQLValidationError(
            "Query references unauthorized database "
            "objects: "
            + ", ".join(
                sorted(unauthorized_tables)
            )
        )

    # --------------------------------------------------------
    # VALIDATION PASSED
    # --------------------------------------------------------

    return sql


# ============================================================
# TEST HELPER
# ============================================================

def run_test(
    name: str,
    sql: str,
    should_pass: bool,
) -> None:

    print("\n" + "-" * 70)
    print(name)
    print("-" * 70)

    try:

        validated_sql = validate_sql(
            sql
        )

        if should_pass:

            print("PASS - Query correctly allowed.")
            print(validated_sql)

        else:

            print(
                "FAIL - Unsafe query was incorrectly allowed."
            )

    except SQLValidationError as error:

        if should_pass:

            print(
                "FAIL - Safe query was incorrectly blocked."
            )

            print(
                f"Reason: {error}"
            )

        else:

            print(
                "PASS - Unsafe query correctly blocked."
            )

            print(
                f"Reason: {error}"
            )


# ============================================================
# VALIDATOR TESTS
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("TESTING SQL SAFETY VALIDATOR")
    print("=" * 70)

    tests = [

        # --------------------------------------------------
        # SAFE
        # --------------------------------------------------

        (
            "SAFE: Department readmission rate",

            """
            SELECT
                department,
                SUM(
                    CASE
                        WHEN is_eligible_30d = 1
                         AND is_readmitted_30d = 1
                        THEN 1
                        ELSE 0
                    END
                ) * 100.0
                /
                NULLIF(
                    SUM(is_eligible_30d),
                    0
                ) AS readmission_rate
            FROM vw_readmission_metrics
            GROUP BY department
            ORDER BY readmission_rate DESC
            LIMIT 1;
            """,

            True,
        ),

        (
            "SAFE: Staffing workload",

            """
            SELECT
                department,
                SUM(patient_count)
                /
                NULLIF(
                    SUM(staff_count),
                    0
                ) AS patient_to_staff_ratio
            FROM vw_staffing_metrics
            GROUP BY department;
            """,

            True,
        ),

        (
            "SAFE: CTE query",

            """
            WITH department_costs AS (
                SELECT
                    department,
                    AVG(billed_amount)
                        AS avg_billed_amount
                FROM vw_cost_metrics
                GROUP BY department
            )

            SELECT
                department,
                avg_billed_amount
            FROM department_costs
            ORDER BY avg_billed_amount DESC
            LIMIT 5;
            """,

            True,
        ),

        # --------------------------------------------------
        # UNSAFE
        # --------------------------------------------------

        (
            "UNSAFE: Raw patients table",

            """
            SELECT *
            FROM patients;
            """,

            False,
        ),

        (
            "UNSAFE: Delete",

            """
            DELETE
            FROM vw_admission_metrics;
            """,

            False,
        ),

        (
            "UNSAFE: Drop",

            """
            DROP TABLE patients;
            """,

            False,
        ),

        (
            "UNSAFE: Multiple statements",

            """
            SELECT *
            FROM vw_admission_metrics;

            DROP TABLE patients;
            """,

            False,
        ),

        (
            "UNSAFE: Update",

            """
            UPDATE costs
            SET billed_amount = 0;
            """,

            False,
        ),
    ]

    for (
        test_name,
        test_sql,
        should_pass,
    ) in tests:

        run_test(
            test_name,
            test_sql,
            should_pass,
        )

    print("\n" + "=" * 70)
    print("SQL VALIDATOR TEST COMPLETED")
    print("=" * 70)