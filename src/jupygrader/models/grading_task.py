# Backwards-compatibility shim.
# Use jupygrader.grading.execution_grading_task.ExecutionGradingTask instead.
from ..grading.execution_grading_task import ExecutionGradingTask as GradingTask

__all__ = ["GradingTask"]
