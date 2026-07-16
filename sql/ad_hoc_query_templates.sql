-- ============================================================================
-- AD-HOC QUERY TEMPLATES: Common analytical queries for business users
-- Portfolio Project: Data Analytics Engineer Role
-- Purpose: Self-serve analytics without requiring SQL expertise
-- ============================================================================

-- ============================================================================
-- TEMPLATE 1: Enrollment Trends by Major (Last 5 Years)
-- ============================================================================
SELECT
  ds.major,
  dd.academic_year,
  COUNT(DISTINCT fe.student_key) as enrollment_count,
  ROUND(AVG(fsp.cumulative_gpa), 2) as avg_gpa,
  ROUND(SUM(CASE WHEN fsp.is_at_risk THEN 1 ELSE 0 END) / COUNT(DISTINCT fe.student_key), 3) as pct_at_risk,
  COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Graduated' THEN fe.student_key END) as graduates
FROM `driiiportfolio.analytics.fact_enrollment` fe
JOIN `driiiportfolio.analytics.dim_student` ds ON fe.student_key = ds.student_key
JOIN `driiiportfolio.analytics.fact_student_performance` fsp ON ds.student_key = fsp.student_key
JOIN `driiiportfolio.analytics.dim_date` dd ON fe.academic_year = dd.academic_year
WHERE ds.dw_is_current
  AND dd.academic_year >= EXTRACT(YEAR FROM CURRENT_DATE()) - 5
GROUP BY ds.major, dd.academic_year
ORDER BY ds.major, dd.academic_year DESC;

-- ============================================================================
-- TEMPLATE 2: Faculty Productivity Comparison (Department Benchmarking)
-- ============================================================================
SELECT
  df.faculty_id,
  df.faculty_rank,
  dd.department_name,
  ffp.total_grants_awarded,
  ffp.total_grant_dollars,
  ffp.total_publications,
  ffp.productivity_score,
  PERCENT_RANK() OVER (PARTITION BY dd.department_key ORDER BY ffp.productivity_score DESC) as rank_in_department
FROM `driiiportfolio.analytics.fact_faculty_productivity` ffp
JOIN `driiiportfolio.analytics.dim_faculty` df ON ffp.faculty_key = df.faculty_key
JOIN `driiiportfolio.analytics.dim_department` dd ON ffp.department_key = dd.department_key
WHERE df.dw_is_current
  AND df.is_active = TRUE
  AND ffp.academic_year = EXTRACT(YEAR FROM CURRENT_DATE())
ORDER BY dd.department_name, ffp.productivity_score DESC;

-- ============================================================================
-- TEMPLATE 3: At-Risk Students Alert (For Advisors)
-- ============================================================================
SELECT
  ds.student_id,
  ds.major,
  ds.cohort_year,
  fsp.cumulative_gpa,
  fsp.failing_courses,
  fsp.degree_progress_pct,
  CASE
    WHEN fsp.cumulative_gpa < 2.0 THEN 'CRITICAL'
    WHEN fsp.cumulative_gpa < 2.5 THEN 'HIGH'
    WHEN fsp.failing_courses > 1 THEN 'MODERATE'
    ELSE 'LOW'
  END as risk_level,
  CASE
    WHEN fsp.cumulative_gpa < 2.0 THEN 'Probation/Dismissal Risk - Immediate Action'
    WHEN fsp.cumulative_gpa < 2.5 THEN 'Intervention Recommended'
    WHEN fsp.failing_courses > 1 THEN 'Monitor Progress'
    ELSE 'On Track'
  END as recommended_action
FROM `driiiportfolio.analytics.dim_student` ds
JOIN `driiiportfolio.analytics.fact_student_performance` fsp ON ds.student_key = fsp.student_key
WHERE ds.dw_is_current
  AND ds.is_active = TRUE
  AND (fsp.cumulative_gpa < 2.5 OR fsp.failing_courses > 0)
ORDER BY risk_level DESC, fsp.cumulative_gpa ASC;

-- ============================================================================
-- TEMPLATE 4: Research Grant Performance by Agency (5-Year Trend)
-- ============================================================================
SELECT
  dfa.agency_name,
  frg.grant_fiscal_year,
  COUNT(DISTINCT frg.grant_key) as grant_count,
  SUM(frg.award_amount) as total_funding,
  ROUND(AVG(frg.award_amount), 0) as avg_grant_size,
  SUM(frg.publication_count) as publications,
  ROUND(SUM(frg.award_amount) / NULLIF(SUM(frg.publication_count), 0), 0) as cost_per_publication,
  LAG(SUM(frg.award_amount)) OVER (PARTITION BY dfa.agency_name ORDER BY frg.grant_fiscal_year) as prior_year_total,
  ROUND(
    (SUM(frg.award_amount) - LAG(SUM(frg.award_amount)) OVER (PARTITION BY dfa.agency_name ORDER BY frg.grant_fiscal_year)) /
    NULLIF(LAG(SUM(frg.award_amount)) OVER (PARTITION BY dfa.agency_name ORDER BY frg.grant_fiscal_year), 0),
    3
  ) as yoy_growth_rate
FROM `driiiportfolio.analytics.fact_research_grant` frg
LEFT JOIN `driiiportfolio.analytics.dim_funding_agency` dfa ON frg.agency_key = dfa.agency_key
WHERE frg.grant_fiscal_year >= EXTRACT(YEAR FROM CURRENT_DATE()) - 5
GROUP BY dfa.agency_name, frg.grant_fiscal_year
ORDER BY dfa.agency_name, frg.grant_fiscal_year DESC;

