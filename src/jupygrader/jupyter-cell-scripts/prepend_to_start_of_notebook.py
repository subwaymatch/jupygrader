# Jupygrader Before File Code
# REMOVE_IN_HTML_OUTPUT
import datetime
from typing import Union
from jupygrader.types import GradedResult, TestCaseResult

grading_start_time = datetime.datetime.now(datetime.timezone.utc)

_graded_result = GradedResult()

is_jupygrader_env = True

# For legacy compatibility
# Should deprecate in the future
is_lambdagrader_env = True


def _record_test_case(
    test_case_name: str,
    did_pass: bool,
    available_points: Union[int, float],
    message: str = "",
    grade_manually: bool = False,
):
    global _graded_result
    warning_message = ""

    if test_case_name in map(
        lambda x: x.test_case_name, _graded_result.test_case_results
    ):
        warning_message = f'[Warning] Jupygrader: An identical test case name "{test_case_name}" already exists. Test cases with identical test case names will be graded \n\n'

    _graded_result.test_case_results.append(
        TestCaseResult(
            test_case_name=test_case_name,
            points=available_points if did_pass else 0,
            available_points=available_points,
            did_pass=did_pass,
            grade_manually=grade_manually,
            message=warning_message + message,
        )
    )
