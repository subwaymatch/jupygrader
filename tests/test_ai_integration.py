import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
import openai

from jupygrader import AIGradingMode, grade_notebooks

# Load environment variables from .env.test
load_dotenv(".env.test")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f"OPENAI_BASE_URL: {OPENAI_BASE_URL}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")

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
        openai_client=openai.OpenAI(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY
        ),
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
    manual_cases_remaining = [tc for tc in result.test_case_results if tc.grade_manually]

    assert (
        len(manual_cases_remaining) == 0
    ), "AI grading should resolve manually graded test cases"

    # Validate generated artifacts
    graded_html_path = TEST_OUTPUT_DIR / f"{filename_base}-graded.html"
    graded_ipynb_path = TEST_OUTPUT_DIR / f"{filename_base}-graded.ipynb"
    graded_json_path = TEST_OUTPUT_DIR / f"{filename_base}-graded-result.json"
    graded_summary_path = TEST_OUTPUT_DIR / f"{filename_base}-graded-result-summary.txt"

    assert graded_html_path.exists(), f"Expected HTML file not found: {graded_html_path}"
    assert graded_ipynb_path.exists(), f"Expected graded notebook not found: {graded_ipynb_path}"
    assert graded_json_path.exists(), f"Expected result JSON file not found: {graded_json_path}"
    assert graded_summary_path.exists(), f"Expected text summary file not found: {graded_summary_path}"