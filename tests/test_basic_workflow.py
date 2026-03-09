from jupygrader import grade_notebooks
from pathlib import Path

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output" / "basic-workflow"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_basic_workflow():
    filename = "basic.ipynb"
    notebook_path = TEST_NOTEBOOKS_DIR / "basic-workflow" / filename
    filename_base = notebook_path.stem

    result = grade_notebooks(
        [
            {
                "notebook_path": notebook_path,
                "output_path": TEST_OUTPUT_DIR,
            }
        ],
        regrade_existing=True,
        execution_timeout=120,
    )[0]

    # Check the accuracy of the result object
    assert result.filename == filename
    assert result.learner_autograded_score == 1.5
    assert result.max_autograded_score == 3
    assert result.max_manually_graded_score == 1
    assert result.max_total_score == 4
    assert result.num_total_test_cases == 4
    assert result.num_passed_cases == 2
    assert result.num_failed_cases == 1
    assert result.num_autograded_cases == 3
    assert result.num_manually_graded_cases == 1

    # Check that results contains a list of test cases
    assert hasattr(result, "test_case_results")
    assert isinstance(result.test_case_results, list)
    assert len(result.test_case_results) == 4

    graded_html_path = TEST_OUTPUT_DIR / f"{filename_base}-graded.html"
    graded_ipynb_path = TEST_OUTPUT_DIR / f"{filename_base}-graded.ipynb"
    graded_json_path = TEST_OUTPUT_DIR / f"{filename_base}-graded-result.json"
    graded_summary_path = TEST_OUTPUT_DIR / f"{filename_base}-graded-result-summary.txt"

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
