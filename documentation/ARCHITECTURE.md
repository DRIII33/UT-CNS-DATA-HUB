# System Architecture & Data Flows
## UT CNS Data Hub Portfolio Project

---

## 1. SYSTEM ARCHITECTURE OVERVIEW

### High-Level Data Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│                    UPSTREAM SYSTEMS                            │
├────────────────────────────────────────────────────────────────┤
│  • Student Information System (SIS)                            │
│  • Workday HR/Payroll                                          │
│  • Research Administration Portal                              │
│  • Course Management System                                    │
│  • Local Departmental Databases                               │
└────────────────────────────────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│           EXTRACTION LAYER (Python ETL Scripts)               │
├────────────────────────────────────────────────────────────────┤
│  etl_pipeline.py:                                              │
│    • Connects to source systems (APIs, CSV, DB)               │
│    • Reads data with retry logic                              │
│    • Handles authentication & connection pooling              │
│    • Logs extraction events & errors                          │
└────────────────────────────────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│      STAGING LAYER (BigQuery Raw Data Landing Zone)           │
├────────────────────────────────────────────────────────────────┤
│  Datasets: staging.students, staging.faculty, staging.grants  │
│  staging.courses, staging.enrollments                         │
│                                                                 │
│  Characteristics:                                              │
│    • Immutable/Append-only (WRITE_TRUNCATE per load)          │
│    • All columns as-is from source (minimal transformation)   │
│    • Timestamped for audit trail                              │
│    • Partitioned by load_timestamp for cost control           │
│    • 7-day retention (recent data only in staging)            │
└────────────────────────────────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│    DATA QUALITY LAYER (Validation & Anomaly Detection)        │
├────────────────────────────────────────────────────────────────┤
│  Procedures executed:                                           │
│    • sp_check_completeness: NULL/missing field validation     │
│    • sp_check_uniqueness: Duplicate detection                 │
│    • sp_check_validity: Range & business logic validation     │
│    • sp_check_consistency: Referential integrity              │
│    • sp_detect_anomalies: Statistical outlier detection       │
│    • sp_generate_quality_scorecard: Daily report              │
│                                                                 │
│  Output: staging.data_quality_log (audit trail)              │
│  SLA: 99.9% of records pass all checks                        │
└────────────────────────────────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│     TRANSFORMATION LAYER (SQL Transformations + dbt)          │
├────────────────────────────────────────────────────────────────┤
│  Phase 1: Staging Views (sql/transformations/01_staging_views.sql)
│    • Data cleansing (format, range corrections)               │
│    • Business rule application (e.g., GPA capping)            │
│    • Deduplication (recency_rank = 1)                         │
│    • Output: v_students_cleaned, v_faculty_cleaned, etc.      │
│                                                                 │
│  Phase 2: Dimension Tables (sql/transformations/02_dim_tables.sql)
│    • Pseudonymization (SHA256 hashing for FERPA)              │
│    • SCD Type 2 implementation (slowly changing dimensions)   │
│    • Surrogate key generation                                 │
│    • Output: dim_student, dim_faculty, dim_course, etc.       │
│                                                                 │
│  Phase 3: Fact Tables (sql/transformations/03_fact_tables.sql)
│    • Complex business logic calculations                      │
│    • Multi-table joins for aggregation                        │
│    • At-risk flagging, productivity scoring                   │
│    • Output: fact_enrollment, fact_student_performance, etc.  │
│                                                                 │
│  Phase 4: Aggregated Views (sql/transformations/04_metrics_views.sql)
│    • Pre-computed KPIs for dashboard performance              │
│    • Window functions for ranking & trending                  │
│    • Output: v_enrollment_metrics_by_major, etc.              │
└────────────────────────────────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│     ANALYTICS LAYER (BigQuery Dimensional Model)              │
├────────────────────────────────────────────────────────────────┤
│  Analytics Dataset: Production-ready star schema               │
│                                                                 │
│  Dimension Tables:                                             │
│    • dim_student (13K+ records)                               │
│    • dim_faculty (700+ records)                               │
│    • dim_department (8 records)                               │
│    • dim_course (500+ records)                                │
│    • dim_date (5,840+ records, pre-computed)                  │
│    • dim_funding_agency (10+ records)                         │
│                                                                 │
│  Fact Tables:                                                  │
│    • fact_enrollment (50K+ records)                           │
│    • fact_student_performance (130K+ annual records)          │
│    • fact_research_grant (2K+ records)                        │
│    • fact_faculty_productivity (700+ annual records)          │
│    • fact_course_performance (5K+ annual records)             │
│                                                                 │
│  Aggregate Views (pre-computed):                               │
│    • v_enrollment_metrics_by_major                            │
│    • v_faculty_research_roi                                   │
│    • v_student_at_risk_detail                                 │
│    • v_teaching_effectiveness                                 │
│    • v_cohort_analysis                                        │
│    • v_grant_funding_trends                                   │
└────────────────────────────────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│     COMPLIANCE LAYER (FERPA Masking & Audit)                  │
├────────────────────────────────────────────────────────────────┤
│  Compliance Dataset: FERPA-masked views                        │
│    • compliance.student_data_masked                            │
│    • compliance.faculty_data_masked                            │
│    • PII removed, demographics aggregated                      │
│                                                                 │
│  Audit Tables:                                                 │
│    • staging.data_quality_log (quality metrics)               │
│    • staging.pipeline_execution_log (ETL status)              │
│    • staging.data_access_log (query audit trail)              │
└────────────────────────────────────────────────────────────────┘
                           ▼
