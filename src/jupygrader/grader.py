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
from typing import Union, List, Tuple, Optional, Iterator
import tempfile
import nbformat
from nbformat import NotebookNode
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
import contextlib


def _validate_paths(
    notebook_path_str: Union[str, Path], output_path_str: Optional[Union[str, Path]]
) -> Tuple[Path, Path]:
    """Validate notebook and output paths."""
    notebook_path = Path(notebook_path_str).resolve()
    if not notebook_path.exists():
        raise FileNotFoundError(f"Notebook file not found: {notebook_path}")

    if output_path_str is None:
        output_path = notebook_path.parent
    else:
        output_path = Path(output_path_str).resolve()

    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    elif not output_path.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {output_path}")

    return notebook_path, output_path


def _copy_required_files(
    grading_item: GradingItemConfig,
    notebook_path: Path,
    temp_workdir_path: Path,
    verbose: bool,
) -> None:
    """Copy notebook and any additional required files to the temporary directory."""
    filename = notebook_path.name
    temp_notebook_path = temp_workdir_path / filename
    # Attempt to preserve the metadata using shutil.copy2()
    shutil.copy2(notebook_path, temp_notebook_path)

    if not grading_item.copy_files:
        return

    copy_files_dict = (
        {}
        if isinstance(grading_item.copy_files, list)
        else copy.deepcopy(grading_item.copy_files)
    )

    if isinstance(grading_item.copy_files, list):
        for src in grading_item.copy_files:
            src_path = Path(src).resolve()
            try:
                relative_path = src_path.relative_to(notebook_path.parent)
            except ValueError:
                # If the file is not a subpath of the notebook's parent directory, copy it to the same folder as the notebook
                relative_path = Path(src_path.name)
            dest = temp_workdir_path / relative_path
            copy_files_dict[src_path] = dest

    for src, dest in copy_files_dict.items():
        src_path = Path(src).resolve()  # Convert back to Path if needed
        dest = temp_workdir_path / dest

        if verbose:
            print(f"Copying {src_path} to {dest}...")
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src_path.exists():
            if src_path.is_file():
                shutil.copy2(src_path, dest)
            elif src_path.is_dir():
                shutil.copytree(src_path, dest, dirs_exist_ok=True)
        else:
            print(f"Warning: Source file/dir not found, skipping copy: {src_path}")


@contextlib.contextmanager
def _prepare_grading_environment(
    grading_item: GradingItemConfig, verbose: bool
) -> Iterator[Tuple[Path, Path]]:
    """Context manager for setting up and cleaning up the grading environment."""
    notebook_path, output_path = _validate_paths(
        grading_item.notebook_path, grading_item.output_path
    )
    filename = notebook_path.name

    # Create a temporary random directory for grading
    temp_workdir_path = Path(tempfile.gettempdir()) / (
        "jupygrader_" + str(uuid.uuid4())[:8]
    )
    temp_workdir_path.mkdir(parents=True, exist_ok=False)
    temp_notebook_path = temp_workdir_path / filename

    original_cwd = os.getcwd()

    try:
        # Copy notebook and other files
        _copy_required_files(grading_item, notebook_path, temp_workdir_path, verbose)

        # Change the current working directory to the temporary directory
        os.chdir(temp_workdir_path)

        yield temp_notebook_path, output_path

    finally:
        # Change back to the original working directory
        os.chdir(original_cwd)

        # Clean up the temporary working directory
        if temp_workdir_path.exists() and temp_workdir_path.is_dir():
            shutil.rmtree(temp_workdir_path, ignore_errors=True)


def _prepare_notebook_for_grading(
    temp_notebook_path: Path,
) -> Tuple[NotebookNode, str]:
    """Reads, preprocesses, and injects grader scripts into the notebook."""
    nb = nbformat.read(temp_notebook_path, as_version=4)
    test_cases_hash = get_test_cases_hash(nb)
    preprocess_test_case_cells(nb)
    add_grader_scripts(nb)
    return nb, test_cases_hash


def _execute_notebook(
    nb: NotebookNode, timeout: int = 600, kernel_name: str = "python3"
) -> NotebookNode:
    """Executes the notebook using NotebookClient."""
    client = NotebookClient(
        nb, timeout=timeout, kernel_name=kernel_name, allow_errors=True
    )
    client.execute()  # Executes in place
    return nb


