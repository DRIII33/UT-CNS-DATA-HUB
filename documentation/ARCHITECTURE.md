# UT CNS Data Analytics Engineering Portfolio Project

**Project Title:** Integrating Decentralized College of Natural Sciences Data into the UT Data Hub: A Cloud-Ready Analytics Platform

**Portfolio Context:** Data Analytics Engineer Role | College of Natural Sciences | UT Austin

**BigQuery Project ID:** driiiportfolio

---

## I. EXECUTIVE SUMMARY

This portfolio project demonstrates the end-to-end data engineering and analytics capabilities required for the **Data Analytics Engineer** position at the College of Natural Sciences. The project simulates a real-world scenario: integrating fragmented, decentralized data from multiple CNS domains (student enrollment, academic performance, research funding, faculty HR) into a unified, cloud-ready analytics platform that complies with university data governance standards (FERPA, privacy regulations).

### Problem Statement

The College of Natural Sciences operates with siloed data across multiple legacy systems:
- **Student Information System (SIS):** Enrollment, degree progress, demographics
- **HR/Payroll System (Workday):** Faculty employment, compensation, roles
- **Research Administration:** Grant funding, project assignments, publication records
- **Local Departmental Systems:** Spreadsheets, ad-hoc databases, shadow IT

**Business Impact:**
- CNS leadership cannot make data-driven decisions on enrollment trends, faculty productivity, or research ROI without manually aggregating reports.
- Compliance risk: Sensitive student data (FERPA-protected) is scattered across uncontrolled systems.
- Opportunity cost: Time spent on data collection/validation instead of analytics.

**Solution:**

Build a **production-grade, scalable data platform** that:
1. Orchestrates data extraction from multiple sources
2. Applies consistent business logic and data quality rules
3. Integrates with the UT Data Hub's centralized governance framework
4. Powers self-serve analytics dashboards (Power BI/Tableau)
5. Maintains compliance and auditability

---

## II. DATASET ARCHITECTURE

### Source Systems & Domains

#### Domain 1: Student Enrollment & Academic Performance
- **Source:** Simulated SIS extract
- **Fields:** Student ID, Cohort Year, Major, GPA, Enrollment Status, Degree Progress (%)
- **Volume:** 13,000 students | 10 years historical
- **Sensitivity:** FERPA-protected (PII + academic records)

#### Domain 2: Faculty & HR Data
- **Source:** Simulated Workday export
- **Fields:** Faculty ID, Department, Rank (Assistant/Associate/Full Prof), Hire Date, Compensation, Employment Status
- **Volume:** 700+ faculty | 5 years historical
- **Sensitivity:** Confidential (compensation data)

#### Domain 3: Research & Grants
- **Source:** Simulated research administration database
- **Fields:** Grant ID, PI (Faculty ID), Award Amount, Funding Agency, Start/End Date, Department
- **Volume:** 2,000+ active grants
- **Sensitivity:** Internal use (some external reporting requirements)

#### Domain 4: Course & Teaching Performance
- **Source:** Simulated course registry + student evaluations
- **Fields:** Course ID, Instructor (Faculty ID), Semester, Enrollment, Avg Rating, Pass Rate
- **Volume:** 500+ courses/semester
- **Sensitivity:** FERPA-protected (student performance)

---

## III. METHODOLOGY

