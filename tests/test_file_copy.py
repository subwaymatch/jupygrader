from jupygrader import grade_notebooks, GradingItemConfig
from pathlib import Path

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-notebooks"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_file_copy():
    item1 = GradingItemConfig(
        notebook_path=TEST_NOTEBOOKS_DIR / "file-copy/file-copy-test-list.ipynb",
        output_path=TEST_OUTPUT_DIR,
        copy_files=[
            TEST_NOTEBOOKS_DIR / "file-copy" / "my-first-input.txt",
            TEST_NOTEBOOKS_DIR / "file-copy" / "input-folder" / "my-second-input.txt",
            (
                TEST_NOTEBOOKS_DIR
                / "file-copy"
                / "input-folder/another-nested-folder/my-third-input.txt"
            ).as_posix(),
        ],
    )

    item2 = GradingItemConfig(
        notebook_path=TEST_NOTEBOOKS_DIR / "file-copy/file-copy-test-dict.ipynb",
        output_path=TEST_OUTPUT_DIR,
        copy_files={
            TEST_NOTEBOOKS_DIR / "file-copy" / "my-first-input.txt": "copied1.txt",
            (
                TEST_NOTEBOOKS_DIR
                / "file-copy"
                / "input-folder"
                / "my-second-input.txt"
            ).as_posix(): Path("created-folder/another-folder/copied2.txt"),
        },
    )

    results = grade_notebooks([item1, item2], verbose=False)

    assert results[0].learner_autograded_score == 30
    assert results[0].max_total_score == 30
    assert results[0].num_total_test_cases == 3

    assert results[1].learner_autograded_score == 20
    assert results[1].max_total_score == 20
    assert results[1].num_total_test_cases == 2