def _process_grading_results(
    graded_nb: NotebookNode,  # Notebook object after execution
    original_notebook_path: Path,
    temp_notebook_path: Path,  # Path to notebook within temp dir
    test_cases_hash: str,
) -> GradedResult:
    """Reads raw results, parses, and populates the GradedResult object."""
    # Read the graded result generated by the injected scripts
    results_json_path = Path(GRADED_RESULT_JSON_FILENAME)
    if not results_json_path.exists():
        raise FileNotFoundError(f"Grading result file not found: {results_json_path}")

    with open(results_json_path, mode="r", encoding="utf-8") as f:
        graded_result_data = json.load(f)

    # Convert the graded result data to a GradedResult object
    graded_result = GradedResult.from_dict(graded_result_data)

    # Add metadata
    graded_result.filename = original_notebook_path.name
    graded_result.test_cases_hash = test_cases_hash

    # Compute the MD5 hash of the *original* submitted notebook file for reference
    # Note: Using the temp_notebook_path *before* modification might be desired,
    # or recalculating from the original_notebook_path. Using temp_notebook_path for now.
    with open(temp_notebook_path, "rb") as f:
        graded_result.submission_notebook_hash = hashlib.md5(f.read()).hexdigest()

    graded_result.grader_python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    graded_result.grader_platform = platform.platform()
    graded_result.jupygrader_version = jupygrader_version

    return graded_result


