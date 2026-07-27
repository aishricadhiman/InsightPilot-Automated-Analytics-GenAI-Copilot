from pathlib import Path

from sqlalchemy import inspect, text

from connection import engine


# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VIEWS_DIR = PROJECT_ROOT / "sql" / "views"


# --------------------------------------------------
# EXPECTED VIEWS
# --------------------------------------------------

EXPECTED_VIEWS = {
    "vw_admission_metrics",
    "vw_readmission_metrics",
    "vw_staffing_metrics",
    "vw_cost_metrics",
}


# --------------------------------------------------
# DEPLOY SINGLE VIEW
# --------------------------------------------------

def deploy_view(sql_file: Path) -> None:
    """
    Read and execute a SQL view file against MySQL.
    """

    if not sql_file.exists():
        raise FileNotFoundError(
            f"SQL file not found: {sql_file}"
        )

    sql_query = sql_file.read_text(
        encoding="utf-8"
    ).strip()

    if not sql_query:
        raise ValueError(
            f"SQL file is empty: {sql_file.name}"
        )

    print(f"Deploying: {sql_file.name}")

    with engine.begin() as connection:
        connection.execute(
            text(sql_query)
        )

    print(
        f"Successfully deployed: {sql_file.name}"
    )


# --------------------------------------------------
# DEPLOY ALL VIEWS
# --------------------------------------------------

def deploy_all_views() -> None:
    """
    Deploy all .sql files from sql/views.
    """

    if not VIEWS_DIR.exists():
        raise FileNotFoundError(
            f"Views directory not found: {VIEWS_DIR}"
        )

    sql_files = sorted(
        VIEWS_DIR.glob("*.sql")
    )

    if not sql_files:
        raise FileNotFoundError(
            f"No SQL files found in: {VIEWS_DIR}"
        )

    print("=" * 60)
    print("DEPLOYING SQL VIEWS")
    print("=" * 60)

    for sql_file in sql_files:
        deploy_view(sql_file)


# --------------------------------------------------
# VERIFY DEPLOYED VIEWS
# --------------------------------------------------

def verify_views() -> None:
    """
    Verify that all expected views exist in MySQL.
    """

    inspector = inspect(engine)

    existing_views = set(
        inspector.get_view_names()
    )

    print("\n" + "=" * 60)
    print("VERIFYING SQL VIEWS")
    print("=" * 60)

    for view_name in sorted(EXPECTED_VIEWS):

        if view_name in existing_views:

            print(
                f"PASS | {view_name}"
            )

        else:

            print(
                f"FAIL | {view_name}"
            )

    missing_views = (
        EXPECTED_VIEWS - existing_views
    )

    if missing_views:

        raise RuntimeError(
            "Missing views: "
            + ", ".join(
                sorted(missing_views)
            )
        )

    print("\nAll SQL views verified successfully.")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main() -> None:

    try:

        deploy_all_views()

        verify_views()

        print("\n" + "=" * 60)
        print("SQL VIEW DEPLOYMENT COMPLETED")
        print("=" * 60)

    except Exception as error:

        print("\n" + "=" * 60)
        print("SQL VIEW DEPLOYMENT FAILED")
        print("=" * 60)

        print(f"\nError: {error}")

        raise


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()