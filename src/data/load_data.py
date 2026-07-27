from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


FILES = {
    "patients": "patients.csv",
    "admissions": "admissions.csv",
    "readmissions": "readmissions.csv",
    "staffing": "staffing.csv",
    "costs": "costs.csv",
}


def load_data(data_type="raw"):
    """Load hospital datasets from raw or processed directory."""

    data_path = DATA_DIR / data_type

    datasets = {}

    for name, filename in FILES.items():

        file_path = data_path / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {file_path}"
            )

        datasets[name] = pd.read_csv(file_path)

    return datasets


def load_raw_data():
    """Load original raw datasets."""
    return load_data("raw")


def load_processed_data():
    """Load cleaned processed datasets."""
    return load_data("processed")