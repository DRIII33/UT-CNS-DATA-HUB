# UT CNS Data Hub - Data Dictionary
## Portfolio Project: Data Analytics Engineer Role

---

## STAGING DATASET TABLES

### staging.students
**Purpose:** Raw student enrollment and demographic data from SIS
**Partitioned by:** load_timestamp (daily)
**Clustered by:** student_id, cohort_year, major

| Column | Type | Nullable | Description | Validation Rules |
|--------|------|----------|-------------|------------------|
| student_id | STRING | NO | Unique student identifier | NOT NULL, UNIQUE, length=8 |
| cohort_year | INT64 | YES | Academic year of admission | 2000 <= year <= current_year+1 |
| major | STRING | YES | Primary degree program | Must exist in discipline list |
| gpa | FLOAT64 | YES | Cumulative GPA | 0.0 <= gpa <= 4.0 |
| enrollment_status | STRING | YES | Current enrollment state | IN ('Active','Inactive','Graduated','Withdrawn') |
| date_enrolled | DATE | YES | First enrollment date | <= current_date |
| date_graduated | DATE | YES | Graduation date | >= date_enrolled (if populated) |
| credits_completed | INT64 | YES | Total credits earned | >= 0 |
| ethnicity | STRING | YES | Demographic category | From approved list |
| first_generation | BOOL | YES | First-gen indicator | TRUE/FALSE |
| load_timestamp | TIMESTAMP | YES | Ingestion timestamp | Auto-populated |

**Data Lineage:** Student Information System (SIS) → Staging.students
**Sensitivity:** FERPA-protected (PII)
**Retention:** 7 years post-graduation

---

### staging.faculty
**Purpose:** Raw faculty employment and compensation data from Workday
**Partitioned by:** load_timestamp (daily)
**Clustered by:** faculty_id, department

| Column | Type | Nullable | Description | Validation Rules |
|--------|------|----------|-------------|------------------|
| faculty_id | STRING | NO | Unique faculty identifier | NOT NULL, UNIQUE, length=8 |
| rank | STRING | YES | Academic rank | IN ('Assistant','Associate','Full','Lecturer','Adjunct') |
| hire_date | DATE | YES | Employment start date | NOT NULL, <= current_date |
| department | STRING | YES | Department affiliation | Must exist in department list |
| salary | INT64 | YES | Annual compensation | > 0, <= 500000 |
| employment_status | STRING | YES | Current employment state | IN ('Active','On Leave','Retired') |
| tenure_status | STRING | YES | Tenure classification | IN ('Tenured','Tenure-Track','Non-Tenure-Track') |
| research_focus | STRING | YES | Research discipline | Must exist in discipline list |
| load_timestamp | TIMESTAMP | YES | Ingestion timestamp | Auto-populated |

**Data Lineage:** Workday HR System → Staging.faculty
**Sensitivity:** Confidential (salary data)
**Retention:** 7 years post-departure

---

### staging.grants
**Purpose:** Research grant awards and funding data
**Partitioned by:** load_timestamp (daily)
**Clustered by:** pi_id, funding_agency

| Column | Type | Nullable | Description | Validation Rules |
|--------|------|----------|-------------|------------------|
| grant_id | STRING | NO | Unique grant identifier | NOT NULL, UNIQUE |
| pi_id | STRING | NO | Principal Investigator (Faculty ID) | NOT NULL, FK to faculty |
| award_amount | INT64 | YES | Grant award in USD | > 0 |
| funding_agency | STRING | YES | Funding organization | IN (approved agencies list) |
| start_date | DATE | YES | Project start date | NOT NULL, <= end_date |
| end_date | DATE | YES | Project end date | >= start_date |
| department | STRING | YES | Department of PI | Must exist in department list |
| status | STRING | YES | Grant lifecycle status | IN ('Active','Completed','Cancelled') |
| publication_count | INT64 | YES | Resulting publications | >= 0 |
| load_timestamp | TIMESTAMP | YES | Ingestion timestamp | Auto-populated |

**Data Lineage:** Research Administration System → Staging.grants
**Sensitivity:** Internal use (may include funded research)
**Retention:** 10 years (federal requirement)

---

### staging.courses
**Purpose:** Course catalog and offering information
**Partitioned by:** load_timestamp (daily)
**Clustered by:** instructor_id, year

