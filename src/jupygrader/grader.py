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
) -> List[GradedResult]:
    batch_config = BatchGradingConfig(
        base_files=base_files,
        verbose=verbose,
        export_csv=export_csv,
        csv_output_path=csv_output_path,
    )

    manager = BatchGradingManager(
        grading_items=grading_items, batch_config=batch_config
    )

    return manager.grade()


def grade_single_notebook(
    grading_item: Union[FilePath, GradingItem, dict],
    *,
    verbose: bool = True,
) -> Optional[GradedResult]:
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