-- ============================================================================
-- TEMPLATE 5: Course Performance Analysis (Teaching Effectiveness)
-- ============================================================================
SELECT
  dc.course_code,
  dc.course_title,
  dd.academic_year,
  dd.academic_semester,
  fcp.total_enrollment,
  fcp.pass_rate,
  ROUND(fcp.avg_grade_point, 2) as avg_grade,
  ROUND(fcp.avg_student_rating, 1) as avg_student_rating,
  CASE
    WHEN fcp.pass_rate >= 0.90 AND fcp.avg_student_rating >= 4.0 THEN 'Excellent'
    WHEN fcp.pass_rate >= 0.80 AND fcp.avg_student_rating >= 3.5 THEN 'Good'
    WHEN fcp.pass_rate < 0.75 OR fcp.avg_student_rating < 3.0 THEN 'Needs Improvement'
    ELSE 'Satisfactory'
  END as performance_category
FROM `driiiportfolio.analytics.fact_course_performance` fcp
JOIN `driiiportfolio.analytics.dim_course` dc ON fcp.course_key = dc.course_key
JOIN `driiiportfolio.analytics.dim_date` dd ON fcp.academic_year = dd.academic_year
WHERE dc.dw_is_current
  AND dd.academic_year = EXTRACT(YEAR FROM CURRENT_DATE())
ORDER BY performance_category, fcp.avg_student_rating DESC;

-- ============================================================================
-- TEMPLATE 6: Student Cohort Retention Analysis
-- ============================================================================
SELECT
  ds.cohort_year,
  ds.major,
  COUNT(DISTINCT ds.student_key) as cohort_size,
  COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Graduated' THEN ds.student_key END) as graduated,
  COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Withdrawn' THEN ds.student_key END) as withdrawn,
  COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Active' THEN ds.student_key END) as still_enrolled,
  ROUND(
    COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Graduated' THEN ds.student_key END) /
    NULLIF(COUNT(DISTINCT ds.student_key), 0),
    3
  ) as graduation_rate,
  ROUND(
    COUNT(DISTINCT CASE WHEN ds.current_enrollment_status IN ('Active', 'Graduated') THEN ds.student_key END) /
    NULLIF(COUNT(DISTINCT ds.student_key), 0),
    3
  ) as retention_rate,
  ROUND(AVG(fsp.cumulative_gpa), 2) as avg_gpa
FROM `driiiportfolio.analytics.dim_student` ds
LEFT JOIN `driiiportfolio.analytics.fact_student_performance` fsp ON ds.student_key = fsp.student_key
WHERE ds.dw_is_current
GROUP BY ds.cohort_year, ds.major
ORDER BY ds.cohort_year DESC, ds.major;

-- ============================================================================
-- TEMPLATE 7: Demographic Equity Analysis
-- ============================================================================
SELECT
  ds.ethnicity_category,
  ds.is_first_generation,
  COUNT(DISTINCT ds.student_key) as student_count,
  ROUND(AVG(fsp.cumulative_gpa), 2) as avg_gpa,
  ROUND(SUM(CASE WHEN fsp.is_at_risk THEN 1 ELSE 0 END) / COUNT(DISTINCT ds.student_key), 3) as pct_at_risk,
  ROUND(
    COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Graduated' THEN ds.student_key END) /
    NULLIF(COUNT(DISTINCT ds.student_key), 0),
    3
  ) as graduation_rate,
  ROUND(
    COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Withdrawn' THEN ds.student_key END) /
    NULLIF(COUNT(DISTINCT ds.student_key), 0),
    3
  ) as withdrawal_rate
FROM `driiiportfolio.analytics.dim_student` ds
LEFT JOIN `driiiportfolio.analytics.fact_student_performance` fsp ON ds.student_key = fsp.student_key
WHERE ds.dw_is_current
GROUP BY ds.ethnicity_category, ds.is_first_generation
ORDER BY ds.ethnicity_category, ds.is_first_generation;

-- ============================================================================
-- TEMPLATE 8: High-Performing Research Faculty (Promotion Candidates)
-- ============================================================================
SELECT
  df.faculty_id,
  df.faculty_rank,
  dd.department_name,
  ffp.total_grants_awarded,
  ffp.total_grant_dollars,
  ffp.avg_funding_per_faculty,
  ffp.total_publications,
  ffp.peer_reviewed_publications,
  ffp.productivity_score,
  ROUND(ffp.peer_rank_percentile * 100, 1) as peer_rank_percentile,
  CASE
    WHEN ffp.peer_rank_percentile >= 0.75 AND ffp.total_publications >= 10 THEN 'Promotion Recommended'
    WHEN ffp.peer_rank_percentile >= 0.5 THEN 'High Performer'
    ELSE 'Standard'
  END as advancement_recommendation
FROM `driiiportfolio.analytics.fact_faculty_productivity` ffp
JOIN `driiiportfolio.analytics.dim_faculty` df ON ffp.faculty_key = df.faculty_key
JOIN `driiiportfolio.analytics.dim_department` dd ON ffp.department_key = dd.department_key
WHERE df.dw_is_current
  AND df.is_active = TRUE
  AND ffp.academic_year = EXTRACT(YEAR FROM CURRENT_DATE())
ORDER BY ffp.productivity_score DESC;
