-- UT CNS Data Hub Schema Definitions
CREATE SCHEMA IF NOT EXISTS `driiiportfolio.staging`;
CREATE SCHEMA IF NOT EXISTS `driiiportfolio.analytics`;
CREATE SCHEMA IF NOT EXISTS `driiiportfolio.compliance`;

CREATE OR REPLACE TABLE `driiiportfolio.staging.students` (student_id STRING, cohort_year INT64, major STRING, gpa FLOAT64, enrollment_status STRING, date_enrolled DATE, date_graduated DATE, credits_completed INT64, ethnicity STRING, first_generation BOOL, load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE `driiiportfolio.staging.faculty` (faculty_id STRING, rank STRING, hire_date DATE, department STRING, salary INT64, employment_status STRING, tenure_status STRING, research_focus STRING, load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE `driiiportfolio.staging.grants` (grant_id STRING, pi_id STRING, award_amount INT64, funding_agency STRING, start_date DATE, end_date DATE, department STRING, status STRING, publication_count INT64, load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE `driiiportfolio.staging.courses` (course_id STRING, course_code STRING, course_title STRING, credits INT64, semester STRING, year INT64, instructor_id STRING, enrollment INT64, pass_rate FLOAT64, avg_rating FLOAT64, load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE `driiiportfolio.staging.enrollments` (enrollment_id STRING, student_id STRING, course_id STRING, semester STRING, year INT64, grade STRING, grade_point FLOAT64, credits_earned INT64, load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP());