def _generate_output_artifacts(
    nb: NotebookNode,
    graded_result: GradedResult,
    output_path: Path,
    filename_base: str,
) -> None:
    """Cleans the notebook and saves all output files."""
    # --- Save Graded Notebook (.ipynb) ---
    graded_notebook_filename = f"{filename_base}-graded.ipynb"
    graded_notebook_path = output_path / graded_notebook_filename
    with open(graded_notebook_path, mode="w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    # Note: No need to store this path in GradedResult, standard naming convention assumed

    # Clean up the notebook by removing grader scripts
    remove_grader_scripts(nb)
    # Add the graded result summary to the notebook metadata
    add_graded_result_to_notebook(nb, graded_result)

    # --- Extract and Save User Code (.py) ---
    extracted_user_code = extract_user_code_from_notebook(nb)
    extracted_code_filename = f"{filename_base}_user_code.py"
    extracted_code_path = output_path / extracted_code_filename
    with open(extracted_code_path, "w", encoding="utf-8") as f:
        f.write(extracted_user_code)
    graded_result.extracted_user_code_file = str(extracted_code_path.resolve())

    # --- Save Graded HTML Report ---
    graded_html_filename = f"{filename_base}-graded.html"
    graded_html_path = output_path / graded_html_filename
    save_graded_notebook_to_html(
        nb,
        html_title=f"{filename_base}.ipynb",  # Use original-like name for title
        output_path=graded_html_path,
        graded_result=graded_result,
    )
    graded_result.graded_html_file = str(graded_html_path.resolve())

    # --- Save Text Summary ---
    text_summary_filename = f"{filename_base}-graded-result-summary.txt"
    text_summary_file_path = output_path / text_summary_filename
    with open(text_summary_file_path, "w", encoding="utf-8") as f:
        f.write(graded_result.text_summary)
    graded_result.text_summary_file = str(text_summary_file_path.resolve())

    # --- Save Final Graded Result JSON ---
    graded_result_json_filename = f"{filename_base}-graded-result.json"
    graded_result_json_path = output_path / graded_result_json_filename
    with open(graded_result_json_path, "w", encoding="utf-8") as f:
        json.dump(graded_result.to_dict(), f, indent=2)
    # Note: No need to store this path in GradedResult, standard naming convention assumed


def _grade_item(
    grading_item: GradingItemConfig,
    verbose: bool = True,
) -> GradedResult:
    """Grade a single notebook based on a GradingItemConfig. (Orchestrator)"""
    start_time = time.time()
    original_notebook_path = Path(grading_item.notebook_path).resolve()
    filename_base = original_notebook_path.stem  # Name without extension

    notebook_path, output_path = _validate_paths(
        grading_item.notebook_path, grading_item.output_path
    )
    # Extract the filename from the path
    filename = notebook_path.name

    # Create a temporary random directory for grading
    temp_workdir_path = Path(tempfile.gettempdir()) / (
        "jupygrader_" + str(uuid.uuid4())[:8]
    )
    temp_workdir_path.mkdir(parents=True, exist_ok=False)

    # Save the current working directory
    original_cwd = os.getcwd()

    try:
        # Copy notebook and other files
        _copy_required_files(grading_item, notebook_path, temp_workdir_path, verbose)

        temp_notebook_path = temp_workdir_path / filename

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

        # Change the current working directory to the temporary directory
        os.chdir(temp_workdir_path)

        # Create a NotebookClient to execute the notebook
        client = NotebookClient(
            nb, timeout=600, kernel_name="python3", allow_errors=True
        )
        # Execute the notebook
        client.execute()

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

        _generate_output_artifacts(nb, graded_result, output_path, filename_base)

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


def _normalize_grading_items(
    items: List[Union[str, Path, GradingItemConfig, dict]],
) -> List[GradingItemConfig]:
    """Converts input list items to GradingItemConfig objects."""
    normalized_items: List[GradingItemConfig] = []
    for item in items:
        if isinstance(item, (str, Path)):
            normalized_items.append(GradingItemConfig(notebook_path=item))
        elif isinstance(item, GradingItemConfig):
            normalized_items.append(item)
        elif isinstance(item, dict):
            normalized_items.append(GradingItemConfig(**item))
        else:
            raise TypeError(f"Unsupported type in grading_items: {type(item)}")
    return normalized_items


def _export_results_to_csv(
    results: List[GradedResult],
    csv_output_path: Optional[Union[str, Path]],
    verbose: bool,
) -> None:
    """Exports the list of GradedResult objects to a CSV file."""
    if not results:
        if verbose:
            print("No results to export to CSV.")
        return

    # Create timestamp for CSV filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"graded_results_{timestamp}.csv"

    # Determine the output path
    if csv_output_path is None:
        csv_path = Path(csv_filename).resolve()  # Save in current dir by default
    else:
        csv_output_path = Path(csv_output_path).resolve()
        csv_path = (
            csv_output_path / csv_filename
            if csv_output_path.is_dir()
            else csv_output_path  # Assume full path if not a dir
        )

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
    try:
        df = pd.DataFrame(data)
        # Ensure the directory exists
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        # Export to CSV
        df.to_csv(csv_path, index=False, encoding="utf-8")
        if verbose:
            print(f"Results exported to CSV: {csv_path}")
    except Exception as e:
        print(f"Error exporting results to CSV: {e}")


def grade_notebooks(
    items_to_grade: List[Union[str, Path, GradingItemConfig, dict]],
    verbose: bool = True,
    export_csv: bool = True,
    csv_output_path: Optional[Union[str, Path]] = None,
) -> List[GradedResult]:
    """Grade multiple Jupyter notebooks and report progress.

    Processes a list of notebook grading tasks, executing each notebook in a clean
    environment, evaluating test cases, and producing graded outputs.

    Args:
        grading_items: List of items to grade, which can be a mix of:
            - Strings with paths to notebook files
            - Path objects pointing to notebook files
            - GradingItemConfig objects with detailed grading configuration
            - Dictionaries with the same keys as GradingItemConfig
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
    try:
        items_to_grade = _normalize_grading_items(items_to_grade)
    except TypeError as e:
        print(f"Error processing grading items: {str(e)}")
        return []

    results: List[GradedResult] = []
    num_items = len(items_to_grade)
    num_failed_grading = 0

    if verbose:
        print(
            f"Starting grading of {num_items} notebook(s) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    start_time = time.time()

    for idx, item in enumerate(items_to_grade, start=1):
        try:
            notebook_path = item.notebook_path
            notebook_name = Path(notebook_path).name

            if verbose:
                print("-" * 70)
                print(
                    f"[{idx}/{num_items}] Grading: {notebook_name} ... ",
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
                print(f"Progress: {round(idx / num_items * 100, 1)}%")

    elapsed_time = time.time() - start_time

    if verbose:
        print("-" * 70)
        print(
            f"Completed grading {num_items} notebook(s) in {elapsed_time:.2f} seconds"
        )

        print(f"Successfully graded: {num_items - num_failed_grading}/{num_items}")
        if num_failed_grading > 0:
            print(f"Failed to grade: {num_failed_grading}/{num_items}")

    # Export results to CSV if requested
    if export_csv:
        _export_results_to_csv(results, csv_output_path, verbose)

    return results


def grade_single_notebook(
    grading_item: Union[str, Path, GradingItemConfig, dict],
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
    r = grade_notebooks([grading_item], verbose=verbose, export_csv=False)

    return r[0] if len(r) > 0 else None
