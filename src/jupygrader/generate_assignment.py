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

OBFUSCATE_PATTERN = re.compile(r"^\s*_obfuscate\s*=\s*True", re.MULTILINE)
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
                # In TS: matchText = `${match}`. In Python, it's just the string itself.
                match_text = match.strip()
                # In TS: matchText.replace(/^/gm, "    ") -> indent every line
                indented_match_text = textwrap.indent(match_text, "    ")

                # In TS: hiddenTestTemplate.split(...).join(...) -> string.replace()
                code = HIDDEN_TEST_TEMPLATE.replace(
                    "# TEST_CASE_REPLACE_HERE", indented_match_text
                )

                # If the cell is not configured for full obfuscation,
                # obfuscate just the hidden test case block.
                if not re.search(OBFUSCATE_PATTERN, cell["source"]):
                    code = obfuscate_python_code(code)

                # Replace the original hidden test block with the new processed code
                source = source.replace(match, code)

            cell.source = HIDDEN_TEST_MESSAGE + source

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
