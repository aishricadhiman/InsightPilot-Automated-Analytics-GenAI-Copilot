-- ============================================================
-- COST & FINANCIAL ANALYSIS
-- Source: vw_cost_metrics
-- Purpose:
-- Analyse billed costs, insurance coverage, patient financial
-- burden, departmental costs, trends, and high-cost cases.
--
-- GRAIN OF SOURCE VIEW:
-- One row per admission_id
-- ============================================================


-- ============================================================
-- 1. OVERALL COST KPIs
-- ============================================================

SELECT
    COUNT(*) AS total_admissions,

    ROUND(
        SUM(billed_amount),
        2
    ) AS total_billed_amount,

    ROUND(
        AVG(billed_amount),
        2
    ) AS avg_cost_per_admission,

    ROUND(
        SUM(insurance_covered_amount),
        2
    ) AS total_insurance_covered,

    ROUND(
        SUM(out_of_pocket),
        2
    ) AS total_out_of_pocket,

    ROUND(
        SUM(insurance_covered_amount) * 100.0
        / NULLIF(SUM(billed_amount), 0),
        2
    ) AS overall_insurance_coverage_pct,

    ROUND(
        SUM(out_of_pocket) * 100.0
        / NULLIF(SUM(billed_amount), 0),
        2
    ) AS overall_out_of_pocket_pct

FROM vw_cost_metrics;


-- ============================================================
-- 2. COST BY DEPARTMENT
-- Which departments account for the highest billed amounts?
-- ============================================================

SELECT
    department,

    COUNT(*) AS admissions,

    ROUND(
        SUM(billed_amount),
        2
    ) AS total_billed_amount,

    ROUND(
        AVG(billed_amount),
        2
    ) AS avg_cost_per_admission,

    ROUND(
        SUM(billed_amount) * 100.0
        / SUM(SUM(billed_amount)) OVER (),
        2
    ) AS share_of_total_cost_pct

FROM vw_cost_metrics

GROUP BY department

ORDER BY total_billed_amount DESC;


-- ============================================================
-- 3. COST BY ADMISSION TYPE
-- Emergency/elective/transfer financial comparison
-- ============================================================

SELECT
    admission_type,

    COUNT(*) AS admissions,

    ROUND(
        SUM(billed_amount),
        2
    ) AS total_billed_amount,

    ROUND(
        AVG(billed_amount),
        2
    ) AS avg_cost_per_admission,

    ROUND(
        AVG(out_of_pocket),
        2
    ) AS avg_out_of_pocket

FROM vw_cost_metrics

GROUP BY admission_type

ORDER BY avg_cost_per_admission DESC;


-- ============================================================
-- 4. MONTHLY COST TREND
-- ============================================================

SELECT
    DATE_FORMAT(
        admission_date,
        '%Y-%m'
    ) AS admission_month,

    COUNT(*) AS admissions,

    ROUND(
        SUM(billed_amount),
        2
    ) AS total_billed_amount,

    ROUND(
        AVG(billed_amount),
        2
    ) AS avg_cost_per_admission,

    ROUND(
        AVG(out_of_pocket),
        2
    ) AS avg_out_of_pocket

FROM vw_cost_metrics

GROUP BY
    DATE_FORMAT(
        admission_date,
        '%Y-%m'
    )

ORDER BY admission_month;


-- ============================================================
-- 5. INSURANCE TYPE FINANCIAL ANALYSIS
-- Compare financial patterns across insurance categories.
-- ============================================================

SELECT
    insurance_type,

    COUNT(*) AS admissions,

    ROUND(
        SUM(billed_amount),
        2
    ) AS total_billed_amount,

    ROUND(
        AVG(billed_amount),
        2
    ) AS avg_cost_per_admission,

    ROUND(
        SUM(insurance_covered_amount) * 100.0
        / NULLIF(SUM(billed_amount), 0),
        2
    ) AS insurance_coverage_pct,

    ROUND(
        SUM(out_of_pocket) * 100.0
        / NULLIF(SUM(billed_amount), 0),
        2
    ) AS out_of_pocket_pct,

    ROUND(
        AVG(out_of_pocket),
        2
    ) AS avg_out_of_pocket

