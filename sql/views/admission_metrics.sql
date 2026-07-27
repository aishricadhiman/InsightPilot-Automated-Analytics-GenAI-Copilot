-- ============================================================
-- VIEW: vw_admission_metrics
-- PURPOSE:
-- Creates an admission-level analytical dataset combining
-- patient, admission, cost, and 30-day readmission information.
--
-- GRAIN:
-- One row per admission_id
-- ============================================================

CREATE OR REPLACE VIEW vw_admission_metrics AS

SELECT
    -- --------------------------------------------------------
    -- Admission information
    -- --------------------------------------------------------

    a.admission_id,
    a.patient_id,
    a.admission_date,
    a.discharge_date,
    a.admission_type,
    a.department,
    a.bed_type,
    a.length_of_stay,


    -- --------------------------------------------------------
    -- Patient information
    -- --------------------------------------------------------

    p.age AS patient_age,
    p.gender,
    p.insurance_type,


    -- --------------------------------------------------------
    -- Cost information
    -- --------------------------------------------------------

    c.billed_amount,
    c.insurance_covered_amount,
    c.out_of_pocket,


    -- --------------------------------------------------------
    -- Readmission information
    -- --------------------------------------------------------

    CASE
        WHEN r.original_admission_id IS NOT NULL
        THEN 1
        ELSE 0
    END AS is_readmitted_30d,

    r.days_since_discharge AS days_to_readmission,

    r.reason_code AS readmission_reason


FROM admissions AS a


-- Every valid admission should have a patient
INNER JOIN patients AS p
    ON a.patient_id = p.patient_id


-- Keep admission even if cost information is unavailable
LEFT JOIN costs AS c
    ON a.admission_id = c.admission_id


-- Keep admissions that were not readmitted
LEFT JOIN readmissions AS r
    ON a.admission_id = r.original_admission_id;