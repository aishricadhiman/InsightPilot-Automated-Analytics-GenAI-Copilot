-- ============================================================
-- CROSS-DOMAIN OPERATIONAL ANALYSIS
--
-- PURPOSE:
-- Combine admissions, LOS, readmissions, staffing, and
-- financial metrics to identify operational patterns.
--
-- IMPORTANT:
-- Source tables/views have different grains.
--
-- Admissions      -> admission_id
-- Readmissions    -> admission_id
-- Costs           -> admission_id
-- Staffing        -> date + department + shift
--
-- Therefore, metrics are aggregated BEFORE joining.
-- Common grain:
--
--      month + department
--
-- This prevents row multiplication and incorrect KPIs.
-- ============================================================


-- ============================================================
-- 1. DEPARTMENT PERFORMANCE SUMMARY
--
-- Creates a high-level comparison of:
-- admissions
-- LOS
-- readmissions
-- staffing workload
-- billed amounts
-- ============================================================

WITH admission_summary AS (

    SELECT
        department,

        COUNT(*) AS total_admissions,

        ROUND(
            AVG(length_of_stay),
            2
        ) AS avg_length_of_stay

    FROM vw_admission_metrics

    GROUP BY department
),

readmission_summary AS (

    SELECT
        department,

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
            /
            NULLIF(
                SUM(is_eligible_30d),
                0
            ),
            2
        ) AS readmission_rate_pct

    FROM vw_readmission_metrics

    GROUP BY department
),

staffing_summary AS (

    SELECT
        department,

        SUM(staff_count)
            AS total_staff_assignments,

        SUM(patient_count)
            AS total_patient_assignments,

        ROUND(
            SUM(patient_count) * 1.0
            /
            NULLIF(
                SUM(staff_count),
                0
            ),
            2
        ) AS patient_to_staff_ratio

    FROM vw_staffing_metrics

    GROUP BY department
),

cost_summary AS (

    SELECT
        department,

        ROUND(
            SUM(billed_amount),
            2
        ) AS total_billed_amount,

        ROUND(
            AVG(billed_amount),
            2
        ) AS avg_billed_per_admission,

        ROUND(
            AVG(out_of_pocket),
            2
        ) AS avg_out_of_pocket

    FROM vw_cost_metrics

    GROUP BY department
)

SELECT
    a.department,

    a.total_admissions,
    a.avg_length_of_stay,

    r.eligible_admissions,
    r.readmitted_admissions,
    r.readmission_rate_pct,

    s.total_staff_assignments,
    s.total_patient_assignments,
    s.patient_to_staff_ratio,

    c.total_billed_amount,
    c.avg_billed_per_admission,
    c.avg_out_of_pocket

FROM admission_summary AS a

LEFT JOIN readmission_summary AS r
    ON a.department = r.department

LEFT JOIN staffing_summary AS s
    ON a.department = s.department

LEFT JOIN cost_summary AS c
    ON a.department = c.department

ORDER BY a.total_admissions DESC;



-- ============================================================
-- 2. MONTHLY DEPARTMENT OPERATIONAL PERFORMANCE
--
-- Common grain:
-- month + department
--
-- Useful for dashboards and trend analysis.
-- ============================================================

WITH monthly_admissions AS (

    SELECT
        DATE_FORMAT(
            admission_date,
            '%Y-%m'
        ) AS analysis_month,

        department,

        COUNT(*) AS admissions,

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
),

monthly_staffing AS (

    SELECT
        DATE_FORMAT(
            date,
            '%Y-%m'
        ) AS analysis_month,

        department,

        SUM(staff_count)
            AS staff_assignments,

        SUM(patient_count)
            AS patient_assignments,

        ROUND(
            SUM(patient_count) * 1.0
            /
            NULLIF(
                SUM(staff_count),
                0
            ),
            2
        ) AS patient_to_staff_ratio

    FROM vw_staffing_metrics

    GROUP BY
        DATE_FORMAT(
            date,
            '%Y-%m'
        ),
        department
),

monthly_costs AS (

    SELECT
        DATE_FORMAT(
            admission_date,
            '%Y-%m'
        ) AS analysis_month,

        department,

        ROUND(
            SUM(billed_amount),
            2
        ) AS total_billed_amount,

        ROUND(
            AVG(billed_amount),
            2
        ) AS avg_billed_per_admission

    FROM vw_cost_metrics

    GROUP BY
        DATE_FORMAT(
            admission_date,
            '%Y-%m'
        ),
        department
)

