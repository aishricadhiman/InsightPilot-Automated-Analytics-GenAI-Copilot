from pathlib import Path
import sys

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT IMPORT SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent.agent import (
    AnalyticsAgentError,
    ask_agent,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Hospital Analytics Copilot",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("Hospital Analytics")

    st.caption(
        "GenAI-powered analytics interface"
    )

    st.divider()

    st.subheader("Available analytics")

    st.markdown(
        """
        - Admissions
        - Length of stay
        - 30-day readmissions
        - Staffing workload
        - Billed amounts
        - Insurance coverage
        - Cross-domain analysis
        """
    )

    st.divider()

    st.subheader("Example questions")

    st.markdown(
        """
        **Admissions**
        
        Which department has the most admissions?

        **Readmissions**
        
        Which department has the highest 30-day readmission rate?

        **Staffing**
        
        Which department has the highest patient-to-staff ratio?

        **Financial**
        
        Which department has the highest average billed amount per admission?

        **Cross-domain**
        
        Compare patient-to-staff ratio and readmission rate by department.
        """
    )

    st.divider()

    if st.button(
        "Clear conversation",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.title("Hospital Analytics Copilot")

st.write(
    "Ask business questions about hospital operations "
    "using natural language."
)

st.caption(
    "Powered by Qwen + Hugging Face Inference Providers + MySQL"
)

st.divider()


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )

        # Show SQL and result for assistant responses.
        if message["role"] == "assistant":

            sql = message.get("sql")

            result = message.get("result")

            if sql:

                with st.expander(
                    "View generated SQL"
                ):

                    st.code(
                        sql,
                        language="sql",
                    )

            if isinstance(result, pd.DataFrame):

                with st.expander(
                    "View query result"
                ):

                    st.dataframe(
                        result,
                        use_container_width=True,
                        hide_index=True,
                    )


# ============================================================
# CHAT INPUT
# ============================================================

user_question = st.chat_input(
    "Ask a question about the hospital data..."
)


# ============================================================
# PROCESS QUESTION
# ============================================================

if user_question:

    # --------------------------------------------------------
    # STORE USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_question,
        }
    )

    with st.chat_message("user"):

        st.markdown(
            user_question
        )

    # --------------------------------------------------------
    # RUN AGENT
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Analysing hospital data..."
        ):

            try:

                agent_result = ask_agent(
                    user_question
                )

                answer = agent_result[
                    "answer"
                ]

                sql = agent_result[
                    "sql"
                ]

                result_df = agent_result[
                    "result"
                ]

                # --------------------------------------------
                # ANSWER
                # --------------------------------------------

                st.markdown(
                    answer
                )

                # --------------------------------------------
                # SQL TRACE
                # --------------------------------------------

                with st.expander(
                    "View generated SQL"
                ):

                    st.code(
                        sql,
                        language="sql",
                    )

                # --------------------------------------------
                # QUERY RESULT
                # --------------------------------------------

                with st.expander(
                    "View query result"
                ):

                    if result_df.empty:

                        st.info(
                            "The query returned no rows."
                        )

                    else:

                        st.dataframe(
                            result_df,
                            use_container_width=True,
                            hide_index=True,
                        )

                # --------------------------------------------
                # STORE ASSISTANT MESSAGE
                # --------------------------------------------

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sql": sql,
                        "result": result_df,
                    }
                )

            except AnalyticsAgentError as error:

                error_message = (
                    "I couldn't complete that analysis. "
                    "Please try rephrasing the question."
                )

                st.error(
                    error_message
                )

                # Development/debug information.
                with st.expander(
                    "Technical details"
                ):

                    st.code(
                        str(error)
                    )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )

            except Exception as error:

                error_message = (
                    "An unexpected error occurred while "
                    "processing the request."
                )

                st.error(
                    error_message
                )

                with st.expander(
                    "Technical details"
                ):

                    st.code(
                        str(error)
                    )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": error_message,
                    }
                )