from jupygrader import grade_notebooks, GradingItem
from pathlib import Path

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

base_files = {
    "https://raw.githubusercontent.com/subwaymatch/jupygrader/refs/heads/main/tests/test-files/plaintext-files/base1.txt": "base1.txt",
    "https://raw.githubusercontent.com/subwaymatch/jupygrader/refs/heads/main/tests/test-files/plaintext-files/another-folder/base2.txt": "created-folder/base2.txt",
    "https://raw.githubusercontent.com/subwaymatch/jupygrader/refs/heads/main/tests/test-files/plaintext-files/another-folder/base3.txt": "created-folder/another-folder/base3.txt",
}


def test_file_copy_https():
    item_copy_dict = GradingItem(
        notebook_path=TEST_NOTEBOOKS_DIR / "file-copy/file-copy-test-dict.ipynb",
        output_path=TEST_OUTPUT_DIR / "network-base-files-test",
        copy_files={
            "https://raw.githubusercontent.com/subwaymatch/jupygrader/refs/heads/main/tests/test-files/file-copy/my-first-input.txt": "copied1.txt",
            "https://raw.githubusercontent.com/subwaymatch/jupygrader/refs/heads/main/tests/test-files/file-copy/input-folder/my-second-input.txt": Path(
                "created-folder/another-folder/copied2.txt"
            ),
            "https://this-file-does-not-exist.net/nonexistent.txt": "nonexistent.txt",  # This should be ignored
        },
    )

    results = grade_notebooks(
        [item_copy_dict], base_files=base_files, verbose=False, export_csv=False
    )

    assert results[0].learner_autograded_score == 50
    assert results[0].max_total_score == 50
    assert results[0].num_total_test_cases == 5
