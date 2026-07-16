"""
Configuration Module for UT CNS Data Hub
Portfolio Project: Data Analytics Engineer Role
Manages all environment variables and project settings
"""

import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# GCP & BIGQUERY CONFIGURATION
# ============================================================================

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "driiiportfolio")
GCP_REGION = os.getenv("GCP_REGION", "US")

# BigQuery Dataset Configuration
DATASET_STAGING = "staging"
DATASET_ANALYTICS = "analytics"
DATASET_COMPLIANCE = "compliance"

# ============================================================================
# TABLE NAMES (STAGING LAYER)
# ============================================================================

STAGING_TABLES = {
    "students": f"{GCP_PROJECT_ID}.{DATASET_STAGING}.students",
    "faculty": f"{GCP_PROJECT_ID}.{DATASET_STAGING}.faculty",
    "grants": f"{GCP_PROJECT_ID}.{DATASET_STAGING}.grants",
    "courses": f"{GCP_PROJECT_ID}.{DATASET_STAGING}.courses",
    "enrollments": f"{GCP_PROJECT_ID}.{DATASET_STAGING}.enrollments",
    "data_quality_log": f"{GCP_PROJECT_ID}.{DATASET_STAGING}.data_quality_log",
    "pipeline_execution_log": f"{GCP_PROJECT_ID}.{DATASET_STAGING}.pipeline_execution_log",
    "data_access_log": f"{GCP_PROJECT_ID}.{DATASET_STAGING}.data_access_log",
}

# ============================================================================
# TABLE NAMES (ANALYTICS LAYER - DIMENSION TABLES)
# ============================================================================

ANALYTICS_DIM_TABLES = {
    "dim_student": f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.dim_student",
    "dim_faculty": f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.dim_faculty",
    "dim_department": f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.dim_department",
    "dim_course": f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.dim_course",
    "dim_date": f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.dim_date",
    "dim_funding_agency": f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.dim_funding_agency",
}

# ============================================================================
# TABLE NAMES (ANALYTICS LAYER - FACT TABLES)
# ============================================================================

ANALYTICS_FACT_TABLES = {
    "fact_enrollment": f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.fact_enrollment",
    "fact_student_performance": f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.fact_student_performance",
    "fact_research_grant": f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.fact_research_grant",
    "fact_faculty_productivity": f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.fact_faculty_productivity",
    "fact_course_performance": f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.fact_course_performance",
}

# ============================================================================
# TABLE NAMES (COMPLIANCE LAYER)
# ============================================================================

COMPLIANCE_TABLES = {
    "student_data_masked": f"{GCP_PROJECT_ID}.{DATASET_COMPLIANCE}.student_data_masked",
    "faculty_data_masked": f"{GCP_PROJECT_ID}.{DATASET_COMPLIANCE}.faculty_data_masked",
}

# ============================================================================
# SYNTHETIC DATA GENERATION PARAMETERS
# ============================================================================

# Student Population
NUM_STUDENTS = 13000
STUDENT_COHORT_YEARS = list(range(2016, 2027))  # 2016-2026
STUDENT_GPA_MEAN = 3.25
STUDENT_GPA_STD = 0.45

# Faculty Population
NUM_FACULTY = 700
FACULTY_HIRE_YEARS = list(range(2000, 2026))  # 2000-2025
FACULTY_SALARY_MIN = 65000
FACULTY_SALARY_MAX = 450000

# Research Grants
NUM_GRANTS = 2000
GRANT_AWARD_MIN = 5000
GRANT_AWARD_MAX = 5000000
GRANT_YEARS = list(range(2018, 2026))  # 2018-2025

# Courses
NUM_COURSES = 500
COURSES_PER_SEMESTER = 500
SEMESTERS = ["Fall", "Spring", "Summer"]
COURSE_YEARS = list(range(2016, 2027))

# Enrollments
ENROLLMENTS_PER_STUDENT_PER_YEAR = 4
TOTAL_COURSES_IN_DEGREE = 120

# Major Disciplines (College of Natural Sciences)
MAJORS = [
    "Biology",
    "Chemistry",
    "Physics",
    "Mathematics",
    "Statistics",
    "Astronomy",
    "Geology",
    "Marine Science",
    "Environmental Science",
    "Neuroscience",
]

DEPARTMENTS = [
    "Department of Biology",
    "Department of Chemistry",
    "Department of Physics",
    "Department of Mathematics",
    "Department of Statistics",
    "Department of Astronomy",
    "Department of Geological Sciences",
    "Marine Science Institute",
]

# Faculty Ranks
FACULTY_RANKS = [
    "Assistant Professor",
    "Associate Professor",
    "Full Professor",
    "Lecturer",
    "Adjunct",
]

TENURE_STATUSES = ["Tenured", "Tenure-Track", "Non-Tenure-Track"]

# Funding Agencies
FUNDING_AGENCIES = [
    "NSF",  # National Science Foundation
    "NIH",  # National Institutes of Health
    "DOE",  # Department of Energy
    "USDA",  # US Department of Agriculture
    "DOD",  # Department of Defense
    "EPA",  # Environmental Protection Agency
    "DOC",  # Department of Commerce
    "Private Foundation",
    "Industrial Partner",
]

# ============================================================================
# DATA QUALITY CONFIGURATION
# ============================================================================

