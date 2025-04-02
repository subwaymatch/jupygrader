from dataclasses import dataclass, field, asdict
from typing import List, Optional, Union, Dict, Any, TypedDict
from pathlib import Path

FilePath = Union[str, Path]
FileDict = Dict[FilePath, FilePath]


@dataclass
class GradingItem:
    notebook_path: FilePath
    output_path: Optional[FilePath] = None
    copy_files: Optional[Union[FilePath, List[FilePath], FileDict]] = None


@dataclass
class BatchGradingConfig:
    verbose: bool = False
    export_csv: bool = True
    base_files: Optional[Dict[Path, Path]] = None
    csv_output_path: Optional[str] = None


@dataclass
class TestCaseMetadata:
    """Metadata for a test case defined in a notebook.

    Extracted from test case cells in notebooks, this class holds
    information about the test case name, point value, and grading mode.

    Args:
        test_case_name: Unique identifier for the test case
        points: Points awarded for passing this test case
        grade_manually: Whether this test case should be graded manually
    """

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
    """Result of an individual test case execution in a notebook.

    This class stores the outcome of executing a test case during grading,
    including the points awarded, whether the test passed, and any output
    messages generated during execution.

    Args:
        test_case_name: Unique identifier for the test case. Defaults to "".
        points: Points awarded for this test case (0 if failed). Defaults to 0.
        available_points: Maximum possible points for this test case. Defaults to 0.
        did_pass: Whether the test case passed (True), failed (False),
            or requires manual grading (None). Defaults to None.
        grade_manually: Whether this test case should be graded manually. Defaults to False.
        message: Output message from the test execution, typically contains
            error information if the test failed. Defaults to "".
    """

    test_case_name: str = ""
    points: Union[int, float] = 0
    available_points: Union[int, float] = 0
    did_pass: Optional[bool] = None  # Can be True, False, or None
    grade_manually: bool = False
    message: str = ""


@dataclass
class GradedResult:
    """Complete results of grading a Jupyter notebook.

    This comprehensive class stores all information related to grading a notebook,
    including scores, test case results, execution environment details, and file paths
    for generated outputs.

    Args:
        filename: Name of the graded notebook file. Defaults to "".
        learner_autograded_score: Points earned from automatically graded test cases. Defaults to 0.
        max_autograded_score: Maximum possible points from automatically graded test cases. Defaults to 0.
        max_manually_graded_score: Maximum possible points from manually graded test cases. Defaults to 0.
        max_total_score: Total maximum possible points across all test cases. Defaults to 0.
        num_autograded_cases: Number of automatically graded test cases. Defaults to 0.
        num_passed_cases: Number of passed test cases. Defaults to 0.
        num_failed_cases: Number of failed test cases. Defaults to 0.
        num_manually_graded_cases: Number of test cases requiring manual grading. Defaults to 0.
        num_total_test_cases: Total number of test cases in the notebook. Defaults to 0.
        grading_finished_at: Timestamp when grading completed. Defaults to "".
        grading_duration_in_seconds: Time taken to complete grading. Defaults to 0.0.
        test_case_results: Detailed results for each individual test case. Defaults to empty list.
        submission_notebook_hash: MD5 hash of the submitted notebook file. Defaults to "".
        test_cases_hash: MD5 hash of test case code in the notebook. Defaults to "".
        grader_python_version: Python version used for grading. Defaults to "".
        grader_platform: Platform information where grading occurred. Defaults to "".
        jupygrader_version: Version of Jupygrader used. Defaults to "".
        extracted_user_code_file: Path to file containing extracted user code. Defaults to None.
        graded_html_file: Path to HTML output of graded notebook. Defaults to None.
        text_summary_file: Path to text summary file. Defaults to None.
    """

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
        result_dict = asdict(self)

        # Add the computed text_summary to the dictionary
        result_dict["text_summary"] = self.text_summary

        return result_dict
