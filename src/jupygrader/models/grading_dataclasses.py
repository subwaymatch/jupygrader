# Backwards-compatibility shim.
# Import from the new focused modules instead.
from .ai_models import AIGradingMode, AIParsedResult, AITestCaseResult
from .config import BatchGradingConfig, CopyFileItem, FileDict, FilePath, GradingItem
from .results import GradedResult, TestCaseMetadata, TestCaseResult

__all__ = [
    "AIGradingMode",
    "AIParsedResult",
    "AITestCaseResult",
    "BatchGradingConfig",
    "CopyFileItem",
    "FileDict",
    "FilePath",
    "GradedResult",
    "GradingItem",
    "TestCaseMetadata",
    "TestCaseResult",
]
