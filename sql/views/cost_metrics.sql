-- ============================================================
-- VIEW: vw_cost_metrics
-- PURPOSE:
-- Creates admission-level financial metrics by combining
-- hospital cost data with admission and patient information.
--
-- GRAIN:
-- One row per admission_id
-- ============================================================

CREATE OR REPLACE VIEW vw_cost_metrics AS

SELECT
    -- --------------------------------------------------------
    -- Admission information
    -- --------------------------------------------------------

    a.admission_id,
    a.patient_id,
    a.admission_date,
    a.discharge_date,
    a.department,
    a.admission_type,
    a.length_of_stay,


    -- --------------------------------------------------------
    -- Patient information
    -- --------------------------------------------------------

    p.insurance_type,


    -- --------------------------------------------------------
    -- Cost information
    -- --------------------------------------------------------

    c.billed_amount,
    c.insurance_covered_amount,
    c.out_of_pocket,


    -- --------------------------------------------------------
    -- Insurance coverage percentage
    -- --------------------------------------------------------

    ROUND(
        c.insurance_covered_amount * 100.0
        / NULLIF(c.billed_amount, 0),
        2
    ) AS insurance_coverage_pct,


    -- --------------------------------------------------------
    -- Patient payment percentage
    -- --------------------------------------------------------

    ROUND(
        c.out_of_pocket * 100.0
        / NULLIF(c.billed_amount, 0),
        2
    ) AS out_of_pocket_pct,


    -- --------------------------------------------------------
    -- Cost per day of stay
    -- --------------------------------------------------------

    ROUND(
        c.billed_amount
        / NULLIF(a.length_of_stay, 0),
        2
    ) AS billed_cost_per_day


FROM admissions AS a

INNER JOIN patients AS p
    ON a.patient_id = p.patient_id

INNER JOIN costs AS c
    ON a.admission_id = c.admission_id;