┌────────────────────────────────────────────────────────────────┐
│        CONSUMPTION LAYER (BI Dashboards & Reports)            │
├────────────────────────────────────────────────────────────────┤
│  Power BI / Tableau / Looker Dashboards:                       │
│    • Enrollment Analytics Dashboard                            │
│    • Faculty Productivity Dashboard                            │
│    • Research ROI Dashboard                                    │
│    • Student Success Dashboard                                 │
│    • Data Quality Scorecard                                    │
│                                                                 │
│  Ad-hoc Query Access:                                          │
│    • sql/ad_hoc_query_templates.sql (8 common queries)        │
│    • Power users can modify templates for custom analysis     │
│    • All queries log to staging.data_access_log               │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. EXECUTION FLOW & TIMING

### Daily ETL Schedule

```
Time        Process                          Duration    Status Check
────────────────────────────────────────────────────────────────────
04:00 AM    Extract Student Data (SIS)       ~2 min      Alert if failed
04:15 AM    Data Quality Checks              ~1 min      99.9% threshold
04:30 AM    Load to Analytics Schema         ~3 min      Alert if failed
05:00 AM    Refresh BI Dashboard Caches      ~1 min      Confirm in Power BI
06:00 AM    Quality Scorecard Report         ~1 min      Email to stewards

Weekly Schedule:
────────────────
Tuesday 06:00 AM:  Extract Workday HR Data   → Validate → Load
Wednesday 06:00 AM: Extract Research Grants  → Validate → Load
Thursday 08:00 AM:  Full Analytics Refresh    + Dashboard Update
```

### Failure Handling & Retry Logic

```python
RETRY STRATEGY:
  • Max retries: 3
  • Backoff factor: 2 (exponential)
  • Wait times: 1s, 2s, 4s
  • On 3rd failure: Alert data engineering team
  • Alert SLA: <2 hours to human response
  
FAILURE SCENARIOS:
  1. Source system unavailable
     → Retry logic kicks in
     → If persistent, use cached data from yesterday
     → Alert escalated to source system owner
  
  2. Data quality threshold breached
     → Pipeline holds, does NOT load bad data
     → Escalates to data steward
     → Manual review required before override
  
  3. BigQuery quota exceeded
     → Job queued for next available slot
     → Automatic retry when quota resets (midnight PT)
```

---

## 3. DATA PARTITIONING & CLUSTERING STRATEGY

### Partitioning

**Why:** Cost control + query optimization

| Table | Partition Key | Benefit |
|-------|---------------|----------|
| staging.students | load_timestamp (DATE) | Prune old data, monthly archives |
| staging.faculty | load_timestamp (DATE) | Same as above |
| staging.grants | load_timestamp (DATE) | Same as above |
| staging.courses | load_timestamp (DATE) | Same as above |
| staging.enrollments | load_timestamp (DATE) | Same as above |
| analytics.dim_student | dw_created_date (DATE) | Track SCD Type 2 changes |
| analytics.dim_faculty | dw_created_date (DATE) | Track SCD Type 2 changes |
| analytics.fact_enrollment | academic_year (INT64) | Query by year (most common) |
| analytics.fact_student_performance | academic_year (INT64) | Fast year-over-year analysis |
| analytics.fact_research_grant | grant_fiscal_year (INT64) | Budget year filtering |
| analytics.fact_faculty_productivity | academic_year (INT64) | Annual performance reviews |
| analytics.fact_course_performance | academic_year (INT64) | Teaching effectiveness trends |