| Column | Type | Nullable | Description | Validation Rules |
|--------|------|----------|-------------|------------------|
| course_id | STRING | NO | Unique course identifier | NOT NULL, UNIQUE |
| course_code | STRING | YES | Course code (e.g., BIO101) | NOT NULL, format validation |
| course_title | STRING | YES | Course name | NOT NULL |
| credits | INT64 | YES | Credit hours | IN (1,2,3,4) |
| semester | STRING | YES | Academic term | IN ('Fall','Spring','Summer') |
| year | INT64 | YES | Academic year | 2000 <= year <= current_year |
| instructor_id | STRING | YES | Teaching faculty (Faculty ID) | FK to faculty |
| enrollment | INT64 | YES | Total students enrolled | >= 0 |
| pass_rate | FLOAT64 | YES | % of students passing | 0.0 <= pass_rate <= 1.0 |
| avg_rating | FLOAT64 | YES | Average student rating (1-5) | 1.0 <= avg_rating <= 5.0 |
| load_timestamp | TIMESTAMP | YES | Ingestion timestamp | Auto-populated |

**Data Lineage:** Course Registration System → Staging.courses
**Sensitivity:** FERPA-protected (performance metrics)
**Retention:** 7 years

---

### staging.enrollments
**Purpose:** Student course enrollment records with grades
**Partitioned by:** load_timestamp (daily)
**Clustered by:** student_id, course_id, year

| Column | Type | Nullable | Description | Validation Rules |
|--------|------|----------|-------------|------------------|
| enrollment_id | STRING | NO | Unique enrollment record | NOT NULL, UNIQUE |
| student_id | STRING | NO | Student identifier | NOT NULL, FK to students |
| course_id | STRING | NO | Course identifier | NOT NULL, FK to courses |
| semester | STRING | YES | Academic term | IN ('Fall','Spring','Summer') |
| year | INT64 | YES | Academic year | >= 2000 |
| grade | STRING | YES | Letter grade | IN ('A','A-','B+','B','B-','C+','C','D','F','I','W') |
| grade_point | FLOAT64 | YES | Numeric grade (0.0-4.0) | 0.0 <= grade_point <= 4.0 |
| credits_earned | INT64 | YES | Credits toward degree | 0 <= credits_earned <= 4 |
| load_timestamp | TIMESTAMP | YES | Ingestion timestamp | Auto-populated |

**Data Lineage:** Course Registration System → Staging.enrollments
**Sensitivity:** FERPA-protected (PII + academic records)
**Retention:** 7 years

---

## ANALYTICS DATASET - DIMENSION TABLES

### analytics.dim_student
**Purpose:** Conformed student dimension with SCD Type 2 (slowly changing dimensions)
**Partitioned by:** dw_created_date
**Clustered by:** student_id, cohort_year, major

| Column | Type | Description | Business Logic |
|--------|------|-------------|----------------|
| student_key | INT64 | Surrogate key (auto-generated) | Primary key |
| student_id | STRING | Natural key from source | Unique identifier |
| student_id_pseudonymized | STRING | FERPA-compliant pseudonym | SHA256(student_id + salt) |
| cohort_year | INT64 | Year of admission | Determines academic progression |
| major | STRING | Primary degree program | Academic discipline |
| department | STRING | Offering department | Always 'College of Natural Sciences' |
| ethnicity_category | STRING | Demographic category | Aggregated for privacy |
| is_first_generation | BOOL | First-generation indicator | Student support flag |
| current_enrollment_status | STRING | Latest enrollment state | Active/Inactive/Graduated/Withdrawn |
| is_active | BOOL | Active enrollment flag | TRUE if status='Active' |
| dw_created_date | TIMESTAMP | Record creation timestamp | SCD Type 2: tracks changes |
| dw_updated_date | TIMESTAMP | Last update timestamp | Identifies stale records |
| dw_is_current | BOOL | Is this record current? | SCD Type 2: TRUE for latest |

**Usage:** Joins to fact_enrollment, fact_student_performance
**FERPA Compliance:** Names/SSN removed; only pseudonymized ID and demographics

---

### analytics.dim_faculty
**Purpose:** Conformed faculty dimension with SCD Type 2
**Partitioned by:** dw_created_date
**Clustered by:** faculty_id, department

| Column | Type | Description | Business Logic |
|--------|------|-------------|----------------|
| faculty_key | INT64 | Surrogate key | Primary key |
| faculty_id | STRING | Natural key from source | Unique identifier |
| faculty_id_pseudonymized | STRING | FERPA-compliant pseudonym | SHA256(faculty_id + salt) |
| faculty_rank | STRING | Academic rank | Affects compensation/expectations |
| hire_date | DATE | Employment start | Seniority indicator |
| department | STRING | Department affiliation | Organizational unit |
| tenure_status | STRING | Tenure classification | Career stage |
| research_focus | STRING | Research discipline | Primary expertise |
| current_employment_status | STRING | Latest employment state | Active/On Leave/Retired |
| is_active | BOOL | Currently employed flag | TRUE if status='Active' |
| dw_created_date | TIMESTAMP | Record creation | SCD Type 2 tracking |
| dw_updated_date | TIMESTAMP | Last update | Identifies stale records |
| dw_is_current | BOOL | Is this record current? | SCD Type 2: TRUE for latest |

