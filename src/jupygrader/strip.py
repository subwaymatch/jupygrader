from nbformat.notebooknode import NotebookNode

def strip_solution_codes_from_notebook(nb: NotebookNode, clear_output: bool = True) -> NotebookNode:
    """Removes code between "# YOUR CODE BEGINS" or "### BEGIN SOLUTION" and "# YOUR CODE ENDS" or "### END SOLUTION" markers.

    Args:
        nb: The notebook to strip solution codes from
        clear_output: Whether to clear the output of code cells

    Returns:
        The notebook with all solution codes removed
    """
    for cell in nb.cells:
        if cell.type == "code":
            if clear_output:
                cell.outputs = []
                cell.execution_count = None

    return nb