-- ============================================================================
-- FACT TABLES: Load dimensional model fact tables with business logic
-- Portfolio Project: Data Analytics Engineer Role
-- ============================================================================

-- ============================================================================
-- FACT_ENROLLMENT: Student course enrollments with grades and progress
-- ============================================================================
CREATE OR REPLACE PROCEDURE `driiiportfolio.analytics.sp_load_fact_enrollment`()
BEGIN
  INSERT INTO `driiiportfolio.analytics.fact_enrollment`
  SELECT
    ROW_NUMBER() OVER (ORDER BY ec.enrollment_id) as enrollment_key,
    ds.student_key,
    dc.course_key,
    dd.academic_year,
    dd.academic_semester,
    ec.semester as date_enrolled,  -- Simplified for demo
    NULL as date_completed,
    ec.grade,
    ec.grade_point,
    ec.credits_earned,
    COALESCE(dc.credit_hours, 3) as credits_attempted,
    CASE WHEN ec.grade_point >= 2.0 THEN TRUE ELSE FALSE END as is_passing,
    CASE WHEN ec.grade != 'I' THEN TRUE ELSE FALSE END as is_completed,
    CASE
      WHEN ec.grade = 'I' THEN 'In Progress'
      WHEN ec.grade IN ('W', 'Z') THEN 'Dropped'
      ELSE 'Completed'
    END as enrollment_status,
    CURRENT_TIMESTAMP() as dw_created_date,
    CURRENT_TIMESTAMP() as dw_updated_date
  FROM `driiiportfolio.staging.v_enrollments_cleaned` ec
  JOIN `driiiportfolio.analytics.dim_student` ds ON ec.student_id = ds.student_id AND ds.dw_is_current
  JOIN `driiiportfolio.analytics.dim_course` dc ON ec.course_id = dc.course_id AND dc.dw_is_current
  JOIN `driiiportfolio.analytics.dim_date` dd ON PARSE_DATE('%Y', CAST(ec.year as STRING)) <= dd.calendar_date
    AND dd.calendar_date < DATE_ADD(PARSE_DATE('%Y', CAST(ec.year as STRING)), INTERVAL 1 YEAR)
  WHERE ec.recency_rank = 1;
END;

-- ============================================================================
-- FACT_STUDENT_PERFORMANCE: Student academic performance by term
-- ============================================================================
CREATE OR REPLACE PROCEDURE `driiiportfolio.analytics.sp_load_fact_student_performance`()
BEGIN
  INSERT INTO `driiiportfolio.analytics.fact_student_performance`
  WITH term_gpa AS (
    SELECT
      ds.student_key,
      dd.academic_year,
      ROUND(AVG(fe.grade_point), 2) as semester_gpa,
      SUM(CASE WHEN fe.is_passing THEN fe.credits_earned ELSE 0 END) as credits_earned,
      SUM(fe.credits_attempted) as credits_attempted,
      SUM(CASE WHEN fe.is_passing THEN 1 ELSE 0 END) as passing_courses,
      SUM(CASE WHEN NOT fe.is_passing THEN 1 ELSE 0 END) as failing_courses
    FROM `driiiportfolio.analytics.fact_enrollment` fe
    JOIN `driiiportfolio.analytics.dim_student` ds ON fe.student_key = ds.student_key
    JOIN `driiiportfolio.analytics.dim_date` dd ON fe.academic_year = dd.academic_year
    WHERE ds.dw_is_current AND fe.is_completed
    GROUP BY ds.student_key, dd.academic_year
  ),
  cumulative_gpa AS (
    SELECT
      ds.student_key,
      dd.academic_year,
      ROUND(
        SUM(fe.grade_point * fe.credits_earned) / NULLIF(SUM(fe.credits_earned), 0),
        2
      ) as cumulative_gpa
    FROM `driiiportfolio.analytics.fact_enrollment` fe
    JOIN `driiiportfolio.analytics.dim_student` ds ON fe.student_key = ds.student_key
    JOIN `driiiportfolio.analytics.dim_date` dd ON fe.academic_year >= dd.academic_year
    WHERE ds.dw_is_current AND fe.is_completed
    GROUP BY ds.student_key, dd.academic_year
  )
  SELECT
    ROW_NUMBER() OVER (ORDER BY tg.student_key, tg.academic_year) as performance_key,
    tg.student_key,
    tg.academic_year,
    tg.semester_gpa,
    cg.cumulative_gpa,
    tg.credits_earned,
    tg.credits_attempted,
    tg.passing_courses,
    tg.failing_courses,
    CASE
      WHEN cg.cumulative_gpa >= 3.0 THEN 'Good'
      WHEN cg.cumulative_gpa >= 2.0 THEN 'Probation'
      ELSE 'Dismissal'
    END as academic_standing,
    CASE
      WHEN cg.cumulative_gpa < 2.0 OR tg.failing_courses > 0 THEN TRUE
      ELSE FALSE
    END as is_at_risk,
    ROUND(tg.credits_earned / NULLIF(120, 0), 2) as degree_progress_pct,
    CURRENT_TIMESTAMP() as dw_created_date,
    CURRENT_TIMESTAMP() as dw_updated_date
  FROM term_gpa tg
  JOIN cumulative_gpa cg ON tg.student_key = cg.student_key AND tg.academic_year = cg.academic_year;