FROM vw_cost_metrics

GROUP BY insurance_type

ORDER BY avg_cost_per_admission DESC;


-- ============================================================
-- 6. COST BY LENGTH OF STAY
-- Does cost increase as hospital stay becomes longer?
-- ============================================================

SELECT
    length_of_stay,

    COUNT(*) AS admissions,

    ROUND(
        AVG(billed_amount),
        2
    ) AS avg_billed_amount,

    ROUND(
        AVG(out_of_pocket),
        2
    ) AS avg_out_of_pocket

FROM vw_cost_metrics

GROUP BY length_of_stay

ORDER BY length_of_stay;


-- ============================================================
-- 7. LOS BUCKET COST ANALYSIS
-- Easier to interpret than every individual LOS value.
-- ============================================================

SELECT
    CASE
        WHEN length_of_stay = 0
            THEN 'Same day'

        WHEN length_of_stay BETWEEN 1 AND 3
            THEN '1-3 days'

        WHEN length_of_stay BETWEEN 4 AND 7
            THEN '4-7 days'

        WHEN length_of_stay BETWEEN 8 AND 14
            THEN '8-14 days'

        ELSE '15+ days'
    END AS los_group,

    COUNT(*) AS admissions,

    ROUND(
        AVG(billed_amount),
        2
    ) AS avg_billed_amount,

    ROUND(
        SUM(billed_amount),
        2
    ) AS total_billed_amount,

    ROUND(
        AVG(out_of_pocket),
        2
    ) AS avg_out_of_pocket

FROM vw_cost_metrics

GROUP BY los_group

ORDER BY
    MIN(length_of_stay);


-- ============================================================
-- 8. HIGHEST-COST ADMISSIONS
-- Investigation candidates, not automatically anomalies/errors.
-- ============================================================

SELECT
    admission_id,
    patient_id,
    department,
    admission_type,
    admission_date,
    length_of_stay,

    billed_amount,
    insurance_covered_amount,
    out_of_pocket,

    insurance_coverage_pct,
    out_of_pocket_pct

FROM vw_cost_metrics

ORDER BY billed_amount DESC

LIMIT 20;


-- ============================================================
-- 9. HIGHEST OUT-OF-POCKET ADMISSIONS
-- Cases with the largest absolute patient payment.
-- ============================================================

SELECT
    admission_id,
    patient_id,
    department,
    insurance_type,
    billed_amount,
    insurance_covered_amount,
    out_of_pocket,
    out_of_pocket_pct

FROM vw_cost_metrics

ORDER BY out_of_pocket DESC

LIMIT 20;


-- ============================================================
-- 10. DEPARTMENT INSURANCE COVERAGE
-- Compare payer mix / financial burden across departments.
-- ============================================================

SELECT
    department,

    ROUND(
        SUM(billed_amount),
        2
    ) AS total_billed_amount,

    ROUND(
        SUM(insurance_covered_amount),
        2
    ) AS insurance_covered,

    ROUND(
        SUM(out_of_pocket),
        2
    ) AS out_of_pocket,

    ROUND(
        SUM(insurance_covered_amount) * 100.0
        / NULLIF(SUM(billed_amount), 0),
        2
    ) AS insurance_coverage_pct,

    ROUND(
        SUM(out_of_pocket) * 100.0
        / NULLIF(SUM(billed_amount), 0),
        2
    ) AS out_of_pocket_pct

FROM vw_cost_metrics

GROUP BY department

ORDER BY out_of_pocket_pct DESC;


-- ============================================================
-- 11. COST PER DAY BY DEPARTMENT
-- Zero-day admissions have NULL billed_cost_per_day and are
-- excluded from this metric.
-- ============================================================

SELECT
    department,

    COUNT(billed_cost_per_day)
        AS admissions_with_cost_per_day,

    ROUND(
        AVG(billed_cost_per_day),
        2
    ) AS avg_billed_cost_per_day

FROM vw_cost_metrics

WHERE billed_cost_per_day IS NOT NULL

GROUP BY department

ORDER BY avg_billed_cost_per_day DESC;