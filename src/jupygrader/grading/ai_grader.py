import copy
import json
from typing import Optional

import openai
from nbconvert import MarkdownExporter
from nbformat import NotebookNode

from ..models.ai_models import AIGradingMode, AIParsedResult
from ..models.config import BatchGradingConfig
from ..models.results import GradedResult


class AIGrader:
    """Handles AI-assisted grading for partial grading modes.

    Converts the notebook to Markdown and sends a single request to the
    OpenAI API to grade the specified test cases.
    """

    MANUAL_GRADING_INSTRUCTION = (
        'Grade this part manually. Assign points and provide feedback. '
        'If the student\'s code or response is close to correct, assign `True` to "did_pass".'
    )
    FAILED_TC_REVIEW_INSTRUCTION = (
        'Review this failed test case based on the error message. Explain why it failed. '
        'Provide partial points if the code was close to passing. '
        'But leave the "did_pass" field as `False`.'
    )

    def __init__(self, openai_client: openai.OpenAI, model: str):
        self.client = openai_client
        self.model = model

    @staticmethod
    def notebook_to_markdown(nb: NotebookNode) -> str:
        """Convert a notebook to Markdown, stripping base64 images to reduce tokens."""
        nb_copy = copy.deepcopy(nb)

        IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/gif", "image/svg+xml"}
        for cell in nb_copy.get("cells", []):
            for output in cell.get("outputs", []):
                data = output.get("data", {})
                for mime_type in IMAGE_MIME_TYPES:
                    data.pop(mime_type, None)

        md_exporter = MarkdownExporter()
        notebook_markdown, _ = md_exporter.from_notebook_node(nb_copy)
        return notebook_markdown

    def grade_partial(
        self,
        graded_result: GradedResult,
        nb: NotebookNode,
        ai_mode: AIGradingMode,
    ) -> bool:
        """Apply partial AI grading (MANUAL_ONLY, REVIEW_FAILED, or MANUAL_AND_FAILED).

        Returns True if any scores were modified, False otherwise.
        """
        test_case_result_dicts = [
            tc.__dict__ for tc in graded_result.test_case_results
        ]

        test_cases_to_review = []

        for tc in graded_result.test_case_results:
            if ai_mode == AIGradingMode.MANUAL_ONLY and tc.grade_manually:
                test_cases_to_review.append(
                    {
                        "test_case_name": tc.test_case_name,
                        "instruction": self.MANUAL_GRADING_INSTRUCTION,
                    }
                )

            elif ai_mode == AIGradingMode.REVIEW_FAILED and tc.did_pass is False:
                test_cases_to_review.append(
                    {
                        "test_case_name": tc.test_case_name,
                        "instruction": self.FAILED_TC_REVIEW_INSTRUCTION,
                    }
                )

            elif ai_mode == AIGradingMode.MANUAL_AND_FAILED and (
                tc.grade_manually or tc.did_pass is False
            ):
                if tc.grade_manually:
                    instruction = self.MANUAL_GRADING_INSTRUCTION
                else:
                    instruction = self.FAILED_TC_REVIEW_INSTRUCTION

                test_cases_to_review.append(
                    {
                        "test_case_name": tc.test_case_name,
                        "instruction": instruction,
                    }
                )

        if not test_cases_to_review:
            return False

        notebook_markdown = self.notebook_to_markdown(nb)

        payload = {
            "notebook": notebook_markdown,
            "test_cases": test_case_result_dicts,
            "cases_to_review": test_cases_to_review,
        }

        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are grading a student's Jupyter notebook submission. "
                            'Evaluate only the requested test cases in "test_cases_to_review" and return results.'
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(payload),
                    },
                ],
                text_format=AIParsedResult,
            )
        except Exception as e:
            print(f"[AI grading error]: {e}")
            return False

        parsed: AIParsedResult = response.output_parsed
        print(parsed)

        has_modified_scores = False

        for result in parsed.results:
            tc = next(
                (
                    t
                    for t in graded_result.test_case_results
                    if t.test_case_name == result.test_case_name
                ),
                None,
            )

            if tc is None:
                continue

            tc.points = result.points
            tc.did_pass = result.did_pass
            tc.is_graded = True
            tc.ai_feedback = result.feedback

            has_modified_scores = True

        return has_modified_scores
