import csv
from pathlib import Path

from jupygrader import grade_notebooks


TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output" / "failure-reporting"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_failed_notebook_is_recorded_in_csv():
    valid_notebook = TEST_NOTEBOOKS_DIR / "failure-reporting" / "minimal.ipynb"
    invalid_notebook = TEST_NOTEBOOKS_DIR / "failure-reporting" / "invalid.ipynb"

    grading_items = [
        {"notebook_path": valid_notebook, "output_path": TEST_OUTPUT_DIR},
        {"notebook_path": invalid_notebook, "output_path": TEST_OUTPUT_DIR},
    ]

    results = grade_notebooks(
        grading_items=grading_items,
        csv_output_path=TEST_OUTPUT_DIR / "graded_results_invalid_notebook.csv",
        regrade_existing=True,
        verbose=False,
    )

    assert len(results) == 1

    csv_files = list(TEST_OUTPUT_DIR.glob("graded_results_invalid_notebook.csv"))
    assert len(csv_files) == 1

    with csv_files[0].open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2

    success_rows = [row for row in rows if row.get("is_success") == "True"]
    failure_rows = [row for row in rows if row.get("is_success") == "False"]

    assert len(success_rows) == 1
    assert len(failure_rows) == 1

    assert success_rows[0]["filename"] == "minimal.ipynb"
    assert failure_rows[0]["filename"] == "invalid.ipynb"


def test_timeout():
    notebook_path = TEST_NOTEBOOKS_DIR / "failure-reporting" / "timeout.ipynb"

    grading_items = [
        {"notebook_path": notebook_path, "output_path": TEST_OUTPUT_DIR},
    ]

    results = grade_notebooks(
        grading_items=grading_items,
        csv_output_path=TEST_OUTPUT_DIR / "graded_results_timeout.csv",
        regrade_existing=True,
        execution_timeout=1,  # 1 second timeout to trigger the timeout test case
        verbose=False,
    )

    print(results)
