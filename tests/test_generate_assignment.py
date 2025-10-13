from jupygrader import generate_assignment, grade_single_notebook
from pathlib import Path
import nbformat

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