SELECT
    a.analysis_month,
    a.department,

    a.admissions,
    a.avg_length_of_stay,

    s.staff_assignments,
    s.patient_assignments,
    s.patient_to_staff_ratio,

    c.total_billed_amount,
    c.avg_billed_per_admission

FROM monthly_admissions AS a

LEFT JOIN monthly_staffing AS s
    ON a.analysis_month = s.analysis_month
    AND a.department = s.department

LEFT JOIN monthly_costs AS c
    ON a.analysis_month = c.analysis_month
    AND a.department = c.department

ORDER BY
    a.analysis_month,
    a.department;



-- ============================================================
-- 3. MONTHLY DEPARTMENT READMISSION PERFORMANCE
--
-- IMPORTANT:
-- Month represents the discharge month of the original
-- admission because readmission performance belongs to
-- the discharged patient cohort.
-- ============================================================

SELECT
    DATE_FORMAT(
        discharge_date,
        '%Y-%m'
    ) AS discharge_month,

    department,

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
        /
        NULLIF(
            SUM(is_eligible_30d),
            0
        ),
        2
    ) AS readmission_rate_pct

FROM vw_readmission_metrics

WHERE is_eligible_30d = 1

GROUP BY
    DATE_FORMAT(
        discharge_date,
        '%Y-%m'
    ),
    department

ORDER BY
    discharge_month,
    readmission_rate_pct DESC;



-- ============================================================
-- 4. STAFFING WORKLOAD VS LENGTH OF STAY
--
-- Compare monthly department workload with LOS.
--
-- This identifies ASSOCIATION patterns only.
-- It does NOT establish that staffing causes LOS changes.
-- ============================================================

WITH monthly_staffing AS (

    SELECT
        DATE_FORMAT(
            date,
            '%Y-%m'
        ) AS analysis_month,

        department,

        ROUND(
            SUM(patient_count) * 1.0
            /
            NULLIF(
                SUM(staff_count),
                0
            ),
            2
        ) AS patient_to_staff_ratio

    FROM vw_staffing_metrics

    GROUP BY
        DATE_FORMAT(
            date,
            '%Y-%m'
        ),
        department
),

monthly_los AS (

    SELECT
        DATE_FORMAT(
            admission_date,
            '%Y-%m'
        ) AS analysis_month,

        department,

        COUNT(*) AS admissions,

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
)

SELECT
    l.analysis_month,
    l.department,

    l.admissions,
    s.patient_to_staff_ratio,
    l.avg_length_of_stay

FROM monthly_los AS l

INNER JOIN monthly_staffing AS s
    ON l.analysis_month = s.analysis_month
    AND l.department = s.department

ORDER BY
    s.patient_to_staff_ratio DESC;



-- ============================================================
-- 5. LENGTH OF STAY VS BILLED AMOUNT
--
-- Admission-level relationship.
-- Useful later for correlation/regression analysis.
-- ============================================================

SELECT
    admission_id,
    department,
    admission_type,

    length_of_stay,
    billed_amount,
    billed_cost_per_day

FROM vw_cost_metrics

ORDER BY length_of_stay DESC;



-- ============================================================
-- 6. READMISSION STATUS VS BILLED AMOUNT
--
-- Compare billed amounts for eligible admissions that were
-- and were not readmitted.
-- ============================================================

SELECT
    CASE
        WHEN r.is_readmitted_30d = 1
            THEN 'Readmitted'
        ELSE 'Not Readmitted'
    END AS readmission_status,

    COUNT(*) AS admissions,

    ROUND(
        AVG(c.billed_amount),
        2
    ) AS avg_billed_amount,

    ROUND(
        AVG(c.out_of_pocket),
        2
    ) AS avg_out_of_pocket,

    ROUND(
        AVG(r.length_of_stay),
        2
    ) AS avg_length_of_stay

FROM vw_readmission_metrics AS r

INNER JOIN vw_cost_metrics AS c
    ON r.admission_id = c.admission_id

WHERE r.is_eligible_30d = 1

GROUP BY r.is_readmitted_30d

ORDER BY r.is_readmitted_30d DESC;



