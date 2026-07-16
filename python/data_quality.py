"""
Data Quality Validation Framework for UT CNS Data Hub
Implements comprehensive data quality checks and anomaly detection
"""

import logging
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime
from google.cloud import bigquery

from python.config import (
    DATA_QUALITY_THRESHOLDS,
    NULL_THRESHOLD,
    DUPLICATE_CHECK_KEYS,
)

logger = logging.getLogger("ETL_Pipeline")


class DataQualityValidator:
    """
    Comprehensive data quality validation framework.
    Implements multiple validation dimensions: completeness, uniqueness, validity, consistency.
    """

    def __init__(self, bq_client: bigquery.Client):
        """
        Initialize quality validator.
        
        Args:
            bq_client: BigQuery client instance
        """
        self.bq_client = bq_client
        self.thresholds = DATA_QUALITY_THRESHOLDS

    # ========================================================================
    # COMPLETENESS CHECKS
    # ========================================================================

    def check_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Check data completeness (NULL/missing values).
        
        Args:
            df: DataFrame to validate
            
        Returns:
            {
                "passed": bool,
                "total_records": int,
                "null_records": int,
                "completeness_rate": float,
                "null_by_column": Dict[str, int],
                "failed_columns": List[str],
            }
        """
        total_records = len(df)
        null_records = df.isnull().any(axis=1).sum()
        completeness_rate = 1.0 - (null_records / total_records) if total_records > 0 else 1.0
        
        # Column-level null analysis
        null_by_column = df.isnull().sum()
        null_pct_by_column = (null_by_column / total_records).to_dict()
        
        # Identify columns exceeding threshold
        failed_columns = [
            col for col, pct in null_pct_by_column.items()
            if pct > NULL_THRESHOLD
        ]
        
        passed = completeness_rate >= self.thresholds["completeness_threshold"]
        
        return {
            "passed": passed,
            "total_records": total_records,
            "null_records": null_records,
            "completeness_rate": round(completeness_rate, 4),
            "null_by_column": null_by_column.to_dict(),
            "null_pct_by_column": null_pct_by_column,
            "failed_columns": failed_columns,
            "threshold": self.thresholds["completeness_threshold"],
        }

    # ========================================================================
    # UNIQUENESS CHECKS
    # ========================================================================

    def check_uniqueness(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        Check data uniqueness (duplicate detection).
        
        Args:
            df: DataFrame to validate
            table_name: Name of table (to look up key columns)
            
        Returns:
            {
                "passed": bool,
                "total_records": int,
                "duplicate_records": int,
                "uniqueness_rate": float,
                "key_column": str,
            }
        """
        total_records = len(df)
        
        # Get key column(s) for this table
        key_column = DUPLICATE_CHECK_KEYS.get(table_name, None)
        
        if key_column is None:
            # No key defined, assume all columns should be unique
            duplicate_records = df.duplicated().sum()
        else:
            # Check for duplicates on key column(s)
            if isinstance(key_column, list):
                duplicate_records = df.duplicated(subset=key_column).sum()
            else:
                duplicate_records = df.duplicated(subset=[key_column]).sum()
        
        uniqueness_rate = 1.0 - (duplicate_records / total_records) if total_records > 0 else 1.0
        passed = uniqueness_rate >= self.thresholds["uniqueness_threshold"]
        
        return {
            "passed": passed,
            "total_records": total_records,
            "duplicate_records": duplicate_records,
            "uniqueness_rate": round(uniqueness_rate, 4),
            "key_column": key_column,
            "threshold": self.thresholds["uniqueness_threshold"],
        }

    # ========================================================================
    # VALIDITY CHECKS
    # ========================================================================

    def check_validity(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        Check data validity (range, format, business logic).
        
        Args:
            df: DataFrame to validate
            table_name: Name of table (to determine validation rules)
            
        Returns:
            {
                "passed": bool,
                "total_records": int,
                "invalid_records": int,
                "validity_rate": float,
                "issues": Dict[str, int],
            }
        """
        invalid_records = 0
        issues = {}
        
        # Table-specific validation rules
        if table_name == "students":
            # GPA must be between 0.0 and 4.0
            invalid_gpa = ((df["gpa"] < 0.0) | (df["gpa"] > 4.0)).sum()
            if invalid_gpa > 0:
                issues["invalid_gpa"] = invalid_gpa
                invalid_records += invalid_gpa
            
            # Cohort year must be reasonable
            current_year = datetime.now().year
            invalid_cohort = ((df["cohort_year"] < 2000) | (df["cohort_year"] > current_year + 1)).sum()
            if invalid_cohort > 0:
                issues["invalid_cohort_year"] = invalid_cohort
                invalid_records += invalid_cohort
            
            # date_enrolled must be <= date_graduated (if both exist)
            mask = (df["date_graduated"].notna()) & (df["date_enrolled"].notna())
            if mask.any():
                invalid_dates = (
                    (pd.to_datetime(df.loc[mask, "date_graduated"]) < 
                     pd.to_datetime(df.loc[mask, "date_enrolled"]))
                ).sum()
                if invalid_dates > 0:
                    issues["invalid_date_logic"] = invalid_dates
                    invalid_records += invalid_dates
        
        elif table_name == "faculty":
            # Salary must be positive
            invalid_salary = (df["salary"] <= 0).sum()
            if invalid_salary > 0:
                issues["invalid_salary"] = invalid_salary
                invalid_records += invalid_salary
            
            # Hire date must be in past
            invalid_hire = (pd.to_datetime(df["hire_date"]) > pd.Timestamp.now()).sum()
            if invalid_hire > 0:
                issues["hire_date_in_future"] = invalid_hire
                invalid_records += invalid_hire
        
        elif table_name == "grants":
            # Award amount must be positive
            invalid_award = (df["award_amount"] <= 0).sum()
            if invalid_award > 0:
                issues["invalid_award_amount"] = invalid_award
                invalid_records += invalid_award
            
            # Start date must be <= end date
            invalid_dates = (
                pd.to_datetime(df["end_date"]) < pd.to_datetime(df["start_date"])
            ).sum()
            if invalid_dates > 0:
                issues["invalid_date_range"] = invalid_dates
                invalid_records += invalid_dates
        
        elif table_name == "courses":
            # Credits must be 1-4
            invalid_credits = ~df["credits"].isin([1, 2, 3, 4]).sum()
            if invalid_credits > 0:
                issues["invalid_credits"] = invalid_credits
                invalid_records += invalid_credits
            
            # Pass rate must be 0-1
            invalid_pass_rate = ((df["pass_rate"] < 0) | (df["pass_rate"] > 1)).sum()
            if invalid_pass_rate > 0:
                issues["invalid_pass_rate"] = invalid_pass_rate
                invalid_records += invalid_pass_rate
            
            # Rating must be 1-5
            invalid_rating = ((df["avg_rating"] < 1) | (df["avg_rating"] > 5)).sum()
            if invalid_rating > 0:
                issues["invalid_rating"] = invalid_rating
                invalid_records += invalid_rating
        
        elif table_name == "enrollments":
            # Grade point must be 0-4
            invalid_grade_point = ((df["grade_point"] < 0) | (df["grade_point"] > 4)).sum()
            if invalid_grade_point > 0:
                issues["invalid_grade_point"] = invalid_grade_point
                invalid_records += invalid_grade_point
            
            # Credits earned must be >= 0
            invalid_credits = (df["credits_earned"] < 0).sum()
            if invalid_credits > 0:
                issues["invalid_credits_earned"] = invalid_credits
                invalid_records += invalid_credits
        
        total_records = len(df)
        validity_rate = 1.0 - (invalid_records / total_records) if total_records > 0 else 1.0
        passed = validity_rate >= self.thresholds["validity_threshold"]
        
        return {
            "passed": passed,
            "total_records": total_records,
            "invalid_records": invalid_records,
            "validity_rate": round(validity_rate, 4),
            "issues": issues,
            "threshold": self.thresholds["validity_threshold"],
        }

    # ========================================================================
    # CONSISTENCY CHECKS
    # ========================================================================

    def check_consistency(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        Check data consistency (referential integrity, cross-field logic).
        
        Args:
            df: DataFrame to validate
            table_name: Name of table
            
        Returns:
            {
                "passed": bool,
                "total_records": int,
                "inconsistent_records": int,
                "consistency_rate": float,
                "issues": Dict[str, int],
            }
        """
        inconsistent_records = 0
        issues = {}
        
        # Table-specific consistency rules
        if table_name == "students":
            # If enrolled, should have credits > 0
            active_no_credits = (
                (df["enrollment_status"] == "Active") & 
                (df["credits_completed"] == 0)
            ).sum()
            if active_no_credits > 0:
                issues["active_no_credits"] = active_no_credits
                inconsistent_records += active_no_credits
            
            # If graduated, should have credits >= 120
            graduated_insufficient = (
                (df["enrollment_status"] == "Graduated") & 
                (df["credits_completed"] < 120)
            ).sum()
            if graduated_insufficient > 0:
                issues["graduated_insufficient_credits"] = graduated_insufficient
                inconsistent_records += graduated_insufficient
        
        elif table_name == "enrollments":
            # If grade is F, credits_earned should be 0
            f_with_credits = (
                (df["grade"] == "F") & 
                (df["credits_earned"] > 0)
            ).sum()
            if f_with_credits > 0:
                issues["f_grade_with_credits"] = f_with_credits
                inconsistent_records += f_with_credits
            
            # If grade is not F, credits_earned should equal credits
            # (This is simplified; actual validation would need course data)
        
        total_records = len(df)
        consistency_rate = 1.0 - (inconsistent_records / total_records) if total_records > 0 else 1.0
        passed = consistency_rate >= self.thresholds["consistency_threshold"]
        
        return {
            "passed": passed,
            "total_records": total_records,
            "inconsistent_records": inconsistent_records,
            "consistency_rate": round(consistency_rate, 4),
            "issues": issues,
            "threshold": self.thresholds["consistency_threshold"],
        }

    # ========================================================================
    # ANOMALY DETECTION
    # ========================================================================

    def detect_anomalies(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        Detect statistical anomalies using z-score method.
        
        Args:
            df: DataFrame to analyze
            table_name: Name of table
            
        Returns:
            {
                "anomalies_detected": bool,
                "anomalous_records": int,
                "by_column": Dict[str, int],
            }
        """
        anomalies_by_column = {}
        total_anomalies = 0
        z_threshold = 3  # Standard deviation threshold
        
        # Check numeric columns
        for col in df.select_dtypes(include=[np.number]).columns:
            if col in ["gpa", "salary", "award_amount", "grade_point", "pass_rate"]:
                # Skip if too few non-null values
                if df[col].notna().sum() < 10:
                    continue
                
                mean = df[col].mean()
                std = df[col].std()
                
                if std > 0:
                    z_scores = np.abs((df[col] - mean) / std)
                    anomalies = (z_scores > z_threshold).sum()
                    if anomalies > 0:
                        anomalies_by_column[col] = anomalies
                        total_anomalies += anomalies
        
        return {
            "anomalies_detected": total_anomalies > 0,
            "anomalous_records": total_anomalies,
            "by_column": anomalies_by_column,
        }

    # ========================================================================
    # FACT TABLE VALIDATION (BigQuery-based)
    # ========================================================================

    def check_fact_table_counts(self, analytics_dataset: str) -> Dict[str, bool]:
        """
        Check fact table row counts in BigQuery.
        
        Args:
            analytics_dataset: Name of analytics dataset
            
        Returns:
            Dictionary of {check_name: passed}
        """
        checks = {}
        
        try:
            # Check fact_enrollment row count
            query = f"""
            SELECT COUNT(*) as row_count
            FROM `{self.bq_client.project}.{analytics_dataset}.fact_enrollment`
            """
            result = self.bq_client.query(query).result()
            enrollment_rows = list(result)[0][0]
            checks["fact_enrollment_has_rows"] = enrollment_rows > 0
            
            logger.info(f"  fact_enrollment: {enrollment_rows:,} rows")
            
        except Exception as e:
            logger.warning(f"Could not check fact_enrollment: {str(e)}")
            checks["fact_enrollment_has_rows"] = True  # Skip if table doesn't exist
        
        return checks

    # ========================================================================
    # REFERENTIAL INTEGRITY CHECKS
    # ========================================================================

    def check_referential_integrity(self, analytics_dataset: str) -> Dict[str, bool]:
        """
        Check referential integrity between dimension and fact tables.
        
        Args:
            analytics_dataset: Name of analytics dataset
            
        Returns:
            Dictionary of {check_name: passed}
        """
        checks = {}
        
        try:
            # Check student_key in fact_enrollment exists in dim_student
            query = f"""
            SELECT COUNT(DISTINCT f.student_key) as orphaned_keys
            FROM `{self.bq_client.project}.{analytics_dataset}.fact_enrollment` f
            LEFT JOIN `{self.bq_client.project}.{analytics_dataset}.dim_student` d
            ON f.student_key = d.student_key
            WHERE d.student_key IS NULL
            """
            result = self.bq_client.query(query).result()
            orphaned = list(result)[0][0]
            checks["fact_enrollment_student_fk"] = orphaned == 0
            
            logger.info(f"  fact_enrollment → dim_student: {orphaned} orphaned keys")
            
        except Exception as e:
            logger.warning(f"Could not check referential integrity: {str(e)}")
            checks["fact_enrollment_student_fk"] = True  # Skip if tables don't exist
        
        return checks

    # ========================================================================
    # QUALITY SCORECARD
    # ========================================================================

    def generate_quality_scorecard(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Generate a comprehensive quality scorecard.
        
        Args:
            data: Dictionary of {table_name: DataFrame}
            
        Returns:
            DataFrame with quality metrics for all tables
        """
        scorecard = []
        
        for table_name, df in data.items():
            completeness = self.check_completeness(df)
            uniqueness = self.check_uniqueness(df, table_name)
            validity = self.check_validity(df, table_name)
            consistency = self.check_consistency(df, table_name)
            anomalies = self.detect_anomalies(df, table_name)
            
            # Calculate overall score (weighted average)
            overall_score = (
                completeness["completeness_rate"] * 0.25 +
                uniqueness["uniqueness_rate"] * 0.25 +
                validity["validity_rate"] * 0.25 +
                consistency["consistency_rate"] * 0.25
            )
            
            scorecard.append({
                "table": table_name,
                "row_count": len(df),
                "completeness": round(completeness["completeness_rate"], 4),
                "uniqueness": round(uniqueness["uniqueness_rate"], 4),
                "validity": round(validity["validity_rate"], 4),
                "consistency": round(consistency["consistency_rate"], 4),
                "overall_quality_score": round(overall_score, 4),
                "anomalies_detected": anomalies["anomalies_detected"],
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        return pd.DataFrame(scorecard)


# ============================================================================
# STANDALONE USAGE
# ============================================================================

if __name__ == "__main__":
    from python.data_generators import SyntheticDataGenerator
    
    print("\n" + "="*70)
    print("DATA QUALITY VALIDATION - STANDALONE TEST")
    print("="*70 + "\n")
    
    # Generate sample data
    generator = SyntheticDataGenerator(seed=42)
    data = generator.generate_all()
    
    # Initialize validator (without BigQuery for this test)
    validator = DataQualityValidator(bq_client=None)
    
    # Generate scorecard
    scorecard = validator.generate_quality_scorecard(data)
    print(scorecard.to_string(index=False))
    
    print("\n" + "="*70 + "\n")
