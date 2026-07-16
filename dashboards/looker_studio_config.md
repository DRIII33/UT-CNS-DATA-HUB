# Looker Studio Dashboard Configuration Guide

**Dashboard Title:** UT CNS Strategic Analytics Hub
**Data Source:** BigQuery `driiiportfolio.compliance.vw_student_enrollment_safe` & `vw_faculty_research_safe`

## Page 1: Student Success & Enrollment
- **Title:** Enrollment Trends & Academic Standing
- **KPI Scorecards:**
    - Total Enrolled Students (Count Distinct student_id)
    - Avg GPA (Metric: gpa)
- **Charts:**
    - **Time Series:** Enrollment Count vs. Academic Year
    - **Pie Chart:** Student Distribution by Major
    - **Table:** List of students with GPAs < 2.5 (At-Risk cohort)

## Page 2: Research Impact & Faculty ROI
- **Title:** Research Funding & Faculty Productivity
- **KPI Scorecards:**
    - Total Research Awards (Sum: award_amount)
    - Total Publications (Sum: publication_count)
- **Charts:**
    - **Bar Chart:** Award Amount by Department
    - **Scatter Plot:** Award Amount (X) vs. Publication Count (Y)
    - **Heat Map:** Funding Agency vs. Department Impact
