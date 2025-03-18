import jupygrader
from pathlib import Path

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-notebooks"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_basic_workflow():
    notebook_path = TEST_NOTEBOOKS_DIR / "simple" / "simple-test.ipynb"

    result = jupygrader.grade_notebook(
        notebook_path=notebook_path,
        output_path=TEST_OUTPUT_DIR,
    )

    # Check the accuracy of the result object
    assert result.filename == "simple-test.ipynb"
    assert result.learner_autograded_score == 55
    assert result.max_autograded_score == 60
    assert result.max_manually_graded_score == 10
    assert result.max_total_score == 70
    assert result.num_total_test_cases == 7
    assert result.num_passed_cases == 5
    assert result.num_failed_cases == 1
    assert result.num_autograded_cases == 6
    assert result.num_manually_graded_cases == 1

    # Check that results contains a list of test cases
    assert hasattr(result, "test_case_results")
    assert isinstance(result.test_case_results, list)
    assert len(result.test_case_results) == 7

    # Check that each test case result has all required attributes
    for test_result in result.test_case_results:
        # Check that all required attributes exist
        assert hasattr(test_result, "test_case_name")
        assert hasattr(test_result, "points")
        assert hasattr(test_result, "available_points")
        assert hasattr(test_result, "did_pass")
        assert hasattr(test_result, "grade_manually")
        assert hasattr(test_result, "message")

        # Check types of values
        assert isinstance(test_result.test_case_name, str)
        assert isinstance(test_result.points, (int, float))
        assert isinstance(test_result.available_points, (int, float))
        assert isinstance(test_result.did_pass, bool) or test_result.did_pass is None
        assert isinstance(test_result.grade_manually, bool)
        assert isinstance(test_result.message, str)


def test_file_copy_01():
    notebook_path = TEST_NOTEBOOKS_DIR / "file-copy/file-copy-test-list.ipynb"

    result = jupygrader.grade_notebook(
        notebook_path=notebook_path,
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

    assert result.learner_autograded_score == 30
    assert result.max_total_score == 30
    assert result.num_total_test_cases == 3


def test_file_copy_02():
    notebook_path = TEST_NOTEBOOKS_DIR / "file-copy/file-copy-test-dict.ipynb"

    result = jupygrader.grade_notebook(
        notebook_path=notebook_path,
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

    assert result.learner_autograded_score == 20
    assert result.max_total_score == 20
    assert result.num_total_test_cases == 2


def test_notebook_without_test_cases():
    notebook_path = TEST_NOTEBOOKS_DIR / "no-test-cases" / "no-test-cases-test.ipynb"

    result = jupygrader.grade_notebook(
        notebook_path=notebook_path, output_path=TEST_OUTPUT_DIR
    )

    assert result.learner_autograded_score == 0
    assert result.max_total_score == 0
    assert result.num_total_test_cases == 0
