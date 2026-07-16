# UT-CNS-DATA-HUB: Data Dictionary & Lineage

## 1. Staging Layer (Raw Ingestion)
*Source: Synthetic CSV Generators*

- **staging.students:** Raw student records (ID, Major, GPA, Cohort).
- **staging.faculty:** Raw HR data (ID, Rank, Salary, Department).
- **staging.grants:** Raw grant funding data (Award Amount, PI ID, Agency).
- **staging.enrollments:** Raw grade records (Grade Point, Semester, Year).

## 2. Analytics Layer (Star Schema)
*Transformation: CTAS / Stored Procedures*

- **dim_student:** Conformed student dimension. Primary Key: `student_key`.
- **dim_faculty:** Conformed faculty dimension. Primary Key: `faculty_key`.
- **fact_enrollment:** Transactional fact table for student grades. Links to `dim_student`.
- **fact_research_grant:** Measurement of funding performance. Links to `dim_faculty`.

## 3. Compliance Layer (Masked Reporting)
*Transformation: SQL Views*

- **vw_student_enrollment_safe:** Joins facts and dimensions but excludes PII. Exposes only Major and Performance metrics.
- **vw_faculty_research_safe:** Aggregates research metrics at the Department level to prevent individual salary/grant exposure.

## 4. Data Lineage
`CSV (Source)` -> `BigQuery Staging (Raw)` -> `SQL Transformation (CTAS)` -> `Analytics (Star Schema)` -> `Governance Views (Compliance)`