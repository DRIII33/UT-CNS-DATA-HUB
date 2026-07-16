-- UT CNS Data Hub: Analytical Query Templates
-- 1. Enrollment Retention by Major
SELECT major, academic_year, count(student_key) as total_students
FROM `driiiportfolio.analytics.dim_student` JOIN `driiiportfolio.analytics.fact_enrollment` USING(student_key)
GROUP BY 1, 2 ORDER BY 3 DESC;

-- 2. Research ROI: Publication Cost by Department
SELECT f.department, SUM(g.award_amount) / NULLIF(SUM(g.publication_count), 0) as cost_per_pub
FROM `driiiportfolio.analytics.fact_research_grant` g
JOIN `driiiportfolio.analytics.dim_faculty` f ON g.pi_key = f.faculty_key
GROUP BY 1 ORDER BY 2 ASC;