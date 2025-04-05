from .models.grading_dataclasses import (
    BatchGradingConfig,
    GradingItem,
    GradedResult,
    FilePath,
    FileDict,
)
from .models.batch_grading_manager import BatchGradingManager
from typing import Union, List, Optional


def grade_notebooks(
    grading_items: List[Union[FilePath, GradingItem, dict]],
    *,
    base_files: Optional[Union[FilePath, List[FilePath], FileDict]] = None,
    verbose: bool = True,
    export_csv: bool = True,
    csv_output_path: Optional[FilePath] = None,
    regrade_existing: bool = False,
) -> List[GradedResult]:
    """Grade multiple Jupyter notebooks with test cases.

    Processes a list of notebook grading items, executes each notebook in a clean
    environment, evaluates test cases, and produces graded outputs. Can handle both
    simple file paths and complex grading configurations.

    Args:
        grading_items: List of items to grade, which can be:
            - Strings or Path objects with paths to notebook files
            - GradingItem objects with detailed grading configuration
            - Dictionaries that can be converted to GradingItem objects
        base_files: Optional files to include in all grading environments. Can be:
            - A single file path (string or Path)
            - A list of file paths
            - A dictionary mapping source paths to destination paths
        verbose: Whether to print progress and diagnostic information. Defaults to True.
        export_csv: Whether to export results to CSV file. Defaults to True.
        csv_output_path: Optional path for the CSV export. If None, uses notebook
            output directories. Defaults to None.
        regrade_existing: Whether to regrade notebooks even if results already exist.
            Defaults to False.

    Returns:
        List of GradedResult objects containing detailed results for each notebook.

    Raises:
        TypeError: If an element in grading_items has an unsupported type.
        ValueError: If a required path doesn't exist or has invalid configuration.

    Examples:
        >>> # Grade multiple notebooks with default settings
        >>> results = grade_notebooks(["student1.ipynb", "student2.ipynb"])
        >>>
        >>> # With custom configurations
        >>> results = grade_notebooks([
        ...     GradingItem(notebook_path="student1.ipynb", output_path="results"),
        ...     GradingItem(notebook_path="student2.ipynb", output_path="results"),
        ... ], base_files=["data.csv", "helpers.py"], export_csv=True)
    """
    batch_config = BatchGradingConfig(
        base_files=base_files,
        verbose=verbose,
        export_csv=export_csv,
        csv_output_path=csv_output_path,
        regrade_existing=regrade_existing,
    )

    manager = BatchGradingManager(
        grading_items=grading_items, batch_config=batch_config
    )

    return manager.grade()


def grade_single_notebook(
    grading_item: Union[FilePath, GradingItem, dict],
    **kwargs,
) -> Optional[GradedResult]:
    """Grade a single Jupyter notebook with test cases.

    Executes a notebook in a clean environment, evaluates test cases, and produces
    graded outputs. A convenience wrapper around grade_notebooks() for single notebook grading.

    Args:
        grading_item: The notebook to grade, which can be:
            - A string or Path object with path to notebook file
            - A GradingItem object with detailed grading configuration
            - A dictionary that can be converted to a GradingItem object
        **kwargs: Additional keyword arguments passed to grade_notebooks():
            - base_files: Files to include in grading environment
            - verbose: Whether to print progress information
            - regrade_existing: Whether to regrade if results exist
            - csv_output_path: Path for CSV output (if needed)

    Returns:
        GradedResult object containing detailed results, or None if grading failed.

    Raises:
        TypeError: If grading_item has an unsupported type.
        ValueError: If a required path doesn't exist or has invalid configuration.

    Examples:
        >>> # Grade a notebook with default settings
        >>> result = grade_single_notebook("student1.ipynb")
        >>> print(f"Score: {result.learner_autograded_score}/{result.max_total_score}")
        >>>
        >>> # With custom configuration
        >>> result = grade_single_notebook(
        ...     GradingItem(
        ...         notebook_path="student1.ipynb",
        ...         output_path="results",
        ...         copy_files=["data.csv"]
        ...     ),
        ...     verbose=True
        ... )
    """
    kwargs["export_csv"] = False

    r = grade_notebooks([grading_item], **kwargs)

    return r[0] if len(r) > 0 else None
