from jupygrader import strip_solution_codes_from_notebook
from pathlib import Path
import nbformat

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / "test-files"
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_strip_and_obfuscate():
    notebook_path = TEST_NOTEBOOKS_DIR / "strip-and-obfuscate" / "strip-and-obfuscate.ipynb"

    nb = nbformat.read(notebook_path, as_version=4)

    stripped_nb = strip_solution_codes_from_notebook(nb)

    output_path = TEST_OUTPUT_DIR / "strip-and-obfuscate-stripped.ipynb"
    nbformat.write(stripped_nb, output_path)