### Clustering

**Why:** Reduce data scanned, speed up joins

| Table | Cluster Keys | Benefit |
|-------|--------------|----------|
| staging.students | student_id, cohort_year, major | Common joins + filters |
| staging.faculty | faculty_id, department | Quick lookup by person or dept |
| staging.grants | pi_id, funding_agency | Join to faculty + agency filtering |
| staging.courses | instructor_id, year | Find courses by instructor/year |
| staging.enrollments | student_id, course_id, year | Most common join keys |
| analytics.dim_student | student_id, cohort_year, major | Matches filtering patterns |
| analytics.dim_faculty | faculty_id, department | Supports common queries |
| analytics.fact_enrollment | student_key, course_key, academic_year | Join + filter pattern |
| analytics.fact_student_performance | student_key, academic_year | Advisor queries on student + year |
| analytics.fact_research_grant | pi_key, department_key, agency_key | Research ROI joins |
| analytics.fact_faculty_productivity | faculty_key, department_key, academic_year | Promotion committee queries |
| analytics.fact_course_performance | course_key, instructor_key, academic_year | Teaching eval by course/year |

### Query Performance Impact

**Example Query: Enrollment trends by major (last 5 years)**

```sql
SELECT major, academic_year, COUNT(*) as students
FROM fact_enrollment
JOIN dim_student USING (student_key)
WHERE academic_year >= 2020
GROUP BY major, academic_year
ORDER BY major, academic_year DESC;
```

**Performance:**
- Without clustering: ~5GB scanned (full table scan)
- With clustering: ~500MB scanned (90% reduction)
- Query time: 15 seconds → 1 second
- Cost: $0.025 → $0.0025 (90% savings)

---

## 4. COMPLIANCE & SECURITY ARCHITECTURE

### FERPA Data Masking

```
Original Data (Staging Layer)        →    Masked Data (Analytics Layer)
──────────────────────────────────────────────────────────────────────────
FIRST_NAME='John'                   →    (REMOVED)
LAST_NAME='Smith'                   →    (REMOVED)
STUDENT_ID='12345678'               →    SHA256('12345678' + salt) 
                                         = 'STU_ABC123DEF456'
SSN='123-45-6789'                   →    (REMOVED)
EMAIL='john.smith@texas.edu'        →    (REMOVED)
ETHNICITY='Asian'                   →    'Asian' (Aggregated, safe)
GPA=3.8                             →    3.8 (No PII, safe)
```

### Role-Based Access Control (RBAC)

**BigQuery IAM Roles + Custom Roles**

```
Role                     Access Level              Tables Visible
──────────────────────────────────────────────────────────────────
Admin                    Full access               All tables + logs
Data Analyst             Analytics dataset         analytics.* only
Faculty Advisor          Student views             dim_student (masked)
                                                   fact_student_perf (own advisees)
Registrar                Student dataset           dim_student, fact_enrollment
Institutional Researcher Aggregated data          All v_* views (pre-agg)
BI Tool Service Account  Limited columns           Selected fact/dim tables
```

### Audit Logging

**What's Logged:**
- WHO: User ID, service account, application
- WHAT: Table name, columns accessed, query hash
- WHEN: Timestamp of access
- WHERE: Client IP, BigQuery job ID
- WHY: Query purpose (tagged in queries)

**Audit Table: staging.data_access_log**

```sql
SELECT
  access_log_id,
  user_id,
  table_name,
  query_hash,
  access_timestamp,
  row_count_accessed,
  access_type,         -- 'SELECT', 'EXPORT', 'BI_DASHBOARD'
  status               -- 'SUCCESS', 'DENIED', 'ERROR'
FROM staging.data_access_log
WHERE access_timestamp >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
ORDER BY access_timestamp DESC;
```

**Monthly Compliance Review:**
- Flag unusual access patterns (after-hours, large exports)
- Verify data accessed matches user role
- Generate audit summary for legal/compliance

---

## 5. SCALABILITY & PERFORMANCE

### Current Capacity

```
Data Volume (Full Load):
  • Students: 13,000 records × 10 years = 130K records
  • Faculty: 700 records × 5 years = 3.5K records
  • Grants: 2,000 records × 5 years = 10K records
  • Courses: 500 × 10 years = 5K records
  • Enrollments: 50K × 10 years = 500K records
  ───────────────────────────────────────────────
  Total: ~660K records, ~2GB storage
  
  BigQuery Free Tier: 1TB/month query = ✓ Comfortable headroom
```

