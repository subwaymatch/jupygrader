from dataclasses import dataclass, field, asdict
from typing import List, Optional, Union, Dict, Any
from pathlib import Path


@dataclass
class GradingItemConfig:
    notebook_path: Union[str, Path]
    output_path: Optional[Union[str, Path]] = None
    copy_files: Optional[Union[str, Path, List[Union[str, Path]]]] = None


@dataclass
class TestCaseMetadata:
    test_case_name: str
    points: Union[int, float]
    grade_manually: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCaseMetadata":
        return cls(
            test_case_name=data["test_case_name"],
            points=data["points"],
            grade_manually=data["grade_manually"],
        )

    @classmethod
    def to_dict(cls, instance: "TestCaseMetadata") -> Dict[str, Any]:
        return {
            "test_case_name": instance.test_case_name,
            "points": instance.points,
            "grade_manually": instance.grade_manually,
        }


@dataclass
class TestCaseResult:
    """Result of an individual test case in the notebook."""

    test_case_name: str = ""
    points: Union[int, float] = 0
    available_points: Union[int, float] = 0
    did_pass: Optional[bool] = None  # Can be True, False, or None
    grade_manually: bool = False
    message: str = ""


@dataclass
class GradedResult:
    """Complete results of grading a notebook."""

    filename: str = ""
    learner_autograded_score: Union[int, float] = 0
    max_autograded_score: Union[int, float] = 0
    max_manually_graded_score: Union[int, float] = 0
    max_total_score: Union[int, float] = 0
    num_autograded_cases: int = 0
    num_passed_cases: int = 0
    num_failed_cases: int = 0
    num_manually_graded_cases: int = 0
    num_total_test_cases: int = 0
    grading_finished_at: str = ""
    grading_duration_in_seconds: float = 0.0
    test_case_results: List[TestCaseResult] = field(default_factory=list)
    submission_notebook_hash: str = ""
    test_cases_hash: str = ""
    grader_python_version: str = ""
    grader_platform: str = ""
    jupygrader_version: str = ""
    extracted_user_code_file: Optional[str] = None
    graded_html_file: Optional[str] = None
    text_summary_file: Optional[str] = None

    @property
    def text_summary(self) -> str:
        """
        Generates a text summary of the grading results.

        Returns
        -------
        str
            A formatted text summary of the grading results
        """
        summary_parts = [
            f"File: {self.filename}",
            f"Autograded Score: {self.learner_autograded_score} out of {self.max_autograded_score}",
            f"Passed {self.num_passed_cases} out of {self.num_autograded_cases} test cases",
        ]

        if self.num_manually_graded_cases > 0:
            summary_parts.extend(
                [
                    f"{self.num_manually_graded_cases} items will be graded manually.",
                    f"{self.max_manually_graded_score} points are available for manually graded items.",
                    f"{self.max_total_score} total points are available.",
                ]
            )

        summary_parts.append(
            f"Grading took {self.grading_duration_in_seconds:.2f} seconds\n"
        )
        summary_parts.append("Test Case Summary")

        for test_case in self.test_case_results:
            summary_parts.append("-----------------")

            if test_case.grade_manually:
                summary_parts.append(
                    f"{test_case.test_case_name}: requires manual grading, {test_case.available_points} points available"
                )
            else:
                summary_parts.append(
                    f"{test_case.test_case_name}: {'PASS' if test_case.did_pass else 'FAIL'}, {test_case.points} out of {test_case.available_points} points"
                )

                if not test_case.did_pass:
                    summary_parts.extend(
                        ["\n[Autograder Output]", f"{test_case.message}"]
                    )

        return "\n".join(summary_parts)

    @classmethod
    def from_dict(cls, data: dict) -> "GradedResult":
        """Creates a GradedResult instance from a dictionary."""
        # Copy the dictionary to avoid modifying the original
        data_copy = data.copy()

        # Remove 'text_summary' if present in the data since it's now a computed property
        if "text_summary" in data_copy:
            del data_copy["text_summary"]

        # Process test_case_results
        test_case_results = [
            TestCaseResult(**item) for item in data_copy.get("test_case_results", [])
        ]
        data_copy["test_case_results"] = test_case_results
        return cls(**data_copy)

    def to_dict(self) -> dict:
        """Converts the GradedResult instance to a dictionary."""
        result_dict = asdict(self)

        # Add the computed text_summary to the dictionary
        result_dict["text_summary"] = self.text_summary

        return result_dict
