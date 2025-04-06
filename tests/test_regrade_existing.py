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
    graded_notebook_path = TEST_OUTPUT_DIR / f"{Path(filename).stem}-graded.ipynb"

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
    modified_time1 = os.path.getmtime(results1[0].graded_result_json_file)

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
    modified_time2 = os.path.getmtime(results2[0].graded_result_json_file)

    # First and second results should be identical (cached result used)
    assert (
        modified_time1 == modified_time2
    ), "Expected second grading to reuse the cached result"

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
    modified_time3 = os.path.getmtime(results3[0].graded_result_json_file)

    # Third result should differ (file regraded and overwritten)
    assert (
        modified_time2 != modified_time3
    ), "Expected third grading to regrade and update the file"

    # Try grading the graded notebook file with regrade_existing=True
    # This should not regrade the notebook since it is already graded
    results4 = grade_notebooks(
        [
            {
                "notebook_path": graded_notebook_path,
                "output_path": TEST_OUTPUT_DIR,
            }
        ],
        regrade_existing=True,
        export_csv=False,
    )

    assert len(results4) == 0
