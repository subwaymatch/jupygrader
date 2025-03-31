import jupygrader
from pathlib import Path
import glob
import shutil

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output"


# use this file to run only a single test function
# hatch test tests/test_single.py
def test_batch_grader():
    notebook_path = TEST_NOTEBOOKS_DIR / "batch"

    test_notebook_paths = glob.glob(str(notebook_path / "grader-file-[0-9][0-9].ipynb"))

    grading_items = [
        jupygrader.GradingItem(notebook_path=notebook)
        for notebook in test_notebook_paths
    ]

    results = jupygrader.grade_notebooks(
        items_to_grade=grading_items,
        csv_output_path=TEST_OUTPUT_DIR / "batch-test-results.csv",
    )

    # Cleanup
    test_notebook_set = {str(Path(tp).resolve()) for tp in test_notebook_paths}

    # Iterate over files in notebook_path
    for file in notebook_path.iterdir():
        if file.is_file() and str(file.resolve()) not in test_notebook_set:
            shutil.move(str(file), str(TEST_OUTPUT_DIR / file.name))

    assert len(results) == 2
