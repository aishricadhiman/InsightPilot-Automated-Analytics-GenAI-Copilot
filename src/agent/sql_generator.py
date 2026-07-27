import re

from src.agent.llm import generate_response
from src.agent.prompts import (
    SQL_GENERATION_SYSTEM_PROMPT,
    build_sql_prompt,
)


# --------------------------------------------------
# CLEAN GENERATED SQL
# --------------------------------------------------

def clean_generated_sql(response: str) -> str:
    """
    Clean the LLM response and return plain SQL.

    Handles cases where the model returns SQL inside
    Markdown code fences despite being instructed not to.
    """

    if not response:
        raise ValueError(
            "LLM returned an empty response."
        )

    sql = response.strip()

    # Remove opening Markdown code fence
    sql = re.sub(
        r"^```(?:sql|mysql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    # Remove closing Markdown code fence
    sql = re.sub(
        r"\s*```$",
        "",
        sql,
    )

    return sql.strip()


# --------------------------------------------------
# GENERATE SQL
# --------------------------------------------------

def generate_sql(user_question: str) -> str:
    """
    Convert a natural-language business question
    into a MySQL analytical query.

    NOTE:
    This function only generates SQL.
    It does NOT execute SQL against the database.
    """

    if not user_question.strip():
        raise ValueError(
            "User question cannot be empty."
        )

    user_prompt = build_sql_prompt(
        user_question
    )

    response = generate_response(
    user_prompt=user_prompt,
    system_prompt=SQL_GENERATION_SYSTEM_PROMPT,
    max_tokens=1500,
    temperature=0.0,
    )

    sql = clean_generated_sql(
        response
    )

    return sql


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    test_questions = [
        (
            "Which department has the highest "
            "30-day readmission rate?"
        ),

        (
            "Which department has the highest "
            "patient-to-staff ratio?"
        ),

        (
            "What is the average billed amount "
            "per admission by department?"
        ),
    ]

    print("=" * 70)
    print("TESTING TEXT-TO-SQL GENERATION")
    print("=" * 70)

    for number, question in enumerate(
        test_questions,
        start=1,
    ):

        print(
            f"\nQUESTION {number}:"
        )

        print(question)

        try:

            sql = generate_sql(
                question
            )

            print("\nGENERATED SQL:")
            print(sql)

        except Exception as error:

            print("\nGENERATION FAILED:")
            print(error)

        print("\n" + "-" * 70)

    print("\nTEXT-TO-SQL TEST COMPLETED")