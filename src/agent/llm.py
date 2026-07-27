from huggingface_hub import InferenceClient

from src.agent.config import HF_MODEL, HF_TOKEN


# --------------------------------------------------
# CREATE CLIENT
# --------------------------------------------------

client = InferenceClient(
    api_key=HF_TOKEN
)


# --------------------------------------------------
# LLM CALL
# --------------------------------------------------

def generate_response(
    user_prompt: str,
    system_prompt: str = (
        "You are a senior data analytics assistant. "
        "Answer accurately and concisely."
    ),
    max_tokens: int = 1000,
    temperature: float = 0.1,
) -> str:
    """
    Send a prompt to the configured Hugging Face model
    and return the generated text.
    """

    if not user_prompt.strip():
        raise ValueError(
            "user_prompt cannot be empty."
        )

    response = client.chat_completion(
        model=HF_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )

    # --------------------------------------------------
    # VALIDATE RESPONSE STRUCTURE
    # --------------------------------------------------

    if not response.choices:
        raise ValueError(
            "LLM returned no response choices."
        )

    message = response.choices[0].message

    content = getattr(
        message,
        "content",
        None
    )

    # --------------------------------------------------
    # HANDLE EMPTY CONTENT
    # --------------------------------------------------

    if content is None or not str(content).strip():

        reasoning = getattr(
            message,
            "reasoning",
            None
        )

        reasoning_content = getattr(
            message,
            "reasoning_content",
            None
        )

        print("\nDEBUG: LLM returned empty content.")

        if reasoning:
            print(
                "Reasoning received:",
                str(reasoning)[:500]
            )

        if reasoning_content:
            print(
                "Reasoning content received:",
                str(reasoning_content)[:500]
            )

        raise ValueError(
            "LLM returned an empty final response."
        )

    return str(content).strip()


# --------------------------------------------------
# CONNECTION TEST
# --------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("TESTING HUGGING FACE LLM CONNECTION")
    print("=" * 60)

    try:

        answer = generate_response(
            user_prompt=(
                "What is a 30-day hospital "
                "readmission rate? "
                "Answer in one sentence."
            ),
            max_tokens=500,
        )

        print("\nModel:")
        print(HF_MODEL)

        print("\nResponse:")
        print(answer)

        print("\n" + "=" * 60)
        print("LLM CONNECTION TEST PASSED")
        print("=" * 60)

    except Exception as error:

        print("\n" + "=" * 60)
        print("LLM CONNECTION TEST FAILED")
        print("=" * 60)

        print(f"\nError: {error}")

        raise