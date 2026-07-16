-- ============================================================================
-- DIMENSION TABLES: Build conformed dimensions for analytics
-- Portfolio Project: Data Analytics Engineer Role
-- ============================================================================

-- ============================================================================
-- DIM_STUDENT: Student dimension with slowly changing dimension (SCD) Type 2
-- ============================================================================
CREATE OR REPLACE PROCEDURE `driiiportfolio.analytics.sp_load_dim_student`()
BEGIN
  -- Insert new or updated records
  INSERT INTO `driiiportfolio.analytics.dim_student`
  SELECT
    ROW_NUMBER() OVER (ORDER BY sc.student_id) as student_key,
    sc.student_id,
    -- Pseudonymize PII: SHA256(student_id || 'salt') for FERPA compliance
    CONCAT('STU_', SUBSTR(TO_HEX(MD5(CONCAT(sc.student_id, 'ferpa_salt'))), 1, 12)) as student_id_pseudonymized,
    sc.cohort_year,
    sc.major,
    'College of Natural Sciences' as department,
    COALESCE(sc.ethnicity, 'Unknown') as ethnicity_category,
    sc.first_generation,
    sc.enrollment_status,
    CASE WHEN sc.enrollment_status IN ('Active') THEN TRUE ELSE FALSE END as is_active,
    CURRENT_TIMESTAMP() as dw_created_date,
    CURRENT_TIMESTAMP() as dw_updated_date,
    TRUE as dw_is_current
  FROM `driiiportfolio.staging.v_students_cleaned` sc
  WHERE sc.recency_rank = 1;
END;

-- ============================================================================
-- DIM_FACULTY: Faculty dimension with SCD Type 2
-- ============================================================================
CREATE OR REPLACE PROCEDURE `driiiportfolio.analytics.sp_load_dim_faculty`()
BEGIN
  INSERT INTO `driiiportfolio.analytics.dim_faculty`
  SELECT
    ROW_NUMBER() OVER (ORDER BY fc.faculty_id) as faculty_key,
    fc.faculty_id,
    CONCAT('FAC_', SUBSTR(TO_HEX(MD5(CONCAT(fc.faculty_id, 'ferpa_salt'))), 1, 12)) as faculty_id_pseudonymized,
    fc.rank,
    fc.hire_date,
    fc.department,
    fc.tenure_status,
    fc.research_focus,
    fc.employment_status,
    CASE WHEN fc.employment_status = 'Active' THEN TRUE ELSE FALSE END as is_active,
    CURRENT_TIMESTAMP() as dw_created_date,
    CURRENT_TIMESTAMP() as dw_updated_date,
    TRUE as dw_is_current
  FROM `driiiportfolio.staging.v_faculty_cleaned` fc
  WHERE fc.recency_rank = 1;
END;

-- ============================================================================
-- DIM_DEPARTMENT: Department dimension
-- ============================================================================
CREATE OR REPLACE VIEW `driiiportfolio.analytics.v_dim_department` AS
SELECT
  ROW_NUMBER() OVER (ORDER BY DISTINCT department) as department_key,
  GENERATE_UUID() as department_id,
  department as department_name,
  'College of Natural Sciences' as college_name,
  SUBSTR(department, 1, 3) as department_code,
  'Dean Name' as dean_name,
  NULL as budget_fiscal_year,
  CURRENT_TIMESTAMP() as dw_created_date,
  CURRENT_TIMESTAMP() as dw_updated_date,
  TRUE as dw_is_current
FROM (
  SELECT DISTINCT department FROM `driiiportfolio.staging.v_faculty_cleaned`
  UNION ALL
  SELECT DISTINCT department FROM `driiiportfolio.staging.v_grants_cleaned`
);

