"""
Utility Functions for UT CNS Data Hub
Helper functions for database operations, logging, and data transformations
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from functools import wraps
import time

import pandas as pd
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

logger = logging.getLogger("ETL_Pipeline")


# ============================================================================
# BIGQUERY UTILITIES
# ============================================================================

class BigQueryClient:
    """Wrapper around BigQuery client with utility methods."""

    def __init__(self, project_id: str):
        """
        Initialize BigQuery client.
        
        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        try:
            self.client = bigquery.Client(project=project_id)
            logger.info(f"BigQuery client initialized for project: {project_id}")
        except DefaultCredentialsError:
            logger.error("Could not authenticate to BigQuery. Ensure GOOGLE_APPLICATION_CREDENTIALS is set.")
            raise

    def table_exists(self, dataset_id: str, table_id: str) -> bool:
        """
        Check if a BigQuery table exists.
        
        Args:
            dataset_id: Dataset name
            table_id: Table name
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            self.client.get_table(f"{self.project_id}.{dataset_id}.{table_id}")
            return True
        except Exception:
            return False

    def dataset_exists(self, dataset_id: str) -> bool:
        """
        Check if a BigQuery dataset exists.
        
        Args:
            dataset_id: Dataset name
            
        Returns:
            True if dataset exists, False otherwise
        """
        try:
            self.client.get_dataset(f"{self.project_id}.{dataset_id}")
            return True
        except Exception:
            return False

    def create_dataset(
        self,
        dataset_id: str,
        location: str = "US",
        description: str = None,
    ) -> bigquery.Dataset:
        """
        Create a BigQuery dataset.
        
        Args:
            dataset_id: Name for the dataset
            location: Geographic location (default: US)
            description: Optional description
            
        Returns:
            bigquery.Dataset object
        """
        dataset_ref = bigquery.DatasetReference(self.project_id, dataset_id)
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        
        if description:
            dataset.description = description
        
        dataset = self.client.create_dataset(dataset, exists_ok=True)
        logger.info(f"Dataset created/verified: {dataset_id}")
        return dataset

    def get_table_row_count(self, dataset_id: str, table_id: str) -> int:
        """
        Get row count for a BigQuery table.
        
        Args:
            dataset_id: Dataset name
            table_id: Table name
            
        Returns:
            Number of rows
        """
        table = self.client.get_table(f"{self.project_id}.{dataset_id}.{table_id}")
        return table.num_rows

    def run_query(self, sql: str, max_results: int = None) -> pd.DataFrame:
        """
        Execute a BigQuery query and return results as DataFrame.
        
        Args:
            sql: SQL query string
            max_results: Maximum number of results to fetch
            
        Returns:
            pandas DataFrame
        """
        try:
            query_job = self.client.query(sql)
            results = query_job.result(max_results=max_results)
            return results.to_dataframe()
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            raise


# ============================================================================
# RETRY & ERROR HANDLING
# ============================================================================

def retry_on_exception(
    max_retries: int = 3,
    backoff_factor: float = 2,
    wait_seconds: float = 1,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for wait time between retries
        wait_seconds: Initial wait time in seconds
        exceptions: Tuple of exceptions to catch
        
    Example:
        @retry_on_exception(max_retries=3, backoff_factor=2)
        def unstable_function():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_retries - 1:
                        wait_time = wait_seconds * (backoff_factor ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}. "
                            f"Retrying in {wait_time}s... Error: {str(e)}"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for {func.__name__}. "
                            f"Final error: {str(e)}"
                        )
                        raise
        return wrapper
    return decorator


# ============================================================================
# DATE & TIME UTILITIES
# ============================================================================

def get_academic_year(date: datetime) -> int:
    """
    Get academic year for a given date.
    Academic year starts in August.
    
    Args:
        date: datetime object
        
    Returns:
        Academic year (e.g., 2026 for Aug 2025 - Jul 2026)
    """
    if date.month >= 8:
        return date.year + 1
    else:
        return date.year


def get_fiscal_year(date: datetime) -> int:
    """
    Get fiscal year for a given date.
    Fiscal year starts in July.
    
    Args:
        date: datetime object
        
    Returns:
        Fiscal year (e.g., 2026 for Jul 2025 - Jun 2026)
    """
    if date.month >= 7:
        return date.year + 1
    else:
        return date.year


def get_semester(date: datetime) -> str:
    """
    Get academic semester for a given date.
    
    Args:
        date: datetime object
        
    Returns:
        Semester: 'Fall', 'Spring', or 'Summer'
    """
    month = date.month
    if month in [8, 9, 10, 11, 12]:
        return "Fall"
    elif month in [1, 2, 3, 4, 5]:
        return "Spring"
    else:
        return "Summer"


def date_range(start_date: datetime, end_date: datetime, freq: str = "D") -> List[datetime]:
    """
    Generate a range of dates.
    
    Args:
        start_date: Start date
        end_date: End date
        freq: Frequency ('D' for day, 'W' for week, 'M' for month, 'Y' for year)
        
    Returns:
        List of dates
    """
    dates = pd.date_range(start=start_date, end=end_date, freq=freq).tolist()
    return dates


# ============================================================================
# DATA TRANSFORMATION UTILITIES
# ============================================================================

def pseudonymize_id(value: str, salt: str = "default_salt") -> str:
    """
    Create pseudonymized ID for PII data (e.g., student ID).
    Uses SHA256 hashing for FERPA compliance.
    
    Args:
        value: Original value to pseudonymize
        salt: Salt for hashing (should be secure in production)
        
    Returns:
        Hashed/pseudonymized value
    """
    import hashlib
    
    combined = f"{value}{salt}".encode()
    hash_obj = hashlib.sha256(combined)
    return hash_obj.hexdigest()[:16]  # First 16 chars


def convert_grade_point_to_letter(grade_point: float) -> str:
    """
    Convert numeric grade (0-4) to letter grade.
    
    Args:
        grade_point: Numeric grade
        
    Returns:
        Letter grade (A, A-, B+, B, B-, C+, C, D, F)
    """
    if grade_point >= 3.7:
        return "A"
    elif grade_point >= 3.3:
        return "A-"
    elif grade_point >= 3.0:
        return "B+"
    elif grade_point >= 2.7:
        return "B"
    elif grade_point >= 2.3:
        return "B-"
    elif grade_point >= 2.0:
        return "C+"
    elif grade_point >= 1.3:
        return "C"
    elif grade_point >= 1.0:
        return "D"
    else:
        return "F"


def convert_letter_to_grade_point(letter_grade: str) -> float:
    """
    Convert letter grade to numeric grade point (0-4).
    
    Args:
        letter_grade: Letter grade
        
    Returns:
        Numeric grade point
    """
    grade_map = {
        "A": 4.0,
        "A-": 3.7,
        "B+": 3.3,
        "B": 3.0,
        "B-": 2.7,
        "C+": 2.3,
        "C": 2.0,
        "C-": 1.7,
        "D+": 1.3,
        "D": 1.0,
        "D-": 0.7,
        "F": 0.0,
        "I": None,  # Incomplete
        "W": None,  # Withdrawn
    }
    return grade_map.get(letter_grade, None)


def calculate_gpa(grades: List[Dict[str, Any]]) -> float:
    """
    Calculate cumulative GPA from list of grade records.
    
    Args:
        grades: List of dicts with 'grade_point' and 'credits' keys
        
    Returns:
        Cumulative GPA (weighted by credits)
    """
    if not grades:
        return 0.0
    
    total_weighted = sum(g["grade_point"] * g["credits"] for g in grades)
    total_credits = sum(g["credits"] for g in grades)
    
    if total_credits == 0:
        return 0.0
    
    return total_weighted / total_credits


def calculate_credits_to_degree(completed_credits: int, total_required: int = 120) -> float:
    """
    Calculate percentage of credits completed toward degree.
    
    Args:
        completed_credits: Credits completed
        total_required: Total required for degree (default: 120)
        
    Returns:
        Percentage (0-1)
    """
    if total_required == 0:
        return 0.0
    return min(completed_credits / total_required, 1.0)


# ============================================================================
# DATA VALIDATION UTILITIES
# ============================================================================

def is_valid_email(email: str) -> bool:
    """Check if email is valid format."""
    import re
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_valid_gpa(gpa: float) -> bool:
    """Check if GPA is valid (0.0-4.0)."""
    return isinstance(gpa, (int, float)) and 0.0 <= gpa <= 4.0


def is_valid_date_logic(start_date: datetime, end_date: datetime) -> bool:
    """Check if date range is valid (start <= end)."""
    return start_date <= end_date


def is_valid_salary(salary: float) -> bool:
    """Check if salary is valid (positive number)."""
    return isinstance(salary, (int, float)) and salary > 0


# ============================================================================
# LOGGING UTILITIES
# ============================================================================

def log_execution_time(func):
    """Decorator to log function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Starting: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"Completed: {func.__name__} ({elapsed:.2f}s)")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed: {func.__name__} ({elapsed:.2f}s) - {str(e)}")
            raise
    
    return wrapper


