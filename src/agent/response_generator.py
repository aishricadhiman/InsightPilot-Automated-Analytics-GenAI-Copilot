import json

import pandas as pd

from src.agent.llm import generate_response


# ============================================================
# RESPONSE GENERATION SYSTEM PROMPT
# ============================================================

RESPONSE_SYSTEM_PROMPT = """
You are a senior healthcare data analytics assistant.

Your job is to answer the user's business question using
ONLY the SQL query result provided to you.

RULES:

1. Base the answer only on the supplied query result.

2. Never invent numbers, departments, trends, causes,
   explanations, or recommendations that are not supported
   by the result.

3. Do not claim causation from associations.

4. Keep numerical values accurate.

5. When a value represents a percentage, clearly include %.

6. billed_amount represents billed charges.
   Do not describe billed amounts as revenue, profit,
   operating cost, or payment received.

7. Patient-to-staff ratio represents patients per staff
   member according to the project's staffing data.

8. If the result is empty, state that the available data
   did not return a result for the question.

9. Answer the user's question directly.

10. Keep simple answers concise. Add interpretation only
    when the query result supports it.

11. Do not discuss SQL unless the user specifically asks
    about the query.

12. Do not mention that you are an AI model.

OUTPUT:
Return a clear natural-language analytical answer.
"""


# ============================================================
# DATAFRAME → JSON
# ============================================================

def prepare_query_result(
    df: pd.DataFrame,
    max_rows: int = 50,
) -> str:
    """
    Convert query results into JSON for the LLM.

    Only a limited number of rows are sent to avoid
    unnecessarily large prompts.
    """

    if max_rows <= 0:
        raise ValueError(
            "max_rows must be greater than zero."
        )

    if df.empty:
        return "[]"

    limited_df = df.head(max_rows).copy()

    # Convert NaN / NaT to None.
    limited_df = limited_df.astype(object).where(
        pd.notnull(limited_df),
        None,
    )

    records = limited_df.to_dict(
        orient="records"
    )

    return json.dumps(
        records,
        default=str,
        ensure_ascii=False,
        indent=2,
    )


# ============================================================
# BUILD RESPONSE PROMPT
# ============================================================

def build_response_prompt(
    user_question: str,
    sql: str,
    result_df: pd.DataFrame,
) -> str:
    """
    Build the prompt used to interpret a SQL result.
    """

    if not user_question.strip():
        raise ValueError(
            "User question cannot be empty."
        )

    if not sql.strip():
        raise ValueError(
            "SQL cannot be empty."
        )

    query_result = prepare_query_result(
        result_df
    )

    return f"""
USER QUESTION:

{user_question}


SQL QUERY USED:

{sql}


QUERY RESULT:

{query_result}


TASK:

Answer the user's question using only the query result above.

Do not invent information that is not present in the result.
""".strip()


# ============================================================
# GENERATE ANALYTICAL RESPONSE
# ============================================================

def generate_analytical_response(
    user_question: str,
    sql: str,
    result_df: pd.DataFrame,
) -> str:
    """
    Convert SQL query results into a concise
    natural-language analytical answer.
    """

    # No reason to call the LLM when MySQL returned nothing.
    if result_df.empty:
        return (
            "The query returned no data for the "
            "requested analysis."
        )

    prompt = build_response_prompt(
        user_question=user_question,
        sql=sql,
        result_df=result_df,
    )

    response = generate_response(
        user_prompt=prompt,
        system_prompt=RESPONSE_SYSTEM_PROMPT,
        max_tokens=700,
        temperature=0.0,
    )

    if not response.strip():
        raise ValueError(
            "LLM returned an empty analytical response."
        )

    return response.strip()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_question = (
        "Which department has the highest "
        "30-day readmission rate?"
    )

    test_sql = """
    SELECT
        department,
        12.20 AS readmission_rate_pct
    FROM vw_readmission_metrics
    LIMIT 1;
    """.strip()

    test_df = pd.DataFrame(
        [
            {
                "department": "Emergency",
                "readmission_rate_pct": 12.20,
            }
        ]
    )

    print("=" * 70)
    print("TESTING RESPONSE GENERATOR")
    print("=" * 70)

    answer = generate_analytical_response(
        user_question=test_question,
        sql=test_sql,
        result_df=test_df,
    )

    print("\nQUESTION:")
    print(test_question)

    print("\nQUERY RESULT:")
    print(test_df.to_string(index=False))

    print("\nGENERATED ANSWER:")
    print(answer)

    print("\n" + "=" * 70)
    print("RESPONSE GENERATOR TEST COMPLETED")
    print("=" * 70)