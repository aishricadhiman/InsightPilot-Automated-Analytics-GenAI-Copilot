-- ============================================================
-- READMISSIONS ANALYSIS
-- Source: vw_readmission_metrics
-- Purpose:
-- Analyse 30-day readmission performance, department patterns,
-- timing, and reasons.
-- ============================================================


-- ============================================================
-- 1. OVERALL 30-DAY READMISSION KPIs
-- Only admissions with a complete 30-day observation window
-- are included in the denominator.
-- ============================================================

SELECT
    COUNT(*) AS total_admissions,

    SUM(is_eligible_30d) AS eligible_admissions,

    SUM(
        CASE
            WHEN is_eligible_30d = 1
             AND is_readmitted_30d = 1
            THEN 1
            ELSE 0
        END
    ) AS readmitted_admissions,

    ROUND(
        SUM(
            CASE
                WHEN is_eligible_30d = 1
                 AND is_readmitted_30d = 1
                THEN 1
                ELSE 0
            END
        ) * 100.0
        / NULLIF(SUM(is_eligible_30d), 0),
        2
    ) AS readmission_rate_pct

FROM vw_readmission_metrics;


-- ============================================================
-- 2. READMISSION RATE BY DEPARTMENT
-- Which departments have higher 30-day readmission rates?
-- ============================================================

SELECT
    department,

    SUM(is_eligible_30d) AS eligible_admissions,

    SUM(
        CASE
            WHEN is_eligible_30d = 1
             AND is_readmitted_30d = 1
            THEN 1
            ELSE 0
        END
    ) AS readmitted_admissions,

    ROUND(
        SUM(
            CASE
                WHEN is_eligible_30d = 1
                 AND is_readmitted_30d = 1
                THEN 1
                ELSE 0
            END
        ) * 100.0
        / NULLIF(SUM(is_eligible_30d), 0),
        2
    ) AS readmission_rate_pct

FROM vw_readmission_metrics

GROUP BY department

ORDER BY readmission_rate_pct DESC;


-- ============================================================
-- 3. READMISSION RATE BY ADMISSION TYPE
-- Emergency/elective/transfer comparison
-- ============================================================

SELECT
    admission_type,

    SUM(is_eligible_30d) AS eligible_admissions,

    SUM(
        CASE
            WHEN is_eligible_30d = 1
             AND is_readmitted_30d = 1
            THEN 1
            ELSE 0
        END
    ) AS readmitted_admissions,

    ROUND(
        SUM(
            CASE
                WHEN is_eligible_30d = 1
                 AND is_readmitted_30d = 1
                THEN 1
                ELSE 0
            END
        ) * 100.0
        / NULLIF(SUM(is_eligible_30d), 0),
        2
    ) AS readmission_rate_pct

FROM vw_readmission_metrics

GROUP BY admission_type

ORDER BY readmission_rate_pct DESC;


-- ============================================================
-- 4. READMISSION REASONS
-- What are the most common recorded reasons?
-- ============================================================

SELECT
    readmission_reason,

    COUNT(*) AS readmissions,

    ROUND(
        COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER (),
        2
    ) AS share_pct

FROM vw_readmission_metrics

WHERE
    is_eligible_30d = 1
    AND is_readmitted_30d = 1

GROUP BY readmission_reason

ORDER BY readmissions DESC;


-- ============================================================
-- 5. TIME TO READMISSION
-- ============================================================

SELECT
    COUNT(*) AS readmissions,

    ROUND(
        AVG(days_to_readmission),
        2
    ) AS avg_days_to_readmission,

    MIN(days_to_readmission)
        AS earliest_readmission_days,

    MAX(days_to_readmission)
        AS latest_readmission_days

FROM vw_readmission_metrics

WHERE
    is_eligible_30d = 1
    AND is_readmitted_30d = 1;


-- ============================================================
-- 6. READMISSION TIMING BUCKETS
-- Are patients returning very quickly or closer to day 30?
-- ============================================================

SELECT
    CASE
        WHEN days_to_readmission BETWEEN 1 AND 7
            THEN '01-07 days'

        WHEN days_to_readmission BETWEEN 8 AND 14
            THEN '08-14 days'

        WHEN days_to_readmission BETWEEN 15 AND 21
            THEN '15-21 days'

        WHEN days_to_readmission BETWEEN 22 AND 30
            THEN '22-30 days'

        ELSE 'Other'
    END AS readmission_window,

    COUNT(*) AS readmissions,

    ROUND(
        COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER (),
        2
    ) AS share_pct

FROM vw_readmission_metrics

WHERE
    is_eligible_30d = 1
    AND is_readmitted_30d = 1

GROUP BY readmission_window

ORDER BY MIN(days_to_readmission);


-- ============================================================
-- 7. MONTHLY READMISSION RATE
-- Cohort month = original admission's discharge month
-- ============================================================

SELECT
    DATE_FORMAT(
        discharge_date,
        '%Y-%m'
    ) AS discharge_month,

    SUM(is_eligible_30d)
        AS eligible_admissions,

    SUM(
        CASE
            WHEN is_eligible_30d = 1
             AND is_readmitted_30d = 1
            THEN 1
            ELSE 0
        END
    ) AS readmitted_admissions,

    ROUND(
        SUM(
            CASE
                WHEN is_eligible_30d = 1
                 AND is_readmitted_30d = 1
                THEN 1
                ELSE 0
            END
        ) * 100.0
        / NULLIF(SUM(is_eligible_30d), 0),
        2
    ) AS readmission_rate_pct

FROM vw_readmission_metrics

WHERE is_eligible_30d = 1

GROUP BY
    DATE_FORMAT(
        discharge_date,
        '%Y-%m'
    )

ORDER BY discharge_month;


-- ============================================================
-- 8. LOS VS READMISSION
-- Compare LOS between readmitted and non-readmitted admissions
-- ============================================================

SELECT
    CASE
        WHEN is_readmitted_30d = 1
            THEN 'Readmitted'
        ELSE 'Not Readmitted'
    END AS readmission_status,

    COUNT(*) AS admissions,

    ROUND(
        AVG(length_of_stay),
        2
    ) AS avg_length_of_stay

FROM vw_readmission_metrics

WHERE is_eligible_30d = 1

GROUP BY is_readmitted_30d

ORDER BY is_readmitted_30d DESC;


-- ============================================================
-- 9. DEPARTMENT + READMISSION REASON
-- Helps identify department-specific patterns
-- ============================================================

SELECT
    department,
    readmission_reason,

    COUNT(*) AS readmissions

FROM vw_readmission_metrics

WHERE
    is_eligible_30d = 1
    AND is_readmitted_30d = 1

GROUP BY
    department,
    readmission_reason

ORDER BY
    department,
    readmissions DESC;