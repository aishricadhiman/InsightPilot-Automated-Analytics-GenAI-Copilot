-- ============================================================
-- VIEW: vw_staffing_metrics
-- PURPOSE:
-- Creates operational staffing metrics for each
-- department, date, and shift.
--
-- GRAIN:
-- One row per date + department + shift
-- ============================================================

CREATE OR REPLACE VIEW vw_staffing_metrics AS

SELECT
    staffing_id,
    date,
    department,
    shift,

    staff_count,
    patient_count,


    -- --------------------------------------------------------
    -- Patient-to-staff ratio
    -- Number of patients handled per staff member
    -- --------------------------------------------------------

    ROUND(
        patient_count * 1.0
        / NULLIF(staff_count, 0),
        2
    ) AS patient_to_staff_ratio,


    -- --------------------------------------------------------
    -- Staff-to-patient ratio
    -- Useful for understanding staffing availability
    -- --------------------------------------------------------

    ROUND(
        staff_count * 1.0
        / NULLIF(patient_count, 0),
        3
    ) AS staff_to_patient_ratio


FROM staffing;