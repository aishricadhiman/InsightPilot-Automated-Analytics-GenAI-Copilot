import re
from pathlib import Path

import pandas as pd
from sqlalchemy import text

# --------------------------------------------------
# IMPORT DATABASE ENGINE
# --------------------------------------------------

try:
    from src.database.connection import engine
except ModuleNotFoundError:
    # Allows running directly:
    # python src/analysis/run_analysis.py
    from sys import path

    PROJECT_ROOT_TEMP = Path(__file__).resolve().parents[2]
    path.insert(0, str(PROJECT_ROOT_TEMP))

    from src.database.connection import engine


# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SQL_ANALYSIS_DIR = PROJECT_ROOT / "sql" / "analysis"

REPORTS_DIR = PROJECT_ROOT / "reports" / "analysis"


# --------------------------------------------------
# ANALYSIS FILES
# --------------------------------------------------

ANALYSIS_FILES = {
    "admissions": "admissions_analysis.sql",
    "readmissions": "readmissions_analysis.sql",
    "staffing": "staffing_analysis.sql",
    "costs": "cost_analysis.sql",
    "operational": "operational_analysis.sql",
}


# --------------------------------------------------
# PARSE SQL FILE
# --------------------------------------------------

def parse_sql_queries(sql_file: Path) -> list[dict]:
    """
    Extract numbered analytical queries from a SQL file.

    Expected section format:

        -- ====================================================
        -- 1. OVERALL ADMISSION KPIs
        -- ====================================================

        SELECT ...

        -- ====================================================
        -- 2. ADMISSIONS BY DEPARTMENT
        -- ====================================================

        SELECT ...

    Returns:
        [
            {
                "number": 1,
                "title": "OVERALL ADMISSION KPIs",
                "query": "SELECT ..."
            },
            ...
        ]
    """

    if not sql_file.exists():
        raise FileNotFoundError(
            f"SQL analysis file not found: {sql_file}"
        )

    sql_content = sql_file.read_text(
        encoding="utf-8"
    )

    # Detect lines such as:
    # -- 1. OVERALL ADMISSION KPIs
    pattern = re.compile(
        r"(?m)^--\s*(\d+)\.\s*(.+?)\s*$"
    )

    matches = list(
        pattern.finditer(sql_content)
    )

    if not matches:
        raise ValueError(
            f"No numbered SQL sections found in {sql_file.name}"
        )

    queries = []

    for index, match in enumerate(matches):

        query_number = int(
            match.group(1)
        )

        query_title = (
            match.group(2)
            .strip()
        )

        query_start = match.end()

        if index + 1 < len(matches):
            query_end = matches[index + 1].start()
        else:
            query_end = len(sql_content)

        section = sql_content[
            query_start:query_end
        ]

        # Remove SQL comment lines from the section.
        query_lines = []

        for line in section.splitlines():

            stripped = line.strip()

            if stripped.startswith("--"):
                continue

            query_lines.append(line)

        query = "\n".join(
            query_lines
        ).strip()

        # Remove final semicolon
        query = query.rstrip(";").strip()

        if not query:
            continue

        # Our analysis files should contain SELECT / WITH queries.
        first_word = query.lstrip().split(
            None,
            1
        )[0].upper()

        if first_word not in {"SELECT", "WITH"}:
            raise ValueError(
                f"Section {query_number} in "
                f"{sql_file.name} does not start "
                f"with SELECT or WITH."
            )

        queries.append(
            {
                "number": query_number,
                "title": query_title,
                "query": query,
            }
        )

    return queries


# --------------------------------------------------
# CREATE SAFE FILE NAME
# --------------------------------------------------

def create_safe_filename(
    query_number: int,
    title: str
) -> str:
    """
    Convert a SQL section title into a safe CSV filename.
    """

    safe_title = title.lower()

    safe_title = re.sub(
        r"[^a-z0-9]+",
        "_",
        safe_title
    )

    safe_title = safe_title.strip("_")

    return (
        f"{query_number:02d}_"
        f"{safe_title}.csv"
    )


# --------------------------------------------------
# EXECUTE ONE QUERY
# --------------------------------------------------

