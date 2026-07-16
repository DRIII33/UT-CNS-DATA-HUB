import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.data_generators import SyntheticDataGenerator

class TestDataGeneration:
    def test_student_generation_zero_tenure(self, tmp_path):
        # Verify that students in the current cohort (years_since_admission = 0) generate without error
        generator = SyntheticDataGenerator(output_dir=str(tmp_path), seed=42)
        # Forcing a small batch to test the logic
        try:
            df = generator.generate_students(num_students=10)
            assert len(df) == 10
            assert 'credits_completed' in df.columns
            assert (df['credits_completed'] >= 0).all()
        except ValueError as e:
            pytest.fail(f'Data generation failed with ValueError: {e}')