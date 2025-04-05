from jupygrader import grade_notebooks
from pathlib import Path

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output" / "file-copy-network"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

base_files = {
    "https://raw.githubusercontent.com/subwaymatch/jupygrader/refs/heads/main/tests/test-files/plaintext-files/base1.txt": "base1.txt",
    "https://raw.githubusercontent.com/subwaymatch/jupygrader/refs/heads/main/tests/test-files/plaintext-files/another-folder/base2.txt": "created-folder/base2.txt",
    "https://raw.githubusercontent.com/subwaymatch/jupygrader/refs/heads/main/tests/test-files/plaintext-files/another-folder/base3.txt": "created-folder/another-folder/base3.txt",
}


def test_file_copy_https():
    item_copy_dict = {
        "notebook_path": TEST_NOTEBOOKS_DIR / "file-copy/file-copy-test-dict.ipynb",
        "output_path": TEST_OUTPUT_DIR,
        "copy_files": {
            TEST_NOTEBOOKS_DIR / "file-copy" / "my-first-input.txt": "copied1.txt",
            (
                TEST_NOTEBOOKS_DIR
                / "file-copy"
                / "input-folder"
                / "my-second-input.txt"
            ).as_posix(): Path("created-folder/another-folder/copied2.txt"),
        },
    }

    results = grade_notebooks(
        [item_copy_dict], base_files=base_files, verbose=False, export_csv=False
    )

    assert results[0].learner_autograded_score == 50
    assert results[0].max_total_score == 50
    assert results[0].num_total_test_cases == 5
