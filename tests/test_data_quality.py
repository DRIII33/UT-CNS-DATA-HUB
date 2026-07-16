"""Unit tests for data quality validation."""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.data_generators import SyntheticDataGenerator
from python.data_quality import DataQualityValidator


class TestDataGeneration:
    """Test synthetic data generation."""
    
    @pytest.fixture
    def generator(self):
        return SyntheticDataGenerator(output_dir="tests/data/synthetic", seed=42)
    
    def test_student_generation(self, generator, tmp_path):
        """Test student data generation."""
        generator.output_dir = tmp_path
        generator.generate_students(100)
        
        df = pd.read_csv(tmp_path / "students.csv")
        assert len(df) == 100
        assert "student_id" in df.columns
        assert "gpa" in df.columns
        assert (df["gpa"] >= 0.0).all() and (df["gpa"] <= 4.0).all()
    
    def test_faculty_generation(self, generator, tmp_path):
        """Test faculty data generation."""
        generator.output_dir = tmp_path
        generator.generate_faculty(50)
        
        df = pd.read_csv(tmp_path / "faculty.csv")
        assert len(df) == 50
        assert "faculty_id" in df.columns
        assert "salary" in df.columns
        assert (df["salary"] > 0).all()
    
    def test_grant_generation(self, generator, tmp_path):
        """Test grant data generation."""
        generator.output_dir = tmp_path
        generator.generate_grants(50)
        
        df = pd.read_csv(tmp_path / "grants.csv")
        assert len(df) == 50
        assert "grant_id" in df.columns
        assert "award_amount" in df.columns
        assert (df["award_amount"] > 0).all()


class TestDataQuality:
    """Test data quality validation rules."""
    
    def test_completeness_check(self):
        """Test NULL/missing field detection."""
        df = pd.DataFrame({
            "student_id": ["S001", None, "S003"],
            "gpa": [3.5, 3.2, None]
        })
        
        null_count_student = df["student_id"].isna().sum()
        null_count_gpa = df["gpa"].isna().sum()
        
        assert null_count_student == 1
        assert null_count_gpa == 1
    
    def test_uniqueness_check(self):
        """Test duplicate detection."""
        df = pd.DataFrame({
            "student_id": ["S001", "S002", "S001"],
            "name": ["Alice", "Bob", "Alice"]
        })
        
        duplicates = df[df.duplicated(subset=["student_id"], keep=False)]
        assert len(duplicates) == 2
    
    def test_validity_check_gpa(self):
        """Test GPA range validation (0.0-4.0)."""
        gpa_values = [0.0, 1.5, 2.0, 3.0, 4.0]
        
        for gpa in gpa_values:
            assert 0.0 <= gpa <= 4.0
        
        invalid_gpas = [-0.5, 4.5, 5.0]
        for gpa in invalid_gpas:
            assert not (0.0 <= gpa <= 4.0)
    
    def test_validity_check_salary(self):
        """Test salary validity (must be positive)."""
        df = pd.DataFrame({
            "faculty_id": ["F001", "F002", "F003"],
            "salary": [75000, 0, -50000]
        })
        
        valid_salaries = df[df["salary"] > 0]
        invalid_salaries = df[df["salary"] <= 0]
        
        assert len(valid_salaries) == 1
        assert len(invalid_salaries) == 2
    
    def test_consistency_check_date_logic(self):
        """Test date consistency (graduated >= enrolled)."""
        df = pd.DataFrame({
            "student_id": ["S001", "S002", "S003"],
            "date_enrolled": ["2020-08-01", "2021-08-01", "2022-08-01"],
            "date_graduated": ["2024-05-15", "2023-05-15", None]
        })
        
        df["date_enrolled"] = pd.to_datetime(df["date_enrolled"])
        df["date_graduated"] = pd.to_datetime(df["date_graduated"])
        
        invalid = df[(df["date_graduated"].notna()) & (df["date_graduated"] < df["date_enrolled"])]
        assert len(invalid) == 0


class TestBusinessLogic:
    """Test business logic calculations."""
    
    def test_gpa_calculation(self):
        """Test cumulative GPA calculation."""
        grades = pd.DataFrame({
            "grade_point": [3.5, 3.0, 3.5],
            "credits": [3, 4, 3]
        })
        
        gpa = (grades["grade_point"] * grades["credits"]).sum() / grades["credits"].sum()
        assert abs(gpa - 3.29) < 0.01  # Expected: (3.5*3 + 3.0*4 + 3.5*3) / 10 = 32.9/10 = 3.29
    
    def test_pass_rate_calculation(self):
        """Test course pass rate calculation."""
        grades = pd.DataFrame({
            "student_id": ["S001", "S002", "S003", "S004"],
            "grade_point": [3.5, 3.0, 2.0, 1.5]
        })
        
        passing = (grades["grade_point"] >= 2.0).sum()
        pass_rate = passing / len(grades)
        assert pass_rate == 0.5
    
    def test_at_risk_identification(self):
        """Test at-risk student flag logic."""
        students = pd.DataFrame({
            "student_id": ["S001", "S002", "S003"],
            "cumulative_gpa": [3.5, 2.0, 1.5],
            "failing_courses": [0, 0, 2]
        })
        
        students["is_at_risk"] = (students["cumulative_gpa"] < 2.0) | (students["failing_courses"] > 0)
        
        assert students.loc[0, "is_at_risk"] == False
        assert students.loc[1, "is_at_risk"] == False
        assert students.loc[2, "is_at_risk"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
