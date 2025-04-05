from jupygrader import grade_single_notebook
from pathlib import Path

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_basic_workflow():
    filename = "common-notebook.ipynb"
    notebook_path = TEST_NOTEBOOKS_DIR / "basic-workflow" / filename
    filename_base = notebook_path.stem

    result = grade_single_notebook(
        {
            "notebook_path": notebook_path,
            "output_path": TEST_OUTPUT_DIR,
        },
        regrade_existing=True,
    )

    # Check the accuracy of the result object
    assert result.filename == filename
    assert result.learner_autograded_score == 55
    assert result.max_autograded_score == 60
    assert result.max_manually_graded_score == 10
    assert result.max_total_score == 70
    assert result.num_total_test_cases == 7
    assert result.num_passed_cases == 5
    assert result.num_failed_cases == 1
    assert result.num_autograded_cases == 6
    assert result.num_manually_graded_cases == 1

    # Check that results contains a list of test cases
    assert hasattr(result, "test_case_results")
    assert isinstance(result.test_case_results, list)
    assert len(result.test_case_results) == 7

    # Check that each test case result has all required attributes
    for test_result in result.test_case_results:
        # Check that all required attributes exist
        assert hasattr(test_result, "test_case_name")
        assert hasattr(test_result, "points")
        assert hasattr(test_result, "available_points")
        assert hasattr(test_result, "did_pass")
        assert hasattr(test_result, "grade_manually")
        assert hasattr(test_result, "message")

        # Check types of values
        assert isinstance(test_result.test_case_name, str)
        assert isinstance(test_result.points, (int, float))
        assert isinstance(test_result.available_points, (int, float))
        assert isinstance(test_result.did_pass, bool) or test_result.did_pass is None
        assert isinstance(test_result.grade_manually, bool)
        assert isinstance(test_result.message, str)

        graded_html_path = TEST_OUTPUT_DIR / f"{filename_base}-graded.html"
        graded_ipynb_path = TEST_OUTPUT_DIR / f"{filename_base}-graded.ipynb"
        graded_json_path = TEST_OUTPUT_DIR / f"{filename_base}-graded-result.json"
        graded_summary_path = (
            TEST_OUTPUT_DIR / f"{filename_base}-graded-result-summary.txt"
        )

        assert (
            graded_html_path.exists()
        ), f"Expected HTML file not found: {graded_html_path}"
        assert (
            graded_ipynb_path.exists()
        ), f"Expected graded notebook not found: {graded_ipynb_path}"
        assert (
            graded_json_path.exists()
        ), f"Expected result JSON file not found: {graded_json_path}"
        assert (
            graded_summary_path.exists()
        ), f"Expected text summary file not found: {graded_summary_path}"
