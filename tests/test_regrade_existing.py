from jupygrader import grade_notebooks
from pathlib import Path
import os
import shutil

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output" / "regrade-existing"

if TEST_OUTPUT_DIR.exists():
    shutil.rmtree(TEST_OUTPUT_DIR)

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_regrade_existing():
    filename = "minimal.ipynb"
    notebook_path = TEST_NOTEBOOKS_DIR / "basic-workflow" / filename

    results1 = grade_notebooks(
        [
            {
                "notebook_path": notebook_path,
                "output_path": TEST_OUTPUT_DIR,
            }
        ],
        regrade_existing=True,
        export_csv=False,
    )

    created_time1 = os.path.getmtime(results1[0].graded_result_json_file)

    results2 = grade_notebooks(
        [
            {
                "notebook_path": notebook_path,
                "output_path": TEST_OUTPUT_DIR,
            }
        ],
        regrade_existing=False,
        export_csv=False,
    )
    created_time2 = os.path.getmtime(results2[0].graded_result_json_file)

    results3 = grade_notebooks(
        [
            {
                "notebook_path": notebook_path,
                "output_path": TEST_OUTPUT_DIR,
            }
        ],
        regrade_existing=True,
        export_csv=False,
    )

    created_time3 = os.path.getmtime(results3[0].graded_result_json_file)

    # First and second results should be identical (cached result used)
    assert (
        created_time1 == created_time2
    ), "Expected second grading to reuse the cached result"

    # Third result should differ (file regraded and overwritten)
    assert (
        created_time2 != created_time3
    ), "Expected third grading to regrade and update the file"
