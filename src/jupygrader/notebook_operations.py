from nbformat.notebooknode import NotebookNode
import ast
import re
import black
import hashlib
from jupygrader.models.grading_dataclasses import TestCaseMetadata
from pathlib import Path
from typing import Union, List, Optional
import nbformat

test_case_name_pattern = r'^\s*_test_case\s*=\s*[\'"](.*)[\'"]'
test_case_points_pattern = r"^\s*_points\s*=\s*(.*)[\s#]*.*[\r\n]"
manual_grading_pattern = r"^\s*_grade_manually\s*=\s*(True|False)"


def _extract_assignment_literal_value(code_str: str, variable_name: str) -> Optional[object]:
    """Extract literal value assigned to a variable in Python source code."""
    try:
        parsed = ast.parse(code_str)
    except SyntaxError:
        return None

    for node in ast.walk(parsed):
        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == variable_name:
                try:
                    return ast.literal_eval(node.value)
                except (ValueError, SyntaxError):
                    return None

    return None


def extract_test_case_metadata_from_code(code_str: str) -> Optional[TestCaseMetadata]:
    """Extract test case metadata from a code cell string.

    Parses a code string to extract test case metadata including the test case name,
    points value, and whether it requires manual grading. The function looks for
    specific patterns in the code:

    - `_test_case = 'name'`  (required)
    - `_points = value`      (optional, defaults to 0)
    - `_grade_manually = True/False`  (optional, defaults to `False`)

    Args:
        code_str: The source code string to parse for test case metadata

    Returns:
        A TestCaseMetadata object with extracted values if a test case is found,
        None if a test case is not found
    """
    test_case_name = _extract_assignment_literal_value(code_str, "_test_case")
    if not isinstance(test_case_name, str):
        return None

    metadata = TestCaseMetadata(
        test_case_name=test_case_name,
        points=0,
        grade_manually=False,
    )

    points = _extract_assignment_literal_value(code_str, "_points")
    if isinstance(points, (int, float)):
        metadata.points = float(points)

    manual_grading = _extract_assignment_literal_value(code_str, "_grade_manually")
    if isinstance(manual_grading, bool):
        metadata.grade_manually = manual_grading

    return metadata


def extract_test_cases_metadata_from_notebook(
    nb: NotebookNode,
) -> List[TestCaseMetadata]:
    """Extract metadata from all test cases in a notebook.

    Iterates through all code cells in the notebook and identifies test case cells
    by looking for specific pattern markers. For each test case found, extracts
    the metadata into a `TestCaseMetadata` object.

    Args:
        nb: The notebook to extract test case metadata from

    Returns:
        A list of TestCaseMetadata objects for all test cases found in the notebook
    """
    metadata_list: List[TestCaseMetadata] = []

    for cell in nb.cells:
        if cell.cell_type == "code":
            test_case_metadata = extract_test_case_metadata_from_code(cell.source)

            if test_case_metadata:
                metadata_list.append(test_case_metadata)

    return metadata_list


def does_cell_contain_test_case(cell: NotebookNode) -> bool:
    """Determine if a notebook cell contains a test case.

    A cell is considered a test case if it contains the pattern '_test_case = "name"'.
    This function uses a regular expression to check for this pattern.

    Args:
        cell: The notebook cell to check

    Returns:
        True if the cell contains a test case pattern, False otherwise
    """
    return isinstance(
        _extract_assignment_literal_value(cell.source, "_test_case"),
        str,
    )


def is_manually_graded_test_case(cell: NotebookNode) -> bool:
    """Determine if a notebook cell contains a manually graded test case.

    A test case is considered manually graded if it contains the pattern
    '_grade_manually = True'. This function checks for this specific pattern
    in the cell's source code.

    Args:
        cell: The notebook cell to check

    Returns:
        True if the cell is a manually graded test case, False otherwise
    """
    return isinstance(
        _extract_assignment_literal_value(cell.source, "_grade_manually"),
        bool,
    )


