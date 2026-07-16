-- UT CNS Data Hub: Data Quality & Integrity Suite
-- 1. Completeness: Check for NULLs in Critical Columns
SELECT 'dim_student' as table_name, 'student_id' as column_name, COUNT(*) as null_count
FROM `driiiportfolio.analytics.dim_student` WHERE student_id IS NULL
UNION ALL
SELECT 'fact_enrollment', 'student_key', COUNT(*) FROM `driiiportfolio.analytics.fact_enrollment` WHERE student_key IS NULL;

-- 2. Uniqueness: Check for Duplicate Surrogate Keys
SELECT student_key, COUNT(*) as dup_count
FROM `driiiportfolio.analytics.dim_student` GROUP BY 1 HAVING dup_count > 1;

-- 3. Referential Integrity: Identify Orphaned Fact Records
SELECT count(e.enrollment_key) as orphaned_enrollments
FROM `driiiportfolio.analytics.fact_enrollment` e
LEFT JOIN `driiiportfolio.analytics.dim_student` s ON e.student_key = s.student_key
WHERE s.student_key IS NULL;

-- 4. Business Logic: GPA Range Validation
SELECT count(*) as invalid_gpa_records
FROM `driiiportfolio.analytics.dim_student` WHERE gpa < 0.0 OR gpa > 4.0;