from jupygrader import grade_notebooks
from pathlib import Path

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output" / "file-copy-local"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

base_files = {
    TEST_NOTEBOOKS_DIR / "plaintext-files" / "base1.txt": "base1.txt",
    TEST_NOTEBOOKS_DIR
    / "plaintext-files"
    / "another-folder"
    / "base2.txt": "created-folder/base2.txt",
    TEST_NOTEBOOKS_DIR
    / "plaintext-files"
    / "another-folder"
    / "base3.txt": "created-folder/another-folder/base3.txt",
}


def test_file_copy_local():
    item_copy_list = {
        "notebook_path": TEST_NOTEBOOKS_DIR / "file-copy/file-copy-test-list.ipynb",
        "output_path": TEST_OUTPUT_DIR,
        "copy_files": [
            TEST_NOTEBOOKS_DIR / "file-copy" / "my-first-input.txt",
            TEST_NOTEBOOKS_DIR / "file-copy" / "input-folder" / "my-second-input.txt",
            (
                TEST_NOTEBOOKS_DIR
                / "file-copy"
                / "input-folder/another-nested-folder/my-third-input.txt"
            ).as_posix(),
        ],
    }

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
        [item_copy_list, item_copy_dict],
        base_files=base_files,
        verbose=True,
        export_csv=False,
        regrade_existing=True,
    )

    assert results[0].learner_autograded_score == 60
    assert results[0].max_total_score == 60
    assert results[0].num_total_test_cases == 6

    assert results[1].learner_autograded_score == 50
    assert results[1].max_total_score == 50
    assert results[1].num_total_test_cases == 5
