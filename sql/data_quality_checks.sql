-- ============================================================================
-- DATA QUALITY CHECKS: Automated validation rules and anomaly detection
-- Portfolio Project: Data Analytics Engineer Role
-- Purpose: Ensure 99.9% data quality across all tables
-- ============================================================================

-- ============================================================================
-- COMPLETENESS CHECKS: Verify required fields are populated
-- ============================================================================

CREATE OR REPLACE PROCEDURE `driiiportfolio.staging.sp_check_completeness`()
BEGIN
  DECLARE quality_log_id STRING DEFAULT GENERATE_UUID();
  
  -- Students completeness
  INSERT INTO `driiiportfolio.staging.data_quality_log`
  SELECT
    GENERATE_UUID() as quality_log_id,
    'students' as table_name,
    'completeness_student_id' as check_name,
    COUNTIF(student_id IS NOT NULL) = COUNT(*) as check_passed,
    COUNTIF(student_id IS NULL) as failed_row_count,
    COUNT(*) as total_row_count,
    COUNTIF(student_id IS NULL) / COUNT(*) as failure_rate,
    'student_id field has NULL values' as details
  FROM `driiiportfolio.staging.students`
  WHERE DATE(load_timestamp) = CURRENT_DATE();
  
  -- Faculty completeness
  INSERT INTO `driiiportfolio.staging.data_quality_log`
  SELECT
    GENERATE_UUID() as quality_log_id,
    'faculty' as table_name,
    'completeness_faculty_id' as check_name,
    COUNTIF(faculty_id IS NOT NULL) = COUNT(*) as check_passed,
    COUNTIF(faculty_id IS NULL) as failed_row_count,
    COUNT(*) as total_row_count,
    COUNTIF(faculty_id IS NULL) / COUNT(*) as failure_rate,
    'faculty_id field has NULL values' as details
  FROM `driiiportfolio.staging.faculty`
  WHERE DATE(load_timestamp) = CURRENT_DATE();
  
  -- Grants completeness
  INSERT INTO `driiiportfolio.staging.data_quality_log`
  SELECT
    GENERATE_UUID() as quality_log_id,
    'grants' as table_name,
    'completeness_pi_id' as check_name,
    COUNTIF(pi_id IS NOT NULL) = COUNT(*) as check_passed,
    COUNTIF(pi_id IS NULL) as failed_row_count,
    COUNT(*) as total_row_count,
    COUNTIF(pi_id IS NULL) / COUNT(*) as failure_rate,
    'pi_id (Principal Investigator) field has NULL values' as details
  FROM `driiiportfolio.staging.grants`
  WHERE DATE(load_timestamp) = CURRENT_DATE();
END;

-- ============================================================================
-- UNIQUENESS CHECKS: Detect duplicate records
-- ============================================================================

CREATE OR REPLACE PROCEDURE `driiiportfolio.staging.sp_check_uniqueness`()
BEGIN
  -- Students uniqueness
  INSERT INTO `driiiportfolio.staging.data_quality_log`
  WITH duplicates AS (
    SELECT
      student_id,
      COUNT(*) as occurrence_count
    FROM `driiiportfolio.staging.students`
    WHERE DATE(load_timestamp) = CURRENT_DATE()
    GROUP BY student_id
    HAVING COUNT(*) > 1
  )
  SELECT
    GENERATE_UUID() as quality_log_id,
    'students' as table_name,
    'uniqueness_student_id' as check_name,
    (SELECT COUNT(*) FROM duplicates) = 0 as check_passed,
    COALESCE((SELECT SUM(occurrence_count - 1) FROM duplicates), 0) as failed_row_count,
    (SELECT COUNT(*) FROM `driiiportfolio.staging.students` WHERE DATE(load_timestamp) = CURRENT_DATE()) as total_row_count,
    COALESCE((SELECT SUM(occurrence_count - 1) FROM duplicates), 0) / 
      NULLIF((SELECT COUNT(*) FROM `driiiportfolio.staging.students` WHERE DATE(load_timestamp) = CURRENT_DATE()), 0) as failure_rate,
    'Duplicate student_id records detected' as details;
  
  -- Faculty uniqueness
  INSERT INTO `driiiportfolio.staging.data_quality_log`
  WITH duplicates AS (
    SELECT
      faculty_id,
      COUNT(*) as occurrence_count
    FROM `driiiportfolio.staging.faculty`
    WHERE DATE(load_timestamp) = CURRENT_DATE()
    GROUP BY faculty_id
    HAVING COUNT(*) > 1
  )
  SELECT
    GENERATE_UUID() as quality_log_id,
    'faculty' as table_name,
    'uniqueness_faculty_id' as check_name,
    (SELECT COUNT(*) FROM duplicates) = 0 as check_passed,
    COALESCE((SELECT SUM(occurrence_count - 1) FROM duplicates), 0) as failed_row_count,
    (SELECT COUNT(*) FROM `driiiportfolio.staging.faculty` WHERE DATE(load_timestamp) = CURRENT_DATE()) as total_row_count,
    COALESCE((SELECT SUM(occurrence_count - 1) FROM duplicates), 0) /
      NULLIF((SELECT COUNT(*) FROM `driiiportfolio.staging.faculty` WHERE DATE(load_timestamp) = CURRENT_DATE()), 0) as failure_rate,
    'Duplicate faculty_id records detected' as details;
