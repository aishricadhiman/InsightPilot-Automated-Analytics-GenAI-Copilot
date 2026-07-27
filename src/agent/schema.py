"""
Trusted analytical schema exposed to the GenAI analytics agent.

The agent should query curated analytical views rather than
raw database tables whenever possible.
"""


# ============================================================
# DATABASE SCHEMA CONTEXT
# ============================================================

DATABASE_SCHEMA = """
DATABASE: hospital_analytics
DATABASE ENGINE: MySQL

The database contains four curated analytical views.

============================================================
1. vw_admission_metrics
============================================================

GRAIN:
One row per hospital admission.

COLUMNS:

admission_id
    Unique identifier for an admission.

patient_id
    Identifier of the patient.

admission_date
    Date the patient was admitted.

discharge_date
    Date the patient was discharged.

admission_type
    Type of admission such as Emergency, Elective, or Transfer.

department
    Hospital department.

bed_type
    Bed category associated with the admission.

length_of_stay
    Number of days between admission and discharge.

patient_age
    Patient age.

gender
    Patient gender.

insurance_type
    Patient insurance category.

billed_amount
    Total amount billed for the admission.

insurance_covered_amount
    Amount covered by insurance.

out_of_pocket
    Amount paid by the patient.

is_readmitted_30d
    1 if a recorded readmission occurred within 30 days,
    otherwise 0.

days_to_readmission
    Number of days between discharge and readmission.
    NULL when there was no readmission.

readmission_reason
    Recorded reason for readmission.
    NULL when there was no readmission.


============================================================
2. vw_readmission_metrics
============================================================

GRAIN:
One row per original hospital admission.

COLUMNS:

admission_id
patient_id
admission_date
discharge_date
department
admission_type
length_of_stay

dataset_end_date
    Latest discharge date available in the dataset.

is_eligible_30d
    1 if the admission has a complete 30-day observation
    window after discharge, otherwise 0.

is_readmitted_30d
    1 if a recorded readmission occurred within 30 days,
    otherwise 0.

days_to_readmission
    Days from discharge to readmission.

readmission_reason
    Recorded reason for readmission.


IMPORTANT READMISSION RULE:

Do NOT calculate 30-day readmission rate using all admissions.

Correct formula:

    eligible readmitted admissions
    ------------------------------ * 100
        eligible admissions

SQL pattern:

SUM(
    CASE
        WHEN is_eligible_30d = 1
         AND is_readmitted_30d = 1
        THEN 1
        ELSE 0
    END
) * 100.0
/
NULLIF(SUM(is_eligible_30d), 0)


============================================================
3. vw_staffing_metrics
============================================================

GRAIN:
One row per date + department + shift.

COLUMNS:

staffing_id
    Staffing observation identifier.

date
    Staffing observation date.

department
    Hospital department.

shift
    Work shift such as Day, Evening, or Night.

staff_count
    Number of staff assigned to the observation.

patient_count
    Number of patients represented by the observation.

patient_to_staff_ratio
    Patients per staff member for that observation.

staff_to_patient_ratio
    Staff members per patient for that observation.


IMPORTANT STAFFING RULE:

When aggregating patient-to-staff workload across multiple
observations, use:

    SUM(patient_count) / NULLIF(SUM(staff_count), 0)

Do NOT use AVG(patient_to_staff_ratio) for the primary
aggregate workload KPI.


============================================================
4. vw_cost_metrics
============================================================

GRAIN:
One row per hospital admission.

COLUMNS:

admission_id
patient_id
admission_date
discharge_date
department
admission_type
length_of_stay
insurance_type

billed_amount
    Amount billed for the admission.

insurance_covered_amount
    Amount covered by insurance.

out_of_pocket
    Patient out-of-pocket amount.

insurance_coverage_pct
    Insurance-covered percentage of billed amount.

out_of_pocket_pct
    Patient-paid percentage of billed amount.

billed_cost_per_day
    Billed amount divided by length of stay.
    NULL when length_of_stay is zero.


IMPORTANT FINANCIAL RULE:

billed_amount represents billed charges.

It must NOT be described as:
    revenue
    profit
    operating cost
    payment received


============================================================
GENERAL ANALYTICAL RULES
============================================================

1. Prefer the curated analytical views above.

2. Understand table grain before joining views.

3. vw_admission_metrics, vw_readmission_metrics and
   vw_cost_metrics are admission-level.

4. vw_staffing_metrics is NOT admission-level.
   Its grain is date + department + shift.

5. Do not directly join individual staffing observations to
   individual admissions merely on department because this
   can multiply rows and corrupt metrics.

6. For cross-domain time analysis, aggregate each domain to
   a common grain such as department + month before joining.

7. Use COUNT(DISTINCT admission_id) when the query requires
   unique admissions and duplicate risk exists.

8. Use NULLIF(..., 0) when a denominator could be zero.

9. Do not infer causation from associations.

10. Unknown categorical values represent missing/unknown
    source information and should not automatically be
    interpreted as a real business category.

11. MySQL syntax must be used.
"""


# ============================================================
# BUSINESS KPI DEFINITIONS
# ============================================================

KPI_DEFINITIONS = """
TRUSTED KPI DEFINITIONS

Total Admissions
    COUNT(DISTINCT admission_id)

Unique Patients
    COUNT(DISTINCT patient_id)

Average Length of Stay
    AVG(length_of_stay)

30-Day Readmission Rate
    Number of eligible admissions with a recorded 30-day
    readmission divided by total 30-day eligible admissions,
    multiplied by 100.

Patient-to-Staff Ratio
    For aggregated analysis:

    SUM(patient_count)
    /
    NULLIF(SUM(staff_count), 0)

Total Billed Amount
    SUM(billed_amount)

Average Billed Amount Per Admission
    AVG(billed_amount)

Insurance Coverage Percentage
    SUM(insurance_covered_amount) * 100.0
    /
    NULLIF(SUM(billed_amount), 0)

Out-of-Pocket Percentage
    SUM(out_of_pocket) * 100.0
    /
    NULLIF(SUM(billed_amount), 0)
"""


# ============================================================
# AGENT SCHEMA CONTEXT
# ============================================================

def get_schema_context() -> str:
    """
    Return the trusted database schema and KPI definitions
    supplied to the LLM during SQL generation.
    """

    return f"""
{DATABASE_SCHEMA}

{KPI_DEFINITIONS}
""".strip()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print(get_schema_context())