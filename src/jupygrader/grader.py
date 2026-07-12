from typing import TYPE_CHECKING, List, Optional, Union

from .grading.batch_grading_manager import BatchGradingManager
from .models.ai_models import AIGradingMode
from .models.config import BatchGradingConfig, FileDict, FilePath, GradingItem
from .models.results import GradedResult

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
    custom_prompt: Optional[str] = None,
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
        execution_timeout: Maximum time (in seconds) allowed for each cell's
            execution. Note this is a per-cell limit, not a limit on the total
            notebook runtime. Set to None to disable the timeout.
            Defaults to 600 seconds.
        ai_mode: Mode for AI grading. Defaults to AIGradingMode.OFF.
        openai_client: OpenAI client instance. Required when ai_mode is not OFF.
        openai_model: Model name for OpenAI API. Required when ai_mode is not OFF.
        custom_prompt: Optional additional instructions for the AI grading model.
            Only used when ai_mode is not OFF.

    Returns:
        List of GradedResult objects containing detailed results for each notebook.

    Raises:
        TypeError: If an element in grading_items has an unsupported type.
        ValueError: If a required path doesn't exist, has invalid configuration,
            or if ai_mode is not OFF but openai_model or openai_client is
            not specified.

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
    if ai_mode != AIGradingMode.OFF:
        if openai_model is None:
            raise ValueError(
                f"openai_model must be specified when using an AI grading mode (ai_mode={ai_mode!r}). "
                "Please provide a model name (e.g., 'gpt-4o', 'gpt-4o-mini')."
            )
        if openai_client is None:
            raise ValueError(
                f"openai_client must be provided when using an AI grading mode (ai_mode={ai_mode!r}). "
                "Without a client, AI grading would be silently skipped and "
                "notebooks could receive zero scores."
            )

    batch_config = BatchGradingConfig(
        base_files=base_files,
        verbose=verbose,
        export_csv=export_csv,
        csv_output_path=csv_output_path,
        regrade_existing=regrade_existing,
        execution_timeout=execution_timeout,
        ai_mode=ai_mode,
        openai_model=openai_model,
        custom_prompt=custom_prompt,
    )

    manager = BatchGradingManager(
        grading_items=grading_items,
        batch_config=batch_config,
        openai_client=openai_client,
    )

    return manager.grade()