END;

-- ============================================================================
-- FACT_RESEARCH_GRANT: Research grant activity and outcomes
-- ============================================================================
CREATE OR REPLACE PROCEDURE `driiiportfolio.analytics.sp_load_fact_research_grant`()
BEGIN
  INSERT INTO `driiiportfolio.analytics.fact_research_grant`
  SELECT
    ROW_NUMBER() OVER (ORDER BY gc.grant_id) as grant_key,
    gc.grant_id,
    df.faculty_key,
    dd.department_key,
    dfa.agency_key,
    gc.award_amount,
    gc.start_date,
    gc.end_date,
    DATE_DIFF(gc.end_date, gc.start_date, MONTH) as grant_duration_months,
    gc.status,
    gc.publication_count,
    gc.publication_count * 3 as citations_count,  -- Simulated: avg 3 citations per pub
    CASE
      WHEN gc.publication_count > 0
        THEN ROUND(gc.award_amount / gc.publication_count, 2)
      ELSE gc.award_amount
    END as cost_per_publication,
    EXTRACT(YEAR FROM gc.start_date) as grant_fiscal_year,
    CURRENT_TIMESTAMP() as dw_created_date,
    CURRENT_TIMESTAMP() as dw_updated_date
  FROM `driiiportfolio.staging.v_grants_cleaned` gc
  JOIN `driiiportfolio.analytics.dim_faculty` df ON gc.pi_id = df.faculty_id AND df.dw_is_current
  JOIN `driiiportfolio.analytics.dim_date` dd ON gc.start_date >= dd.calendar_date  -- Simplified join
  LEFT JOIN `driiiportfolio.analytics.dim_funding_agency` dfa ON gc.funding_agency = dfa.agency_name
  WHERE gc.recency_rank = 1;
END;

