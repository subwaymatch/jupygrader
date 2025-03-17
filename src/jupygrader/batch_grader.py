"""
Batch grading functionality for processing multiple Jupyter notebooks.
"""

import time
from typing import List, Dict, Any, Union
from pathlib import Path
from datetime import datetime
from .grader import grade_notebook
from .types import GradingItemConfig


def grade_notebooks(
    grading_items: Union[
        str, Path, List[Union[str, Path]], GradingItemConfig, List[GradingItemConfig]
    ],
    verbose: bool = True,
) -> List[Dict[str, Any]]:
    """
    Grade one or multiple Jupyter notebooks using GradingItemConfig objects and report progress.

    Parameters
    ----------
    grading_items : GradingItemConfig or List[GradingItemConfig]
        Either a single grading item configuration or a list of them, each containing:
        - notebook_path: Path to the Jupyter notebook to be graded
        - output_path: Optional directory where results will be saved
        - copy_files: Optional files to be copied to the grading directory
    verbose : bool, default=True
        Whether to print progress information to stdout.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries containing grading results for each notebook.

    Notes
    -----
    This function processes notebooks sequentially and reports progress.
    Any errors encountered during grading are caught and reported, allowing
    the batch process to continue with remaining notebooks.
    """

    # Convert single str or Path to a list of GradingItemConfig
    if isinstance(grading_items, (str, Path)):
        grading_items = [GradingItemConfig(notebook_path=grading_items)]

    # Convert single GradingItemConfig to a list if needed
    elif isinstance(grading_items, GradingItemConfig):
        grading_items = [grading_items]

    # Convert list of str, Path, or GradingItemConfig to a list of GradingItemConfig
    elif isinstance(grading_items, list) and not all(
        isinstance(item, GradingItemConfig) for item in grading_items
    ):
        temp_grading_items = []
        for item in grading_items:
            if isinstance(item, (str, Path)):
                temp_grading_items.append(GradingItemConfig(notebook_path=item))
            elif isinstance(item, GradingItemConfig):
                temp_grading_items.append(item)
            else:
                raise TypeError(f"Unsupported type in grading_items: {type(item)}")
        grading_items = temp_grading_items

    results = []
    total_notebooks = len(grading_items)

    if verbose:
        print(
            f"Starting batch grading of {total_notebooks} notebook(s) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print("-" * 70)

    start_time = time.time()

    for idx, item in enumerate(grading_items, 1):
        try:
            notebook_path = item.notebook_path
            notebook_name = Path(notebook_path).name

            if verbose:
                print(
                    f"[{idx}/{total_notebooks}] Grading: {notebook_name} ... ",
                    end="",
                    flush=True,
                )

            # Grade individual notebook using the item's configuration
            result = grade_notebook(
                notebook_path=item.notebook_path,
                output_path=item.output_path,
                copy_files=item.copy_files,
            )

            # Add to results list
            results.append(result)

            if verbose:
                score = result.get("learner_autograded_score", 0)
                max_score = result.get("max_autograded_score", 0)
                print(f"Done. Score: {score}/{max_score}")

        except Exception as e:
            if verbose:
                print(f"Error: {str(e)}")
                print(f"Failed to grade notebook: {item.notebook_path}")

            # Add error information to results
            results.append(
                {
                    "filename": (
                        Path(item.notebook_path).name
                        if hasattr(item.notebook_path, "name")
                        else str(item.notebook_path)
                    ),
                    "status": "error",
                    "error_message": str(e),
                    "error_type": type(e).__name__,
                }
            )

    elapsed_time = time.time() - start_time

    if verbose:
        print("-" * 70)
        print(
            f"Completed grading {total_notebooks} notebook(s) in {elapsed_time:.2f} seconds"
        )

        # Summary statistics
        successful = sum(1 for r in results if r.get("status", "") != "error")
        failed = total_notebooks - successful
        print(f"Successfully graded: {successful}/{total_notebooks}")
        if failed > 0:
            print(f"Failed to grade: {failed}/{total_notebooks}")

    return results
