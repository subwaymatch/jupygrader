from dataclasses import dataclass
from typing import TypedDict, Union, List, Optional
from pathlib import Path

@dataclass
class GradingItemConfig:
    notebook_path: Union[str, Path]
    output_path: Optional[Union[str, Path]] = None
    copy_files: Optional[Union[str, Path, List[Union[str, Path]]]] = None