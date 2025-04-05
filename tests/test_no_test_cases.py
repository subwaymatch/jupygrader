from jupygrader import grade_single_notebook
from pathlib import Path

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_notebook_without_test_cases():
    notebook_path = TEST_NOTEBOOKS_DIR / "no-test-cases" / "no-test-cases-test.ipynb"

    result = grade_single_notebook(
        {
            "notebook_path": notebook_path,
            "output_path": TEST_OUTPUT_DIR,
        }
    )

    assert result.learner_autograded_score == 0
    assert result.max_total_score == 0
    assert result.num_total_test_cases == 0
