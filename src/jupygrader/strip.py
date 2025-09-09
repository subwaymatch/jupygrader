from nbformat.notebooknode import NotebookNode
import re

SOLUTION_STRIP_PATTERN = re.compile(
    r"(#\s*YOUR CODE BEGINS|###\s*BEGIN SOLUTION).*?(#\s*YOUR CODE ENDS|###\s*END SOLUTION)",
    re.DOTALL
)
SOLUTION_REPLACEMENT = "# YOUR CODE BEGINS\n\n# YOUR CODE ENDS"

def strip_solution_codes_from_notebook(nb: NotebookNode, clear_output: bool = True) -> NotebookNode:
    """Removes code between "# YOUR CODE BEGINS" or "### BEGIN SOLUTION" and "# YOUR CODE ENDS" or "### END SOLUTION" markers.

    Args:
        nb: The notebook to strip solution codes from
        clear_output: Whether to clear the output of code cells

    Returns:
        The notebook with all solution codes removed
    """
    for cell in nb.cells:
        # print(cell.cell_type)
        if cell.cell_type == "code":
            # Use a single regex substitution to replace all solution blocks
            cell.source = SOLUTION_STRIP_PATTERN.sub(SOLUTION_REPLACEMENT, cell.source)
            
            if clear_output:
                cell.outputs = []
                cell.execution_count = None

    return nb