from pathlib import Path

import numpy as np
import pandas as pd

from load_data import load_raw_data


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def clean_patients(df):
    df = df.copy()

    # Invalid ages become missing
    invalid_age = (df["age"] < 0) | (df["age"] > 100)
    df.loc[invalid_age, "age"] = np.nan

    # Impute age using median
    df["age"] = df["age"].fillna(df["age"].median())

    # Missing categorical values
    df["gender"] = df["gender"].fillna("Unknown")

    df["insurance_type"] = (
        df["insurance_type"].fillna("Unknown")
    )

    # Defensive PK duplicate removal
    df = df.drop_duplicates(
        subset=["patient_id"],
        keep="first"
    )

    return df


DEPARTMENT_MAPPING = {
    "ER": "Emergency",
    "emergency": "Emergency",
    "EMERGENCY": "Emergency",

    "cardiology": "Cardiology",
    "CARDIO": "Cardiology",
    "Cardio": "Cardiology",

    "Gen Med": "General Medicine",
    "general medicine": "General Medicine",
    "GENERAL MEDICINE": "General Medicine",

    "Ortho": "Orthopedics",
    "orthopedics": "Orthopedics",

    "Pulmonary": "Pulmonology",
    "pulmonology": "Pulmonology",
}

def standardise_department(series):
    return series.replace(DEPARTMENT_MAPPING)

def clean_admissions(df):
    df = df.copy()

    # Remove duplicate admission IDs
    df = df.drop_duplicates(
        subset=["admission_id"],
        keep="first"
    )

    # Standardise departments
    df["department"] = standardise_department(
        df["department"]
    )

    # Missing bed types
    df["bed_type"] = df["bed_type"].fillna("Unknown")

    # Convert dates
    df["admission_date"] = pd.to_datetime(
        df["admission_date"],
        errors="coerce"
    )

    df["discharge_date"] = pd.to_datetime(
        df["discharge_date"],
        errors="coerce"
    )


    reversed_dates = (
        df["discharge_date"] < df["admission_date"]
    )

    valid_los = (
        df["length_of_stay"].notna()
        & (df["length_of_stay"] >= 0)
    )

    repair_date = reversed_dates & valid_los

    df.loc[repair_date, "discharge_date"] = (
        df.loc[repair_date, "admission_date"]
        + pd.to_timedelta(
            df.loc[repair_date, "length_of_stay"],
            unit="D"
        )
    )

    calculated_los = (
        df["discharge_date"] - df["admission_date"]
    ).dt.days

    valid_dates = calculated_los >= 0

    df.loc[valid_dates, "length_of_stay"] = (
        calculated_los[valid_dates]
    )

    return df

def remove_orphan_admissions(admissions, patients):

    valid_patient_ids = set(patients["patient_id"])

    return admissions[
        admissions["patient_id"].isin(valid_patient_ids)
    ].copy()

def clean_readmissions(df):
    df = df.copy()

    df = df.drop_duplicates(
        subset=["readmission_id"],
        keep="first"
    )

    valid_window = (
        df["days_since_discharge"].between(1, 30)
    )

    df = df[valid_window].copy()

    return df

def clean_staffing(df):
    df = df.copy()

    df["department"] = standardise_department(
        df["department"]
    )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df.loc[
        df["staff_count"] <= 0,
        "staff_count"
    ] = np.nan

    df["staff_count"] = (
        df.groupby(
            ["department", "shift"]
        )["staff_count"]
        .transform(
            lambda x: x.fillna(x.median())
        )
    )

    df["patient_count"] = (
        df.groupby(
            ["department", "shift"]
        )["patient_count"]
        .transform(
            lambda x: x.fillna(x.median())
        )
    )

    return df

def clean_costs(df):
    df = df.copy()

    missing_coverage = (
        df["insurance_covered_amount"].isna()
        & df["billed_amount"].notna()
        & df["out_of_pocket"].notna()
    )

    df.loc[
        missing_coverage,
        "insurance_covered_amount"
    ] = (
        df.loc[missing_coverage, "billed_amount"]
        - df.loc[missing_coverage, "out_of_pocket"]
    )

    invalid_oop = (
        df["out_of_pocket"] > df["billed_amount"]
    )
        # Reconcile cost components
    complete_costs = (
        df["billed_amount"].notna()
        & df["insurance_covered_amount"].notna()
        & df["out_of_pocket"].notna()
    )

    calculated_total = (
        df["insurance_covered_amount"]
        + df["out_of_pocket"]
    )

    cost_mismatch = (
        complete_costs
        & ~np.isclose(
            df["billed_amount"],
            calculated_total,
            atol=0.02,
        )
    )

    df.loc[cost_mismatch, "out_of_pocket"] = (
        df.loc[cost_mismatch, "billed_amount"]
        - df.loc[cost_mismatch, "insurance_covered_amount"]
    )

    df["out_of_pocket"] = df["out_of_pocket"].clip(lower=0)
    
    df.loc[
            invalid_oop,
            "out_of_pocket"
        ] = (
            df.loc[invalid_oop, "billed_amount"]
            - df.loc[
                invalid_oop,
                "insurance_covered_amount"
            ]
        )

    df["out_of_pocket"] = (
            df["out_of_pocket"].clip(lower=0)
        )

    df["insurance_covered_amount"] = (
        df["insurance_covered_amount"].clip(lower=0)
    )

    return df

def clean_relationships(
    patients,
    admissions,
    readmissions,
    costs
):

    admissions = remove_orphan_admissions(
        admissions,
        patients
    )

    valid_admission_ids = set(
        admissions["admission_id"]
    )

    readmissions = readmissions[
        readmissions["original_admission_id"].isin(
            valid_admission_ids
        )
    ].copy()

    costs = costs[
        costs["admission_id"].isin(
            valid_admission_ids
        )
    ].copy()

    return admissions, readmissions, costs

def save_processed_data(datasets):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for name, df in datasets.items():

        output = PROCESSED_DIR / f"{name}.csv"

        df.to_csv(
            output,
            index=False
        )

        print(
            f"Saved {name}: "
            f"{len(df):,} rows"
        )

def main():

    raw = load_raw_data()

    patients = clean_patients(
            raw["patients"]
            )

    admissions = clean_admissions(
                raw["admissions"]
            )

    readmissions = clean_readmissions(
                raw["readmissions"]
            )

    staffing = clean_staffing(
                raw["staffing"]
            )

    costs = clean_costs(
                raw["costs"]
            )

    admissions, readmissions, costs = (
                clean_relationships(
                    patients,
                    admissions,
                    readmissions,
                    costs,
                )
            )

    cleaned = {
                "patients": patients,
                "admissions": admissions,
                "readmissions": readmissions,
                "staffing": staffing,
                "costs": costs,
            }

    save_processed_data(cleaned)


if __name__ == "__main__":
    main()