import re
import textwrap

from nbformat.notebooknode import NotebookNode

from .notebook_operations import does_cell_contain_test_case
from .obfuscate import obfuscate_python_code

SOLUTION_STRIP_PATTERN = re.compile(
    r"(#\s*YOUR CODE BEGINS|###\s*BEGIN SOLUTION).*?(#\s*YOUR CODE ENDS|###\s*END SOLUTION)",
    re.DOTALL,
)
SOLUTION_REPLACEMENT = "# YOUR CODE BEGINS\n\n# YOUR CODE ENDS"

POINTS_PATTERN = re.compile(r"^_points\s*=\s*([\d\.]*)$", re.MULTILINE)
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
GRADER_ONLY_PATTERNS = [
    re.compile(r"^\s*#\s*grader_only\b", re.IGNORECASE),
    re.compile(r"^\s*!\s*grader_only\b", re.IGNORECASE),
    re.compile(r"^\s*_grader_only\s*=\s*True\b"),
]


def strip_solution_codes_from_notebook(nb: NotebookNode) -> NotebookNode:
    """Removes code between solution markers in code cells."""
    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.source = SOLUTION_STRIP_PATTERN.sub(SOLUTION_REPLACEMENT, cell.source)
            cell.outputs = []
            cell.execution_count = None

    return nb


def strip_grader_only_cells_from_notebook(nb: NotebookNode) -> NotebookNode:
    """Removes grader-only cells from a notebook regardless of cell type."""
    nb.cells = [
        cell
        for cell in nb.cells
        if not any(pattern.search(cell.source) for pattern in GRADER_ONLY_PATTERNS)
    ]

    return nb


def obfuscate_hidden_test_cases(nb: NotebookNode) -> NotebookNode:
    """Finds and obfuscates all hidden test blocks in code cells."""
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
    """Locks test cells by setting notebook metadata."""
    for cell in nb.cells:
        if does_cell_contain_test_case(cell):
            cell.metadata["editable"] = False
            cell.metadata["deletable"] = False

    return nb


def generate_assignment(nb: NotebookNode) -> NotebookNode:
    """Generates a student-facing assignment from an instructor notebook."""
    nb = strip_grader_only_cells_from_notebook(nb)
    nb = strip_solution_codes_from_notebook(nb)
    nb = obfuscate_hidden_test_cases(nb)
    nb = lock_test_cells(nb)

    return nb
