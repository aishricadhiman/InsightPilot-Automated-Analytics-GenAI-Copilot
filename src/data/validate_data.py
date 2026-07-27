from pathlib import Path
from py_compile import main

import numpy as np
import pandas as pd
from sklearn import datasets

from load_data import load_processed_data


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "reports" / "data_quality"


VALID_DEPARTMENTS = {
    "Emergency",
    "Cardiology",
    "General Medicine",
    "Orthopedics",
    "Neurology",
    "Oncology",
    "Pulmonology",
    "Gastroenterology",
    "Nephrology",
    "Surgery",
}

VALID_INSURANCE_TYPES = {
    "Government",
    "Private",
    "Employer",
    "Self-pay",
    "Unknown",
}

VALID_ADMISSION_TYPES = {
    "Emergency",
    "Elective",
    "Transfer",
}

VALID_GENDERS = {
    "Female",
    "Male",
    "Other",
    "Unknown",
}

VALID_BED_TYPES = {
    "General",
    "ICU",
    "Observation",
    "Unknown",
}

VALID_SHIFTS = {
    "Day",
    "Evening",
    "Night",
}

def make_result(dataset, check, severity, failed_count):
    return {
        "dataset": dataset,
        "check": check,
        "severity": severity,
        "failed_rows": int(failed_count),
        "status": "PASS" if failed_count == 0 else "FAIL",
    }


def validate_patients(df):
    results = []

    results.append(
        make_result(
            "patients",
            "patient_id_unique",
            "ERROR",
            df["patient_id"].duplicated().sum(),
        )
    )

    results.append(
        make_result(
            "patients",
            "patient_id_not_null",
            "ERROR",
            df["patient_id"].isna().sum(),
        )
    )

    invalid_age = (
        df["age"].isna()
        | (df["age"] < 0)
        | (df["age"] > 100)
    )

    results.append(
        make_result(
            "patients",
            "age_between_0_and_100",
            "ERROR",
            invalid_age.sum(),
        )
    )

    results.append(
        make_result(
            "patients",
            "gender_not_missing",
            "WARNING",
            df["gender"].isna().sum(),
        )
    )

    invalid_gender = (
        df["gender"].notna()
        & ~df["gender"].isin(VALID_GENDERS)
    )

    results.append(
        make_result(
            "patients",
            "gender_valid_category",
            "WARNING",
            invalid_gender.sum(),
        )
    )

    results.append(
        make_result(
            "patients",
            "insurance_not_missing",
            "WARNING",
            df["insurance_type"].isna().sum(),
        )
    )

    invalid_insurance = (
        df["insurance_type"].notna()
        & ~df["insurance_type"].isin(VALID_INSURANCE_TYPES)
    )

    results.append(
        make_result(
            "patients",
            "insurance_valid_category",
            "WARNING",
            invalid_insurance.sum(),
        )
    )

    return results

def validate_admissions(df):
    results = []

    results.append(
        make_result(
            "admissions",
            "admission_id_unique",
            "ERROR",
            df["admission_id"].duplicated().sum(),
        )
    )

    results.append(
        make_result(
            "admissions",
            "admission_id_not_null",
            "ERROR",
            df["admission_id"].isna().sum(),
        )
    )

    admission_date = pd.to_datetime(
        df["admission_date"],
        errors="coerce",
    )

    discharge_date = pd.to_datetime(
        df["discharge_date"],
        errors="coerce",
    )

    results.append(
        make_result(
            "admissions",
            "admission_date_valid",
            "ERROR",
            admission_date.isna().sum(),
        )
    )

    results.append(
        make_result(
            "admissions",
            "discharge_date_valid",
            "ERROR",
            discharge_date.isna().sum(),
        )
    )

    invalid_date_order = (
        admission_date.notna()
        & discharge_date.notna()
        & (discharge_date < admission_date)
    )

    results.append(
        make_result(
            "admissions",
            "discharge_not_before_admission",
            "ERROR",
            invalid_date_order.sum(),
        )
    )

    invalid_los = (
        df["length_of_stay"].isna()
        | (df["length_of_stay"] < 0)
    )

    results.append(
        make_result(
            "admissions",
            "length_of_stay_non_negative",
            "ERROR",
            invalid_los.sum(),
        )
    )

    calculated_los = (
    discharge_date - admission_date
    ).dt.days

    los_mismatch = (
        calculated_los.notna()
        & df["length_of_stay"].notna()
        & (calculated_los != df["length_of_stay"])
    )

    results.append(
        make_result(
            "admissions",
            "length_of_stay_matches_dates",
            "ERROR",
            los_mismatch.sum(),
        )
    )

    invalid_department = (
        df["department"].isna()
        | ~df["department"].isin(VALID_DEPARTMENTS)
    )

    results.append(
        make_result(
            "admissions",
            "department_valid",
            "WARNING",
            invalid_department.sum(),
        )
    )

    invalid_admission_type = (
        df["admission_type"].isna()
        | ~df["admission_type"].isin(VALID_ADMISSION_TYPES)
    )

    results.append(
        make_result(
            "admissions",
            "admission_type_valid",
            "WARNING",
            invalid_admission_type.sum(),
        )
    )

    invalid_bed = (
        df["bed_type"].notna()
        & ~df["bed_type"].isin(VALID_BED_TYPES)
    )

    results.append(
        make_result(
            "admissions",
            "bed_type_valid",
            "WARNING",
            invalid_bed.sum(),
        )
    )

    results.append(
        make_result(
            "admissions",
            "bed_type_not_missing",
            "WARNING",
            df["bed_type"].isna().sum(),
        )
    )

    return results

