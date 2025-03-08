import jupygrader
from typing import Union, Dict, Any
import tempfile
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

def grade_notebook(
    notebook_path: Union[str, Path],
    output_path: Union[str, Path] = None,
    copy_files: Union[list, dict] = None
) -> Dict[str, Any]:
    """
    Grades a Jupyter notebook by executing it and evaluating test cases.

    Parameters:
    -----------
    notebook_path : str or Path
        Path to the Jupyter notebook to be graded.
    output_path : str or Path, optional
        Directory where the graded notebook and results will be saved.
        Defaults to the parent directory of `notebook_path` if not provided.
    copy_files : list or dict, optional
        List or dictionary of files to be copied to the temporary grading directory.
        If a list is provided, the files will be copied with their original names.
        If a dictionary is provided, the keys are the source file paths and the values are the destination file names.

    Functionality:
    --------------
    - Copies the original notebook to a temporary directory for grading.
    - Executes the notebook and evaluates embedded test cases.
    - Saves the graded notebook in multiple formats:
        - `.ipynb`: Includes execution results and grading feedback.
        - `.html`: A rendered version of the graded notebook.
        - `.json`: Stores grading results, scores, and metadata.
        - `.txt`: A text summary of the grading results.
    - Extracts user code from the notebook and saves it as a separate Python file.
    - Computes an MD5 hash of the submitted notebook for duplicate detection.
    - Stores metadata including Python version and system information.
    - Cleans up temporary files after grading.

    Returns:
    --------
    dict
        A dictionary containing the grading results, including:
        - Filename
        - Scores
        - Test case results
        - Submission hash
        - Test case hash
        - Grading environment details

    Raises:
    -------
    FileNotFoundError:
        If the specified notebook file does not exist.
    NotADirectoryError:
        If `output_path` is provided but is not a valid directory.
    """

    # Convert notebook_path to an absolute Path object
    notebook_path = Path(notebook_path).resolve()
    
    # Ensure the notebook file exists
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook file not found: {notebook_path}")
    
    # Extract the filename from the path
    filename = notebook_path.name
    
    # If output_path is not provided, use the parent directory of notebook_path
    if output_path is None:
        output_path = notebook_path.parent
    else:
        # Convert output_path to an absolute Path object
        output_path = Path(output_path).resolve()
    
    # Create the output directory if it does not exist
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    elif not output_path.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {output_path}")
    
    # Create a temporary random directory for grading
    temp_workdir_path = Path(tempfile.gettempdir()) / ('jupygrader_' + str(uuid.uuid4())[:8])
    temp_workdir_path.mkdir(parents=True, exist_ok=False)
    
    # Save the current working directory
    original_cwd = os.getcwd()
    
    try:
        # Change the current working directory to the temporary directory
        os.chdir(temp_workdir_path)
        
        # Create a temporary path for the notebook
        temp_notebook_path = temp_workdir_path / filename
        
        # Copy the original notebook to the temporary directory
        # Attempt to preserve the metadata using shutil.copy2()
        shutil.copy2(
            notebook_path,
            temp_notebook_path
        )
        
        # Copy additional files if provided
        if copy_files:
            if isinstance(copy_files, list):
                copy_files = {file: Path(file).name for file in copy_files}
            for src, dest in copy_files.items():
                src_path = Path(src).resolve()
                dest_path = temp_workdir_path / dest
                print(f'Copying {src_path} to {dest_path}...')
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
        
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

        # Generate a text summary of the graded result
        text_summary = jupygrader.generate_text_summary(graded_result)

        # Create a copy of the graded result and add the text summary
        result_summary = graded_result.copy()
        result_summary['text_summary'] = text_summary

        text_summary_file_path = os.path.join(output_path, filename.replace('.ipynb', '-graded-result-summary.txt'))

        with open(text_summary_file_path, 'w', encoding='utf-8') as f:
            f.write(text_summary)

        print(f'Finished grading {filename}')
    finally:
        # Change back to the original working directory
        os.chdir(original_cwd)

        # Clean up the temporary working directory
        if temp_workdir_path.exists() and temp_workdir_path.is_dir():
            shutil.rmtree(temp_workdir_path, ignore_errors=True)

    # Return the result summary
    return result_summary