END;

-- ============================================================================
-- VALIDITY CHECKS: Verify data values are within acceptable ranges
-- ============================================================================

CREATE OR REPLACE PROCEDURE `driiiportfolio.staging.sp_check_validity`()
BEGIN
  -- GPA validity (0.0 - 4.0)
  INSERT INTO `driiiportfolio.staging.data_quality_log`
  SELECT
    GENERATE_UUID() as quality_log_id,
    'students' as table_name,
    'validity_gpa_range' as check_name,
    COUNTIF(gpa >= 0.0 AND gpa <= 4.0) = COUNT(*) as check_passed,
    COUNTIF(gpa < 0.0 OR gpa > 4.0) as failed_row_count,
    COUNT(*) as total_row_count,
    COUNTIF(gpa < 0.0 OR gpa > 4.0) / COUNT(*) as failure_rate,
    'GPA outside range [0.0, 4.0]' as details
  FROM `driiiportfolio.staging.students`
  WHERE DATE(load_timestamp) = CURRENT_DATE() AND gpa IS NOT NULL;
  
  -- Award amount validity (must be positive)
  INSERT INTO `driiiportfolio.staging.data_quality_log`
  SELECT
    GENERATE_UUID() as quality_log_id,
    'grants' as table_name,
    'validity_award_amount' as check_name,
    COUNTIF(award_amount > 0) = COUNT(*) as check_passed,
    COUNTIF(award_amount <= 0) as failed_row_count,
    COUNT(*) as total_row_count,
    COUNTIF(award_amount <= 0) / COUNT(*) as failure_rate,
    'Award amount is zero or negative' as details
  FROM `driiiportfolio.staging.grants`
  WHERE DATE(load_timestamp) = CURRENT_DATE();
  
  -- Date logic validity (graduated >= enrolled)
  INSERT INTO `driiiportfolio.staging.data_quality_log`
  SELECT
    GENERATE_UUID() as quality_log_id,
    'students' as table_name,
    'validity_date_logic' as check_name,
    COUNTIF(date_graduated IS NULL OR date_graduated >= date_enrolled) = COUNT(*) as check_passed,
    COUNTIF(date_graduated IS NOT NULL AND date_graduated < date_enrolled) as failed_row_count,
    COUNT(*) as total_row_count,
    COUNTIF(date_graduated IS NOT NULL AND date_graduated < date_enrolled) / COUNT(*) as failure_rate,
    'date_graduated before date_enrolled' as details
  FROM `driiiportfolio.staging.students`
  WHERE DATE(load_timestamp) = CURRENT_DATE();
END;

-- ============================================================================
-- CONSISTENCY CHECKS: Cross-system referential integrity
-- ============================================================================

CREATE OR REPLACE PROCEDURE `driiiportfolio.staging.sp_check_consistency`()
BEGIN
  -- Faculty references in grants
  INSERT INTO `driiiportfolio.staging.data_quality_log`
  WITH missing_refs AS (
    SELECT COUNT(*) as orphaned_count
    FROM `driiiportfolio.staging.grants` g
    WHERE DATE(g.load_timestamp) = CURRENT_DATE()
      AND g.pi_id NOT IN (
        SELECT DISTINCT faculty_id
        FROM `driiiportfolio.staging.faculty`
        WHERE DATE(load_timestamp) = CURRENT_DATE()
      )
  )
  SELECT
    GENERATE_UUID() as quality_log_id,
    'grants' as table_name,
    'consistency_faculty_reference' as check_name,
    (SELECT orphaned_count FROM missing_refs) = 0 as check_passed,
    COALESCE((SELECT orphaned_count FROM missing_refs), 0) as failed_row_count,
    (SELECT COUNT(*) FROM `driiiportfolio.staging.grants` WHERE DATE(load_timestamp) = CURRENT_DATE()) as total_row_count,
    COALESCE((SELECT orphaned_count FROM missing_refs), 0) /
      NULLIF((SELECT COUNT(*) FROM `driiiportfolio.staging.grants` WHERE DATE(load_timestamp) = CURRENT_DATE()), 0) as failure_rate,
    'Grant PI_ID does not exist in faculty table' as details;
