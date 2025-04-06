from jupygrader import grade_single_notebook
from pathlib import Path
import nbformat
from nbformat.v4 import new_notebook, new_code_cell

TEST_OUTPUT_DIR = Path(__file__).resolve().parent / "test-output"

# Create the output directory if it doesn't exist
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_large_number_of_test_cases():
    generated_notebook_path = TEST_OUTPUT_DIR / "large-number-of-test-cases-test.ipynb"

    nb = new_notebook()
    cells = []

    for test_case_number in range(1, 101):
        if test_case_number % 4 <= 1:
            code = (
                f'_test_case = "tc-{test_case_number}"\n'
                f"_points = {test_case_number}"
            )
        elif test_case_number % 4 == 2:
            code = (
                f'_test_case = "tc-{test_case_number}"\n'
                f"_points = {test_case_number}\n\n"
                "assert 1 == 2"
            )
        else:  # test_case_number % 4 == 3
            code = (
                f'_test_case = "tc-{test_case_number}"\n'
                f"_points = {test_case_number}\n"
                f"_grade_manually = True"
            )

        cells.append(new_code_cell(source=code))

    nb.cells = cells

    # Save to file
    with generated_notebook_path.open("w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    result = grade_single_notebook(
        {
            "notebook_path": generated_notebook_path,
            "output_path": TEST_OUTPUT_DIR,
        },
        regrade_existing=True,
    )

    assert result.num_total_test_cases == 100
