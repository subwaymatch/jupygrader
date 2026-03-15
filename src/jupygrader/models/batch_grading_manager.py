# Backwards-compatibility shim.
# Use jupygrader.grading.batch_grading_manager.BatchGradingManager instead.
from ..grading.batch_grading_manager import BatchGradingManager

__all__ = ["BatchGradingManager"]