### Data Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│           UPSTREAM LEGACY SYSTEMS                       │
│  (SIS, Workday, Research DB, Local Spreadsheets)       │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│     EXTRACTION LAYER (Python ETL Scripts)              │
│  - Read from APIs/CSV/Database connections             │
│  - Initial validation & schema inference               │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│   STAGING LAYER (BigQuery Raw Dataset)                 │
│  - Immutable landing zone                              │
│  - Timestamp all ingestion events                       │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│   TRANSFORMATION LAYER (SQL + dbt)                      │
│  - Business logic implementation                        │
│  - Data quality rules & validation                      │
│  - PII masking & compliance enforcement                │
│  - Conformed dimensions & fact tables                   │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│   ANALYTICS LAYER (BigQuery Datasets)                   │
│  - Aggregated metrics & KPIs                            │
│  - Pre-computed summaries for BI tools                  │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│   CONSUMPTION LAYER (Dashboards & Reports)             │
│  - Power BI / Tableau Dashboards                        │
│  - Ad-hoc SQL queries for analysts                      │
│  - Exported reports for stakeholders                    │
└─────────────────────────────────────────────────────────┘
```

### Key Techniques

1. **Data Quality Framework:**
   - Completeness checks (null/missing fields)
   - Uniqueness validation (duplicate detection)
   - Referential integrity (foreign key validation)
   - Business logic validation (e.g., GPA ranges, date logic)
   - Automated data quality reporting

2. **Business Logic Implementation:**
   - Enrollment status classification (Active/Inactive/Graduated)
   - Faculty productivity scoring (publications per grant $)
   - Research ROI calculation (outcomes per award)
   - Student success metrics (on-time graduation, GPA improvements)

3. **Compliance & Governance:**
   - FERPA masking for PII (pseudonymization via hash IDs)
   - Role-based access control (RBAC) - simulated via SQL views
   - Audit logging (who accessed what, when)
   - Data lineage tracking (source → transform → output)

4. **Performance Optimization:**
   - Materialized views for common aggregations
   - Partitioning by date/department for faster queries
   - Clustering on frequently filtered columns
   - Query optimization for BI tool compatibility

---

## IV. DELIVERABLES MAPPING TO JOB REQUIREMENTS

| Job Responsibility | Deliverable | Location |
|---|---|---|
| Develops, codes, validates relational databases | Snowflake/BigQuery schema definitions + DDL scripts | `/sql/schema_definitions.sql` |
| Collaborates to collect business requirements | Requirements documentation + stakeholder impact analysis | `/documentation/BUSINESS_REQUIREMENTS.md` |
| Locates, cleans, orchestrates source data | Python ETL scripts + data quality checks | `/python/etl_pipeline.py` |
| Translates business logic into SQL | Transformation queries + stored procedures | `/sql/transformations/` |
| Designs database structures for BI | Star schema design + fact/dimension tables | `/sql/schema_definitions.sql` |
| Best practices: validation, testing, version control | Unit tests + CI/CD pipeline definition | `/tests/` + `.github/workflows/` |
| Special projects & ad hoc requests | Dynamic SQL templates + query patterns | `/sql/ad_hoc_query_templates.sql` |
| Communicates with cross-functional teams | Project documentation + stakeholder communication plan | `/documentation/` |
| Develops institutional knowledge | Data dictionary + process documentation | `/documentation/DATA_DICTIONARY.md` |

---

## V. TECHNOLOGY STACK

| Layer | Technology | Rationale |
|---|---|---|
| Cloud Data Platform | Google BigQuery (Free Tier) | Serverless, ANSI SQL, cost-effective, UT Austin compatible |
| Data Extraction | Python 3.10+ | Flexible, industry standard for ETL |
| Data Transformation | SQL (BigQuery) + dbt (optional) | SQL for business logic; dbt for modularity |
| Data Quality | Great Expectations (Python) | Open-source, framework-agnostic |
| BI & Visualization | Looker / Power BI / Tableau (simulated) | Widely used in enterprise & higher ed |
| Version Control | Git + GitHub | Required for production data engineering |
| Orchestration | Apache Airflow (simulated) or Cloud Scheduler | Production pipeline automation |
| Compliance | Custom audit logging + encryption | FERPA/privacy compliance |

---

## VI. PROJECT STRUCTURE

```
UT-CNS-DATA-HUB/
├── README.md                          # Main project guide
├── PROJECT_OVERVIEW.md                # This file
├── BUSINESS_REQUIREMENTS.md           # Functional requirements
├── DATA_DICTIONARY.md                 # Column definitions
│
├── python/
│   ├── requirements.txt               # Python dependencies
│   ├── etl_pipeline.py                # Main ETL orchestration
│   ├── data_generators.py             # Synthetic data generation
│   ├── data_quality.py                # Validation & quality checks
│   └── config.py                      # Configuration (API keys, project IDs)
│
├── sql/
│   ├── schema_definitions.sql         # DDL: Create all tables
│   ├── transformations/
│   │   ├── 01_staging_views.sql       # Raw data staging
│   │   ├── 02_dim_tables.sql          # Dimension tables (students, faculty, etc.)
│   │   ├── 03_fact_tables.sql         # Fact tables (enrollments, grants, etc.)
│   │   └── 04_metrics_views.sql       # Pre-aggregated metrics & KPIs
│   ├── data_quality_checks.sql        # Validation queries
│   └── ad_hoc_query_templates.sql     # Common analytical queries
│
├── tests/
│   ├── test_data_quality.py           # Unit tests for validation rules
│   ├── test_business_logic.py         # Tests for metric calculations
│   └── test_sql_transformations.py    # SQL query validation
│
├── dashboards/
│   ├── enrollment_analytics.json      # Looker/BI dashboard config
│   ├── faculty_productivity.json      # Faculty metrics dashboard
│   └── research_roi_analysis.json     # Research funding dashboard
│
├── documentation/
│   ├── ARCHITECTURE.md                # System design & data flows
│   ├── GOVERNANCE.md                  # Compliance & access control
│   ├── DEPLOYMENT.md                  # Setup & deployment guide
│   └── TROUBLESHOOTING.md             # Common issues & solutions
│
├── .github/workflows/
│   ├── etl_pipeline.yml               # Automated ETL execution
│   └── data_quality_checks.yml        # Automated validation runs
│
└── .gitignore                         # Exclude sensitive files
```

---

## VII. KEY METRICS & SUCCESS INDICATORS

### Operational Metrics
- **Pipeline Uptime:** Target 99.5% (automated monitoring)
- **Data Freshness:** Daily updates, <4 hour latency
- **Quality Score:** 99.9% records passing validation

### Business Metrics
- **Dashboard Adoption:** Tracked via BI tool usage logs
- **Decision Velocity:** Time from data request → insight delivery (target: <2 days)
- **Compliance:** Zero FERPA violations, 100% audit trail completion

### Technical Metrics
- **Query Performance:** 95% of BI queries complete in <5 seconds
- **Data Volume:** Support 13K+ students, 700+ faculty, 10+ years historical
- **Scalability:** Add new data sources without re-architecture

---

## VIII. EXPECTED OUTCOMES

Upon completion, this portfolio project demonstrates:

✅ **SQL Mastery:** Complex queries, optimization, business logic translation  
✅ **Python Proficiency:** ETL development, data manipulation, automation  
✅ **Data Engineering:** Schema design, pipeline development, data quality  
✅ **Business Acumen:** Requirements gathering, stakeholder communication  
✅ **Compliance Knowledge:** FERPA, data governance, audit trails  
✅ **Cloud Platforms:** BigQuery, data warehouse design, cost optimization  
✅ **BI Tool Integration:** Dashboard design, KPI definition, user adoption  

---

## IX. NEXT STEPS

1. Review `BUSINESS_REQUIREMENTS.md` for detailed functional specifications
2. Run `python/data_generators.py` to create synthetic datasets
3. Execute `sql/schema_definitions.sql` to create BigQuery tables
4. Run ETL via `python/etl_pipeline.py`
5. Validate data quality with tests in `/tests/`
6. Build dashboards using configs in `/dashboards/`
7. Review documentation for deployment to production

---

**Project Status:** ✅ Portfolio Ready  
**Last Updated:** July 16, 2026  
**Analyst:** DRIII33 Portfolio Team
