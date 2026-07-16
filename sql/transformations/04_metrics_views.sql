-- ============================================================================
-- AGGREGATE VIEWS & METRICS: Pre-computed KPIs and dashboards
-- Portfolio Project: Data Analytics Engineer Role
-- ============================================================================

-- ============================================================================
-- ENROLLMENT METRICS: Summary by major and academic year
-- ============================================================================
CREATE OR REPLACE VIEW `driiiportfolio.analytics.v_enrollment_metrics_by_major` AS
SELECT
  ds.major,
  dd.academic_year,
  COUNT(DISTINCT ds.student_key) as total_students,
  ROUND(AVG(fsp.cumulative_gpa), 2) as avg_cumulative_gpa,
  ROUND(SUM(CASE WHEN fsp.is_at_risk THEN 1 ELSE 0 END) / COUNT(DISTINCT ds.student_key), 3) as pct_at_risk,
  COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Graduated' THEN ds.student_key END) as graduates,
  ROUND(
    COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Graduated' THEN ds.student_key END) /
    NULLIF(COUNT(DISTINCT ds.student_key), 0),
    3
  ) as graduation_rate
FROM `driiiportfolio.analytics.dim_student` ds
LEFT JOIN `driiiportfolio.analytics.fact_student_performance` fsp ON ds.student_key = fsp.student_key
LEFT JOIN `driiiportfolio.analytics.dim_date` dd ON fsp.academic_year = dd.academic_year
WHERE ds.dw_is_current
GROUP BY ds.major, dd.academic_year;

-- ============================================================================
-- RESEARCH IMPACT: Faculty and grant performance dashboard
-- ============================================================================
CREATE OR REPLACE VIEW `driiiportfolio.analytics.v_research_impact_summary` AS
SELECT
  dd.department_key,
  dd.department_name,
  COUNT(DISTINCT ffp.faculty_key) as faculty_count,
  SUM(ffp.total_grants_awarded) as total_grants,
  SUM(ffp.total_grant_dollars) as total_funding,
  ROUND(AVG(ffp.total_grant_dollars), 0) as avg_funding_per_faculty,
  SUM(ffp.total_publications) as total_publications,
  ROUND(SUM(ffp.total_grant_dollars) / NULLIF(SUM(ffp.total_publications), 0), 0) as cost_per_publication,
  ROUND(AVG(ffp.productivity_score), 2) as avg_productivity_score
FROM `driiiportfolio.analytics.fact_faculty_productivity` ffp
JOIN `driiiportfolio.analytics.dim_department` dd ON ffp.department_key = dd.department_key
GROUP BY dd.department_key, dd.department_name;

-- ============================================================================
-- STUDENT SUCCESS: At-risk student identification and intervention
-- ============================================================================
CREATE OR REPLACE VIEW `driiiportfolio.analytics.v_student_at_risk_detail` AS
SELECT
  ds.student_id,
  ds.student_id_pseudonymized,
  ds.major,
  ds.cohort_year,
  fsp.cumulative_gpa,
  fsp.academic_standing,
  fsp.is_at_risk,
  CASE
    WHEN fsp.cumulative_gpa < 2.0 THEN 'CRITICAL - Below 2.0 GPA'
    WHEN fsp.cumulative_gpa < 2.5 THEN 'HIGH - Below 2.5 GPA'
    WHEN fsp.failing_courses > 1 THEN 'MODERATE - Multiple failures'
    WHEN fsp.is_at_risk THEN 'LOW - Monitor'
    ELSE 'ON TRACK'
  END as risk_assessment,
  fsp.failing_courses,
  fsp.degree_progress_pct,
  CASE
    WHEN fsp.cumulative_gpa < 2.0 THEN 'Immediate - Probation/Dismissal risk'
    WHEN fsp.cumulative_gpa < 2.5 THEN 'High priority - Intervention needed'
    WHEN fsp.is_at_risk THEN 'Standard - Monitor progress'
    ELSE 'None - On track'
  END as recommended_intervention
FROM `driiiportfolio.analytics.dim_student` ds
LEFT JOIN `driiiportfolio.analytics.fact_student_performance` fsp ON ds.student_key = fsp.student_key
WHERE ds.dw_is_current AND (fsp.is_at_risk OR fsp.cumulative_gpa < 2.5);

