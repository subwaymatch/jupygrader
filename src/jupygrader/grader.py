from .__about__ import __version__ as jupygrader_version
from .notebook_operations import (
    get_test_cases_hash,
    preprocess_test_case_cells,
    add_grader_scripts,
    remove_grader_scripts,
    add_graded_result_to_notebook,
    extract_user_code_from_notebook,
    save_graded_notebook_to_html,
)
from .constants import GRADED_RESULT_JSON_FILENAME
from .types import GradingItemConfig, GradedResult
from typing import Union, List, Optional
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
import copy
import time
from datetime import datetime
import pandas as pd


def _grade_item(
    grading_item: GradingItemConfig,
    verbose: bool = True,
) -> GradedResult:
    # Convert notebook_path to an absolute Path object
    notebook_path = Path(grading_item.notebook_path).resolve()

    # Ensure the notebook file exists
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook file not found: {notebook_path}")

    # Extract the filename from the path
    filename = notebook_path.name

    # By default, use the notebook's parent directory as the output path
    output_path = notebook_path.parent

    # If output_path is provided, use it instead
    if grading_item.output_path is not None:
        # Convert output_path to an absolute Path object
        output_path = Path(grading_item.output_path).resolve()

    # Create the output directory if it does not exist
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    elif not output_path.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {output_path}")

    # Create a temporary random directory for grading
    temp_workdir_path = Path(tempfile.gettempdir()) / (
        "jupygrader_" + str(uuid.uuid4())[:8]
    )
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
        shutil.copy2(notebook_path, temp_notebook_path)

        # Copy additional files if provided
        if grading_item.copy_files:
            copy_files_dict = (
                {}
                if type(grading_item.copy_files) is list
                else copy.deepcopy(grading_item.copy_files)
            )
            if isinstance(grading_item.copy_files, list):
                for src in grading_item.copy_files:
                    src_path = Path(src).resolve()
                    relative_path = src_path.relative_to(notebook_path.parent)
                    dest = temp_workdir_path / relative_path
                    copy_files_dict[src] = dest

            for src, dest in copy_files_dict.items():
                src_path = Path(src).resolve()
                dest_path = temp_workdir_path / dest
                if verbose:
                    print(f"Copying {src_path} to {dest_path}...")
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)

        # Read the notebook from the temporary path
        nb = nbformat.read(temp_notebook_path, as_version=4)

        # Get the hash of the test cases in the notebook
        test_cases_hash = get_test_cases_hash(nb)

        # Preprocess the test case cells in the notebook
        preprocess_test_case_cells(nb)

        # Add grader scripts to the notebook
        add_grader_scripts(nb)

        if verbose:
            print(f"Grading {temp_notebook_path}")

        # Create a NotebookClient to execute the notebook
        client = NotebookClient(
            nb, timeout=600, kernel_name="python3", allow_errors=True
        )
        # Execute the notebook
        client.execute()

        # Save the graded notebook
        converted_notebook_path = os.path.join(
            output_path, filename.replace(".ipynb", "-graded.ipynb")
        )
        with open(converted_notebook_path, mode="w", encoding="utf-8") as f:
            nbformat.write(nb, f)

        # Read the graded result to generate a summary
        with open(GRADED_RESULT_JSON_FILENAME, mode="r") as f:
            graded_result_data = json.load(f)

        # Convert the graded result data to a GradedResult object
        graded_result = GradedResult.from_dict(graded_result_data)

        # Add the filename to the graded result
        graded_result.filename = filename

        # Compute the MD5 hash of the submitted Jupyter notebook file
        with open(temp_notebook_path, "rb") as f:
            graded_result.submission_notebook_hash = hashlib.md5(f.read()).hexdigest()

        # Add the MD5 hash of the test cases code
        graded_result.test_cases_hash = test_cases_hash

        # Store the Python version and platform used to run the notebook
        graded_result.grader_python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        graded_result.grader_platform = platform.platform()
        graded_result.jupygrader_version = jupygrader_version

        # Clean up the notebook by removing grader scripts
        remove_grader_scripts(nb)
        # Add the graded result to the notebook
        add_graded_result_to_notebook(nb, graded_result)

        # Extract user code to a Python file
        extracted_user_code = extract_user_code_from_notebook(nb)
        extracted_code_path = os.path.join(
            output_path, filename.replace(".ipynb", "_user_code.py")
        )

        graded_result.extracted_user_code_file = extracted_code_path

        with open(extracted_code_path, "w", encoding="utf-8") as f:
            f.write(extracted_user_code)

        # Store the graded result to HTML
        filename_only = Path(temp_notebook_path).name
        graded_html_path = os.path.join(
            output_path, filename.replace(".ipynb", "-graded.html")
        )
        save_graded_notebook_to_html(
            nb,
            html_title=filename_only,
            output_path=graded_html_path,
            graded_result=graded_result,
        )

        graded_result.graded_html_file = graded_html_path

        text_summary_file_path = os.path.join(
            output_path, filename.replace(".ipynb", "-graded-result-summary.txt")
        )

        with open(text_summary_file_path, "w", encoding="utf-8") as f:
            f.write(graded_result.text_summary)

        graded_result.text_summary_file = text_summary_file_path

        # Save the updated JSON to file
        graded_result_json_path = os.path.join(
            output_path, filename.replace(".ipynb", "-graded-result.json")
        )

        with open(graded_result_json_path, "w") as f:
            json.dump(graded_result.to_dict(), f, indent=2)

        if verbose:
            print(f"Finished grading {filename}")
    finally:
        # Change back to the original working directory
        os.chdir(original_cwd)

        # Clean up the temporary working directory
        if temp_workdir_path.exists() and temp_workdir_path.is_dir():
            shutil.rmtree(temp_workdir_path, ignore_errors=True)

    # Return the GradedResult object
    return graded_result


