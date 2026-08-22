"""Regression tests for bugs found during the code audit."""

import csv
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from nbformat.v4 import new_code_cell, new_notebook

from jupygrader import AIGradingMode, grade_notebooks
from jupygrader.grading.ai_grader import AIGrader
from jupygrader.grading.base_grading_task import sanitize_for_markdown_table
from jupygrader.grading.batch_grading_manager import BatchGradingManager
from jupygrader.grading.execution_grading_task import ExecutionGradingTask
from jupygrader.models.ai_models import AIParsedResult, AITestCaseResult
from jupygrader.models.results import GradedResult, TestCaseResult
from jupygrader.notebook_operations import replace_test_case

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"


def _make_ai_grader(parsed_result: AIParsedResult) -> AIGrader:
    response = MagicMock()
    response.output_parsed = parsed_result
    mock_client = MagicMock()
    mock_client.responses.parse.return_value = response
    return AIGrader(mock_client, "gpt-test")


def test_ai_points_are_clamped_to_available_points():
    grader = _make_ai_grader(
        AIParsedResult(
            results=[
                AITestCaseResult(
                    test_case_name="q1",
                    points=1000,
                    did_pass=True,
                    feedback="Great job.",
                )
            ]
        )
    )

    tc = TestCaseResult(
        test_case_name="q1",
        points=0,
        available_points=5,
        did_pass=None,
        grade_manually=True,
    )
    graded_result = GradedResult(test_case_results=[tc])

    modified = grader.grade_partial(
        graded_result, new_notebook(), AIGradingMode.MANUAL_ONLY
    )

    assert modified is True
    assert tc.points == 5  # clamped to available_points
    assert tc.is_graded is True


def test_ai_negative_points_are_clamped_to_zero():
    grader = _make_ai_grader(
        AIParsedResult(
            results=[
                AITestCaseResult(
                    test_case_name="q1",
                    points=-10,
                    did_pass=False,
                    feedback="Incorrect.",
                )
            ]
        )
    )

    tc = TestCaseResult(
        test_case_name="q1",
        points=0,
        available_points=5,
        did_pass=None,
        grade_manually=True,
    )
    graded_result = GradedResult(test_case_results=[tc])

    grader.grade_partial(graded_result, new_notebook(), AIGradingMode.MANUAL_ONLY)

    assert tc.points == 0


def test_reviewed_failed_test_cases_stay_failed():
    """REVIEW_FAILED mode may award partial points but must not flip did_pass."""
    grader = _make_ai_grader(
        AIParsedResult(
            results=[
                AITestCaseResult(
                    test_case_name="q1",
                    points=2,
                    did_pass=True,  # model (or prompt injection) tries to pass it
                    feedback="Close to correct.",
                )
            ]
        )
    )

    tc = TestCaseResult(
        test_case_name="q1",
        points=0,
        available_points=5,
        did_pass=False,
        grade_manually=False,
        error_message="AssertionError",
    )
    graded_result = GradedResult(test_case_results=[tc])

    grader.grade_partial(graded_result, new_notebook(), AIGradingMode.REVIEW_FAILED)

    assert tc.points == 2
    assert tc.did_pass is False


def test_replace_test_case_replaces_matching_cell():
    nb = new_notebook()
    nb.cells = [
        new_code_cell("_test_case = 'q1'\n_points = 5\nassert my_var == 3"),
        new_code_cell("_test_case = 'q2'\n_points = 5\nassert other_var == 1"),
    ]

    new_code = "_test_case = 'q1'\n_points = 6\nassert my_var == 4"
    replace_test_case(nb, "q1", new_code)

    assert nb.cells[0].source == new_code
    assert "other_var" in nb.cells[1].source  # untouched


def test_copy_file_destination_cannot_escape_workdir(tmp_path):
    task = object.__new__(ExecutionGradingTask)
    task.temp_workdir_path = tmp_path / "workdir"
    task.temp_workdir_path.mkdir()

    with pytest.raises(ValueError):
        task._resolve_dest_within_workdir("../evil.txt", "copy_file")

    with pytest.raises(ValueError):
        task._resolve_dest_within_workdir("/tmp/evil.txt", "copy_file")

    resolved = task._resolve_dest_within_workdir("sub/dir/ok.txt", "copy_file")
    assert resolved == (task.temp_workdir_path / "sub/dir/ok.txt").resolve()


def test_sanitize_for_markdown_table_escapes_html():
    sanitized = sanitize_for_markdown_table('<script>alert("x")</script>|\nend')
    assert "<script>" not in sanitized
    assert "\n" not in sanitized
    assert "\\|" in sanitized
    assert sanitize_for_markdown_table(None) == ""


def test_normalize_grading_items_accepts_single_string():
    items = BatchGradingManager.normalize_grading_items("some-notebook.ipynb")
    assert len(items) == 1
    assert items[0].notebook_path == "some-notebook.ipynb"


def test_ai_mode_requires_openai_client():
    with pytest.raises(ValueError, match="openai_client"):
        grade_notebooks(
            [],
            ai_mode=AIGradingMode.FULL,
            openai_model="gpt-test",
        )


def test_failed_notebook_records_actual_error_message(tmp_path):
    """A grading failure must surface the real error, not 'Unknown grading error'."""
    invalid_notebook = TEST_NOTEBOOKS_DIR / "failure-reporting" / "invalid.ipynb"
    csv_path = tmp_path / "results.csv"

    grade_notebooks(
        [{"notebook_path": invalid_notebook, "output_path": tmp_path}],
        csv_output_path=csv_path,
        regrade_existing=True,
        verbose=False,
    )

    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert rows[0]["is_success"] == "False"
    assert rows[0]["text_summary"]
    assert rows[0]["text_summary"] != "Unknown grading error"