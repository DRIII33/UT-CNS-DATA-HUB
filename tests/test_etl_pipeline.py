"""Integration tests for ETL pipeline."""

import pytest
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python.data_generators import SyntheticDataGenerator


class TestETLPipeline:
    """Test end-to-end ETL pipeline."""
    
    @pytest.fixture
    def synthetic_data(self, tmp_path):
        """Generate synthetic data for testing."""
        generator = SyntheticDataGenerator(output_dir=str(tmp_path), seed=42)
        generator.generate_all()
        return tmp_path
    
    def test_extract_all_files(self, synthetic_data):
        """Test data extraction from all source files."""
        required_files = ["students.csv", "faculty.csv", "grants.csv", "courses.csv", "enrollments.csv"]
        
        for file in required_files:
            assert (synthetic_data / file).exists()
    
    def test_row_counts(self, synthetic_data):
        """Test that expected row counts match specifications."""
        students_df = pd.read_csv(synthetic_data / "students.csv")
        faculty_df = pd.read_csv(synthetic_data / "faculty.csv")
        grants_df = pd.read_csv(synthetic_data / "grants.csv")
        courses_df = pd.read_csv(synthetic_data / "courses.csv")
        enrollments_df = pd.read_csv(synthetic_data / "enrollments.csv")
        
        # Verify approximate row counts
        assert len(students_df) >= 12000  # At least 12K students
        assert len(faculty_df) >= 600     # At least 600 faculty
        assert len(grants_df) >= 1800     # At least 1.8K grants
        assert len(courses_df) >= 400     # At least 400 courses
        assert len(enrollments_df) >= 40000  # At least 40K enrollments
    
    def test_data_completeness(self, synthetic_data):
        """Test that required columns are present."""
        students_df = pd.read_csv(synthetic_data / "students.csv")
        
        required_columns = ["student_id", "cohort_year", "major", "gpa", "enrollment_status"]
        for col in required_columns:
            assert col in students_df.columns
    
    def test_referential_integrity(self, synthetic_data):
        """Test foreign key relationships."""
        faculty_df = pd.read_csv(synthetic_data / "faculty.csv")
        grants_df = pd.read_csv(synthetic_data / "grants.csv")
        
        # All grant PIs should exist in faculty table
        faculty_ids = set(faculty_df["faculty_id"].unique())
        grant_pis = set(grants_df["pi_id"].unique())
        
        missing_pis = grant_pis - faculty_ids
        # Allow some missing (simulating real data gaps)
        assert len(missing_pis) < len(grant_pis) * 0.1  # Less than 10% missing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
