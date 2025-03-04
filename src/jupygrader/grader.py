import tempfile
import jupygrader
import nbformat
from nbclient import NotebookClient
import os
from pathlib import Path
import shutil
import json
import hashlib
import sys
import platform
import uuid

# if output_path is not provided, it will be set to the parent directory of notebook_path
# This is useful for saving the graded notebook and result files in the same directory as the original notebook
# The function will also create a temporary directory to store the notebook while it is being graded
# The function will return a summary of the grading results, including the filename, scores, and test case results
# The function will also generate a text summary of the grading results
# The function will also extract the user code from the notebook and save it to a separate Python file
# The function will also save the graded notebook to HTML format
# The function will also save the graded result to a JSON file
def grade_notebook(
    notebook_path: str,
    output_path: str = None
):
    # Create a Path object for the notebook path
    p = Path(notebook_path)

    # Extract the filename from the path
    filename = p.name

    # If output_path is not provided, use the parent directory of notebook_path
    if output_path is None:
        output_path = str(p.parent)

    # Create the output directory if it does not exist
    output_path = Path(output_path)
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    # Create a temporary random directory for grading
    temp_workdir_path = Path(tempfile.gettempdir()) / ('jupygrader_' + str(uuid.uuid4())[:8])
    temp_workdir_path.mkdir(parents=True, exist_ok=False)

    # Save the current working directory
    original_cwd = os.getcwd()

    try:
        # Change the current working directory to the temporary directory
        os.chdir(temp_workdir_path)

        # Create a temporary path for the notebook
        temp_notebook_path = os.path.join(temp_workdir_path, filename)

        # Copy the original notebook to the temporary directory
        # Attempt to preserve the metadata using shutil.copy2()
        shutil.copy2(
            notebook_path,
            temp_notebook_path
        )

        print('=============================')
        # Read the notebook from the temporary path
        nb = nbformat.read(temp_notebook_path, as_version=4)

        # Get the hash of the test cases in the notebook
        test_cases_hash = jupygrader.get_test_cases_hash(nb)

        # Preprocess the test case cells in the notebook
        jupygrader.preprocess_test_case_cells(nb)
        # Add grader scripts to the notebook
        jupygrader.add_grader_scripts(nb)

        print(f'Grading {temp_notebook_path}')

        # Create a NotebookClient to execute the notebook
        client = NotebookClient(
            nb,
            timeout=600,
            kernel_name='python3',
            allow_errors=True
        )
        # Execute the notebook
        client.execute()

        # Save the graded notebook
        converted_notebook_path = os.path.join(output_path, filename.replace('.ipynb', '-graded.ipynb'))
        with open(converted_notebook_path, mode='w', encoding='utf-8') as f:
            nbformat.write(nb, f)

        # Running the notebook will store the graded result to a JSON file
        # Rename the graded result JSON file
        graded_result_json_path = os.path.join(output_path, filename.replace('.ipynb', '-result.json'))
        shutil.move('jupygrader-result.json', graded_result_json_path)

        # Read the graded result to generate a summary
        with open(graded_result_json_path, mode='r') as f:
            graded_result = json.load(f)

        # Add the filename to the graded result
        # We add it here instead of trying to add it within the Jupyter notebook
        # because it is tricky to grab the current file name inside a Jupyter kernel
        graded_result['filename'] = filename

        # Compute the MD5 hash of the submitted Jupyter notebook file
        # This can be used to detect duplicate submissions to prevent unnecessary re-grading
        with open(temp_notebook_path, 'rb') as f:
            graded_result['submission_notebook_hash'] = hashlib.md5(f.read()).hexdigest()

        # Add the MD5 hash of the test cases code
        # This helps us to identify any potential cases
        # where a learner has modified or deleted the test cases code cell
        graded_result['test_cases_hash'] = test_cases_hash

        # Store the Python version and platform used to run the notebook
        graded_result['grader_python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        graded_result['grader_platform'] = platform.platform()

        # Save the updated JSON to file
        with open(graded_result_json_path, 'w') as f:
            json.dump(graded_result, f, indent=2)
            
        # Clean up the notebook by removing grader scripts
        jupygrader.remove_grader_scripts(nb)
        # Add the graded result to the notebook
        jupygrader.add_graded_result(nb, graded_result)
            
        # Extract user code to a Python file
        extracted_user_code = jupygrader.extract_user_code_from_notebook(nb)
        extracted_code_path = os.path.join(output_path, filename.replace('.ipynb', '_user_code.py'))

        with open(extracted_code_path, "w", encoding="utf-8") as f:
            f.write(extracted_user_code)

        # Store the graded result to HTML
        filename_only = Path(temp_notebook_path).name
        graded_html_path = os.path.join(output_path, filename.replace('.ipynb', '-graded.html'))
        jupygrader.save_graded_notebook_to_html(
            nb,
            html_title=filename_only,
            output_path=graded_html_path,
            graded_result=graded_result
        )

        # LOCAL ENVIRONMENT ONLY
        # Generate a text summary of the graded result
        text_summary = jupygrader.generate_text_summary(graded_result)

        # Create a copy of the graded result and add the text summary
        result_summary = graded_result.copy()
        result_summary['text_summary'] = text_summary
        # del result_summary['results']

        text_summary_file_path = os.path.join(output_path, filename.replace('.ipynb', '-graded-result-summary.txt'))

        with open(text_summary_file_path, 'w', encoding='utf-8') as f:
            f.write(text_summary)

        print(f'Finished grading {filename}')
    finally:
        # Change back to the original working directory
        os.chdir(original_cwd)

        # Clean up the temporary working directory
        if temp_workdir_path.exists() and temp_workdir_path.is_dir():
            shutil.rmtree(temp_workdir_path)

    # Return the result summary
    return result_summary