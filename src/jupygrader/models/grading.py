from ..types import Path, FilePath, FileDict, GradingItem
from typing import Optional, Tuple


class GradingTask:
    def __init__(self, item: GradingItem):
        self.item = item
        self.output

        self.notebook_path, self.output_path = self._validate_paths()

    def _validate_paths(self) -> None:
        """Validate notebook and output paths."""
        self.notebook_path = Path(self.item.notebook_path).resolve()
        if not self.notebook_path.exists():
            raise FileNotFoundError(f"Notebook file not found: {self.notebook_path}")

        if self.item.output_path_str is None:
            self.output_path = self.notebook_path.parent
        else:
            self.output_path = Path(self.item.output_path_str).resolve()

        if not self.output_path.exists():
            self.output_path.mkdir(parents=True, exist_ok=True)
        elif not self.output_path.is_dir():
            raise NotADirectoryError(
                f"Output path is not a directory: {self.output_path}"
            )
