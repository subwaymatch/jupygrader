import jupygrader
from pathlib import Path
import glob

TEST_NOTEBOOKS_DIR = Path(__file__).resolve().parent / 'test-notebooks'
TEST_OUTPUT_DIR = Path(__file__).resolve().parent / 'test-output'

notebook_files = glob.glob('')

# use this file to run only a single test function
# hatch test --ignore tests/test_grader.py
def test_batch_grader():
    notebook_path = TEST_NOTEBOOKS_DIR / 'batch'

    print('notebook_path')
    print(str(notebook_path / '*.ipynb'))
    
    test_notebook_paths = glob.glob(str(notebook_path / '*.ipynb'))

    print('test_notebook_paths')
    print(test_notebook_paths)

    results = jupygrader.grade_notebooks(
        notebook_paths=test_notebook_paths,
        output_path=TEST_OUTPUT_DIR
    )

    print('results')
    print(results)