# ============================================================================
# DIRECTORY & FILE UTILITIES
# ============================================================================

def ensure_directory(directory: str) -> str:
    """
    Ensure a directory exists, create if not.
    
    Args:
        directory: Directory path
        
    Returns:
        Directory path
    """
    os.makedirs(directory, exist_ok=True)
    return directory


def get_file_size(filepath: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        filepath: Path to file
        
    Returns:
        File size in bytes
    """
    return os.path.getsize(filepath)


def get_file_size_mb(filepath: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        filepath: Path to file
        
    Returns:
        File size in MB
    """
    return get_file_size(filepath) / (1024 * 1024)


# ============================================================================
# ENVIRONMENT UTILITIES
# ============================================================================

def load_environment_variables(env_file: str = ".env") -> Dict[str, str]:
    """
    Load environment variables from .env file.
    
    Args:
        env_file: Path to .env file
        
    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    
    if not os.path.exists(env_file):
        logger.warning(f"Environment file not found: {env_file}")
        return env_vars
    
    try:
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
        
        logger.info(f"Loaded {len(env_vars)} environment variables from {env_file}")
        return env_vars
    
    except Exception as e:
        logger.error(f"Error loading environment file: {str(e)}")
        return env_vars


# ============================================================================
# STATISTICS UTILITIES
# ============================================================================

def calculate_percentile(data: List[float], percentile: float) -> float:
    """
    Calculate percentile value.
    
    Args:
        data: List of numeric values
        percentile: Percentile (0-100)
        
    Returns:
        Percentile value
    """
    if not data:
        return 0.0
    
    sorted_data = sorted(data)
    index = (percentile / 100.0) * (len(sorted_data) - 1)
    
    if index == int(index):
        return sorted_data[int(index)]
    else:
        lower = sorted_data[int(index)]
        upper = sorted_data[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))


def calculate_z_score(value: float, mean: float, std_dev: float) -> float:
    """
    Calculate z-score for a value.
    
    Args:
        value: Data point
        mean: Population mean
        std_dev: Population standard deviation
        
    Returns:
        Z-score
    """
    if std_dev == 0:
        return 0.0
    return (value - mean) / std_dev


def is_outlier(value: float, mean: float, std_dev: float, threshold: float = 3.0) -> bool:
    """
    Determine if a value is a statistical outlier.
    
    Args:
        value: Data point
        mean: Population mean
        std_dev: Population standard deviation
        threshold: Z-score threshold (default: 3.0)
        
    Returns:
        True if outlier, False otherwise
    """
    z_score = calculate_z_score(value, mean, std_dev)
    return abs(z_score) > threshold


if __name__ == "__main__":
    # Test utilities
    print("\n" + "="*70)
    print("UTILITY FUNCTIONS TEST")
    print("="*70 + "\n")
    
    # Test academic year
    test_date = datetime(2025, 9, 15)
    print(f"Date: {test_date.strftime('%Y-%m-%d')}")
    print(f"  Academic Year: {get_academic_year(test_date)}")
    print(f"  Semester: {get_semester(test_date)}")
    
    # Test GPA calculation
    grades = [
        {"grade_point": 3.5, "credits": 3},
        {"grade_point": 3.0, "credits": 4},
        {"grade_point": 3.5, "credits": 3},
    ]
    gpa = calculate_gpa(grades)
    print(f"\nGPA from {len(grades)} courses: {gpa:.2f}")
    
    # Test grade conversion
    print(f"\nGrade conversions:")
    for gp in [4.0, 3.7, 3.3, 3.0, 2.7, 2.0, 1.0, 0.0]:
        letter = convert_grade_point_to_letter(gp)
        print(f"  {gp:.1f} → {letter}")
    
    print("\n" + "="*70 + "\n")
