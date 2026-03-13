from typing import TYPE_CHECKING, List, Optional, Union

from .models.batch_grading_manager import BatchGradingManager
from .models.grading_dataclasses import (
    AIGradingMode,
    BatchGradingConfig,
    FileDict,
    FilePath,
    GradedResult,
    GradingItem,
)

if TYPE_CHECKING:
    import openai


def grade_notebooks(
    grading_items: List[Union[FilePath, GradingItem, dict]],
    *,
    base_files: Optional[Union[FilePath, List[FilePath], FileDict]] = None,
    verbose: bool = True,
    export_csv: bool = True,
    csv_output_path: Optional[FilePath] = None,
    regrade_existing: bool = False,
    execution_timeout: Optional[int] = 600,
    ai_mode: AIGradingMode = AIGradingMode.OFF,
    openai_client: Optional["openai.OpenAI"] = None,
    openai_model: Optional[str] = None,
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
        execution_timeout: Maximum time (in seconds) allowed for notebook execution.
            Set to None to disable the timeout. Defaults to 600 seconds.
        ai_mode: Mode for AI grading. Defaults to AIGradingMode.OFF.
        openai_client: OpenAI client instance (optional).
        openai_model: Model name for OpenAI API (optional).

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
        execution_timeout=execution_timeout,
        ai_mode=ai_mode,
        openai_model=openai_model,
    )

    manager = BatchGradingManager(
        grading_items=grading_items,
        batch_config=batch_config,
        openai_client=openai_client,
    )

    return manager.grade()
