from nbformat.v4 import new_code_cell

from jupygrader.notebook_operations import (
    does_cell_contain_test_case,
    extract_test_case_metadata_from_code,
)


def test_extract_test_case_metadata_with_parenthesized_string():
    code = """_test_case = (\n    \"Part 3.3: Remove punctuation\"\n)\n_points = 5\n"""

    metadata = extract_test_case_metadata_from_code(code)

    assert metadata is not None
    assert metadata.test_case_name == "Part 3.3: Remove punctuation"
    assert metadata.points == 5


def test_extract_manual_grading_boolean_false():
    code = """_test_case = \"manual\"\n_grade_manually = False\n"""

    metadata = extract_test_case_metadata_from_code(code)

    assert metadata is not None
    assert metadata.grade_manually is False


def test_does_cell_contain_test_case_with_parenthesized_string():
    cell = new_code_cell('_test_case = (\n    "Part 4.3C: Apply count_occurrences"\n)')

    assert does_cell_contain_test_case(cell) is True
