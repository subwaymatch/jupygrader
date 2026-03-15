from enum import Enum
from typing import List, Union

from pydantic import BaseModel


class AIGradingMode(str, Enum):
    OFF = "off"  # default: no AI
    MANUAL_ONLY = "manual_only"  # grade manual items only
    REVIEW_FAILED = "review_failed"  # review failed autograded tests
    MANUAL_AND_FAILED = "manual_and_failed"
    FULL = "full"  # LLM grades everything


class AITestCaseResult(BaseModel):
    test_case_name: str
    points: Union[int, float]
    did_pass: bool = False
    feedback: str


class AIParsedResult(BaseModel):
    results: List[AITestCaseResult]
