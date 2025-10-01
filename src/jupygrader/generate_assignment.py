from nbformat.notebooknode import NotebookNode
import re
import textwrap
from .notebook_operations import does_cell_contain_test_case
from .obfuscate import obfuscate_python_code


SOLUTION_STRIP_PATTERN = re.compile(
    r"(#\s*YOUR CODE BEGINS|###\s*BEGIN SOLUTION).*?(#\s*YOUR CODE ENDS|###\s*END SOLUTION)",
    re.DOTALL,
)
SOLUTION_REPLACEMENT = "# YOUR CODE BEGINS\n\n# YOUR CODE ENDS"

POINTS_PATTERN = re.compile(r"^_points\s*=\s*([\d\.]*).*$", re.MULTILINE)
TEST_CASE_NAME_PATTERN = re.compile(
    r"^_test_case\s*=\s*[\'\"](.*)[\'\"].*$", re.MULTILINE
)
HIDDEN_TEST_PATTERN = re.compile(
    r"^### BEGIN HIDDEN TESTS(.*?)### END HIDDEN TESTS", re.DOTALL | re.MULTILINE
)
HIDDEN_TEST_MESSAGE = """
# ⚠️ This cell contains hidden tests that 
# will only run during the grading process.
# You will not see these test results 
# when running the notebook yourself.
"""
HIDDEN_TEST_TEMPLATE = (
    "\nif 'is_jupygrader_env' in globals():\n# TEST_CASE_REPLACE_HERE\n\n"
)


def strip_solution_codes_from_notebook(nb: NotebookNode) -> NotebookNode:
    """Removes code between "# YOUR CODE BEGINS" or "### BEGIN SOLUTION" and "# YOUR CODE ENDS" or "### END SOLUTION" markers.

    Args:
        nb: The notebook to strip solution codes from

    Returns:
        The notebook with all solution codes removed
    """
    for cell in nb.cells:
        # print(cell.cell_type)
        if cell.cell_type == "code":
            # Use a single regex substitution to replace all solution blocks
            cell.source = SOLUTION_STRIP_PATTERN.sub(SOLUTION_REPLACEMENT, cell.source)

            # Clear outputs and execution counts
            cell.outputs = []
            cell.execution_count = None

    return nb


def obfuscate_hidden_test_cases(nb: NotebookNode) -> NotebookNode:
    """Obfuscates hidden test cases in a Jupyter Notebook by replacing the relevant code with a base-64 encoded string

    Args:
        nb: The notebook to obfuscate hidden test cases in
    """
    cells_to_process = [
        cell
        for cell in nb.cells
        if (cell.cell_type == "code" and re.search(HIDDEN_TEST_PATTERN, cell.source))
    ]

    for cell in cells_to_process:
        source = cell.source

        hidden_test_matches = [m.group(0) for m in HIDDEN_TEST_PATTERN.finditer(source)]

        if hidden_test_matches:
            for match in hidden_test_matches:
                match_text = match.strip()
                indented_match_text = textwrap.indent(match_text, "    ")

                code = HIDDEN_TEST_TEMPLATE.replace(
                    "# TEST_CASE_REPLACE_HERE", indented_match_text
                )
                code = obfuscate_python_code(code)
                source = source.replace(match, code)

            cell.source = HIDDEN_TEST_MESSAGE + source

    return nb


import re
import textwrap
from nbformat.notebooknode import NotebookNode
from .obfuscate import obfuscate_python_code

# (Assuming HIDDEN_TEST_PATTERN, HIDDEN_TEST_TEMPLATE,
# and HIDDEN_TEST_MESSAGE are defined elsewhere in the file)


def obfuscate_hidden_test_cases(nb: NotebookNode) -> NotebookNode:
    """
    Finds and unconditionally obfuscates all hidden test cases in a notebook.

    This function searches for blocks marked with "### BEGIN HIDDEN TESTS"
    and "### END HIDDEN TESTS", wraps them in a conditional execution block,
    obfuscates the result, and adds a warning message to the cell. This
    process is applied to all found hidden tests.

    Args:
        nb: The notebook to process.

    Returns:
        The notebook with hidden test cases obfuscated.
    """
    cells_to_process = [
        cell
        for cell in nb.cells
        if cell.cell_type == "code" and re.search(HIDDEN_TEST_PATTERN, cell.source)
    ]

    for cell in cells_to_process:
        source = cell.source
        hidden_test_matches = [m.group(0) for m in HIDDEN_TEST_PATTERN.finditer(source)]

        if hidden_test_matches:
            for match in hidden_test_matches:
                match_text = match.strip()
                indented_match_text = textwrap.indent(match_text, "    ")

                code = HIDDEN_TEST_TEMPLATE.replace(
                    "# TEST_CASE_REPLACE_HERE", indented_match_text
                )
                code = obfuscate_python_code(code)

                source = source.replace(match, code)

            cell.source = HIDDEN_TEST_MESSAGE.strip() + "\n" + source

    return nb


def lock_test_cells(nb: NotebookNode) -> NotebookNode:
    """Locks test cells in a Jupyter Notebook by setting their metadata.

    Args:
        nb: The notebook to lock test cells in
    """
    for cell in nb.cells:
        if does_cell_contain_test_case(cell):
            cell.metadata["editable"] = False
            cell.metadata["deletable"] = False

    return nb


def generate_assignment(nb: NotebookNode) -> NotebookNode:
    """Generates an assignment notebook by stripping solution codes, obfuscating hidden test cases, obfuscating test cases, and locking test cells.

    Args:
        nb: The notebook to generate an assignment from

    Returns:
        The generated assignment notebook
    """
    nb = strip_solution_codes_from_notebook(nb)
    nb = obfuscate_hidden_test_cases(nb)
    nb = lock_test_cells(nb)

    return nb
