import copy
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import nbformat
import openai
import pytest
from dotenv import load_dotenv
from nbformat.v4 import new_code_cell

from jupygrader import AIGradingMode, grade_notebooks

# Load environment variables from .env.test
load_dotenv(".env.test")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output" / "ai-integration"

# Create output directory
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@pytest.mark.ai
@pytest.mark.skipif(
    not OPENAI_API_KEY or not OPENAI_BASE_URL,
    reason="OPENAI_API_KEY or OPENAI_BASE_URL not set in environment",
)
def test_ai_integration_workflow():
    filename = "for-llm-grading.ipynb"
    notebook_path = TEST_NOTEBOOKS_DIR / "ai-integration" / filename
    filename_base = notebook_path.stem

    result = grade_notebooks(
        [
            {
                "notebook_path": notebook_path,
                "output_path": TEST_OUTPUT_DIR,
            }
        ],
        export_csv=False,
        regrade_existing=True,
        execution_timeout=120,
        ai_mode=AIGradingMode.MANUAL_AND_FAILED,
        openai_client=openai.OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY),
        openai_model="gpt-5-mini",
    )[0]

    # Basic result checks
    assert result.filename == filename
    assert result.num_total_test_cases == 6

    # Ensure test cases exist
    assert hasattr(result, "test_case_results")
    assert isinstance(result.test_case_results, list)
    assert len(result.test_case_results) == 6

    # Ensure AI grading filled manual cases
    ungraded_cases_remaining = [
        tc for tc in result.test_case_results if tc.is_graded is False
    ]

    assert len(ungraded_cases_remaining) == 0, (
        "AI grading should resolve manually graded test cases"
    )

    # Validate generated artifacts
    graded_html_path = TEST_OUTPUT_DIR / f"{filename_base}-graded.html"
    graded_ipynb_path = TEST_OUTPUT_DIR / f"{filename_base}-graded.ipynb"
    graded_json_path = TEST_OUTPUT_DIR / f"{filename_base}-graded-result.json"
    graded_summary_path = TEST_OUTPUT_DIR / f"{filename_base}-graded-result-summary.txt"

    assert graded_html_path.exists(), (
        f"Expected HTML file not found: {graded_html_path}"
    )
    assert graded_ipynb_path.exists(), (
        f"Expected graded notebook not found: {graded_ipynb_path}"
    )
    assert graded_json_path.exists(), (
        f"Expected result JSON file not found: {graded_json_path}"
    )
    assert graded_summary_path.exists(), (
        f"Expected text summary file not found: {graded_summary_path}"
    )


def test_apply_partial_ai_grading_does_not_modify_original_notebook():
    """The original notebook must not be modified when preprocessing for the AI payload."""
    from jupygrader.grading.execution_grading_task import ExecutionGradingTask
    from jupygrader.models.ai_models import AIGradingMode, AIParsedResult, AITestCaseResult
    from jupygrader.models.config import BatchGradingConfig
    from jupygrader.models.results import GradedResult, TestCaseResult

    GradingTask = ExecutionGradingTask

    # Build a minimal notebook that contains a base64 PNG image output
    nb = nbformat.v4.new_notebook()
    cell = new_code_cell(source='print("hello")')
    image_output = nbformat.v4.new_output(
        output_type="display_data",
        data={
            "image/png": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk",
            "text/plain": "<Figure>",
        },
    )
    cell.outputs = [image_output]
    nb.cells = [cell]

    # Build a minimal GradingTask with mocked fields
    task = object.__new__(GradingTask)
    task.nb = nb
    task.batch_config = BatchGradingConfig(
        ai_mode=AIGradingMode.MANUAL_AND_FAILED,
        openai_model="gpt-test",
    )

    tc = TestCaseResult(
        test_case_name="tc1",
        grade_manually=True,
        points=0,
        available_points=5,
        did_pass=None,
    )
    task.graded_result = GradedResult(test_case_results=[tc])

    # Track the payload sent to the API
    captured_payload = {}

    def fake_parse(**kwargs):
        user_content = kwargs["input"][1]["content"]
        captured_payload.update(json.loads(user_content))
        parsed = AIParsedResult(
            results=[
                AITestCaseResult(
                    test_case_name="tc1",
                    did_pass=True,
                    points=5,
                    feedback="Looks correct.",
                )
            ]
        )
        response = MagicMock()
        response.output_parsed = parsed
        return response

    mock_client = MagicMock()
    mock_client.responses.parse.side_effect = fake_parse
    task.openai_client = mock_client
    task._recalculate_scores = MagicMock()

    task.apply_partial_ai_grading()

    # The original notebook cell output must still contain the image
    assert "image/png" in nb.cells[0].outputs[0].data, (
        "Original notebook was modified – base64 image was removed from the source notebook"
    )

    # The payload must contain a Markdown string, not a dict/notebook object
    assert "notebook" in captured_payload
    assert isinstance(captured_payload["notebook"], str), (
        "Payload 'notebook' field should be a Markdown string, not a notebook dict"
    )
    # The Markdown should not contain the raw base64 image data
    assert "iVBORw0KGgo" not in captured_payload["notebook"], (
        "Payload must not include raw base64 image data"
    )


def test_apply_partial_ai_grading_payload_is_markdown():
    """Payload 'notebook' field must be a Markdown string converted from the notebook."""
    from jupygrader.grading.execution_grading_task import ExecutionGradingTask
    from jupygrader.models.ai_models import AIGradingMode, AIParsedResult, AITestCaseResult
    from jupygrader.models.config import BatchGradingConfig
    from jupygrader.models.results import GradedResult, TestCaseResult

    GradingTask = ExecutionGradingTask

    nb = nbformat.v4.new_notebook()
    cell = new_code_cell(source='x = 42\nprint(x)')
    stream_output = nbformat.v4.new_output(
        output_type="stream", name="stdout", text="42\n"
    )
    cell.outputs = [stream_output]
    nb.cells = [cell]

    task = object.__new__(GradingTask)
    task.nb = nb
    task.batch_config = BatchGradingConfig(
        ai_mode=AIGradingMode.REVIEW_FAILED,
        openai_model="gpt-test",
    )

    tc = TestCaseResult(
        test_case_name="tc_fail",
        grade_manually=False,
        points=0,
        available_points=3,
        did_pass=False,
        error_message="AssertionError",
    )
    task.graded_result = GradedResult(test_case_results=[tc])

    captured_payload = {}

    def fake_parse(**kwargs):
        user_content = kwargs["input"][1]["content"]
        captured_payload.update(json.loads(user_content))
        parsed = AIParsedResult(
            results=[
                AITestCaseResult(
                    test_case_name="tc_fail",
                    did_pass=False,
                    points=1,
                    feedback="Partial credit.",
                )
            ]
        )
        response = MagicMock()
        response.output_parsed = parsed
        return response

    mock_client = MagicMock()
    mock_client.responses.parse.side_effect = fake_parse
    task.openai_client = mock_client
    task._recalculate_scores = MagicMock()

    task.apply_partial_ai_grading()

    notebook_field = captured_payload.get("notebook", "")
    # Must be a non-empty string
    assert isinstance(notebook_field, str) and len(notebook_field) > 0
    # Source code should appear in the Markdown representation
    assert "x = 42" in notebook_field
