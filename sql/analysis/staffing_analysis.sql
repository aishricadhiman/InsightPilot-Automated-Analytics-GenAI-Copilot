-- ============================================================
-- STAFFING OPERATIONAL ANALYSIS
-- Source: vw_staffing_metrics
-- Purpose:
-- Analyse staffing levels, patient workload, department
-- pressure, shift patterns, and trends.
--
-- GRAIN OF SOURCE VIEW:
-- date + department + shift
-- ============================================================


-- ============================================================
-- 1. OVERALL STAFFING KPIs
-- ============================================================

SELECT
    COUNT(*) AS staffing_observations,

    SUM(staff_count) AS total_staff_assignments,

    SUM(patient_count) AS total_patient_assignments,

    ROUND(
        SUM(patient_count) * 1.0
        / NULLIF(SUM(staff_count), 0),
        2
    ) AS overall_patient_to_staff_ratio

FROM vw_staffing_metrics;


-- ============================================================
-- 2. STAFFING BY DEPARTMENT
-- Compare workload across departments.
--
-- IMPORTANT:
-- Ratio is calculated from totals rather than AVG(ratio).
-- This gives a weighted patient-to-staff ratio.
-- ============================================================

SELECT
    department,

    SUM(staff_count) AS total_staff,

    SUM(patient_count) AS total_patients,

    ROUND(
        SUM(patient_count) * 1.0
        / NULLIF(SUM(staff_count), 0),
        2
    ) AS patient_to_staff_ratio

FROM vw_staffing_metrics

GROUP BY department

ORDER BY patient_to_staff_ratio DESC;


-- ============================================================
-- 3. STAFFING BY SHIFT
-- Which shifts experience the greatest workload?
-- ============================================================

SELECT
    shift,

    SUM(staff_count) AS total_staff,

    SUM(patient_count) AS total_patients,

    ROUND(
        SUM(patient_count) * 1.0
        / NULLIF(SUM(staff_count), 0),
        2
    ) AS patient_to_staff_ratio

FROM vw_staffing_metrics

GROUP BY shift

ORDER BY patient_to_staff_ratio DESC;


-- ============================================================
-- 4. DEPARTMENT + SHIFT WORKLOAD
-- Identify specific department/shift combinations under
-- comparatively higher workload.
-- ============================================================

SELECT
    department,
    shift,

    SUM(staff_count) AS total_staff,

    SUM(patient_count) AS total_patients,

    ROUND(
        SUM(patient_count) * 1.0
        / NULLIF(SUM(staff_count), 0),
        2
    ) AS patient_to_staff_ratio

FROM vw_staffing_metrics

GROUP BY
    department,
    shift

ORDER BY patient_to_staff_ratio DESC;


-- ============================================================
-- 5. MONTHLY STAFFING TREND
-- ============================================================

SELECT
    DATE_FORMAT(
        date,
        '%Y-%m'
    ) AS staffing_month,

    SUM(staff_count) AS total_staff,

    SUM(patient_count) AS total_patients,

    ROUND(
        SUM(patient_count) * 1.0
        / NULLIF(SUM(staff_count), 0),
        2
    ) AS patient_to_staff_ratio

FROM vw_staffing_metrics

GROUP BY
    DATE_FORMAT(
        date,
        '%Y-%m'
    )

ORDER BY staffing_month;


-- ============================================================
-- 6. MONTHLY WORKLOAD BY DEPARTMENT
-- Useful for detecting changing operational pressure.
-- ============================================================

SELECT
    DATE_FORMAT(
        date,
        '%Y-%m'
    ) AS staffing_month,

    department,

    SUM(staff_count) AS total_staff,

    SUM(patient_count) AS total_patients,

    ROUND(
        SUM(patient_count) * 1.0
        / NULLIF(SUM(staff_count), 0),
        2
    ) AS patient_to_staff_ratio

FROM vw_staffing_metrics

GROUP BY
    DATE_FORMAT(
        date,
        '%Y-%m'
    ),
    department

ORDER BY
    staffing_month,
    patient_to_staff_ratio DESC;


-- ============================================================
-- 7. HIGHEST WORKLOAD OBSERVATIONS
-- Find individual date/department/shift observations with
-- the highest patient-to-staff ratios.
-- ============================================================

SELECT
    date,
    department,
    shift,
    staff_count,
    patient_count,
    patient_to_staff_ratio

FROM vw_staffing_metrics

ORDER BY patient_to_staff_ratio DESC

LIMIT 20;


-- ============================================================
-- 8. LOWEST STAFFING OBSERVATIONS
-- Shows observations with the fewest staff members.
-- This does NOT automatically mean understaffing.
-- ============================================================

SELECT
    date,
    department,
    shift,
    staff_count,
    patient_count,
    patient_to_staff_ratio

FROM vw_staffing_metrics

ORDER BY
    staff_count ASC,
    patient_to_staff_ratio DESC

LIMIT 20;


-- ============================================================
-- 9. DAILY HOSPITAL WORKLOAD
-- Aggregate all departments and shifts for each date.
-- ============================================================

SELECT
    date,

    SUM(staff_count) AS total_staff,

    SUM(patient_count) AS total_patients,

    ROUND(
        SUM(patient_count) * 1.0
        / NULLIF(SUM(staff_count), 0),
        2
    ) AS patient_to_staff_ratio

FROM vw_staffing_metrics

GROUP BY date

ORDER BY date;


-- ============================================================
-- 10. WORKLOAD VARIABILITY BY DEPARTMENT
-- Shows whether workload ratios are stable or fluctuate.
-- ============================================================

SELECT
    department,

    ROUND(
        AVG(patient_to_staff_ratio),
        2
    ) AS avg_observation_ratio,

    ROUND(
        STDDEV_POP(patient_to_staff_ratio),
        2
    ) AS ratio_std_dev,

    MIN(patient_to_staff_ratio)
        AS min_ratio,

    MAX(patient_to_staff_ratio)
        AS max_ratio

FROM vw_staffing_metrics

GROUP BY department

ORDER BY ratio_std_dev DESC;