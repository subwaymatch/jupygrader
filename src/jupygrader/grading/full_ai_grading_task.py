from typing import Optional

import nbformat
import openai

from ..models.ai_models import AIGradingMode
from ..models.config import BatchGradingConfig, GradingItem
from ..models.results import GradedResult, TestCaseResult
from ..notebook_operations import (
    extract_test_cases_metadata_from_notebook,
    get_test_cases_hash,
)
from .ai_grader import AIGrader
from .base_grading_task import BaseGradingTask


class FullAIGradingTask(BaseGradingTask):
    """Grading task for AIGradingMode.FULL.

    Reads the notebook directly without executing it and grades all test cases
    using the AI model based solely on the notebook's content. No temporary
    grading environment is created.
    """

    def __init__(
        self,
        item: GradingItem,
        batch_config: BatchGradingConfig,
        openai_client: Optional[openai.OpenAI] = None,
    ):
        super().__init__(item, batch_config)
        self.openai_client = openai_client

    def prepare_notebook(self) -> None:
        """Read the notebook from disk without executing it."""
        with open(self.notebook_path, "r", encoding="utf-8") as f:
            self.nb = nbformat.read(f, as_version=4)

    def build_graded_result_from_notebook(self) -> None:
        """Parse test case metadata from notebook cells and build a GradedResult."""
        metadata_list = extract_test_cases_metadata_from_notebook(self.nb)

        test_case_results = [
            TestCaseResult(
                test_case_name=meta.test_case_name,
                points=0,
                available_points=meta.points,
                did_pass=None,
                grade_manually=meta.grade_manually,
                is_graded=False,
            )
            for meta in metadata_list
        ]

        total_available = sum(tc.available_points for tc in test_case_results)

        self.graded_result = GradedResult(
            test_case_results=test_case_results,
            num_total_test_cases=len(test_case_results),
            num_manually_graded_cases=len(test_case_results),
            max_manually_graded_score=total_available,
            max_total_score=total_available,
            ai_mode=AIGradingMode.FULL,
        )

        self.graded_result.test_cases_hash = get_test_cases_hash(self.nb)
        self._populate_graded_result_metadata()

    def apply_full_ai_grading(self) -> None:
        """Send all test cases to the AI model for grading."""
        if self.openai_client is None:
            return

        grader = AIGrader(self.openai_client, self.batch_config.openai_model)

        has_modified = grader.grade_full(
            self.graded_result, self.nb, self.batch_config.custom_prompt
        )

        if has_modified:
            self._recalculate_scores()

    def grade(self) -> Optional[GradedResult]:
        """Execute the full-AI grading pipeline and return the result."""
        self.error_message = None
        try:
            self.prepare_notebook()
            self.build_graded_result_from_notebook()
            self.apply_full_ai_grading()
            self.generate_output_artifacts()
            return self.graded_result
        except Exception as e:
            print(f"[Error in FullAIGradingTask.grade()]: {e}")
            self.error_message = str(e)
            return None