# Quality Thresholds
DATA_QUALITY_THRESHOLDS = {
    "completeness_threshold": 0.95,  # 95% records should be complete
    "uniqueness_threshold": 0.98,  # 98% records should be unique
    "validity_threshold": 0.99,  # 99% records should be valid
    "consistency_threshold": 0.97,  # 97% records should be consistent
}

# Null Value Handling
NULL_THRESHOLD = 0.10  # Flag column if >10% nulls

# Duplicate Detection
DUPLICATE_CHECK_KEYS = {
    "students": ["student_id"],
    "faculty": ["faculty_id"],
    "grants": ["grant_id"],
    "courses": ["course_id"],
    "enrollments": ["enrollment_id"],
}

# ============================================================================
# ETL PIPELINE CONFIGURATION
# ============================================================================

# Retry Configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: 1s, 2s, 4s
RETRY_WAIT_SECONDS = 1

# Batch Processing
BATCH_SIZE = 10000  # Records per batch
CHUNK_SIZE = 1000  # Rows per insert to BigQuery

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "logs/etl_pipeline.log"

# ============================================================================
# DATA RETENTION POLICIES
# ============================================================================

DATA_RETENTION_DAYS = {
    "staging": 7,  # Keep staging data for 7 days
    "pipeline_logs": 60,  # Keep logs for 60 days
    "student_records": 2555,  # 7 years after graduation
    "faculty_records": 2555,  # 7 years after departure
    "grant_records": 3650,  # 10 years (federal requirement)
}

# ============================================================================
# FERPA COMPLIANCE CONFIGURATION
# ============================================================================

# PII Fields that must be masked
PII_FIELDS = ["first_name", "last_name", "ssn", "email", "phone"]

# Salt for pseudonymization (in production, load from secure store)
FERPA_SALT = os.getenv("FERPA_SALT", "ut_cns_ferpa_salt_default")

# Approved Demographic Categories (aggregation-safe)
APPROVED_ETHNICITIES = [
    "Asian",
    "Black",
    "Hispanic",
    "Native American",
    "Non-Resident Alien",
    "Two or More Races",
    "White",
    "Unknown",
]

# ============================================================================
# TESTING CONFIGURATION
# ============================================================================

# Test Data Parameters
TEST_NUM_STUDENTS = 100
TEST_NUM_FACULTY = 50
TEST_NUM_GRANTS = 50
TEST_NUM_COURSES = 20
TEST_NUM_ENROLLMENTS = 500

# Test Database (use staging for integration tests)
TEST_DATASET = "staging"

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

# BigQuery Query Configuration
BQ_QUERY_TIMEOUT_SECONDS = 300  # 5 minute timeout
BQ_MAX_RESULTS = 100000

# Clustering Optimization
USE_CLUSTERING = True
USE_PARTITIONING = True

# Pre-computed View Refresh Interval (hours)
VIEW_REFRESH_INTERVAL_HOURS = 4

# ============================================================================
# MONITORING & ALERTING
# ============================================================================

# Alert Thresholds
ALERT_THRESHOLDS = {
    "pipeline_failure": True,  # Alert on any failure
    "quality_score_below": 0.995,  # Alert if quality < 99.5%
    "data_freshness_hours": 6,  # Alert if data >6 hours old
    "query_timeout": 30,  # Alert if queries > 30 seconds
}

# Alert Recipients (in production)
ALERT_EMAIL_RECIPIENTS = [
    "data-team@cns.utexas.edu",
    "data-engineering@utexas.edu",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_table_name(layer: str, table: str) -> str:
    """
    Get fully qualified BigQuery table name.
    
    Args:
        layer: 'staging', 'analytics', or 'compliance'
        table: Table name
        
    Returns:
        Fully qualified table name: project.dataset.table
    """
    if layer == "staging":
        return STAGING_TABLES.get(table, f"{GCP_PROJECT_ID}.{DATASET_STAGING}.{table}")
    elif layer == "analytics_dim":
        return ANALYTICS_DIM_TABLES.get(table, f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.{table}")
    elif layer == "analytics_fact":
        return ANALYTICS_FACT_TABLES.get(table, f"{GCP_PROJECT_ID}.{DATASET_ANALYTICS}.{table}")
    elif layer == "compliance":
        return COMPLIANCE_TABLES.get(table, f"{GCP_PROJECT_ID}.{DATASET_COMPLIANCE}.{table}")
    else:
        raise ValueError(f"Unknown layer: {layer}")


def get_all_tables() -> Dict[str, List[str]]:
    """Return all configured tables by layer."""
    return {
        "staging": list(STAGING_TABLES.keys()),
        "analytics_dim": list(ANALYTICS_DIM_TABLES.keys()),
        "analytics_fact": list(ANALYTICS_FACT_TABLES.keys()),
        "compliance": list(COMPLIANCE_TABLES.keys()),
    }


if __name__ == "__main__":
    # Test configuration
    print(f"GCP Project: {GCP_PROJECT_ID}")
    print(f"Staging Dataset: {DATASET_STAGING}")
    print(f"Analytics Dataset: {DATASET_ANALYTICS}")
    print(f"Compliance Dataset: {DATASET_COMPLIANCE}")
    print(f"\nAll Tables: {get_all_tables()}")
