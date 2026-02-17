from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_raw_cell

from jupygrader import generate_assignment

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = (
    Path(__file__).resolve().parent / "test-output" / "generate-assignment"
)

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_strip_and_obfuscate():
    notebook_path = (
        TEST_NOTEBOOKS_DIR / "generate-assignment" / "generate-assignment.ipynb"
    )

    nb = nbformat.read(notebook_path, as_version=4)

    processed_nb = generate_assignment(nb)

    output_path = TEST_OUTPUT_DIR / "generated-assignment.ipynb"
    nbformat.write(processed_nb, output_path)


def test_strip_grader_only_cells():
    nb = new_notebook(
        cells=[
            new_markdown_cell("# GRADER_ONLY\ninternal note"),
            new_code_cell("# grader_only\nprint('remove')"),
            new_code_cell("! grader_only\nprint('remove too')"),
            new_code_cell(" _grader_only=True\nprint('remove three')"),
            new_code_cell("\t_grader_only\t=\tTrue\nprint('remove four')"),
            new_code_cell("_grader_only = true\nprint('keep due to case')"),
            new_raw_cell("# GRADER_ONLY\nraw cell to remove"),
            new_markdown_cell("# public note"),
            new_code_cell("print('keep')"),
        ]
    )

    processed_nb = generate_assignment(nb)

    sources = [cell.source for cell in processed_nb.cells]
    assert "# public note" in sources
    assert "print('keep')" in sources
    assert "_grader_only = true\nprint('keep due to case')" in sources

    assert "# GRADER_ONLY\ninternal note" not in sources
    assert "# GRADER_ONLY\nraw cell to remove" not in sources
    assert "# grader_only\nprint('remove')" not in sources
    assert "! grader_only\nprint('remove too')" not in sources
    assert " _grader_only=True\nprint('remove three')" not in sources
    assert "\t_grader_only\t=\tTrue\nprint('remove four')" not in sources