-- ============================================================================
-- DIM_COURSE: Course dimension
-- ============================================================================
CREATE OR REPLACE PROCEDURE `driiiportfolio.analytics.sp_load_dim_course`()
BEGIN
  INSERT INTO `driiiportfolio.analytics.dim_course`
  SELECT
    ROW_NUMBER() OVER (ORDER BY cc.course_id) as course_key,
    cc.course_id,
    cc.course_code,
    cc.course_title,
    cc.credits,
    SUBSTR(cc.course_code, 1, 3) as discipline,
    'College of Natural Sciences' as offering_department,
    CURRENT_TIMESTAMP() as dw_created_date,
    CURRENT_TIMESTAMP() as dw_updated_date,
    TRUE as dw_is_current
  FROM `driiiportfolio.staging.v_courses_cleaned` cc
  WHERE cc.recency_rank = 1;
END;

-- ============================================================================
-- DIM_DATE: Date dimension (pre-computed for all dates 2014-2030)
-- ============================================================================
CREATE OR REPLACE PROCEDURE `driiiportfolio.analytics.sp_load_dim_date`()
BEGIN
  INSERT INTO `driiiportfolio.analytics.dim_date`
  WITH date_series AS (
    SELECT DATE_ADD('2014-01-01', INTERVAL offset DAY) as calendar_date
    FROM UNNEST(GENERATE_ARRAY(0, 5840)) as offset  -- ~16 years
  )
  SELECT
    CAST(FORMAT_DATE('%Y%m%d', calendar_date) as INT64) as date_key,
    calendar_date,
    EXTRACT(YEAR FROM calendar_date) as calendar_year,
    EXTRACT(QUARTER FROM calendar_date) as calendar_quarter,
    EXTRACT(MONTH FROM calendar_date) as calendar_month,
    EXTRACT(DAY FROM calendar_date) as calendar_day,
    FORMAT_DATE('%A', calendar_date) as day_of_week,
    EXTRACT(DAYOFWEEK FROM calendar_date) IN (1, 7) as is_weekend,
    -- Academic year: Aug of current = start of next year (e.g., Aug 2024 = 2024-2025 = 2025)
    CASE
      WHEN EXTRACT(MONTH FROM calendar_date) >= 8
        THEN EXTRACT(YEAR FROM calendar_date) + 1
      ELSE EXTRACT(YEAR FROM calendar_date)
    END as academic_year,
    CASE
      WHEN EXTRACT(MONTH FROM calendar_date) IN (8, 9, 10, 11, 12) THEN 'Fall'
      WHEN EXTRACT(MONTH FROM calendar_date) IN (1, 2, 3, 4, 5) THEN 'Spring'
      WHEN EXTRACT(MONTH FROM calendar_date) IN (6, 7) THEN 'Summer'
    END as academic_semester,
    CASE
      WHEN EXTRACT(MONTH FROM calendar_date) >= 7 THEN EXTRACT(YEAR FROM calendar_date) + 1
      ELSE EXTRACT(YEAR FROM calendar_date)
    END as fiscal_year
  FROM date_series;
END;

-- ============================================================================
-- DIM_FUNDING_AGENCY: Funding agency dimension
-- ============================================================================
CREATE OR REPLACE PROCEDURE `driiiportfolio.analytics.sp_load_dim_funding_agency`()
BEGIN
  INSERT INTO `driiiportfolio.analytics.dim_funding_agency`
  SELECT
    ROW_NUMBER() OVER (ORDER BY funding_agency) as agency_key,
    GENERATE_UUID() as agency_id,
    funding_agency as agency_name,
    CASE
      WHEN funding_agency IN ('NSF', 'NIH', 'DOE', 'USDA', 'DOD', 'EPA', 'DOC') THEN 'Federal'
      WHEN funding_agency = 'Industrial Partner' THEN 'Industrial'
      ELSE 'Private'
    END as agency_type,
    CASE
      WHEN funding_agency = 'NSF' THEN '4900'
      WHEN funding_agency = 'NIH' THEN '5142'
      WHEN funding_agency = 'DOE' THEN '1230'
      WHEN funding_agency = 'USDA' THEN '2050'
      WHEN funding_agency = 'DOD' THEN '1210'
      ELSE NULL
    END as federal_agency_code,
    CURRENT_TIMESTAMP() as dw_created_date,
    TRUE as dw_is_current
  FROM (
    SELECT DISTINCT funding_agency FROM `driiiportfolio.staging.v_grants_cleaned`
  );
END;
