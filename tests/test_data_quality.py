import pytest
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.data_generators import SyntheticDataGenerator

class TestDataQuality:
    def test_validity_check_gpa(self):
        gpa_values = [0.0, 1.5, 2.0, 3.0, 4.0]
        for gpa in gpa_values:
            assert 0.0 <= gpa <= 4.0

    def test_completeness_check(self):
        df = pd.DataFrame({
            'student_id': ['S001', None, 'S003'],
            'gpa': [3.5, 3.2, None]
        })
        assert df['student_id'].isna().sum() == 1
        assert df['gpa'].isna().sum() == 1