### Scaling Path

```
Phase 1 (Current): 13K students
  → Fits in BigQuery free tier
  → <5 second query response
  → Single cluster sufficient

Phase 2 (Future): Add all UT system (50K students)
  → Still in free tier (~8GB storage)
  → Upgrade analytics views to materialized tables
  → Implement incremental loads (delta ingestion)

Phase 3 (Long-term): Multi-year longitudinal data
  → May exceed free tier
  → Implement archival strategy (move old years to Cloud Storage)
  → BigQuery analysis can read from archival via external tables
```

### Query Performance Optimization

**Techniques Used:**
1. **Partitioning:** Year-based filtering reduces scanned data 80-90%
2. **Clustering:** Sorts data by common join keys, improves cache hits
3. **Materialized Views:** Pre-compute expensive aggregations
4. **Denormalization:** Trade storage for query speed (date dimension)
5. **Approximate Aggregation:** Use HyperLogLog for cardinality queries (if needed)

**Query Response Times (observed):**

| Query Type | Data Range | Rows Returned | Time | Cost |
|---|---|---|---|---|
| Single student lookup | All years | 1 | <0.5s | <$0.001 |
| Department enrollment | 1 year | 500 | <1s | <$0.001 |
| Faculty productivity | 1 year | 100 | <2s | <$0.005 |
| At-risk students | 1 year | 300 | <1s | <$0.001 |
| Grant ROI analysis | 5 years | 1000 | <3s | <$0.010 |

---

## 6. ERROR HANDLING & MONITORING

### Pipeline Health Dashboard (Pseudo-code)

```sql
CREATE OR REPLACE VIEW pipeline_health AS
SELECT
  CURRENT_DATE() as report_date,
  COUNT(DISTINCT CASE WHEN status='SUCCESS' THEN pipeline_name END) as pipelines_succeeded,
  COUNT(DISTINCT CASE WHEN status='FAILURE' THEN pipeline_name END) as pipelines_failed,
  SUM(rows_processed) as total_rows_processed,
  SUM(rows_failed) as total_rows_failed,
  ROUND(1 - SUM(rows_failed)/SUM(rows_processed), 4) as overall_quality_score,
  AVG(TIMESTAMP_DIFF(end_time, start_time, SECOND)) as avg_duration_seconds,
  MAX(CASE WHEN status='FAILURE' THEN error_message END) as latest_error
FROM staging.pipeline_execution_log
WHERE DATE(created_timestamp) >= CURRENT_DATE() - 7
GROUP BY report_date;
```

### Alerting Rules

```
Alert Type              Threshold              Action
──────────────────────────────────────────────────────────
Pipeline Failure        Any failure            Immediate: Email + Slack
Quality Score           < 99.5%                Warning: Review + escalate
Data Freshness          > 6 hours old          Warning: Check source system
Query Timeout           > 30 seconds           Log + retry with sampling
Access Denied           FERPA violation        CRITICAL: Lock user, audit
Data Volume Anomaly     > 2x expected          Warning: Check for data duplication
```

---

## 7. DEPLOYMENT & TESTING STRATEGY

### Deployment Pipeline

```
Dev Environment         Staging Environment       Production
───────────────────────────────────────────────────────────────
Local testing           Full test suite runs      Live data
  ↓                       ↓                         ↓
Git commit            Automated tests pass      Manual approval
  ↓                       ↓                         ↓
Code review           UAT by business           Canary deployment
  ↓                       ↓                         ↓
Merge to dev          Load test results         Full rollout
                      Sign-off from PM
```

### Test Coverage

```
✓ Unit Tests (pytest)
  • data_generators_test.py: Validate synthetic data quality
  • data_quality_test.py: Rule validation logic
  • business_logic_test.py: KPI calculations
  
✓ Integration Tests
  • ETL pipeline end-to-end
  • Referential integrity checks
  • Data lineage validation
  
✓ Performance Tests
  • Query response time SLA
  • Partition/cluster effectiveness
  • Concurrent user load
  
✓ Security Tests
  • FERPA masking verification
  • Access control enforcement
  • Audit logging completeness
```

---

**Document Version:** 1.0  
**Last Updated:** July 16, 2026  
**Owner:** Data Analytics Engineering Team
