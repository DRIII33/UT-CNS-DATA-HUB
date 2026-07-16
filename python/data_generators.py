"""
Synthetic Data Generator for UT CNS Data Hub
Generates realistic, reproducible datasets for testing and portfolio demonstration
Includes 10 years of historical data with realistic distributions
"""

import os
import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from pathlib import Path
import numpy as np
import pandas as pd
from python.config import (
    NUM_STUDENTS,
    NUM_FACULTY,
    NUM_GRANTS,
    NUM_COURSES,
    STUDENT_COHORT_YEARS,
    STUDENT_GPA_MEAN,
    STUDENT_GPA_STD,
    FACULTY_RANKS,
    TENURE_STATUSES,
    MAJORS,
    DEPARTMENTS,
    FUNDING_AGENCIES,
    GRANT_AWARD_MIN,
    GRANT_AWARD_MAX,
    ENROLLMENTS_PER_STUDENT_PER_YEAR,
    TOTAL_COURSES_IN_DEGREE,
)


class SyntheticDataGenerator:
    """
    Generates realistic synthetic data for UT CNS Data Hub portfolio project.
    
    Characteristics:
    - Reproducible (seed-based)
    - Realistic distributions (normal, uniform, exponential where appropriate)
    - Referential integrity (foreign keys)
    - FERPA-compliant (no real PII, synthetic IDs only)
    - Spanning 10 years of historical data
    """

    def __init__(self, output_dir: str = "data/synthetic", seed: int = 42):
        """
        Initialize the data generator.
        
        Args:
            output_dir: Directory to write CSV files
            seed: Random seed for reproducibility
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
        
        # Store generated data for referential integrity
        self.student_ids: List[str] = []
        self.faculty_ids: List[str] = []
        self.grant_ids: List[str] = []
        self.course_ids: List[str] = []
        
    def generate_students(self, num_students: int = NUM_STUDENTS) -> pd.DataFrame:
        """
        Generate student enrollment and demographic data.
        
        Returns DataFrame with columns:
        - student_id: Unique identifier (STU_XXXXXXXX)
        - cohort_year: Year of admission
        - major: Degree program
        - gpa: Cumulative GPA (0.0-4.0)
        - enrollment_status: Active/Inactive/Graduated/Withdrawn
        - date_enrolled: First enrollment date
        - date_graduated: Graduation date (if applicable)
        - credits_completed: Total credits earned
        - ethnicity: Demographic category
        - first_generation: Boolean flag
        """
        print(f"[GENERATE] Creating {num_students} student records...")
        
        students = []
        self.student_ids = [f"STU_{str(i).zfill(8)}" for i in range(num_students)]
        
        for student_id in self.student_ids:
            # Cohort year: admission year
            cohort_year = np.random.choice(STUDENT_COHORT_YEARS)
            
            # Major: random discipline
            major = np.random.choice(MAJORS)
            
            # GPA: normally distributed around 3.25
            gpa = np.clip(
                np.random.normal(STUDENT_GPA_MEAN, STUDENT_GPA_STD),
                0.0, 4.0
            )
            
            # Enrollment status based on cohort year
            years_since_admission = 2026 - cohort_year
            if years_since_admission < 2:
                enrollment_status = np.random.choice(
                    ["Active", "Withdrawn"], p=[0.95, 0.05]
                )
            elif years_since_admission < 4:
                enrollment_status = np.random.choice(
                    ["Active", "Graduated", "Withdrawn"],
                    p=[0.60, 0.35, 0.05]
                )
            else:
                enrollment_status = np.random.choice(
                    ["Graduated", "Withdrawn"],
                    p=[0.90, 0.10]
                )
            
            # Enrollment date: random date in cohort year
            date_enrolled = datetime(cohort_year, 8, 1) + timedelta(
                days=random.randint(0, 31)
            )
            
            # Graduation date: 4 years after enrollment (if graduated)
            if enrollment_status == "Graduated":
                graduation_year = cohort_year + 4
                date_graduated = datetime(graduation_year, 5, 15) + timedelta(
                    days=random.randint(-30, 30)
                )
            else:
                date_graduated = None
            
            # Credits completed: based on years enrolled and status
            if enrollment_status == "Graduated":
                credits_completed = np.random.randint(120, 135)
            elif enrollment_status == "Active":
                credits_completed = np.random.randint(
                    30 * years_since_admission, 50 * years_since_admission
                )
            else:
                credits_completed = np.random.randint(0, 60)
            
            # Ethnicity: representative of UT Austin demographics
            ethnicity = np.random.choice(
                ["Asian", "White", "Hispanic", "Black", "Non-Resident Alien", "Two or More Races"],
                p=[0.238, 0.351, 0.271, 0.054, 0.050, 0.036]
            )
            
            # First generation: ~22.9% at UT Austin
            first_generation = np.random.choice([True, False], p=[0.229, 0.771])
            
            students.append({
                "student_id": student_id,
                "cohort_year": cohort_year,
                "major": major,
                "gpa": round(gpa, 2),
                "enrollment_status": enrollment_status,
                "date_enrolled": date_enrolled.strftime("%Y-%m-%d"),
                "date_graduated": date_graduated.strftime("%Y-%m-%d") if date_graduated else None,
                "credits_completed": credits_completed,
                "ethnicity": ethnicity,
                "first_generation": first_generation,
            })
        
        df_students = pd.DataFrame(students)
        
        # Write to CSV
        output_file = self.output_dir / "students.csv"
        df_students.to_csv(output_file, index=False)
        print(f"✓ Students saved: {output_file}")
        print(f"  Sample stats: Mean GPA = {df_students['gpa'].mean():.2f}, "
              f"Graduated = {(df_students['enrollment_status']=='Graduated').sum()}")
        
        return df_students
    
    def generate_faculty(self, num_faculty: int = NUM_FACULTY) -> pd.DataFrame:
        """
        Generate faculty employment and compensation data.
        
        Returns DataFrame with columns:
        - faculty_id: Unique identifier (FAC_XXXXXXXX)
        - rank: Academic rank
        - hire_date: Employment start date
        - department: Department affiliation
        - salary: Annual compensation
        - employment_status: Active/On Leave/Retired
        - tenure_status: Tenured/Tenure-Track/Non-Tenure-Track
        - research_focus: Research discipline
        """
        print(f"[GENERATE] Creating {num_faculty} faculty records...")
        
        faculty = []
        self.faculty_ids = [f"FAC_{str(i).zfill(8)}" for i in range(num_faculty)]
        
        for faculty_id in self.faculty_ids:
            # Rank distribution
            rank = np.random.choice(
                FACULTY_RANKS,
                p=[0.35, 0.30, 0.20, 0.10, 0.05]  # Assistant, Associate, Full, Lecturer, Adjunct
            )
            
            # Hire date
            hire_year = np.random.randint(2000, 2025)
            hire_date = datetime(hire_year, random.randint(1, 12), random.randint(1, 28))
            
            # Department
            department = np.random.choice(DEPARTMENTS)
            
            # Salary based on rank (realistic distribution)
            salary_ranges = {
                "Assistant Professor": (70000, 120000),
                "Associate Professor": (95000, 160000),
                "Full Professor": (120000, 280000),
                "Lecturer": (50000, 90000),
                "Adjunct": (30000, 65000),
            }
            salary_min, salary_max = salary_ranges[rank]
            salary = int(np.random.uniform(salary_min, salary_max))
            
            # Employment status (mostly active)
            years_employed = 2026 - hire_year
            if years_employed > 35:
                employment_status = "Retired"
            else:
                employment_status = np.random.choice(
                    ["Active", "On Leave"],
                    p=[0.95, 0.05]
                )
            
            # Tenure status based on rank and years employed
            if rank == "Full Professor":
                tenure_status = "Tenured"
            elif rank == "Associate Professor":
                tenure_status = np.random.choice(
                    ["Tenured", "Tenure-Track"],
                    p=[0.80, 0.20]
                )
            elif rank == "Assistant Professor":
                tenure_status = "Tenure-Track"
            else:
                tenure_status = "Non-Tenure-Track"
            
            # Research focus
            research_focus = np.random.choice(MAJORS)
            
            faculty.append({
                "faculty_id": faculty_id,
                "rank": rank,
                "hire_date": hire_date.strftime("%Y-%m-%d"),
                "department": department,
                "salary": salary,
                "employment_status": employment_status,
                "tenure_status": tenure_status,
                "research_focus": research_focus,
            })
        
        df_faculty = pd.DataFrame(faculty)
        
        # Write to CSV
        output_file = self.output_dir / "faculty.csv"
        df_faculty.to_csv(output_file, index=False)
        print(f"✓ Faculty saved: {output_file}")
        print(f"  Sample stats: Mean salary = ${df_faculty['salary'].mean():,.0f}, "
              f"Tenured = {(df_faculty['tenure_status']=='Tenured').sum()}")
        
        return df_faculty
    
    def generate_grants(self, num_grants: int = NUM_GRANTS) -> pd.DataFrame:
        """
        Generate research grant awards and funding data.
        
        Returns DataFrame with columns:
        - grant_id: Unique identifier
        - pi_id: Principal Investigator (FK to faculty)
        - award_amount: Grant amount in USD
        - funding_agency: Federal, private, industrial
        - start_date: Project start date
        - end_date: Project end date
        - department: Department of PI
        - status: Active/Completed/Cancelled
        - publication_count: Resulting publications
        """
        print(f"[GENERATE] Creating {num_grants} grant records...")
        
        if not self.faculty_ids:
            raise ValueError("Generate faculty records first!")
        
        grants = []
        self.grant_ids = [f"GNT_{str(i).zfill(10)}" for i in range(num_grants)]
        
        for grant_id in self.grant_ids:
            # PI: random faculty member
            pi_id = np.random.choice(self.faculty_ids)
            
            # Award amount: log-normal distribution (most grants are small, some are large)
            award_amount = int(np.random.lognormal(
                mean=np.log(200000),
                sigma=1.5
            ))
            award_amount = max(GRANT_AWARD_MIN, min(award_amount, GRANT_AWARD_MAX))
            
            # Funding agency
            funding_agency = np.random.choice(FUNDING_AGENCIES)
            
            # Start date (2018-2025)
            start_year = np.random.randint(2018, 2025)
            start_date = datetime(start_year, random.randint(1, 12), random.randint(1, 28))
            
            # End date: typically 1-5 years after start
            duration_years = np.random.choice([1, 2, 3, 4, 5], p=[0.10, 0.30, 0.35, 0.15, 0.10])
            end_date = start_date + timedelta(days=duration_years * 365)
            
            # Determine grant status based on end date
            if end_date > datetime(2026, 7, 16):
                status = "Active"
            else:
                status = np.random.choice(["Completed", "Cancelled"], p=[0.95, 0.05])
            
            # Department: infer from faculty (simplified)
            department = "College of Natural Sciences"
            
            # Publications: correlated with award amount and duration
            avg_pubs = (award_amount / 100000) * duration_years
            publication_count = max(0, int(np.random.poisson(avg_pubs)))
            
            grants.append({
                "grant_id": grant_id,
                "pi_id": pi_id,
                "award_amount": award_amount,
                "funding_agency": funding_agency,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "department": department,
                "status": status,
                "publication_count": publication_count,
            })
        
        df_grants = pd.DataFrame(grants)
        
        # Write to CSV
        output_file = self.output_dir / "grants.csv"
        df_grants.to_csv(output_file, index=False)
        print(f"✓ Grants saved: {output_file}")
        print(f"  Sample stats: Mean award = ${df_grants['award_amount'].mean():,.0f}, "
              f"Total funding = ${df_grants['award_amount'].sum():,.0f}")
        
        return df_grants
    
    def generate_courses(self, num_courses: int = NUM_COURSES) -> pd.DataFrame:
        """
        Generate course catalog and teaching information.
        
        Returns DataFrame with columns:
        - course_id: Unique identifier
        - course_code: Department code + number (e.g., BIO101)
        - course_title: Course name
        - credits: Credit hours (1-4)
        - semester: Fall/Spring/Summer
        - year: Academic year
        - instructor_id: Teaching faculty (FK to faculty)
        - enrollment: Student enrollment
        - pass_rate: Percentage passing (0-1)
        - avg_rating: Student rating (1-5)
        """
        print(f"[GENERATE] Creating {num_courses} course records...")
        
        if not self.faculty_ids:
            raise ValueError("Generate faculty records first!")
        
        course_prefixes = ["BIO", "CHEM", "PHYS", "MATH", "STAT", "ASTR", "GEO", "MARIN"]
        courses = []
        self.course_ids = []
        
        for i in range(num_courses):
            # Course code
            prefix = np.random.choice(course_prefixes)
            course_number = np.random.randint(100, 600)
            course_code = f"{prefix}{course_number}"
            course_id = f"CRS_{str(i).zfill(8)}"
            self.course_ids.append(course_id)
            
            # Course title
            course_titles = {
                "BIO": "Biology", "CHEM": "Chemistry", "PHYS": "Physics",
                "MATH": "Mathematics", "STAT": "Statistics", "ASTR": "Astronomy",
                "GEO": "Geology", "MARIN": "Marine Science"
            }
            base_title = course_titles.get(prefix, "Science")
            course_title = f"{base_title} {course_number}"
            
            # Credits
            credits = np.random.choice([1, 2, 3, 4], p=[0.05, 0.10, 0.70, 0.15])
            
            # Semester and year
            semester = np.random.choice(["Fall", "Spring", "Summer"], p=[0.45, 0.45, 0.10])
            year = np.random.randint(2016, 2027)
            
            # Instructor
            instructor_id = np.random.choice(self.faculty_ids)
            
            # Enrollment
            enrollment = np.random.randint(15, 250)
            
            # Pass rate: typically 80-95%
            pass_rate = np.random.uniform(0.75, 0.98)
            
            # Rating: normally distributed around 4.0
            avg_rating = np.clip(np.random.normal(4.0, 0.5), 1.0, 5.0)
            
            courses.append({
                "course_id": course_id,
                "course_code": course_code,
                "course_title": course_title,
                "credits": credits,
                "semester": semester,
                "year": year,
                "instructor_id": instructor_id,
                "enrollment": enrollment,
                "pass_rate": round(pass_rate, 3),
                "avg_rating": round(avg_rating, 1),
            })
        
        df_courses = pd.DataFrame(courses)
        
        # Write to CSV
        output_file = self.output_dir / "courses.csv"
        df_courses.to_csv(output_file, index=False)
        print(f"✓ Courses saved: {output_file}")
        print(f"  Sample stats: Mean enrollment = {df_courses['enrollment'].mean():.0f}, "
              f"Avg rating = {df_courses['avg_rating'].mean():.2f}")
        
        return df_courses
    
    def generate_enrollments(self, df_students: pd.DataFrame, df_courses: pd.DataFrame) -> pd.DataFrame:
        """
        Generate student course enrollments with grades.
        
        Returns DataFrame with columns:
        - enrollment_id: Unique identifier
        - student_id: Student (FK)
        - course_id: Course (FK)
        - semester: Academic term
        - year: Academic year
        - grade: Letter grade
        - grade_point: Numeric grade (0-4)
        - credits_earned: Credits toward degree
        """
        print(f"[GENERATE] Creating enrollment records...")
        
        enrollments = []
        enrollment_counter = 0
        
        for _, student in df_students.iterrows():
            student_id = student["student_id"]
            cohort_year = student["cohort_year"]
            student_gpa = student["gpa"]
            
            # Number of enrollments per student (typically 4 per year)
            years_enrolled = 2026 - cohort_year
            num_enrollments = years_enrolled * ENROLLMENTS_PER_STUDENT_PER_YEAR
            
            for _ in range(num_enrollments):
                # Random course
                course = df_courses.sample(1).iloc[0]
                course_id = course["course_id"]
                
                # Random semester/year within student's enrollment window
                enrollment_year = np.random.randint(cohort_year, 2026)
                semester = np.random.choice(["Fall", "Spring", "Summer"])
                
                # Grade: correlated with student GPA
                if student_gpa >= 3.5:
                    grade_point = np.clip(np.random.normal(3.6, 0.3), 0.0, 4.0)
                elif student_gpa >= 3.0:
                    grade_point = np.clip(np.random.normal(3.2, 0.4), 0.0, 4.0)
                elif student_gpa >= 2.5:
                    grade_point = np.clip(np.random.normal(2.7, 0.5), 0.0, 4.0)
                else:
                    grade_point = np.clip(np.random.normal(2.0, 0.8), 0.0, 4.0)
                
                # Convert grade point to letter grade
                if grade_point >= 3.7:
                    grade = "A"
                elif grade_point >= 3.3:
                    grade = "A-"
                elif grade_point >= 3.0:
                    grade = "B+"
                elif grade_point >= 2.7:
                    grade = "B"
                elif grade_point >= 2.3:
                    grade = "B-"
                elif grade_point >= 2.0:
                    grade = "C"
                elif grade_point >= 1.0:
                    grade = "D"
                else:
                    grade = "F"
                
                # Credits earned (0 if F, else course credits)
                credits_earned = 0 if grade == "F" else int(course["credits"])
                
                enrollment_id = f"ENR_{str(enrollment_counter).zfill(10)}"
                enrollment_counter += 1
                
                enrollments.append({
                    "enrollment_id": enrollment_id,
                    "student_id": student_id,
                    "course_id": course_id,
                    "semester": semester,
                    "year": enrollment_year,
                    "grade": grade,
                    "grade_point": round(grade_point, 2),
                    "credits_earned": credits_earned,
                })
        
        df_enrollments = pd.DataFrame(enrollments)
        
        # Write to CSV
        output_file = self.output_dir / "enrollments.csv"
        df_enrollments.to_csv(output_file, index=False)
        print(f"✓ Enrollments saved: {output_file}")
        print(f"  Total records: {len(df_enrollments)}")
        
        return df_enrollments
    
    def generate_all(self) -> Dict[str, pd.DataFrame]:
        """
        Generate all datasets in correct order (respecting referential integrity).
        
        Returns:
            Dictionary of all generated DataFrames
        """
        print("\n" + "="*70)
        print("UT CNS DATA HUB - SYNTHETIC DATA GENERATION")
        print("="*70 + "\n")
        
        # Generate dimension data first
        df_students = self.generate_students()
        df_faculty = self.generate_faculty()
        df_grants = self.generate_grants()
        df_courses = self.generate_courses()
        
        # Generate fact data (dependent on dimensions)
        df_enrollments = self.generate_enrollments(df_students, df_courses)
        
        print("\n" + "="*70)
        print("DATA GENERATION COMPLETE")
        print("="*70)
        print(f"Output directory: {self.output_dir}")
        print(f"\nSummary:")
        print(f"  Students: {len(df_students):,}")
        print(f"  Faculty: {len(df_faculty):,}")
        print(f"  Grants: {len(df_grants):,}")
        print(f"  Courses: {len(df_courses):,}")
        print(f"  Enrollments: {len(df_enrollments):,}")
        print("="*70 + "\n")
        
        return {
            "students": df_students,
            "faculty": df_faculty,
            "grants": df_grants,
            "courses": df_courses,
            "enrollments": df_enrollments,
        }


def main():
    """Main entry point for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate synthetic data for UT CNS Data Hub"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/synthetic",
        help="Output directory for CSV files"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--students", "-st",
        type=int,
        default=NUM_STUDENTS,
        help="Number of students to generate"
    )
    parser.add_argument(
        "--faculty", "-f",
        type=int,
        default=NUM_FACULTY,
        help="Number of faculty to generate"
    )
    parser.add_argument(
        "--grants", "-g",
        type=int,
        default=NUM_GRANTS,
        help="Number of grants to generate"
    )
    parser.add_argument(
        "--courses", "-c",
        type=int,
        default=NUM_COURSES,
        help="Number of courses to generate"
    )
    
    args = parser.parse_args()
    
    # Create generator and run
    generator = SyntheticDataGenerator(output_dir=args.output, seed=args.seed)
    
    # Override defaults with CLI arguments
    generator.generate_all()


if __name__ == "__main__":
    main()