def extract_user_code_from_notebook(nb: NotebookNode) -> str:
    """Extract user code from a notebook.

    Collects all code from non-test-case code cells in the notebook.

    Args:
        nb: The notebook to extract code from

    Returns:
        String containing all user code concatenated with newlines
    """
    full_code = ""

    for cell in nb.cells:
        if (
            (cell.cell_type == "code")
            and not does_cell_contain_test_case(cell)
            and cell.source
        ):
            full_code += cell.source + "\n\n"

    return full_code


def comment_out_magic_commands(nb: NotebookNode) -> NotebookNode:
    """Comment out IPython magic/shell command lines in code cells.

    Converts code lines that start with ``!`` or ``%`` (after optional leading
    whitespace) into Python comments so notebook execution and downstream Python
    processing can continue without syntax errors.

    Args:
        nb: Notebook to process

    Returns:
        The same notebook object with transformed code cell sources
    """
    pattern = re.compile(r"^(\s*)([!%].*)$", re.MULTILINE)

    for cell in nb.cells:
        if cell.cell_type == "code" and cell.source:
            cell.source = pattern.sub(r"\1# \2", cell.source)

    return nb


def remove_code_cells_that_contain(
    nb: NotebookNode, search_str: Union[str, List[str]]
) -> NotebookNode:
    if isinstance(search_str, str):
        search_list = [search_str]
    else:
        search_list = search_str

    nb.cells = [
        cell
        for cell in nb.cells
        if not (cell.cell_type == "code" and any(s in cell.source for s in search_list))
    ]
    return nb


def replace_test_case(
    nb: NotebookNode, test_case_name: str, new_test_case_code: str
) -> NotebookNode:
    """Replace a test case in a notebook with new code.

    Finds a test case with the specified name and replaces its code.

    Args:
        nb: The notebook containing the test case
        test_case_name: Name of the test case to replace
        new_test_case_code: New code to use for the test case

    Returns:
        The notebook with the specified test case replaced
    """
    for cell in nb.cells:
        if (cell.cell_type == "code") and does_cell_contain_test_case(cell):
            test_case_metadata = extract_test_case_metadata_from_code(cell.source)

            if test_case_metadata.get("test_case") == test_case_name:
                cell.source = new_test_case_code

    return nb


def remove_comments(source: str) -> str:
    """Remove comments from Python source code.

    Removes both single line comments (starting with #) and
    multi-line comments (/* ... */), while preserving strings.

    Args:
        source: Python source code as string

    Returns:
        Source code with comments removed
    """
    pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|#[^\r\n]*$)"
    # first group captures quoted strings (double or single)
    # second group captures comments (# single-line or /* multi-line */)
    regex = re.compile(pattern, re.MULTILINE | re.DOTALL)

    def _replacer(match):
        # if the 2nd group (capturing comments) is not None,
        # it means we have captured a non-quoted (real) comment string.
        if match.group(2) is not None:
            return ""  # so we will return empty to remove the comment
        else:  # otherwise, we will return the 1st group
            return match.group(1)  # captured quoted-string

    return regex.sub(_replacer, source)


def get_test_cases_hash(nb: NotebookNode) -> str:
    """Generate a hash of all test cases in a notebook.

    Creates a standardized representation of all test case cells by
    removing comments and formatting with Black, then generates an MD5 hash.

    Args:
        nb: The notebook to generate a hash for

    Returns:
        MD5 hash string representing the test cases
    """
    test_cases_code = ""

    for cell in nb.cells:
        if (cell.cell_type == "code") and does_cell_contain_test_case(cell):
            # standardize code before hasing
            # by removing comments and formatting the code using the Black formatter
            standardized_code = remove_comments(cell.source)
            standardized_code = black.format_str(standardized_code, mode=black.Mode())

            # concatenate to test_cases_code
            test_cases_code += standardized_code

    # generate an MD5 hash
    hash_str = hashlib.md5(test_cases_code.encode("utf-8")).hexdigest()
    return hash_str


def is_notebook_graded(notebook_path: Union[str, Path]) -> bool:
    """
    Checks whether the given notebook has been graded by Jupygrader.

    Args:
        notebook_path (str or Path): Path to the .ipynb notebook file.

    Returns:
        bool: True if the notebook has `"jupygrader": {"graded": True}` in its metadata.
    """
    path = Path(notebook_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Notebook not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    return nb.metadata.get("jupygrader", {}).get("graded", False) is True
