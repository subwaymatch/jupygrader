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
    kwargs["export_csv"] = False

    r = grade_notebooks([grading_item], **kwargs)

    return r[0] if len(r) > 0 else None