-- ============================================================================
-- FACT_FACULTY_PRODUCTIVITY: Annual faculty performance scorecard
-- ============================================================================
CREATE OR REPLACE PROCEDURE `driiiportfolio.analytics.sp_load_fact_faculty_productivity`()
BEGIN
  INSERT INTO `driiiportfolio.analytics.fact_faculty_productivity`
  WITH faculty_stats AS (
    SELECT
      df.faculty_key,
      dd.department_key,
      EXTRACT(YEAR FROM CURRENT_DATE()) as academic_year,
      COUNT(DISTINCT frg.grant_key) as total_grants_awarded,
      SUM(frg.award_amount) as total_grant_dollars,
      ROUND(AVG(frg.award_amount), 0) as avg_grant_size,
      SUM(frg.publication_count) as total_publications,
      ROUND(SUM(frg.publication_count) * 0.8, 0) as peer_reviewed_publications,
      ROUND(SUM(frg.publication_count) * 0.1, 0) as books_authored,
      ROUND(SUM(frg.publication_count) * 0.1, 0) as conference_presentations
    FROM `driiiportfolio.analytics.dim_faculty` df
    LEFT JOIN `driiiportfolio.analytics.fact_research_grant` frg ON df.faculty_key = frg.pi_key
    LEFT JOIN `driiiportfolio.analytics.dim_department` dd ON df.faculty_key = df.faculty_key  -- Placeholder
    WHERE df.dw_is_current AND df.is_active
    GROUP BY df.faculty_key, dd.department_key
  )
  SELECT
    ROW_NUMBER() OVER (ORDER BY fs.faculty_key) as productivity_key,
    fs.faculty_key,
    fs.department_key,
    fs.academic_year,
    fs.total_grants_awarded,
    fs.total_grant_dollars,
    fs.avg_grant_size,
    fs.total_publications,
    fs.peer_reviewed_publications,
    fs.books_authored,
    fs.conference_presentations,
    0 as courses_taught,  -- Would join to course fact table
    0 as students_advised,
    4.0 as avg_course_rating,
    5 as committee_assignments,
    40 as professional_development_hours,
    -- Weighted productivity score: 50% research, 30% teaching, 20% service
    ROUND(
      (COALESCE(fs.total_grant_dollars, 0) / 100000.0 * 0.50) +
      (COALESCE(fs.total_publications, 0) * 10 * 0.30) +
      (5 * 0.20),
      2
    ) as productivity_score,
    PERCENT_RANK() OVER (PARTITION BY fs.department_key ORDER BY fs.total_grant_dollars) as peer_rank_percentile,
    CURRENT_TIMESTAMP() as dw_created_date,
    CURRENT_TIMESTAMP() as dw_updated_date
  FROM faculty_stats fs;
END;

-- ============================================================================
-- FACT_COURSE_PERFORMANCE: Course-level teaching effectiveness metrics
-- ============================================================================
CREATE OR REPLACE PROCEDURE `driiiportfolio.analytics.sp_load_fact_course_performance`()
BEGIN
  INSERT INTO `driiiportfolio.analytics.fact_course_performance`
  SELECT
    ROW_NUMBER() OVER (ORDER BY dc.course_key, dd.academic_year) as course_performance_key,
    dc.course_key,
    df.faculty_key,
    dd.department_key,
    dd.academic_year,
    dd.academic_semester,
    COUNT(DISTINCT fe.enrollment_key) as total_enrollment,
    SUM(CASE WHEN fe.is_completed THEN 1 ELSE 0 END) as total_completed,
    SUM(CASE WHEN fe.is_passing THEN 1 ELSE 0 END) as passing_students,
    SUM(CASE WHEN NOT fe.is_passing THEN 1 ELSE 0 END) as failing_students,
    ROUND(AVG(fe.grade_point), 2) as avg_grade_point,
    ROUND(SUM(CASE WHEN fe.is_passing THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT fe.enrollment_key), 0), 3) as pass_rate,
    cc.avg_rating as avg_student_rating,
    ROUND((AVG(fe.grade_point) - 3.0) / 0.5, 2) as course_difficulty_index,
    0.0 as repeat_enrollment_pct,
    CURRENT_TIMESTAMP() as dw_created_date,
    CURRENT_TIMESTAMP() as dw_updated_date
  FROM `driiiportfolio.analytics.dim_course` dc
  LEFT JOIN `driiiportfolio.analytics.fact_enrollment` fe ON dc.course_key = fe.course_key
  LEFT JOIN `driiiportfolio.analytics.dim_date` dd ON fe.academic_year = dd.academic_year
  LEFT JOIN `driiiportfolio.analytics.dim_faculty` df ON dc.course_key = dc.course_key  -- Placeholder
  LEFT JOIN `driiiportfolio.staging.v_courses_cleaned` cc ON dc.course_id = cc.course_id
  WHERE dc.dw_is_current
  GROUP BY dc.course_key, df.faculty_key, dd.department_key, dd.academic_year, dd.academic_semester, cc.avg_rating;
END;
