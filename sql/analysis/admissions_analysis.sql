-- ============================================================
-- ADMISSIONS OPERATIONAL ANALYSIS
-- Source: vw_admission_metrics
-- ============================================================


-- ============================================================
-- 1. OVERALL ADMISSION KPIs
-- ============================================================

SELECT
    COUNT(DISTINCT admission_id) AS total_admissions,

    COUNT(DISTINCT patient_id) AS unique_patients,

    ROUND(
        AVG(length_of_stay),
        2
    ) AS avg_length_of_stay,

    MIN(length_of_stay) AS min_length_of_stay,

    MAX(length_of_stay) AS max_length_of_stay

FROM vw_admission_metrics;


-- ============================================================
-- 2. ADMISSIONS BY DEPARTMENT
-- Which departments handle the highest volume?
-- ============================================================

SELECT
    department,

    COUNT(*) AS total_admissions,

    ROUND(
        COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER (),
        2
    ) AS admission_share_pct

FROM vw_admission_metrics

GROUP BY department

ORDER BY total_admissions DESC;


-- ============================================================
-- 3. LENGTH OF STAY BY DEPARTMENT
-- Which departments have longer patient stays?
-- ============================================================

SELECT
    department,

    COUNT(*) AS total_admissions,

    ROUND(
        AVG(length_of_stay),
        2
    ) AS avg_length_of_stay,

    MIN(length_of_stay) AS min_length_of_stay,

    MAX(length_of_stay) AS max_length_of_stay

FROM vw_admission_metrics

GROUP BY department

ORDER BY avg_length_of_stay DESC;


-- ============================================================
-- 4. ADMISSION TYPE MIX
-- Emergency vs elective vs transfer etc.
-- ============================================================

SELECT
    admission_type,

    COUNT(*) AS total_admissions,

    ROUND(
        COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER (),
        2
    ) AS admission_pct

FROM vw_admission_metrics

GROUP BY admission_type

ORDER BY total_admissions DESC;


-- ============================================================
-- 5. MONTHLY ADMISSION TREND
-- ============================================================

SELECT
    DATE_FORMAT(
        admission_date,
        '%Y-%m'
    ) AS admission_month,

    COUNT(*) AS total_admissions,

    ROUND(
        AVG(length_of_stay),
        2
    ) AS avg_length_of_stay

FROM vw_admission_metrics

GROUP BY
    DATE_FORMAT(
        admission_date,
        '%Y-%m'
    )

ORDER BY admission_month;


-- ============================================================
-- 6. MONTHLY ADMISSIONS BY DEPARTMENT
-- Useful for identifying department-specific demand changes
-- ============================================================

SELECT
    DATE_FORMAT(
        admission_date,
        '%Y-%m'
    ) AS admission_month,

    department,

    COUNT(*) AS total_admissions,

    ROUND(
        AVG(length_of_stay),
        2
    ) AS avg_length_of_stay

FROM vw_admission_metrics

GROUP BY
    DATE_FORMAT(
        admission_date,
        '%Y-%m'
    ),
    department

ORDER BY
    admission_month,
    total_admissions DESC;


-- ============================================================
-- 7. BED TYPE UTILISATION
-- ============================================================

SELECT
    bed_type,

    COUNT(*) AS total_admissions,

    ROUND(
        COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER (),
        2
    ) AS utilisation_pct,

    ROUND(
        AVG(length_of_stay),
        2
    ) AS avg_length_of_stay

FROM vw_admission_metrics

GROUP BY bed_type

ORDER BY total_admissions DESC;


-- ============================================================
-- 8. DEPARTMENT + ADMISSION TYPE
-- Understand what drives department workload
-- ============================================================

SELECT
    department,
    admission_type,

    COUNT(*) AS total_admissions,

    ROUND(
        AVG(length_of_stay),
        2
    ) AS avg_length_of_stay

FROM vw_admission_metrics

GROUP BY
    department,
    admission_type

ORDER BY
    department,
    total_admissions DESC;