def execute_query(
    query: str
) -> pd.DataFrame:
    """
    Execute one analytical SQL query
    and return the result as a DataFrame.
    """

    with engine.connect() as connection:

        df = pd.read_sql_query(
            text(query),
            connection
        )

    return df


# --------------------------------------------------
# RUN ONE ANALYSIS DOMAIN
# --------------------------------------------------

def run_analysis_domain(
    domain: str,
    filename: str
) -> list[dict]:
    """
    Execute every numbered query in one SQL analysis file
    and save each result as a separate CSV.
    """

    sql_file = (
        SQL_ANALYSIS_DIR / filename
    )

    output_dir = (
        REPORTS_DIR / domain
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    queries = parse_sql_queries(
        sql_file
    )

    print("\n" + "=" * 70)
    print(
        f"RUNNING {domain.upper()} ANALYSIS"
    )
    print("=" * 70)

    results = []

    for query_info in queries:

        number = query_info["number"]
        title = query_info["title"]
        query = query_info["query"]

        print(
            f"\n[{number}] {title}"
        )

        try:

            df = execute_query(
                query
            )

            output_filename = (
                create_safe_filename(
                    number,
                    title
                )
            )

            output_path = (
                output_dir
                / output_filename
            )

            df.to_csv(
                output_path,
                index=False
            )

            print(
                f"PASS | "
                f"{len(df):,} rows | "
                f"{output_filename}"
            )

            results.append(
                {
                    "domain": domain,
                    "query_number": number,
                    "title": title,
                    "rows": len(df),
                    "status": "PASS",
                    "output_file": str(
                        output_path.relative_to(
                            PROJECT_ROOT
                        )
                    ),
                    "error": "",
                }
            )

        except Exception as error:

            print(
                f"FAIL | {error}"
            )

            results.append(
                {
                    "domain": domain,
                    "query_number": number,
                    "title": title,
                    "rows": None,
                    "status": "FAIL",
                    "output_file": "",
                    "error": str(error),
                }
            )

    return results


# --------------------------------------------------
# SAVE EXECUTION SUMMARY
# --------------------------------------------------

def save_execution_summary(
    results: list[dict]
) -> pd.DataFrame:
    """
    Save a summary showing which analytical queries
    executed successfully.
    """

    summary_df = pd.DataFrame(
        results
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    summary_path = (
        REPORTS_DIR
        / "analysis_execution_summary.csv"
    )

    summary_df.to_csv(
        summary_path,
        index=False
    )

    return summary_df


# --------------------------------------------------
# RUN ALL ANALYSES
# --------------------------------------------------

def run_all_analyses() -> None:
    """
    Execute all SQL analysis files and save results.
    """

    print("=" * 70)
    print("STARTING SQL ANALYTICS PIPELINE")
    print("=" * 70)

    all_results = []

    for domain, filename in ANALYSIS_FILES.items():

        domain_results = (
            run_analysis_domain(
                domain,
                filename
            )
        )

        all_results.extend(
            domain_results
        )

    summary_df = (
        save_execution_summary(
            all_results
        )
    )

    total_queries = len(
        summary_df
    )

    passed_queries = (
        summary_df["status"]
        .eq("PASS")
        .sum()
    )

    failed_queries = (
        summary_df["status"]
        .eq("FAIL")
        .sum()
    )

    print("\n" + "=" * 70)
    print("ANALYSIS EXECUTION SUMMARY")
    print("=" * 70)

    print(
        f"Total queries : {total_queries}"
    )

    print(
        f"Passed        : {passed_queries}"
    )

    print(
        f"Failed        : {failed_queries}"
    )

    print(
        "\nSummary saved to:"
    )

    print(
        REPORTS_DIR
        / "analysis_execution_summary.csv"
    )

    if failed_queries > 0:

        print("\nANALYTICS PIPELINE FAILED")

        failed = summary_df[
            summary_df["status"] == "FAIL"
        ]

        print(
            failed[
                [
                    "domain",
                    "query_number",
                    "title",
                    "error",
                ]
            ].to_string(
                index=False
            )
        )

        raise RuntimeError(
            f"{failed_queries} analytical "
            f"queries failed."
        )

    print("\n" + "=" * 70)
    print("SQL ANALYTICS PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    run_all_analyses()