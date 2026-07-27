import os
from pathlib import Path

from dotenv import load_dotenv


# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


# --------------------------------------------------
# HUGGING FACE CONFIGURATION
# --------------------------------------------------

HF_TOKEN = os.getenv("HF_TOKEN")

HF_MODEL = os.getenv(
    "HF_MODEL",
    "Qwen/Qwen3-32B"
)


# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

if not HF_TOKEN:
    raise ValueError(
        "HF_TOKEN is missing. "
        "Add it to the project's .env file."
    )

if not HF_MODEL:
    raise ValueError(
        "HF_MODEL is missing."
    )