-- ============================================================
-- VIEW: vw_readmission_metrics
-- PURPOSE:
-- Creates admission-level readmission metrics and identifies
-- admissions eligible for the 30-day readmission KPI.
--
-- GRAIN:
-- One row per admission_id
-- ============================================================

CREATE OR REPLACE VIEW vw_readmission_metrics AS

SELECT
    a.admission_id,
    a.patient_id,
    a.admission_date,
    a.discharge_date,
    a.department,
    a.admission_type,
    a.length_of_stay,

    -- --------------------------------------------------------
    -- Observation endpoint
    -- Latest discharge date available in the dataset
    -- --------------------------------------------------------

    dataset.dataset_end_date,


    -- --------------------------------------------------------
    -- 30-day eligibility
    -- Admission must have at least 30 days of follow-up
    -- available after discharge
    -- --------------------------------------------------------

    CASE
        WHEN a.discharge_date <=
             DATE_SUB(dataset.dataset_end_date, INTERVAL 30 DAY)
        THEN 1
        ELSE 0
    END AS is_eligible_30d,


    -- --------------------------------------------------------
    -- Readmission flag
    -- --------------------------------------------------------

    CASE
        WHEN r.original_admission_id IS NOT NULL
        THEN 1
        ELSE 0
    END AS is_readmitted_30d,


    r.days_since_discharge AS days_to_readmission,
    r.reason_code AS readmission_reason


FROM admissions AS a


-- ------------------------------------------------------------
-- Find observation endpoint once and attach it to admissions
-- ------------------------------------------------------------

CROSS JOIN (
    SELECT
        MAX(discharge_date) AS dataset_end_date
    FROM admissions
) AS dataset


-- ------------------------------------------------------------
-- Join recorded 30-day readmissions
-- ------------------------------------------------------------

LEFT JOIN readmissions AS r
    ON a.admission_id = r.original_admission_id;