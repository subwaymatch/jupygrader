import nbformat

from jupygrader.notebook_operations import comment_out_magic_commands


def test_comment_out_magic_commands_in_code_cells():
    nb = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell("!pip install statsmodels\n%rm -rf some_dir\nx = 1"),
            nbformat.v4.new_markdown_cell("%not-in-markdown"),
            nbformat.v4.new_code_cell("print('ok')\n  !echo hello"),
        ]
    )

    comment_out_magic_commands(nb)

    assert nb.cells[0].source == "# !pip install statsmodels\n# %rm -rf some_dir\nx = 1"
    assert nb.cells[1].source == "%not-in-markdown"
    assert nb.cells[2].source == "print('ok')\n  # !echo hello"
