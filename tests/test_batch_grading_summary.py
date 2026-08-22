from unittest.mock import patch

from jupygrader.grading.batch_grading_manager import BatchGradingManager
from jupygrader.models.config import BatchGradingConfig


class FakeGradingTask:
    def __init__(self, item, batch_config, openai_client):
        self.notebook_name = str(item.notebook_path)
        self.error_message = "grading failed"

    def get_existing_graded_result(self):
        if self.notebook_name == "cached.ipynb":
            return object()
        return None

    def grade(self):
        if self.notebook_name == "failed.ipynb":
            return None
        return object()


def test_verbose_summary_reports_separate_outcome_totals(capsys):
    manager = BatchGradingManager(
        [
            "graded.ipynb",
            "cached.ipynb",
            "already-graded.ipynb",
            "failed.ipynb",
        ],
        BatchGradingConfig(verbose=True, export_csv=False),
    )

    with (
        patch(
            "jupygrader.grading.batch_grading_manager.ExecutionGradingTask",
            FakeGradingTask,
        ),
        patch(
            "jupygrader.grading.batch_grading_manager.is_notebook_graded",
            side_effect=lambda path: str(path) == "already-graded.ipynb",
        ),
        patch.object(manager, "_record_success"),
        patch.object(manager, "_record_failure"),
    ):
        manager.grade()

    output = capsys.readouterr().out
    assert "Completed processing 4 notebook(s)" in output
    assert "Successfully graded: 1" in output
    assert "Used cached results: 1" in output
    assert "Skipped already graded notebooks: 1" in output
    assert "Failed to grade: 1" in output
