from .models.grading_dataclasses import (
    BatchGradingConfig,
    GradingItem,
    GradedResult,
    FilePath,
    FileDict,
)
from .models.grading_task import GradingTask
from typing import Union, List, Tuple, Optional, Iterator, Dict
from pathlib import Path
import time
from datetime import datetime
import pandas as pd


def _normalize_grading_items(
    items: List[Union[str, Path, GradingItem, dict]],
) -> List[GradingItem]:
    """Converts input list items to GradingItem objects."""
    normalized_items: List[GradingItem] = []
    for item in items:
        if isinstance(item, (str, Path)):
            normalized_items.append(GradingItem(notebook_path=item))
        elif isinstance(item, GradingItem):
            normalized_items.append(item)
        elif isinstance(item, dict):
            normalized_items.append(GradingItem(**item))
        else:
            raise TypeError(f"Unsupported type in grading_items: {type(item)}")
    return normalized_items


def _export_results_to_csv(
    results: List[GradedResult],
    csv_output_path: Optional[FilePath],
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
    grading_items: List[Union[FilePath, GradingItem, dict]],
    *,
    base_files: Optional[Union[FilePath, List[FilePath], FileDict]] = None,
    verbose: bool = True,
    export_csv: bool = True,
    csv_output_path: Optional[FilePath] = None,
) -> List[GradedResult]:
    try:
        working_items: List[GradingItem] = _normalize_grading_items(grading_items)
    except TypeError as e:
        print(f"Error processing grading items: {str(e)}")
        return []

    results: List[GradedResult] = []
    num_items = len(working_items)
    num_failed_grading = 0

    if verbose:
        print(
            f"Starting grading of {num_items} notebook(s) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    start_time = time.time()

    for idx, item in enumerate(working_items, start=1):
        try:
            notebook_path = item.notebook_path
            notebook_name = Path(notebook_path).name

            if verbose:
                print("-" * 70)
                print(
                    f"[{idx}/{num_items}] Grading: {notebook_name} ... ",
                )

            batch_config = BatchGradingConfig(
                base_files=base_files,
                verbose=verbose,
                export_csv=export_csv,
                csv_output_path=csv_output_path,
            )

            grading_task = GradingTask(item, batch_config)

            graded_result = grading_task.grade()

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
    grading_item: Union[FilePath, GradingItem, dict],
    *,
    verbose: bool = True,
) -> Union[GradedResult, None]:
    """Grade a single Jupyter notebook.

    Convenience function to grade just one notebook. Internally calls `grade_notebooks()`
    with a single-item list.

    Args:
        grading_item: The notebook to grade, can be:
            - String with path to a notebook file
            - Path object pointing to a notebook file
            - GradingItem object with detailed grading configuration
        verbose: Whether to print progress and diagnostic information. Defaults to True.

    Returns:
        GradedResult object with detailed grading results, or None if grading failed.
    """
    r = grade_notebooks([grading_item], verbose=verbose, export_csv=False)

    return r[0] if len(r) > 0 else None
