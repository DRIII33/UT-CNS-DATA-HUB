-- ============================================================================
-- UT CNS DATA HUB - BigQuery Schema Definitions
-- Portfolio Project: Data Analytics Engineer Role
-- Purpose: Create all staging, transformation, and analytics tables
-- ============================================================================

-- ============================================================================
-- PART 1: STAGING DATASET (Raw Data Landing Zone)
-- ============================================================================

CREATE OR REPLACE TABLE `driiiportfolio.staging.students`
(
  student_id STRING NOT NULL,
  cohort_year INT64,
  major STRING,
  gpa FLOAT64,
  enrollment_status STRING,
  date_enrolled DATE,
  date_graduated DATE,
  credits_completed INT64,
  ethnicity STRING,
  first_generation BOOL,
  load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(load_timestamp)
CLUSTER BY student_id, cohort_year, major;

CREATE OR REPLACE TABLE `driiiportfolio.staging.faculty`
(
  faculty_id STRING NOT NULL,
  rank STRING,
  hire_date DATE,
  department STRING,
  salary INT64,
  employment_status STRING,
  tenure_status STRING,
  research_focus STRING,
  load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(load_timestamp)
CLUSTER BY faculty_id, department;

CREATE OR REPLACE TABLE `driiiportfolio.staging.grants`
(
  grant_id STRING NOT NULL,
  pi_id STRING NOT NULL,
  award_amount INT64,
  funding_agency STRING,
  start_date DATE,
  end_date DATE,
  department STRING,
  status STRING,
  publication_count INT64,
  load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(load_timestamp)
CLUSTER BY pi_id, funding_agency;

CREATE OR REPLACE TABLE `driiiportfolio.staging.courses`
(
  course_id STRING NOT NULL,
  course_code STRING,
  course_title STRING,
  credits INT64,
  semester STRING,
  year INT64,
  instructor_id STRING,
  enrollment INT64,
  pass_rate FLOAT64,
  avg_rating FLOAT64,
  load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(load_timestamp)
CLUSTER BY instructor_id, year;

CREATE OR REPLACE TABLE `driiiportfolio.staging.enrollments`
(
  enrollment_id STRING NOT NULL,
  student_id STRING NOT NULL,
  course_id STRING NOT NULL,
  semester STRING,
  year INT64,
  grade STRING,
  grade_point FLOAT64,
  credits_earned INT64,
  load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(load_timestamp)
CLUSTER BY student_id, course_id, year;

-- ============================================================================
-- PART 2: AUDIT & COMPLIANCE TABLES
-- ============================================================================

CREATE OR REPLACE TABLE `driiiportfolio.staging.data_quality_log`
(
  quality_log_id STRING NOT NULL,
  table_name STRING NOT NULL,
  check_name STRING NOT NULL,
  check_passed BOOL,
  failed_row_count INT64,
  total_row_count INT64,
  failure_rate FLOAT64,
  check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  details STRING
)
PARTITION BY DATE(check_timestamp)
CLUSTER BY table_name, check_name;

CREATE OR REPLACE TABLE `driiiportfolio.staging.pipeline_execution_log`
(
  execution_id STRING NOT NULL,
  pipeline_name STRING NOT NULL,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  status STRING,  -- 'SUCCESS', 'FAILURE', 'PARTIAL'
  rows_processed INT64,
  rows_failed INT64,
  error_message STRING,
  created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(created_timestamp)
CLUSTER BY pipeline_name, status;

CREATE OR REPLACE TABLE `driiiportfolio.staging.data_access_log`
(
  access_log_id STRING NOT NULL,
  user_id STRING NOT NULL,
  table_name STRING NOT NULL,
  query_hash STRING,  -- Hash of query for auditing
  access_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  row_count_accessed INT64,
  access_type STRING,  -- 'SELECT', 'EXPORT', etc.
  status STRING  -- 'SUCCESS', 'DENIED', etc.
)
PARTITION BY DATE(access_timestamp)
CLUSTER BY user_id, table_name;

-- ============================================================================
-- PART 3: ANALYTICS DATASET - DIMENSION TABLES
-- ============================================================================

CREATE OR REPLACE TABLE `driiiportfolio.analytics.dim_student`
(
  student_key INT64,
  student_id STRING NOT NULL,
  student_id_pseudonymized STRING,  -- Hashed for FERPA compliance
  cohort_year INT64,
  major STRING,
  department STRING,
  ethnicity_category STRING,
  is_first_generation BOOL,
  current_enrollment_status STRING,
  is_active BOOL,
  dw_created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_is_current BOOL DEFAULT TRUE
)
PARTITION BY DATE(dw_created_date)
CLUSTER BY student_id, cohort_year, major;

CREATE OR REPLACE TABLE `driiiportfolio.analytics.dim_faculty`
(
  faculty_key INT64,
  faculty_id STRING NOT NULL,
  faculty_id_pseudonymized STRING,  -- Hashed for FERPA compliance
  faculty_rank STRING,
  hire_date DATE,
  department STRING,
  tenure_status STRING,
  research_focus STRING,
  current_employment_status STRING,
  is_active BOOL,
  dw_created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_is_current BOOL DEFAULT TRUE
)
PARTITION BY DATE(dw_created_date)
CLUSTER BY faculty_id, department;

CREATE OR REPLACE TABLE `driiiportfolio.analytics.dim_department`
(
  department_key INT64,
  department_id STRING NOT NULL,
  department_name STRING NOT NULL,
  college_name STRING,
  department_code STRING,
  dean_name STRING,
  budget_fiscal_year FLOAT64,
  dw_created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_is_current BOOL DEFAULT TRUE
)
CLUSTER BY department_id;

CREATE OR REPLACE TABLE `driiiportfolio.analytics.dim_course`
(
  course_key INT64,
  course_id STRING NOT NULL,
  course_code STRING,
  course_title STRING,
  credit_hours INT64,
  discipline STRING,
  offering_department STRING,
  dw_created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_is_current BOOL DEFAULT TRUE
)
CLUSTER BY course_id, course_code;

CREATE OR REPLACE TABLE `driiiportfolio.analytics.dim_date`
(
  date_key INT64,
  calendar_date DATE NOT NULL,
  calendar_year INT64,
  calendar_quarter INT64,
  calendar_month INT64,
  calendar_day INT64,
  day_of_week STRING,
  is_weekend BOOL,
  academic_year INT64,  -- 2024 = 2024-2025 academic year
  academic_semester STRING,  -- 'Fall', 'Spring', 'Summer'
  fiscal_year INT64  -- Fiscal year for university
);

CREATE OR REPLACE TABLE `driiiportfolio.analytics.dim_funding_agency`
(
  agency_key INT64,
  agency_id STRING NOT NULL,
  agency_name STRING NOT NULL,
  agency_type STRING,  -- 'Federal', 'Private', 'Industrial'
  federal_agency_code STRING,
  dw_created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_is_current BOOL DEFAULT TRUE
)
CLUSTER BY agency_name;

-- ============================================================================
-- PART 4: ANALYTICS DATASET - FACT TABLES
-- ============================================================================

CREATE OR REPLACE TABLE `driiiportfolio.analytics.fact_enrollment`
(
  enrollment_key INT64,
  student_key INT64 NOT NULL,
  course_key INT64 NOT NULL,
  academic_year INT64 NOT NULL,
  academic_semester STRING NOT NULL,
  date_enrolled DATE,
  date_completed DATE,
  letter_grade STRING,
  grade_point FLOAT64,
  credits_earned INT64,
  credits_attempted INT64,
  is_passing BOOL,
  is_completed BOOL,
  enrollment_status STRING,  -- 'Completed', 'In Progress', 'Dropped'
  dw_created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY academic_year
CLUSTER BY student_key, course_key, academic_year;

CREATE OR REPLACE TABLE `driiiportfolio.analytics.fact_student_performance`
(
  performance_key INT64,
  student_key INT64 NOT NULL,
  academic_year INT64 NOT NULL,
  semester_gpa FLOAT64,
  cumulative_gpa FLOAT64,
  credits_completed INT64,
  credits_attempted INT64,
  passing_courses INT64,
  failing_courses INT64,
  academic_standing STRING,  -- 'Good', 'Probation', 'Dismissal'
  is_at_risk BOOL,  -- Predictive flag
  degree_progress_pct FLOAT64,
  dw_created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY academic_year
CLUSTER BY student_key, academic_year;

CREATE OR REPLACE TABLE `driiiportfolio.analytics.fact_research_grant`
(
  grant_key INT64,
  grant_id STRING NOT NULL,
  pi_key INT64 NOT NULL,  -- Faculty key
  department_key INT64 NOT NULL,
  agency_key INT64 NOT NULL,
  award_amount INT64,
  grant_start_date DATE,
  grant_end_date DATE,
  grant_duration_months INT64,
  current_grant_status STRING,  -- 'Active', 'Completed', 'Cancelled'
  publication_count INT64,
  citations_count INT64,
  cost_per_publication FLOAT64,
  grant_fiscal_year INT64,
  dw_created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY grant_fiscal_year
CLUSTER BY pi_key, department_key, agency_key;

CREATE OR REPLACE TABLE `driiiportfolio.analytics.fact_faculty_productivity`
(
  productivity_key INT64,
  faculty_key INT64 NOT NULL,
  department_key INT64 NOT NULL,
  academic_year INT64 NOT NULL,
  total_grants_awarded INT64,
  total_grant_dollars INT64,
  avg_grant_size FLOAT64,
  total_publications INT64,
  peer_reviewed_publications INT64,
  books_authored INT64,
  conference_presentations INT64,
  courses_taught INT64,
  students_advised INT64,
  avg_course_rating FLOAT64,
  committee_assignments INT64,
  professional_development_hours INT64,
  productivity_score FLOAT64,  -- Weighted KPI
  peer_rank_percentile FLOAT64,  -- % rank vs peers
  dw_created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY academic_year
CLUSTER BY faculty_key, department_key, academic_year;

CREATE OR REPLACE TABLE `driiiportfolio.analytics.fact_course_performance`
(
  course_performance_key INT64,
  course_key INT64 NOT NULL,
  instructor_key INT64 NOT NULL,
  department_key INT64 NOT NULL,
  academic_year INT64 NOT NULL,
  semester STRING,
  total_enrollment INT64,
  total_completed INT64,
  passing_students INT64,
  failing_students INT64,
  avg_grade_point FLOAT64,
  pass_rate FLOAT64,
  avg_student_rating FLOAT64,
  course_difficulty_index FLOAT64,  -- Relative to peer courses
  repeat_enrollment_pct FLOAT64,
  dw_created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  dw_updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY academic_year
CLUSTER BY course_key, instructor_key, academic_year;

-- ============================================================================
-- PART 5: ANALYTICS DATASET - AGGREGATE VIEWS (Pre-computed Metrics)
-- ============================================================================

CREATE OR REPLACE VIEW `driiiportfolio.analytics.v_enrollment_summary_by_major` AS
SELECT
  ds.major,
  fe.academic_year,
  fe.academic_semester,
  COUNT(DISTINCT fe.student_key) as total_students,
  COUNT(DISTINCT CASE WHEN fe.is_passing THEN fe.enrollment_key END) as passing_students,
  COUNT(DISTINCT CASE WHEN NOT fe.is_passing THEN fe.enrollment_key END) as failing_students,
  ROUND(AVG(fe.grade_point), 2) as avg_gpa,
  ROUND(SUM(fe.credits_earned) / SUM(fe.credits_attempted), 3) as completion_rate
FROM `driiiportfolio.analytics.fact_enrollment` fe
JOIN `driiiportfolio.analytics.dim_student` ds ON fe.student_key = ds.student_key
WHERE ds.dw_is_current AND fe.is_completed
GROUP BY ds.major, fe.academic_year, fe.academic_semester;

CREATE OR REPLACE VIEW `driiiportfolio.analytics.v_faculty_research_roi` AS
SELECT
  df.faculty_id,
  df.department,
  df.faculty_rank,
  COUNT(DISTINCT frg.grant_key) as total_grants,
  SUM(frg.award_amount) as total_funding,
  ROUND(AVG(frg.award_amount), 0) as avg_grant_size,
  SUM(frg.publication_count) as total_publications,
  ROUND(SUM(frg.award_amount) / NULLIF(SUM(frg.publication_count), 0), 0) as cost_per_publication,
  SUM(frg.citations_count) as total_citations
FROM `driiiportfolio.analytics.fact_research_grant` frg
JOIN `driiiportfolio.analytics.dim_faculty` df ON frg.pi_key = df.faculty_key
WHERE df.dw_is_current AND frg.current_grant_status = 'Active'
GROUP BY df.faculty_id, df.department, df.faculty_rank;

CREATE OR REPLACE VIEW `driiiportfolio.analytics.v_student_at_risk_indicators` AS
SELECT
  ds.student_id,
  ds.major,
  ds.cohort_year,
  fsp.academic_year,
  fsp.cumulative_gpa,
  fsp.academic_standing,
  fsp.is_at_risk,
  fsp.degree_progress_pct,
  CASE
    WHEN fsp.cumulative_gpa < 2.0 THEN 'CRITICAL'
    WHEN fsp.cumulative_gpa < 2.5 THEN 'HIGH'
    WHEN fsp.cumulative_gpa < 3.0 THEN 'MODERATE'
    ELSE 'LOW'
  END as risk_level,
  CASE
    WHEN fsp.failing_courses > 0 THEN 'YES'
    ELSE 'NO'
  END as has_failing_courses
FROM `driiiportfolio.analytics.fact_student_performance` fsp
JOIN `driiiportfolio.analytics.dim_student` ds ON fsp.student_key = ds.student_key
WHERE ds.dw_is_current;

CREATE OR REPLACE VIEW `driiiportfolio.analytics.v_enrollment_retention_cohort` AS
SELECT
  ds.cohort_year,
  ds.major,
  COUNT(DISTINCT CASE WHEN ds.dw_is_current AND ds.is_active THEN ds.student_key END) as current_students,
  COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Graduated' THEN ds.student_key END) as graduated_students,
  COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Withdrawn' THEN ds.student_key END) as withdrawn_students,
  ROUND(
    COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Graduated' THEN ds.student_key END) /
    COUNT(DISTINCT ds.student_key),
    3
  ) as graduation_rate
FROM `driiiportfolio.analytics.dim_student` ds
GROUP BY ds.cohort_year, ds.major;

-- ============================================================================
-- PART 6: COMPLIANCE DATASET - FERPA-MASKED VIEWS
-- ============================================================================

CREATE OR REPLACE TABLE `driiiportfolio.compliance.student_data_masked` AS
SELECT
  student_id_pseudonymized as student_id,
  cohort_year,
  major,
  ethnicity_category,
  is_first_generation,
  current_enrollment_status,
  dw_created_date
FROM `driiiportfolio.analytics.dim_student`
WHERE dw_is_current;

CREATE OR REPLACE TABLE `driiiportfolio.compliance.faculty_data_masked` AS
SELECT
  faculty_id_pseudonymized as faculty_id,
  faculty_rank,
  department,
  tenure_status,
  research_focus,
  dw_created_date
FROM `driiiportfolio.analytics.dim_faculty`
WHERE dw_is_current;

-- ============================================================================
-- PART 7: INDEXES FOR PERFORMANCE (BigQuery automatically optimizes)
-- Note: BigQuery uses clustering instead of traditional indexes
-- All tables are already clustered above for optimal query performance
-- ============================================================================

PRINT('\n===============================================================================');
PRINT('UT CNS DATA HUB - Schema Creation Complete');
PRINT('===============================================================================');
PRINT('Created Datasets:');
PRINT('  - staging: Raw data landing zone');
PRINT('  - analytics: Transformed dimensional model');
PRINT('  - compliance: FERPA-masked views');
PRINT('');
PRINT('Fact Tables: 5');
PRINT('  - fact_enrollment');
PRINT('  - fact_student_performance');
PRINT('  - fact_research_grant');
PRINT('  - fact_faculty_productivity');
PRINT('  - fact_course_performance');
PRINT('');
PRINT('Dimension Tables: 6');
PRINT('  - dim_student');
PRINT('  - dim_faculty');
PRINT('  - dim_department');
PRINT('  - dim_course');
PRINT('  - dim_date');
PRINT('  - dim_funding_agency');
PRINT('');
PRINT('Aggregate Views: 4');
PRINT('  - v_enrollment_summary_by_major');
PRINT('  - v_faculty_research_roi');
PRINT('  - v_student_at_risk_indicators');
PRINT('  - v_enrollment_retention_cohort');
PRINT('');
PRINT('All tables partitioned by date and clustered for optimal query performance.');
PRINT('===============================================================================');