def validate_readmissions(df):
    results = []

    results.append(
        make_result(
            "readmissions",
            "readmission_id_unique",
            "ERROR",
            df["readmission_id"].duplicated().sum(),
        )
    )

    invalid_days = (
        df["days_since_discharge"].isna()
        | (df["days_since_discharge"] < 1)
        | (df["days_since_discharge"] > 30)
    )

    results.append(
        make_result(
            "readmissions",
            "days_since_discharge_between_1_and_30",
            "ERROR",
            invalid_days.sum(),
        )
    )

    return results

def validate_staffing(df):
    results = []

    invalid_staff = (
        df["staff_count"].isna()
        | (df["staff_count"] <= 0)
    )

    results.append(
        make_result(
            "staffing",
            "staff_count_positive",
            "ERROR",
            invalid_staff.sum(),
        )
    )

    invalid_patient_count = (
        df["patient_count"].notna()
        & (df["patient_count"] < 0)
    )

    results.append(
        make_result(
            "staffing",
            "patient_count_non_negative",
            "ERROR",
            invalid_patient_count.sum(),
        )
    )

    results.append(
        make_result(
            "staffing",
            "patient_count_not_missing",
            "WARNING",
            df["patient_count"].isna().sum(),
        )
    )

    invalid_department = (
        df["department"].isna()
        | ~df["department"].isin(VALID_DEPARTMENTS)
    )

    results.append(
        make_result(
            "staffing",
            "department_valid",
            "WARNING",
            invalid_department.sum(),
        )
    )

    invalid_shift = (
        df["shift"].isna()
        | ~df["shift"].isin(VALID_SHIFTS)
    )

    results.append(
        make_result(
            "staffing",
            "shift_valid",
            "WARNING",
            invalid_shift.sum(),
        )
    )

    return results

def validate_costs(df):
    results = []

    results.append(
        make_result(
            "costs",
            "admission_id_unique",
            "ERROR",
            df["admission_id"].duplicated().sum(),
        )
    )

    for column in [
        "billed_amount",
        "insurance_covered_amount",
        "out_of_pocket",
    ]:
        negative = (
            df[column].notna()
            & (df[column] < 0)
        )

        results.append(
            make_result(
                "costs",
                f"{column}_non_negative",
                "ERROR",
                negative.sum(),
            )
        )

    results.append(
        make_result(
            "costs",
            "insurance_covered_amount_not_missing",
            "WARNING",
            df["insurance_covered_amount"].isna().sum(),
        )
    )

    invalid_oop = (
        df["out_of_pocket"] > df["billed_amount"]
    )

    results.append(
        make_result(
            "costs",
            "out_of_pocket_not_above_bill",
            "ERROR",
            invalid_oop.sum(),
        )
    )

    complete_costs = (
        df["billed_amount"].notna()
        & df["insurance_covered_amount"].notna()
        & df["out_of_pocket"].notna()
    )

    calculated_bill = (
        df["insurance_covered_amount"]
        + df["out_of_pocket"]
    )

    mismatch = (
        complete_costs
        & ~np.isclose(
            df["billed_amount"],
            calculated_bill,
            atol=0.02,
        )
    )

    results.append(
        make_result(
            "costs",
            "bill_matches_covered_plus_oop",
            "ERROR",
            mismatch.sum(),
        )
    )

    return results

def validate_foreign_keys(datasets):
    results = []

    patients = datasets["patients"]
    admissions = datasets["admissions"]
    readmissions = datasets["readmissions"]
    costs = datasets["costs"]

    invalid_patient_fk = (
        ~admissions["patient_id"].isin(
            patients["patient_id"]
        )
    )

    results.append(
        make_result(
            "admissions",
            "patient_id_exists_in_patients",
            "ERROR",
            invalid_patient_fk.sum(),
        )
    )

    invalid_readmission_fk = (
        ~readmissions["original_admission_id"].isin(
            admissions["admission_id"]
        )
    )

    results.append(
        make_result(
            "readmissions",
            "original_admission_exists",
            "ERROR",
            invalid_readmission_fk.sum(),
        )
    )

    invalid_cost_fk = (
        ~costs["admission_id"].isin(
            admissions["admission_id"]
        )
    )

    results.append(
        make_result(
            "costs",
            "admission_id_exists",
            "ERROR",
            invalid_cost_fk.sum(),
        )
    )

    return results


def run_validations(datasets):

    results = []

    results.extend(
        validate_patients(datasets["patients"])
    )

    results.extend(
        validate_admissions(datasets["admissions"])
    )

    results.extend(
        validate_readmissions(datasets["readmissions"])
    )

    results.extend(
        validate_staffing(datasets["staffing"])
    )

    results.extend(
        validate_costs(datasets["costs"])
    )

    results.extend(
        validate_foreign_keys(datasets)
    )

    return pd.DataFrame(results)

def save_validation_report(report):

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        REPORT_DIR / "validation_summary.csv"
    )

    report.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nValidation report saved to: "
        f"{output_path}"
    )

def main():

    datasets = load_processed_data()

    report = run_validations(datasets)

    print("\nDATA QUALITY VALIDATION")
    print("=" * 80)

    print(
        report.to_string(index=False)
    )

    save_validation_report(report)


if __name__ == "__main__":
    main()