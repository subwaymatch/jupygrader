from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from .ai_models import AIGradingMode

FilePath = Union[str, Path]
FileDict = Dict[FilePath, FilePath]


@dataclass
class GradingItem:
    notebook_path: FilePath
    output_path: Optional[FilePath] = None
    copy_files: Optional[Union[FilePath, List[FilePath], FileDict]] = None


@dataclass
class BatchGradingConfig:
    grading_items: List[GradingItem] = None
    verbose: bool = False
    export_csv: bool = True
    base_files: Optional[Union[FilePath, List[FilePath], FileDict]] = None
    csv_output_path: Optional[str] = None
    regrade_existing: bool = False
    execution_timeout: Optional[int] = 600
    ai_mode: AIGradingMode = AIGradingMode.OFF
    openai_model: Optional[str] = None


@dataclass
class CopyFileItem:
    src: FilePath
    dest: FilePath
    is_url: bool = False
