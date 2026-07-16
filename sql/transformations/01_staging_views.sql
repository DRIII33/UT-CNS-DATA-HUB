-- ============================================================================
-- STAGING VIEWS: Transform raw staging data into structured staging layer
-- Portfolio Project: Data Analytics Engineer Role
-- ============================================================================

-- Cleanse and validate student staging data
CREATE OR REPLACE VIEW `driiiportfolio.staging.v_students_cleaned` AS
SELECT
  student_id,
  cohort_year,
  UPPER(major) as major,
  CASE
    WHEN gpa IS NULL OR gpa < 0 THEN 0.0
    WHEN gpa > 4.0 THEN 4.0
    ELSE ROUND(gpa, 2)
  END as gpa,
  CASE
    WHEN enrollment_status IN ('Active', 'Inactive', 'Graduated', 'Withdrawn')
      THEN enrollment_status
    ELSE 'Unknown'
  END as enrollment_status,
  date_enrolled,
  CASE
    WHEN date_graduated >= date_enrolled THEN date_graduated
    ELSE NULL
  END as date_graduated,
  CASE
    WHEN credits_completed IS NULL OR credits_completed < 0 THEN 0
    ELSE credits_completed
  END as credits_completed,
  ethnicity,
  COALESCE(first_generation, FALSE) as first_generation,
  load_timestamp,
  ROW_NUMBER() OVER (PARTITION BY student_id ORDER BY load_timestamp DESC) as recency_rank
FROM `driiiportfolio.staging.students`
WHERE student_id IS NOT NULL
  AND DATE(load_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);

-- Cleanse and validate faculty staging data
CREATE OR REPLACE VIEW `driiiportfolio.staging.v_faculty_cleaned` AS
SELECT
  faculty_id,
  CASE
    WHEN rank IN ('Assistant Professor', 'Associate Professor', 'Full Professor', 'Lecturer', 'Adjunct')
      THEN rank
    ELSE 'Unknown'
  END as rank,
  hire_date,
  UPPER(department) as department,
  CASE
    WHEN salary IS NULL OR salary <= 0 THEN NULL
    WHEN salary > 500000 THEN 500000  -- Cap at reasonable max
    ELSE salary
  END as salary,
  CASE
    WHEN employment_status IN ('Active', 'On Leave', 'Retired')
      THEN employment_status
    ELSE 'Unknown'
  END as employment_status,
  CASE
    WHEN tenure_status IN ('Tenured', 'Tenure-Track', 'Non-Tenure-Track')
      THEN tenure_status
    ELSE 'Unknown'
  END as tenure_status,
  research_focus,
  load_timestamp,
  ROW_NUMBER() OVER (PARTITION BY faculty_id ORDER BY load_timestamp DESC) as recency_rank
FROM `driiiportfolio.staging.faculty`
WHERE faculty_id IS NOT NULL
  AND DATE(load_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);

-- Cleanse and validate grant staging data
CREATE OR REPLACE VIEW `driiiportfolio.staging.v_grants_cleaned` AS
SELECT
  grant_id,
  pi_id,
  CASE
    WHEN award_amount IS NULL OR award_amount <= 0 THEN 0
    ELSE award_amount
  END as award_amount,
  UPPER(funding_agency) as funding_agency,
  start_date,
  CASE
    WHEN end_date >= start_date THEN end_date
    ELSE start_date
  END as end_date,
  UPPER(department) as department,
  CASE
    WHEN status IN ('Active', 'Completed', 'Cancelled')
      THEN status
    ELSE 'Unknown'
  END as status,
  CASE
    WHEN publication_count IS NULL OR publication_count < 0 THEN 0
    ELSE publication_count
  END as publication_count,
  load_timestamp,
  ROW_NUMBER() OVER (PARTITION BY grant_id ORDER BY load_timestamp DESC) as recency_rank
FROM `driiiportfolio.staging.grants`
WHERE grant_id IS NOT NULL
  AND pi_id IS NOT NULL
  AND DATE(load_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);

-- Cleanse and validate course staging data
CREATE OR REPLACE VIEW `driiiportfolio.staging.v_courses_cleaned` AS
SELECT
  course_id,
  UPPER(course_code) as course_code,
  course_title,
  CASE
    WHEN credits IN (1, 2, 3, 4) THEN credits
    ELSE 3  -- Default to 3 credits
  END as credits,
  CASE
    WHEN semester IN ('Fall', 'Spring', 'Summer')
      THEN semester
    ELSE 'Unknown'
  END as semester,
  year,
  instructor_id,
  CASE
    WHEN enrollment IS NULL OR enrollment < 0 THEN 0
    ELSE enrollment
  END as enrollment,
  CASE
    WHEN pass_rate IS NULL OR pass_rate < 0 THEN 0.0
    WHEN pass_rate > 1.0 THEN 1.0
    ELSE ROUND(pass_rate, 3)
  END as pass_rate,
  CASE
    WHEN avg_rating IS NULL OR avg_rating < 1 THEN 1.0
    WHEN avg_rating > 5 THEN 5.0
    ELSE ROUND(avg_rating, 1)
  END as avg_rating,
  load_timestamp,
  ROW_NUMBER() OVER (PARTITION BY course_id ORDER BY load_timestamp DESC) as recency_rank
FROM `driiiportfolio.staging.courses`
WHERE course_id IS NOT NULL
  AND DATE(load_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);

-- Cleanse and validate enrollment staging data
CREATE OR REPLACE VIEW `driiiportfolio.staging.v_enrollments_cleaned` AS
SELECT
  enrollment_id,
  student_id,
  course_id,
  CASE
    WHEN semester IN ('Fall', 'Spring', 'Summer')
      THEN semester
    ELSE 'Unknown'
  END as semester,
  year,
  CASE
    WHEN grade IN ('A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'D', 'F')
      THEN grade
    ELSE 'I'  -- Incomplete
  END as grade,
  CASE
    WHEN grade_point IS NULL OR grade_point < 0 THEN 0.0
    WHEN grade_point > 4.0 THEN 4.0
    ELSE ROUND(grade_point, 2)
  END as grade_point,
  CASE
    WHEN credits_earned IS NULL OR credits_earned < 0 THEN 0
    WHEN credits_earned > 4 THEN 4
    ELSE credits_earned
  END as credits_earned,
  load_timestamp,
  ROW_NUMBER() OVER (PARTITION BY enrollment_id ORDER BY load_timestamp DESC) as recency_rank
FROM `driiiportfolio.staging.enrollments`
WHERE enrollment_id IS NOT NULL
  AND student_id IS NOT NULL
  AND course_id IS NOT NULL
  AND DATE(load_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);
