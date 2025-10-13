import csv
from pathlib import Path

from jupygrader import grade_notebooks


TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"


def test_failed_notebook_is_recorded_in_csv(tmp_path):
    valid_notebook = TEST_NOTEBOOKS_DIR / "basic-workflow" / "minimal.ipynb"
    invalid_notebook = tmp_path / "invalid.ipynb"
    invalid_notebook.write_text("{ not valid json", encoding="utf-8")

    output_dir = tmp_path / "outputs"
    output_dir.mkdir()

    csv_dir = tmp_path / "csv"
    csv_dir.mkdir()

    grading_items = [
        {"notebook_path": valid_notebook, "output_path": output_dir},
        {"notebook_path": invalid_notebook, "output_path": output_dir},
    ]

    results = grade_notebooks(
        grading_items=grading_items,
        csv_output_path=csv_dir,
        regrade_existing=True,
        verbose=False,
    )

    assert len(results) == 1

    csv_files = list(csv_dir.glob("graded_results_*.csv"))
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
    assert "Notebook does not appear to be JSON" in failure_rows[0]["text_summary"]
