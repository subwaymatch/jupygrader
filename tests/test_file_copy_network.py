from jupygrader import grade_notebooks, GradingItem
from pathlib import Path

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_file_copy_https():
    item_copy_dict = GradingItem(
        notebook_path=TEST_NOTEBOOKS_DIR / "file-copy/file-copy-test-dict.ipynb",
        output_path=TEST_OUTPUT_DIR,
        copy_files={
            "https://raw.githubusercontent.com/subwaymatch/jupygrader/refs/heads/main/tests/test-files/file-copy/my-first-input.txt": "copied1.txt",
            "https://raw.githubusercontent.com/subwaymatch/jupygrader/refs/heads/main/tests/test-files/file-copy/input-folder/my-second-input.txt": Path(
                "created-folder/another-folder/copied2.txt"
            ),
        },
    )

    results = grade_notebooks([item_copy_dict], verbose=False, export_csv=False)

    assert results[0].learner_autograded_score == 20
    assert results[0].max_total_score == 20
    assert results[0].num_total_test_cases == 2
