import json
import textwrap
from typing import Optional

import nbformat
import openai
from nbclient import NotebookClient
from nbformat import NotebookNode
from nbformat.v4 import new_code_cell

from ..constants import GRADED_RESULT_JSON_FILENAME
from ..models.ai_models import AIGradingMode
from ..models.config import BatchGradingConfig, GradingItem
from ..models.results import GradedResult
from ..notebook_operations import (
    comment_out_magic_commands,
    does_cell_contain_test_case,
    extract_test_case_metadata_from_code,
    get_test_cases_hash,
    is_manually_graded_test_case,
)
from ..utils import get_jupyter_cell_script
from .ai_grader import AIGrader
from .base_grading_task import BaseGradingTask


class ExecutionGradingTask(BaseGradingTask):
    """Grading task that executes the notebook via nbclient and reads test results from JSON."""

    def __init__(
        self,
        item: GradingItem,
        batch_config: BatchGradingConfig,
        openai_client: Optional[openai.OpenAI] = None,
    ):
        super().__init__(item, batch_config)
        self.openai_client = openai_client

    # ------------------------------------------------------------------
    # Notebook preparation
    # ------------------------------------------------------------------

    def convert_test_case_using_grader_template(self, cell: NotebookNode) -> None:
        """Wrap a test case cell with the appropriate grader template.

        The test case name and points parsed from the cell source are injected
        ahead of the try block, so that a cell failing before its own
        ``_test_case = ...`` assignment runs is still recorded under the correct
        name instead of a stale value from a previously executed test cell.
        """
        if not does_cell_contain_test_case(cell):
            return

        metadata = extract_test_case_metadata_from_code(cell.source)
        if metadata is None:
            return

        metadata_lines = [
            f"_test_case = {metadata.test_case_name!r}",
            f"_points = {metadata.points!r}",
        ]

        if is_manually_graded_test_case(cell):
            grader_template_code = get_jupyter_cell_script("grader_manual_template.py")
            metadata_lines.append(f"_grade_manually = {metadata.grade_manually!r}")
        else:
            grader_template_code = get_jupyter_cell_script("grader_template.py")

        source = textwrap.indent(cell.source, "    ")

        converted_source = grader_template_code.replace(
            "# TEST_CASE_METADATA_REPLACE_HERE", "\n".join(metadata_lines)
        ).replace("# TEST_CASE_REPLACE_HERE", source)

        cell.source = converted_source

    def preprocess_test_case_cells(self) -> None:
        for cell in self.nb.cells:
            if does_cell_contain_test_case(cell):
                self.convert_test_case_using_grader_template(cell)

    def add_grader_scripts(self) -> None:
        prepend_cell = new_code_cell(
            get_jupyter_cell_script("prepend_to_start_of_notebook.py")
        )
        append_cell = new_code_cell(
            get_jupyter_cell_script("append_to_end_of_notebook.py")
        )

        self.nb.cells.insert(0, prepend_cell)
        self.nb.cells.append(append_cell)

    def remove_grader_scripts(self) -> None:
        """Remove the prepend/append cells added by Jupygrader before storing to HTML."""
        self.nb.cells.pop(0)  # first cell (added by Jupygrader)
        self.nb.cells.pop()  # last cell (added by Jupygrader)

    def _pre_annotate_cleanup(self) -> None:
        self.remove_grader_scripts()

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def prepare_and_execute_notebook(self) -> None:
        self.nb = nbformat.read(self.temp_notebook_path, as_version=4)
        comment_out_magic_commands(self.nb)
        self.preprocess_test_case_cells()
        self.add_grader_scripts()

        client_kwargs = {
            "kernel_name": "python3",
            "allow_errors": True,
        }

        if self.execution_timeout is not None:
            client_kwargs["timeout"] = self.execution_timeout

        client = NotebookClient(self.nb, **client_kwargs)
        client.execute()

    # ------------------------------------------------------------------
    # Result parsing
    # ------------------------------------------------------------------

    def process_grading_results(self) -> None:
        results_json_path = self.temp_workdir_path / GRADED_RESULT_JSON_FILENAME

        if not results_json_path.exists():
            raise FileNotFoundError(
                f"Graded results JSON file not found: {results_json_path}"
            )

        with open(results_json_path, "r", encoding="utf-8") as f:
            graded_result_data = json.load(f)

        self.graded_result = GradedResult.from_dict(graded_result_data)
        self.graded_result.test_cases_hash = get_test_cases_hash(self.nb)
        self._populate_graded_result_metadata()

    # ------------------------------------------------------------------
    # AI review (partial modes only)
    # ------------------------------------------------------------------

    def apply_partial_ai_grading(self) -> None:
        """Delegate partial AI grading to AIGrader for non-FULL modes."""
        ai_mode = self.batch_config.ai_mode

        if ai_mode in (AIGradingMode.OFF, AIGradingMode.FULL):
            return
        if self.openai_client is None:
            return

        model = self.batch_config.openai_model
        grader = AIGrader(self.openai_client, model)

        has_modified = grader.grade_partial(
            self.graded_result, self.nb, ai_mode, self.batch_config.custom_prompt
        )

        if has_modified:
            self._recalculate_scores()

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def grade(self) -> Optional[GradedResult]:
        self.error_message = None
        try:
            with self.use_temporary_grading_environment():
                # 1. Prepare and execute the notebook
                self.prepare_and_execute_notebook()

                # 2. Process results (read JSON, parse, add metadata)
                self.process_grading_results()

                # 3. Apply partial AI grading if enabled
                self.apply_partial_ai_grading()

                # 4. Generate output files
                self.generate_output_artifacts()

            return self.graded_result
        except Exception as e:
            print(f"[Error in ExecutionGradingTask.grade()]: {e}")
            self.error_message = str(e)
            return None
