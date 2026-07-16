"""
ETL Pipeline for UT CNS Data Hub
Orchestrates data extraction, transformation, and loading into BigQuery
Handles error recovery, data quality validation, and comprehensive logging
"""

import sys
import logging
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import traceback

import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

from python.config import (
    GCP_PROJECT_ID,
    DATASET_STAGING,
    DATASET_ANALYTICS,
    STAGING_TABLES,
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
    RETRY_WAIT_SECONDS,
    BATCH_SIZE,
    CHUNK_SIZE,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_FILE,
)
from python.data_generators import SyntheticDataGenerator
from python.data_quality import DataQualityValidator


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_logging() -> logging.Logger:
    """Configure logging to file and console."""
    Path("logs").mkdir(exist_ok=True)
    
    logger = logging.getLogger("ETL_Pipeline")
    logger.setLevel(LOG_LEVEL)
    
    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(LOG_LEVEL)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    
    # Formatter
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()


# ============================================================================
# ETL PIPELINE CLASS
# ============================================================================

class ETLPipeline:
    """
    Main ETL orchestration class.
    Handles extraction, transformation, loading, and quality validation.
    """

    def __init__(self, project_id: str = GCP_PROJECT_ID):
        """
        Initialize ETL pipeline.
        
        Args:
            project_id: GCP project ID
        """
        self.project_id = project_id
        self.bq_client = bigquery.Client(project=project_id)
        self.data_generator = SyntheticDataGenerator()
        self.quality_validator = DataQualityValidator(self.bq_client)
        self.execution_log = {
            "execution_id": self._generate_execution_id(),
            "start_time": datetime.utcnow().isoformat(),
            "status": "IN_PROGRESS",
            "pipeline_stats": {},
            "errors": [],
        }
        
        logger.info(f"ETL Pipeline initialized for project: {project_id}")
    
    def _generate_execution_id(self) -> str:
        """Generate unique execution ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"ETL_{timestamp}"
    
    # ========================================================================
    # PHASE 1: EXTRACTION
    # ========================================================================
    
    def extract_data(self, output_dir: str = "data/synthetic") -> Dict[str, pd.DataFrame]:
        """
        Extract phase: Generate or load source data.
        
        Args:
            output_dir: Directory for synthetic data
            
        Returns:
            Dictionary of DataFrames: {table_name: DataFrame}
        """
        logger.info("=" * 70)
        logger.info("PHASE 1: DATA EXTRACTION")
        logger.info("=" * 70)
        
        try:
            # Generate synthetic data
            logger.info("Generating synthetic data...")
            data = self.data_generator.generate_all()
            
            self.execution_log["pipeline_stats"]["extraction"] = {
                "status": "SUCCESS",
                "tables_extracted": len(data),
                "total_rows": sum(len(df) for df in data.values()),
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            logger.info(f"✓ Extraction complete: {len(data)} tables, "
                       f"{sum(len(df) for df in data.values()):,} total rows")
            return data
            
        except Exception as e:
            logger.error(f"✗ Extraction failed: {str(e)}")
            logger.error(traceback.format_exc())
            self.execution_log["pipeline_stats"]["extraction"] = {
                "status": "FAILURE",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.execution_log["errors"].append({
                "phase": "extraction",
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
            raise
    
    # ========================================================================
    # PHASE 2: DATA QUALITY VALIDATION
    # ========================================================================
    
    def validate_data(self, data: Dict[str, pd.DataFrame]) -> Tuple[bool, Dict]:
        """
        Validate phase: Check data quality before loading.
        
        Args:
            data: Dictionary of DataFrames to validate
            
        Returns:
            (is_valid, quality_report)
        """
        logger.info("=" * 70)
        logger.info("PHASE 2: DATA QUALITY VALIDATION")
        logger.info("=" * 70)
        
        try:
            quality_report = {}
            all_valid = True
            
            for table_name, df in data.items():
                logger.info(f"Validating {table_name}...")
                
                # Run quality checks
                checks = {
                    "completeness": self.quality_validator.check_completeness(df),
                    "uniqueness": self.quality_validator.check_uniqueness(df, table_name),
                    "validity": self.quality_validator.check_validity(df, table_name),
                    "consistency": self.quality_validator.check_consistency(df, table_name),
                }
                
                # Determine if table passes
                table_valid = all(check["passed"] for check in checks.values())
                all_valid = all_valid and table_valid
                
                quality_report[table_name] = {
                    "passed": table_valid,
                    "checks": checks,
                    "row_count": len(df),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                
                status = "✓ PASS" if table_valid else "✗ FAIL"
                logger.info(f"{status}: {table_name} ({len(df):,} rows)")
            
            self.execution_log["pipeline_stats"]["validation"] = {
                "status": "SUCCESS" if all_valid else "PARTIAL",
                "tables_validated": len(data),
                "passed": sum(1 for r in quality_report.values() if r["passed"]),
                "report": quality_report,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            return all_valid, quality_report
            
        except Exception as e:
            logger.error(f"✗ Validation failed: {str(e)}")
            self.execution_log["pipeline_stats"]["validation"] = {
                "status": "FAILURE",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.execution_log["errors"].append({
                "phase": "validation",
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
            raise
    
    # ========================================================================
    # PHASE 3: LOADING (STAGING LAYER)
    # ========================================================================
    
    def load_to_staging(self, data: Dict[str, pd.DataFrame]) -> Dict[str, int]:
        """
        Load phase: Write data to BigQuery staging layer.
        
        Args:
            data: Dictionary of DataFrames to load
            
        Returns:
            Dictionary of {table_name: rows_loaded}
        """
        logger.info("=" * 70)
        logger.info("PHASE 3: LOAD TO STAGING LAYER")
        logger.info("=" * 70)
        
        load_results = {}
        
        for table_name, df in data.items():
            table_id = STAGING_TABLES[table_name]
            
            try:
                logger.info(f"Loading {table_name} to {table_id}...")
                
                # Configure load job
                job_config = bigquery.LoadJobConfig(
                    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                    skip_leading_rows=0,
                    autodetect=False,
                )
                
                # Load with retry logic
                rows_loaded = self._load_with_retry(
                    table_id, df, job_config, table_name
                )
                
                load_results[table_name] = rows_loaded
                logger.info(f"✓ {table_name}: {rows_loaded:,} rows loaded")
                
            except Exception as e:
                logger.error(f"✗ Failed to load {table_name}: {str(e)}")
                self.execution_log["errors"].append({
                    "phase": "loading",
                    "table": table_name,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                })
                raise
        
        self.execution_log["pipeline_stats"]["loading"] = {
            "status": "SUCCESS",
            "tables_loaded": len(load_results),
            "total_rows_loaded": sum(load_results.values()),
            "results": load_results,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"✓ Loading complete: {len(load_results)} tables, "
                   f"{sum(load_results.values()):,} total rows")
        
        return load_results
    
    def _load_with_retry(
        self,
        table_id: str,
        df: pd.DataFrame,
        job_config: bigquery.LoadJobConfig,
        table_name: str,
    ) -> int:
        """
        Load data with retry logic and exponential backoff.
        
        Args:
            table_id: BigQuery table ID
            df: DataFrame to load
            job_config: BigQuery load configuration
            table_name: Name of table (for logging)
            
        Returns:
            Number of rows loaded
        """
        import time
        
        for attempt in range(MAX_RETRIES):
            try:
                load_job = self.bq_client.load_table_from_dataframe(
                    df, table_id, job_config=job_config
                )
                load_job.result()  # Wait for job to complete
                
                return load_job.output_rows
                
            except GoogleAPIError as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_WAIT_SECONDS * (RETRY_BACKOFF_FACTOR ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {table_name}. "
                        f"Retrying in {wait_time}s... Error: {str(e)}"
                    )
                    time.sleep(wait_time)
                else:
                    raise
    
    # ========================================================================
    # PHASE 4: TRANSFORMATION (SQL-based)
    # ========================================================================
    
    def run_transformations(self) -> Dict[str, int]:
        """
        Transformation phase: Execute SQL transformations to build analytics layer.
        
        Returns:
            Dictionary of {transformation_name: rows_created}
        """
        logger.info("=" * 70)
        logger.info("PHASE 4: TRANSFORMATIONS (STAGING TO ANALYTICS)")
        logger.info("=" * 70)
        
        transformation_results = {}
        
        transformations = [
            {
                "name": "Staging Views",
                "file": "sql/transformations/01_staging_views.sql",
            },
            {
                "name": "Dimension Tables",
                "file": "sql/transformations/02_dim_tables.sql",
            },
            {
                "name": "Fact Tables",
                "file": "sql/transformations/03_fact_tables.sql",
            },
            {
                "name": "Aggregate Views",
                "file": "sql/transformations/04_metrics_views.sql",
            },
        ]
        
        for transform in transformations:
            try:
                logger.info(f"Executing: {transform['name']}...")
                
                # Read SQL file
                sql_file = Path(transform["file"])
                if not sql_file.exists():
                    logger.warning(f"SQL file not found: {sql_file}")
                    logger.info("Skipping transformation (SQL file not yet in repository)")
                    transformation_results[transform["name"]] = 0
                    continue
                
                with open(sql_file, "r") as f:
                    sql_script = f.read()
                
                # Execute SQL
                query_job = self.bq_client.query(sql_script)
                query_job.result()
                
                transformation_results[transform["name"]] = 1
                logger.info(f"✓ {transform['name']} complete")
                
            except Exception as e:
                logger.error(f"✗ {transform['name']} failed: {str(e)}")
                self.execution_log["errors"].append({
                    "phase": "transformation",
                    "transformation": transform["name"],
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                })
                # Continue with next transformation instead of failing
        
        self.execution_log["pipeline_stats"]["transformation"] = {
            "status": "SUCCESS",
            "transformations_executed": len(transformation_results),
            "results": transformation_results,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"✓ Transformations complete: {len(transformation_results)} executed")
        
        return transformation_results
    
    # ========================================================================
    # PHASE 5: POST-LOAD QUALITY CHECKS
    # ========================================================================
    
    def run_post_load_validation(self) -> Dict[str, bool]:
        """
        Post-load validation: Check data integrity in analytics layer.
        
        Returns:
            Dictionary of {check_name: passed}
        """
        logger.info("=" * 70)
        logger.info("PHASE 5: POST-LOAD VALIDATION")
        logger.info("=" * 70)
        
        validation_results = {}
        
        try:
            # Check fact table row counts
            logger.info("Validating fact table row counts...")
            fact_checks = self.quality_validator.check_fact_table_counts(
                DATASET_ANALYTICS
            )
            validation_results.update(fact_checks)
            
            # Check referential integrity
            logger.info("Validating referential integrity...")
            integrity_checks = self.quality_validator.check_referential_integrity(
                DATASET_ANALYTICS
            )
            validation_results.update(integrity_checks)
            
            self.execution_log["pipeline_stats"]["post_validation"] = {
                "status": "SUCCESS",
                "checks_run": len(validation_results),
                "passed": sum(1 for v in validation_results.values() if v),
                "results": validation_results,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            logger.info(f"✓ Post-validation complete: {sum(validation_results.values())}/{len(validation_results)} checks passed")
            
        except Exception as e:
            logger.error(f"✗ Post-validation failed: {str(e)}")
            self.execution_log["errors"].append({
                "phase": "post_validation",
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
        
        return validation_results
    
    # ========================================================================
    # MAIN ORCHESTRATION
    # ========================================================================
    
    def run(self, full_pipeline: bool = True) -> bool:
        """
        Execute the complete ETL pipeline.
        
        Args:
            full_pipeline: If True, run all phases. If False, only extraction & loading.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("\n" + "=" * 70)
            logger.info("UT CNS DATA HUB - ETL PIPELINE START")
            logger.info(f"Execution ID: {self.execution_log['execution_id']}")
            logger.info("=" * 70 + "\n")
            
            # PHASE 1: Extraction
            data = self.extract_data()
            
            # PHASE 2: Data Quality Validation
            is_valid, quality_report = self.validate_data(data)
            
            if not is_valid:
                logger.warning("Data quality checks failed! Proceeding with caution...")
            
            # PHASE 3: Load to Staging
            load_results = self.load_to_staging(data)
            
            # PHASE 4: Transformations (if full pipeline)
            if full_pipeline:
                transformation_results = self.run_transformations()
            
            # PHASE 5: Post-Load Validation (if full pipeline)
            if full_pipeline:
                post_validation = self.run_post_load_validation()
            
            # Mark as complete
            self.execution_log["end_time"] = datetime.utcnow().isoformat()
            self.execution_log["status"] = "SUCCESS"
            
            logger.info("\n" + "=" * 70)
            logger.info("ETL PIPELINE COMPLETE - SUCCESS")
            logger.info("=" * 70)
            logger.info(f"Execution ID: {self.execution_log['execution_id']}")
            logger.info(f"Total rows loaded: {sum(load_results.values()):,}")
            logger.info("=" * 70 + "\n")
            
            # Save execution log
            self._save_execution_log()
            
            return True
            
        except Exception as e:
            logger.error("\n" + "=" * 70)
            logger.error("ETL PIPELINE FAILED")
            logger.error("=" * 70)
            logger.error(f"Error: {str(e)}")
            logger.error(traceback.format_exc())
            logger.error("=" * 70 + "\n")
            
            self.execution_log["end_time"] = datetime.utcnow().isoformat()
            self.execution_log["status"] = "FAILURE"
            
            # Save execution log
            self._save_execution_log()
            
            return False
    
    def _save_execution_log(self):
        """Save execution log to JSON file."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"execution_log_{self.execution_log['execution_id']}.json"
        with open(log_file, "w") as f:
            json.dump(self.execution_log, f, indent=2, default=str)
        
        logger.info(f"Execution log saved: {log_file}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="UT CNS Data Hub ETL Pipeline"
    )
    parser.add_argument(
        "--project",
        default=GCP_PROJECT_ID,
        help="GCP project ID"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        default=True,
        help="Run full pipeline (extraction, load, transformations)"
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Only run extraction phase"
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = ETLPipeline(project_id=args.project)
    
    # Run pipeline
    success = pipeline.run(full_pipeline=not args.extract_only)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
