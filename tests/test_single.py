import jupygrader
from pathlib import Path

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / 'test-notebooks'
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / 'test-output'

# use this file to run only a single test function
# hatch test --ignore tests/test_grader.py