import sys
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# PROJECT IMPORT SETUP
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.agent.sql_generator import generate_sql
from src.agent.sql_validator import (
    SQLValidationError,
    validate_sql,
)
from src.agent.database_tools import (
    DatabaseQueryError,
    execute_analytical_query,
)
from src.agent.response_generator import (
    generate_analytical_response,
)


# ============================================================
# AGENT ERROR
# ============================================================

class AnalyticsAgentError(RuntimeError):
    """
    Raised when the analytics agent cannot complete
    the requested analysis.
    """

    pass


# ============================================================
# ANALYTICS AGENT
# ============================================================

def ask_agent(
    user_question: str,
) -> dict:
    """
    Run the complete analytics-agent workflow.

    Pipeline:
        user question
            ->
        SQL generation
            ->
        SQL validation
            ->
        MySQL execution
            ->
        natural-language interpretation

    Returns:
        Dictionary containing:
            question
            sql
            result
            answer
    """

    if not user_question or not user_question.strip():
        raise ValueError(
            "User question cannot be empty."
        )

    user_question = user_question.strip()

    # --------------------------------------------------------
    # STEP 1: GENERATE SQL
    # --------------------------------------------------------

    try:

        generated_sql = generate_sql(
            user_question
        )

    except Exception as error:

        raise AnalyticsAgentError(
            f"SQL generation failed: {error}"
        ) from error


    # --------------------------------------------------------
    # STEP 2: VALIDATE SQL
    # --------------------------------------------------------

    try:

        validated_sql = validate_sql(
            generated_sql
        )

    except SQLValidationError as error:

        raise AnalyticsAgentError(
            f"Generated SQL failed safety validation: {error}"
        ) from error


    # --------------------------------------------------------
    # STEP 3: EXECUTE SQL
    # --------------------------------------------------------

    try:

        result_df = execute_analytical_query(
            validated_sql
        )

    except DatabaseQueryError as error:

        raise AnalyticsAgentError(
            f"Database analysis failed: {error}"
        ) from error


    # --------------------------------------------------------
    # STEP 4: GENERATE BUSINESS RESPONSE
    # --------------------------------------------------------

    try:

        answer = generate_analytical_response(
            user_question=user_question,
            sql=validated_sql,
            result_df=result_df,
        )

    except Exception as error:

        raise AnalyticsAgentError(
            f"Response generation failed: {error}"
        ) from error


    # --------------------------------------------------------
    # RETURN COMPLETE TRACE
    # --------------------------------------------------------

    return {
        "question": user_question,
        "sql": validated_sql,
        "result": result_df,
        "answer": answer,
    }


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_agent_result(
    agent_result: dict,
) -> None:
    """
    Display an agent response in the terminal.
    """

    print("\n" + "=" * 70)
    print("AGENT INSIGHT")
    print("=" * 70)

    print("\nQUESTION:")
    print(
        agent_result["question"]
    )

    print("\nGENERATED SQL:")
    print(
        agent_result["sql"]
    )

    print("\nDATABASE RESULT:")

    result_df = agent_result["result"]

    if isinstance(result_df, pd.DataFrame):

        if result_df.empty:

            print(
                "No rows returned."
            )

        else:

            print(
                result_df.to_string(
                    index=False
                )
            )

    print("\nANSWER:")
    print(
        agent_result["answer"]
    )

    print("\n" + "=" * 70)


# ============================================================
# END-TO-END TEST
# ============================================================

if __name__ == "__main__":

    test_questions = [

    # Admissions
    "What are the top 5 departments by total admissions?",

    # LOS
    "Which department has the longest average length of stay?",

    # Readmissions
    "What is the hospital-wide 30-day readmission rate?",

    # Staffing
    "Compare patient-to-staff ratio across shifts.",

    # Financial
    "Which 5 departments have the highest total billed amount?",

    # Time analysis
    "Show monthly admission volume for 2025.",

    # Multi-metric
    (
        "Show each department's total admissions, "
        "average length of stay, and average billed amount."
    ),

    # Cross-domain — harder
    (
        "Compare patient-to-staff ratio and 30-day "
        "readmission rate by department."
    ),
    ]

    print("=" * 70)
    print("AGENT INSIGHT - END-TO-END TEST")
    print("=" * 70)

    for number, question in enumerate(
        test_questions,
        start=1,
    ):

        print(
            f"\nRunning question {number}..."
        )

        try:

            result = ask_agent(
                question
            )

            display_agent_result(
                result
            )

        except Exception as error:

            print(
                f"\nQUESTION {number} FAILED"
            )

            print(
                f"Error: {error}"
            )

    print("\n" + "=" * 70)
    print("END-TO-END AGENT TEST COMPLETED")
    print("=" * 70)