-- ============================================================
-- 7. DEPARTMENT OPERATIONAL RANKING INPUT
--
-- Creates the metrics needed to identify departments with
-- combinations of:
--
-- high workload
-- high LOS
-- high readmission rate
-- high billed amount
--
-- No arbitrary "good/bad" threshold is applied here.
-- ============================================================

WITH department_los AS (

    SELECT
        department,

        COUNT(*) AS admissions,

        ROUND(
            AVG(length_of_stay),
            2
        ) AS avg_length_of_stay

    FROM vw_admission_metrics

    GROUP BY department
),

department_staffing AS (

    SELECT
        department,

        ROUND(
            SUM(patient_count) * 1.0
            /
            NULLIF(
                SUM(staff_count),
                0
            ),
            2
        ) AS patient_to_staff_ratio

    FROM vw_staffing_metrics

    GROUP BY department
),

department_readmissions AS (

    SELECT
        department,

        ROUND(
            SUM(
                CASE
                    WHEN is_eligible_30d = 1
                     AND is_readmitted_30d = 1
                    THEN 1
                    ELSE 0
                END
            ) * 100.0
            /
            NULLIF(
                SUM(is_eligible_30d),
                0
            ),
            2
        ) AS readmission_rate_pct

    FROM vw_readmission_metrics

    GROUP BY department
),

department_costs AS (

    SELECT
        department,

        ROUND(
            AVG(billed_amount),
            2
        ) AS avg_billed_per_admission

    FROM vw_cost_metrics

    GROUP BY department
)

SELECT
    l.department,
    l.admissions,
    l.avg_length_of_stay,

    s.patient_to_staff_ratio,

    r.readmission_rate_pct,

    c.avg_billed_per_admission,

    DENSE_RANK() OVER (
        ORDER BY
            s.patient_to_staff_ratio DESC
    ) AS workload_rank,

    DENSE_RANK() OVER (
        ORDER BY
            l.avg_length_of_stay DESC
    ) AS los_rank,

    DENSE_RANK() OVER (
        ORDER BY
            r.readmission_rate_pct DESC
    ) AS readmission_rank,

    DENSE_RANK() OVER (
        ORDER BY
            c.avg_billed_per_admission DESC
    ) AS billed_amount_rank

FROM department_los AS l

INNER JOIN department_staffing AS s
    ON l.department = s.department

INNER JOIN department_readmissions AS r
    ON l.department = r.department

INNER JOIN department_costs AS c
    ON l.department = c.department

ORDER BY
    workload_rank,
    readmission_rank;



-- ============================================================
-- 8. MONTHLY HOSPITAL EXECUTIVE TREND
--
-- Hospital-level monthly view across admissions, staffing,
-- LOS, and billed amounts.
-- ============================================================

WITH monthly_admissions AS (

    SELECT
        DATE_FORMAT(
            admission_date,
            '%Y-%m'
        ) AS analysis_month,

        COUNT(*) AS admissions,

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
),

monthly_staffing AS (

    SELECT
        DATE_FORMAT(
            date,
            '%Y-%m'
        ) AS analysis_month,

        SUM(staff_count)
            AS staff_assignments,

        SUM(patient_count)
            AS patient_assignments,

        ROUND(
            SUM(patient_count) * 1.0
            /
            NULLIF(
                SUM(staff_count),
                0
            ),
            2
        ) AS patient_to_staff_ratio

    FROM vw_staffing_metrics

    GROUP BY
        DATE_FORMAT(
            date,
            '%Y-%m'
        )
),

monthly_costs AS (

    SELECT
        DATE_FORMAT(
            admission_date,
            '%Y-%m'
        ) AS analysis_month,

        ROUND(
            SUM(billed_amount),
            2
        ) AS total_billed_amount,

        ROUND(
            AVG(billed_amount),
            2
        ) AS avg_billed_per_admission

    FROM vw_cost_metrics

    GROUP BY
        DATE_FORMAT(
            admission_date,
            '%Y-%m'
        )
)

SELECT
    a.analysis_month,

    a.admissions,
    a.avg_length_of_stay,

    s.staff_assignments,
    s.patient_assignments,
    s.patient_to_staff_ratio,

    c.total_billed_amount,
    c.avg_billed_per_admission

FROM monthly_admissions AS a

LEFT JOIN monthly_staffing AS s
    ON a.analysis_month = s.analysis_month

LEFT JOIN monthly_costs AS c
    ON a.analysis_month = c.analysis_month

ORDER BY a.analysis_month;