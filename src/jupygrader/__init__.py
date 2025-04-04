# SPDX-FileCopyrightText: 2025-present Ye Joo Park <subwaymatch@gmail.com>
#
# SPDX-License-Identifier: MIT
from .__about__ import __version__
from .notebook_operations import (
    extract_test_case_metadata_from_code,
    extract_test_cases_metadata_from_notebook,
    remove_code_cells_that_contain,
    does_cell_contain_test_case,
    is_manually_graded_test_case,
    extract_user_code_from_notebook,
    remove_comments,
    get_test_cases_hash,
)
from .models.grading_dataclasses import GradedResult, TestCaseResult
from .grader import grade_notebooks, grade_single_notebook

__all__ = [
    # Version info
    "__version__",
    # Grading interface
    "grade_notebooks",
    "grade_single_notebook",
    "GradedResult",
    "TestCaseResult",
    # Notebook/test utilities
    "extract_test_case_metadata_from_code",
    "extract_test_cases_metadata_from_notebook",
    "remove_code_cells_that_contain",
    "does_cell_contain_test_case",
    "is_manually_graded_test_case",
    "extract_user_code_from_notebook",
    "remove_comments",
    "get_test_cases_hash",
]