**Usage:** Joins to fact_research_grant, fact_faculty_productivity
**Compensation Sensitivity:** Salary data NOT included in analytics dimension

---

### analytics.dim_course
**Purpose:** Course catalog dimension
**Clustered by:** course_id, course_code

| Column | Type | Description |
|--------|------|-------------|---|
| course_key | INT64 | Surrogate key |
| course_id | STRING | Natural key |
| course_code | STRING | Department code + number |
| course_title | STRING | Full course name |
| credit_hours | INT64 | Credits awarded |
| discipline | STRING | Academic discipline |
| offering_department | STRING | Always 'College of Natural Sciences' |
| dw_created_date | TIMESTAMP | Creation timestamp |
| dw_updated_date | TIMESTAMP | Last update timestamp |
| dw_is_current | BOOL | Is current record? |

---

### analytics.dim_date
**Purpose:** Date dimension (pre-computed for performance)
**Coverage:** 2014-2030 (16 years)

| Column | Type | Description | Usage |
|--------|------|-------------|-------|
| date_key | INT64 | YYYYMMDD format | Foreign key |
| calendar_date | DATE | Actual date | Business logic |
| calendar_year | INT64 | Year (2014-2030) | Year-over-year analysis |
| calendar_quarter | INT64 | Quarter (1-4) | Quarterly reporting |
| calendar_month | INT64 | Month (1-12) | Monthly trends |
| calendar_day | INT64 | Day of month | Daily precision |
| day_of_week | STRING | 'Monday', etc. | Weekend vs weekday |
| is_weekend | BOOL | TRUE for Sat/Sun | Exclude weekends |
| academic_year | INT64 | 2015-2030 | Academic year (Aug start) |
| academic_semester | STRING | Fall/Spring/Summer | Term identification |
| fiscal_year | INT64 | 2015-2030 | Fiscal year (Jul start) |

**Note:** Pre-computed and denormalized for query performance

---

## ANALYTICS DATASET - FACT TABLES

### analytics.fact_enrollment
**Purpose:** Student course enrollments with performance
**Partitioned by:** academic_year
**Clustered by:** student_key, course_key, academic_year

| Column | Type | Description | Calculation |
|--------|------|-------------|-------------|
| enrollment_key | INT64 | Surrogate key | Auto-generated |
| student_key | INT64 | FK to dim_student | Join key |
| course_key | INT64 | FK to dim_course | Join key |
| academic_year | INT64 | Academic year | Partitioning key |
| academic_semester | STRING | Fall/Spring/Summer | Term identifier |
| date_enrolled | DATE | Enrollment date | Start date |
| date_completed | DATE | Completion date | End date |
| letter_grade | STRING | A-F or I | From source |
| grade_point | FLOAT64 | 0.0-4.0 numeric | GPA value |
| credits_earned | INT64 | Credits awarded | If passing |
| credits_attempted | INT64 | Credits taken | Course credits |
| is_passing | BOOL | Passing indicator | grade_point >= 2.0 |
| is_completed | BOOL | Completion flag | grade != 'I' |
| enrollment_status | STRING | Completed/In Progress/Dropped | Lifecycle status |

**Usage:** Joins to dim_student, dim_course, dim_date for enrollment analytics

---

### analytics.fact_student_performance
**Purpose:** Academic performance by student and term
**Partitioned by:** academic_year
**Clustered by:** student_key, academic_year

| Column | Type | Description | Calculation |
|--------|------|-------------|-------------|
| performance_key | INT64 | Surrogate key | Auto-generated |
| student_key | INT64 | FK to dim_student | Join key |
| academic_year | INT64 | Academic year | Partitioning key |
| semester_gpa | FLOAT64 | Term GPA | AVG(grade_point) by term |
| cumulative_gpa | FLOAT64 | Running GPA | SUM(grade_point * credits) / SUM(credits) |
| credits_completed | INT64 | Credits earned | SUM(credits_earned) |
| credits_attempted | INT64 | Credits taken | SUM(credits_attempted) |
| passing_courses | INT64 | Courses passed | COUNTIF(is_passing) |
| failing_courses | INT64 | Courses failed | COUNTIF(NOT is_passing) |
| academic_standing | STRING | Good/Probation/Dismissal | CASE WHEN cumulative_gpa >= 3.0 THEN 'Good'... |
| is_at_risk | BOOL | At-risk flag | cumulative_gpa < 2.0 OR failing_courses > 0 |
| degree_progress_pct | FLOAT64 | % toward degree | credits_completed / 120 |

**Usage:** Predictive analytics, intervention targeting, academic standing tracking

---

### analytics.fact_research_grant
**Purpose:** Research grant awards and outcomes
**Partitioned by:** grant_fiscal_year
**Clustered by:** pi_key, department_key, agency_key