def grade_notebooks(
    grading_items: List[Union[str, Path, GradingItemConfig]],
    verbose: bool = True,
    export_csv: bool = True,
    csv_output_path: Optional[Union[str, Path]] = None,
) -> List[GradedResult]:
    """Grade multiple Jupyter notebooks and report progress.

    Processes a list of notebook grading tasks, executing each notebook in a clean
    environment, evaluating test cases, and producing graded outputs.

    Args:
        grading_items: List of items to grade, which can be:
            - Strings with paths to notebook files
            - Path objects pointing to notebook files
            - GradingItemConfig objects with detailed grading configuration
        verbose: Whether to print progress and diagnostic information. Defaults to True.
        export_csv: Whether to export results to CSV file. Defaults to True.
        csv_output_path: Optional path for the CSV export. If None, uses current directory.
            Defaults to None.

    Returns:
        List of GradedResult objects containing detailed results for each notebook.

    Raises:
        TypeError: If an element in grading_items is not a supported type.
        ImportError: If pandas is not available when export_csv=True.
    """
    temp_grading_items: List[GradingItemConfig] = []
    for item in grading_items:
        if isinstance(item, (str, Path)):
            temp_grading_items.append(GradingItemConfig(notebook_path=item))
        elif isinstance(item, GradingItemConfig):
            temp_grading_items.append(item)
        else:
            raise TypeError(f"Unsupported type in grading_items: {type(item)}")
    grading_items = temp_grading_items

    results: List[GradedResult] = []
    total_notebooks = len(grading_items)
    num_failed_grading = 0

    if verbose:
        print(
            f"Starting grading of {total_notebooks} notebook(s) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    start_time = time.time()

    for idx, item in enumerate(grading_items, start=1):
        try:
            notebook_path = item.notebook_path
            notebook_name = Path(notebook_path).name

            if verbose:
                print("-" * 70)
                print(
                    f"[{idx}/{total_notebooks}] Grading: {notebook_name} ... ",
                )

            # Grade individual notebook using the item's configuration
            graded_result = _grade_item(item, verbose=verbose)

            # Add to results list
            results.append(graded_result)

            if verbose:
                score = graded_result.learner_autograded_score
                max_score = graded_result.max_autograded_score
                print(f"Done. Score: {score}/{max_score}")

        except Exception as e:
            num_failed_grading += 1

            if verbose:
                print(f"Error: {str(e)}")
                print(f"Failed to grade notebook: {item.notebook_path}")

        finally:
            if verbose:
                print(f"Progress: {round(idx / total_notebooks * 100, 1)}%")

    elapsed_time = time.time() - start_time

    if verbose:
        print("-" * 70)
        print(
            f"Completed grading {total_notebooks} notebook(s) in {elapsed_time:.2f} seconds"
        )

        print(
            f"Successfully graded: {total_notebooks - num_failed_grading}/{total_notebooks}"
        )
        if num_failed_grading > 0:
            print(f"Failed to grade: {num_failed_grading}/{total_notebooks}")

    # Export results to CSV if requested
    if export_csv and results:
        # Create timestamp for CSV filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"graded_results_{timestamp}.csv"

        # Determine the output path
        if csv_output_path is None:
            csv_path = Path(csv_filename)

        else:
            csv_output_path = Path(csv_output_path)

            if csv_output_path.is_dir():
                csv_path = Path(csv_output_path) / csv_filename
                csv_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                csv_path = Path(csv_output_path)

        # Extract main attributes from GradedResult objects
        data = []
        for result in results:
            # Create a dictionary with selected attributes
            result_dict = {
                "filename": result.filename,
                "learner_autograded_score": result.learner_autograded_score,
                "max_autograded_score": result.max_autograded_score,
                "max_manually_graded_score": result.max_manually_graded_score,
                "max_total_score": result.max_total_score,
                "num_autograded_cases": result.num_autograded_cases,
                "num_passed_cases": result.num_passed_cases,
                "num_failed_cases": result.num_failed_cases,
                "num_manually_graded_cases": result.num_manually_graded_cases,
                "num_total_test_cases": result.num_total_test_cases,
                "grading_finished_at": result.grading_finished_at,
                "grading_duration_in_seconds": result.grading_duration_in_seconds,
                "submission_notebook_hash": result.submission_notebook_hash,
                "test_cases_hash": result.test_cases_hash,
                "grader_python_version": result.grader_python_version,
                "grader_platform": result.grader_platform,
                "text_summary": result.text_summary,
            }
            data.append(result_dict)

        # Create DataFrame and export
        df = pd.DataFrame(data)

        # Ensure the directory exists
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # Export to CSV
        df.to_csv(csv_path, index=False)

        if verbose:
            print(f"Results exported to CSV: {csv_path}")

    return results


def grade_single_notebook(
    grading_item: Union[str, Path, GradingItemConfig],
    verbose: bool = True,
) -> Union[GradedResult, None]:
    """Grade a single Jupyter notebook.

    Convenience function to grade just one notebook. Internally calls `grade_notebooks()`
    with a single-item list.

    Args:
        grading_item: The notebook to grade, can be:
            - String with path to a notebook file
            - Path object pointing to a notebook file
            - GradingItemConfig object with detailed grading configuration
        verbose: Whether to print progress and diagnostic information. Defaults to True.

    Returns:
        GradedResult object with detailed grading results, or None if grading failed.
    """
    r = grade_notebooks([grading_item], verbose=verbose)

    return r[0] if len(r) > 0 else None