END;

-- ============================================================================
-- ANOMALY DETECTION: Identify statistical outliers
-- ============================================================================

CREATE OR REPLACE PROCEDURE `driiiportfolio.staging.sp_detect_anomalies`()
BEGIN
  -- GPA anomalies (>3 std devs from mean)
  INSERT INTO `driiiportfolio.staging.data_quality_log`
  WITH gpa_stats AS (
    SELECT
      AVG(gpa) as mean_gpa,
      STDDEV_POP(gpa) as stddev_gpa
    FROM `driiiportfolio.staging.students`
    WHERE DATE(load_timestamp) = CURRENT_DATE() AND gpa IS NOT NULL
  )
  SELECT
    GENERATE_UUID() as quality_log_id,
    'students' as table_name,
    'anomaly_gpa_outlier' as check_name,
    TRUE as check_passed,
    COUNTIF(ABS(s.gpa - gs.mean_gpa) > 3 * gs.stddev_gpa) as failed_row_count,
    COUNT(*) as total_row_count,
    COUNTIF(ABS(s.gpa - gs.mean_gpa) > 3 * gs.stddev_gpa) / COUNT(*) as failure_rate,
    'GPA values >3 standard deviations from mean (statistical anomalies)' as details
  FROM `driiiportfolio.staging.students` s
  CROSS JOIN gpa_stats gs
  WHERE DATE(s.load_timestamp) = CURRENT_DATE();
  
  -- Salary anomalies (>3 std devs from rank mean)
  INSERT INTO `driiiportfolio.staging.data_quality_log`
  WITH salary_stats AS (
    SELECT
      rank,
      AVG(salary) as mean_salary,
      STDDEV_POP(salary) as stddev_salary
    FROM `driiiportfolio.staging.faculty`
    WHERE DATE(load_timestamp) = CURRENT_DATE() AND salary IS NOT NULL
    GROUP BY rank
  )
  SELECT
    GENERATE_UUID() as quality_log_id,
    'faculty' as table_name,
    'anomaly_salary_outlier' as check_name,
    TRUE as check_passed,
    COUNTIF(ABS(f.salary - ss.mean_salary) > 3 * ss.stddev_salary) as failed_row_count,
    COUNT(*) as total_row_count,
    COUNTIF(ABS(f.salary - ss.mean_salary) > 3 * ss.stddev_salary) / COUNT(*) as failure_rate,
    'Faculty salary >3 std devs from rank average (compensation anomaly)' as details
  FROM `driiiportfolio.staging.faculty` f
  JOIN salary_stats ss ON f.rank = ss.rank
  WHERE DATE(f.load_timestamp) = CURRENT_DATE();
END;

-- ============================================================================
-- QUALITY SCORECARD: Generate daily summary report
-- ============================================================================

CREATE OR REPLACE PROCEDURE `driiiportfolio.staging.sp_generate_quality_scorecard`()
BEGIN
  -- Run all checks
  CALL `driiiportfolio.staging.sp_check_completeness`();
  CALL `driiiportfolio.staging.sp_check_uniqueness`();
  CALL `driiiportfolio.staging.sp_check_validity`();
  CALL `driiiportfolio.staging.sp_check_consistency`();
  CALL `driiiportfolio.staging.sp_detect_anomalies`();
  
  -- Generate summary
  SELECT
    CURRENT_DATE() as report_date,
    COUNT(DISTINCT table_name) as tables_checked,
    COUNT(DISTINCT check_name) as checks_run,
    COUNTIF(check_passed = TRUE) as checks_passed,
    COUNTIF(check_passed = FALSE) as checks_failed,
    SUM(failed_row_count) as total_failed_rows,
    SUM(total_row_count) as total_rows_processed,
    ROUND(SUM(failed_row_count) / NULLIF(SUM(total_row_count), 0), 4) as overall_failure_rate,
    ROUND(1 - (SUM(failed_row_count) / NULLIF(SUM(total_row_count), 0)), 4) as overall_quality_score
  FROM `driiiportfolio.staging.data_quality_log`
  WHERE DATE(check_timestamp) = CURRENT_DATE();
END;
