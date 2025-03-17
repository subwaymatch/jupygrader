from dataclasses import dataclass
from typing import List, Optional, Union
from pathlib import Path


@dataclass
class GradingItemConfig:
    notebook_path: Union[str, Path]
    output_path: Optional[Union[str, Path]] = None
    copy_files: Optional[Union[str, Path, List[Union[str, Path]]]] = None


@dataclass
class TestCaseResult:
    """Result of an individual test case in the notebook."""

    test_case_name: str
    points: int
    available_points: int
    did_pass: Optional[bool]  # Can be true, false, or null
    grade_manually: bool
    message: str


@dataclass
class GradedResult:
    """Complete results of grading a notebook."""

    filename: str
    learner_autograded_score: int
    max_autograded_score: int
    max_manually_graded_score: int
    max_total_score: int
    num_autograded_cases: int
    num_passed_cases: int
    num_failed_cases: int
    num_manually_graded_cases: int
    num_total_test_cases: int
    grading_finished_at: str
    grading_duration_in_seconds: float
    results: List[TestCaseResult]
    submission_notebook_hash: str
    test_cases_hash: str
    grader_python_version: str
    grader_platform: str
    jupygrader_version: str
    extracted_user_code_file: Optional[str] = None
    graded_html_file: Optional[str] = None
    text_summary_file: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "GradedResult":
        """Create a GradedResult instance from a dictionary."""
        # Create TestCaseResult objects from the 'results' list in the data
        test_results = []
        for result in data.get("results", []):
            test_results.append(TestCaseResult(**result))

        # Create the GradedResult with all other fields
        return cls(
            **{k: v for k, v in data.items() if k != "results"}, results=test_results
        )

    def to_dict(self) -> dict:
        """Convert the GradedResult to a dictionary."""
        # Create a base dictionary from main attributes
        result_dict = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
            if field != "results"
        }

        # Convert test results to list of dictionaries
        result_dict["results"] = [
            {
                "test_case_name": result.test_case_name,
                "points": result.points,
                "available_points": result.available_points,
                "did_pass": result.did_pass,
                "grade_manually": result.grade_manually,
                "message": result.message,
            }
            for result in self.results
        ]

        return result_dict