| Column | Type | Description | Calculation |
|--------|------|-------------|-------------|
| grant_key | INT64 | Surrogate key | Auto-generated |
| grant_id | STRING | Natural key | From source |
| pi_key | INT64 | FK to dim_faculty | Principal Investigator |
| department_key | INT64 | FK to dim_department | PI's department |
| agency_key | INT64 | FK to dim_funding_agency | Funding source |
| award_amount | INT64 | Grant amount USD | From source |
| grant_start_date | DATE | Project start | From source |
| grant_end_date | DATE | Project end | From source |
| grant_duration_months | INT64 | Duration in months | DATE_DIFF(end_date, start_date) |
| current_grant_status | STRING | Active/Completed/Cancelled | From source |
| publication_count | INT64 | Publications produced | From source |
| citations_count | INT64 | Total citations | publication_count * 3 (estimated) |
| cost_per_publication | FLOAT64 | $/publication | award_amount / publication_count |
| grant_fiscal_year | INT64 | Fiscal year of award | YEAR(start_date) |

**Usage:** Research ROI analysis, faculty productivity, grant trend analysis

---

### analytics.fact_faculty_productivity
**Purpose:** Annual faculty performance scorecard
**Partitioned by:** academic_year
**Clustered by:** faculty_key, department_key, academic_year

| Column | Type | Description | Calculation |
|--------|------|-------------|-------------|
| productivity_key | INT64 | Surrogate key | Auto-generated |
| faculty_key | INT64 | FK to dim_faculty | Faculty member |
| department_key | INT64 | FK to dim_department | Department |
| academic_year | INT64 | Academic year | Year of measurement |
| total_grants_awarded | INT64 | Number of grants | COUNT(DISTINCT grant_key) |
| total_grant_dollars | INT64 | Total funding | SUM(award_amount) |
| avg_funding_per_faculty | INT64 | Average grant size | AVG(award_amount) |
| total_publications | INT64 | All publications | SUM(publication_count) |
| peer_reviewed_publications | INT64 | Peer-reviewed | total_publications * 0.8 |
| books_authored | INT64 | Books/chapters | total_publications * 0.1 |
| conference_presentations | INT64 | Conferences | total_publications * 0.1 |
| courses_taught | INT64 | Course count | COUNT(DISTINCT course_key) |
| students_advised | INT64 | Advisees | COUNT(DISTINCT student_key) |
| avg_course_rating | FLOAT64 | Teaching quality | AVG(avg_student_rating) |
| committee_assignments | INT64 | Service count | From HR data |
| professional_development_hours | INT64 | Development hours | From HR data |
| productivity_score | FLOAT64 | Weighted KPI | 0.5*research + 0.3*teaching + 0.2*service |
| peer_rank_percentile | FLOAT64 | % rank in department | PERCENT_RANK() by department |

**Usage:** Promotion decisions, resource allocation, compensation review

---

## AGGREGATE VIEWS

### v_enrollment_summary_by_major
Pre-aggregated enrollment metrics by major and academic year

### v_faculty_research_roi
Faculty research productivity and return on investment

### v_student_at_risk_indicators
Students flagged for intervention based on GPA and completion risk

### v_enrollment_retention_cohort
Cohort-level retention and graduation rates

---

## DATA LINEAGE SUMMARY

```
Source Systems:
├─ Student Information System (SIS)
│  └─ staging.students → analytics.dim_student → fact_enrollment, fact_student_performance
├─ Workday HR System
│  └─ staging.faculty → analytics.dim_faculty → fact_research_grant, fact_faculty_productivity
├─ Research Administration
│  └─ staging.grants → analytics.fact_research_grant
├─ Course Registration
│  ├─ staging.courses → analytics.dim_course
│  └─ staging.enrollments → analytics.fact_enrollment
└─ Pre-computed
   └─ analytics.dim_date (pre-computed for performance)
```

---

## COMPLIANCE & GOVERNANCE

### FERPA Masking
- Student names, SSN, email → Hashed pseudonymized IDs
- Faculty names, SSN → Hashed pseudonymized IDs
- All identifying PII removed from analytics layer
- Only approved demographic aggregates exposed

### Access Control (Role-Based)
- **Admin:** Full access to all tables
- **Faculty:** Access to own records and anonymized aggregates
- **Students:** Access to own academic records only
- **Registrar:** Full access to student data
- **Institutional Researcher:** Access to all anonymized/aggregated data

### Audit Logging
- All data access logged to `staging.data_access_log`
- Query hashes stored for audit trail
- Monthly compliance review
- Annual FERPA audit by legal team

### Retention Policy
- Student records: 7 years post-graduation
- Faculty records: 7 years post-departure
- Grant records: 10 years (federal requirement)
- Logs: 2 years

---

**Document Version:** 1.0  
**Last Updated:** July 16, 2026  
**Owner:** Data Analytics Engineering Team  
**Next Review:** October 16, 2026