-- ============================================================================
-- TEACHING EFFECTIVENESS: Course and instructor performance
-- ============================================================================
CREATE OR REPLACE VIEW `driiiportfolio.analytics.v_teaching_effectiveness` AS
SELECT
  df.faculty_id,
  df.faculty_rank,
  dc.course_code,
  dc.course_title,
  dd.academic_year,
  fcp.total_enrollment,
  fcp.pass_rate,
  fcp.avg_grade_point,
  fcp.avg_student_rating,
  CASE
    WHEN fcp.avg_student_rating >= 4.5 THEN 'Excellent'
    WHEN fcp.avg_student_rating >= 4.0 THEN 'Very Good'
    WHEN fcp.avg_student_rating >= 3.5 THEN 'Good'
    ELSE 'Needs Improvement'
  END as rating_category,
  CASE
    WHEN fcp.pass_rate >= 0.90 AND fcp.avg_student_rating >= 4.0 THEN 'High Performer'
    WHEN fcp.pass_rate < 0.80 OR fcp.avg_student_rating < 3.0 THEN 'Needs Support'
    ELSE 'Standard'
  END as performance_category
FROM `driiiportfolio.analytics.fact_course_performance` fcp
JOIN `driiiportfolio.analytics.dim_course` dc ON fcp.course_key = dc.course_key
JOIN `driiiportfolio.analytics.dim_faculty` df ON fcp.course_key = fcp.course_key  -- Placeholder
JOIN `driiiportfolio.analytics.dim_date` dd ON fcp.academic_year = dd.academic_year
WHERE dc.dw_is_current;

-- ============================================================================
-- COHORT ANALYSIS: Multi-year enrollment and graduation trends
-- ============================================================================
CREATE OR REPLACE VIEW `driiiportfolio.analytics.v_cohort_analysis` AS
SELECT
  ds.cohort_year,
  ds.major,
  ds.ethnicity_category,
  COUNT(DISTINCT ds.student_key) as cohort_size,
  COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Graduated' THEN ds.student_key END) as graduated_count,
  ROUND(
    COUNT(DISTINCT CASE WHEN ds.current_enrollment_status = 'Graduated' THEN ds.student_key END) /
    NULLIF(COUNT(DISTINCT ds.student_key), 0),
    3
  ) as graduation_rate,
  ROUND(AVG(fsp.cumulative_gpa), 2) as avg_gpa,
  ROUND(
    SUM(CASE WHEN fsp.is_at_risk THEN 1 ELSE 0 END) /
    NULLIF(COUNT(DISTINCT ds.student_key), 0),
    3
  ) as pct_at_risk,
  YEAR(CURRENT_DATE()) - ds.cohort_year as years_since_entry
FROM `driiiportfolio.analytics.dim_student` ds
LEFT JOIN `driiiportfolio.analytics.fact_student_performance` fsp ON ds.student_key = fsp.student_key
WHERE ds.dw_is_current
GROUP BY ds.cohort_year, ds.major, ds.ethnicity_category;

-- ============================================================================
-- GRANT FUNDING TRENDS: Year-over-year analysis
-- ============================================================================
CREATE OR REPLACE VIEW `driiiportfolio.analytics.v_grant_funding_trends` AS
SELECT
  frg.grant_fiscal_year,
  dfa.agency_name,
  COUNT(DISTINCT frg.grant_key) as grant_count,
  SUM(frg.award_amount) as total_award_amount,
  ROUND(AVG(frg.award_amount), 0) as avg_award_size,
  ROUND(AVG(frg.grant_duration_months), 1) as avg_duration_months,
  SUM(frg.publication_count) as publication_count,
  ROUND(SUM(frg.award_amount) / NULLIF(SUM(frg.publication_count), 0), 0) as cost_per_publication,
  LAG(SUM(frg.award_amount)) OVER (PARTITION BY dfa.agency_name ORDER BY frg.grant_fiscal_year) as prior_year_funding,
  ROUND(
    (SUM(frg.award_amount) - LAG(SUM(frg.award_amount)) OVER (PARTITION BY dfa.agency_name ORDER BY frg.grant_fiscal_year)) /
    NULLIF(LAG(SUM(frg.award_amount)) OVER (PARTITION BY dfa.agency_name ORDER BY frg.grant_fiscal_year), 0),
    3
  ) as yoy_growth_rate
FROM `driiiportfolio.analytics.fact_research_grant` frg
LEFT JOIN `driiiportfolio.analytics.dim_funding_agency` dfa ON frg.agency_key = dfa.agency_key
GROUP BY frg.grant_fiscal_year, dfa.agency_name;
