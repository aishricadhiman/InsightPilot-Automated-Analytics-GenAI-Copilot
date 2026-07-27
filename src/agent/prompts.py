from src.agent.schema import get_schema_context


# --------------------------------------------------
# SQL GENERATION SYSTEM PROMPT
# --------------------------------------------------

SQL_GENERATION_SYSTEM_PROMPT = """
You are an expert MySQL data analyst.

Your job is to convert a user's business question into
a correct MySQL analytical query.

You have access only to the database schema and business
definitions provided to you.

RULES:

1. Generate MySQL-compatible SQL.

2. Use only tables, views, and columns provided in the
   schema context.

3. Prefer curated analytical views instead of raw tables.

4. Generate read-only analytical queries.

5. Never generate:
   INSERT
   UPDATE
   DELETE
   DROP
   ALTER
   TRUNCATE
   CREATE
   REPLACE
   GRANT
   REVOKE

6. Respect the grain of each analytical view.

7. Do not directly join admission-level data to staffing
   observations only by department.

8. For cross-domain analysis, aggregate each source to a
   common grain before joining.

9. Follow the supplied KPI definitions exactly.

10. For 30-day readmission rate, only admissions where
    is_eligible_30d = 1 belong in the denominator.

11. For aggregated patient-to-staff ratio, calculate:

        SUM(patient_count)
        /
        NULLIF(SUM(staff_count), 0)

12. Use NULLIF when division by zero is possible.

13. Do not invent columns, tables, categories, metrics,
    or business definitions.

14. Do not infer causal relationships.

15. Unless the user explicitly asks for every row,
    return only the amount of data necessary to answer
    the question.

OUTPUT RULE:

Return ONLY the SQL query.

Do not include:
- explanations
- Markdown
- ```sql
- comments
- introductory text
"""


# --------------------------------------------------
# BUILD SQL GENERATION PROMPT
# --------------------------------------------------

def build_sql_prompt(user_question: str) -> str:
    """
    Build the complete prompt used to generate SQL.

    Combines:
        database schema
        KPI definitions
        user business question
    """

    if not user_question.strip():
        raise ValueError(
            "User question cannot be empty."
        )

    schema_context = get_schema_context()

    prompt = f"""
DATABASE CONTEXT:

{schema_context}


USER QUESTION:

{user_question}


TASK:

Generate one MySQL SELECT query that answers the
user's question using the provided database context.

Return only the SQL query.
"""

    return prompt.strip()


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    test_question = (
        "Which department has the highest "
        "30-day readmission rate?"
    )

    print(
        build_sql_prompt(test_question)
    )
