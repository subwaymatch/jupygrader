import contextlib
import copy
import time
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional, Union

import openai
import pandas as pd
import tempfile
from tqdm.auto import tqdm

from ..models.ai_models import AIGradingMode
from ..models.config import BatchGradingConfig, FileDict, FilePath, GradingItem
from ..models.results import GradedResult
from ..notebook_operations import is_notebook_graded
from ..utils import download_file, is_url
from .execution_grading_task import ExecutionGradingTask
from .full_ai_grading_task import FullAIGradingTask


class BatchGradingManager:
    def __init__(
        self,
        grading_items: Union[
            FilePath, GradingItem, List[Union[FilePath, GradingItem, dict]]
        ],
        batch_config: BatchGradingConfig,
        openai_client: Optional[openai.OpenAI] = None,
    ):
        self.verbose = batch_config.verbose
        self.batch_config: BatchGradingConfig = copy.deepcopy(batch_config)
        self.grading_items: List[GradingItem] = self.normalize_grading_items(
            grading_items
        )
        self.graded_results: List[GradedResult] = []
        self._csv_rows: List[dict] = []
        self.openai_client: Optional[openai.OpenAI] = openai_client

    @staticmethod
    def _initialize_csv_row() -> dict:
        return {
            "filename": None,
            "learner_autograded_score": None,
            "max_autograded_score": None,
            "max_manually_graded_score": None,
            "max_total_score": None,
            "num_autograded_cases": None,
            "num_passed_cases": None,
            "num_failed_cases": None,
            "num_manually_graded_cases": None,
            "num_total_test_cases": None,
            "grading_finished_at": None,
            "grading_duration_in_seconds": None,
            "submission_notebook_hash": None,
            "test_cases_hash": None,
            "grader_python_version": None,
            "grader_platform": None,
            "text_summary": None,
            "is_success": None,
        }

    def _record_success(self, result: GradedResult) -> None:
        row = self._initialize_csv_row()
        row.update(
            {
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
                "is_success": True,
            }
        )
        self._csv_rows.append(row)

    def _record_failure(self, notebook_path: FilePath, error_message: str) -> None:
        row = self._initialize_csv_row()
        try:
            filename = Path(notebook_path).name
        except Exception:
            filename = str(notebook_path)

        row.update(
            {
                "filename": filename,
                "text_summary": error_message,
                "is_success": False,
            }
        )
        self._csv_rows.append(row)

    @staticmethod
    def normalize_grading_items(
        items: Union[FilePath, GradingItem, List[Union[FilePath, GradingItem, dict]]],
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

    @contextlib.contextmanager
    def cache_remote_base_files(
        self,
    ) -> Iterator[None]:
        cached_files: List[Path] = []

        try:
            if isinstance(self.batch_config.base_files, dict):
                for src in list(self.batch_config.base_files.keys()):
                    if is_url(src):
                        temp_path = Path(tempfile.NamedTemporaryFile(delete=False).name)

                        print(f"Caching remote base file: {src}")
                        download_file(src, temp_path)
                        cached_files.append(temp_path)

                        # Replace the original URL with the local cached path
                        self.batch_config.base_files[temp_path] = (
                            self.batch_config.base_files.pop(src)
                        )

            yield

        except Exception as e:
            print(f"[Error in cache_remote_base_files()]: {e}")

        finally:
            for file_path in cached_files:
                file_path.unlink(missing_ok=True)

    def export_results_to_csv(
        self,
    ) -> None:
        """Exports the list of GradedResult objects to a CSV file."""
        if not self._csv_rows:
            if self.verbose:
                print("No results to export to CSV.")
            return

        # Create datetime for CSV filename
        formatted_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"graded_results_{formatted_datetime}.csv"

        # Determine the output path
        if self.batch_config.csv_output_path is None:
            csv_resolved_path = Path(
                csv_filename
            ).resolve()  # Save in the current directory by default
        else:
            csv_resolved_path = Path(self.batch_config.csv_output_path).resolve()
            csv_resolved_path = (
                csv_resolved_path / csv_filename
                if csv_resolved_path.is_dir()
                else csv_resolved_path  # Assume full path if not a dir
            )

        data = []
        for row in self._csv_rows:
            data.append(row)

        try:
            df = pd.DataFrame(data)
            csv_resolved_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(csv_resolved_path, index=False, encoding="utf-8")
            if self.verbose:
                print(f"Results exported to CSV: {csv_resolved_path}")
        except Exception as e:
            print(f"Error exporting results to CSV: {e}")

    def grade(
        self,
    ) -> List[GradedResult]:
        num_items = len(self.grading_items)
        num_skipped_items = 0
        num_already_graded_skipped = 0
        num_failed_items = 0

        start_time = time.time()

        with self.cache_remote_base_files():
            loop = enumerate(
                tqdm(
                    self.grading_items,
                    desc=f"Grading {num_items} notebook{'s' if num_items > 1 else ''}",
                    unit="notebook",
                ),
                start=1,
            )
            for idx, item in loop:
                try:
                    notebook_path = item.notebook_path

                    notebook_name = Path(notebook_path).name

                    if self.verbose:
                        print(
                            f"[{idx}/{num_items}] Grading: {notebook_name}",
                        )

                    if self.batch_config.ai_mode == AIGradingMode.FULL:
                        grading_task = FullAIGradingTask(
                            item, self.batch_config, self.openai_client
                        )
                    else:
                        grading_task = ExecutionGradingTask(
                            item, self.batch_config, self.openai_client
                        )

                    if (
                        grading_task.get_existing_graded_result() is not None
                        and not self.batch_config.regrade_existing
                    ):
                        if self.verbose:
                            print(
                                f"Using previously graded results for: {notebook_name}"
                            )

                        num_skipped_items += 1
                        graded_result = grading_task.get_existing_graded_result()

                    elif is_notebook_graded(item.notebook_path):
                        if self.verbose:
                            print(f"Skipping already graded notebook: {notebook_path}")
                        num_already_graded_skipped += 1
                        continue

                    else:
                        graded_result = grading_task.grade()

                    if graded_result is not None:
                        self.graded_results.append(graded_result)
                        self._record_success(graded_result)
                    else:
                        num_failed_items += 1
                        error_message = (
                            grading_task.error_message
                            if grading_task.error_message
                            else "Unknown grading error"
                        )
                        self._record_failure(
                            item.notebook_path,
                            error_message,
                        )

                except Exception as e:
                    num_failed_items += 1

                    if self.verbose:
                        print(f"Error: {str(e)}")
                        print(f"Failed to grade notebook: {item.notebook_path}")

                    self._record_failure(item.notebook_path, str(e))

        elapsed_time = time.time() - start_time

        num_graded_items = num_items - num_already_graded_skipped

        if self.verbose:
            print("-" * 70)
            print(
                f"Completed grading {num_graded_items} notebook(s) in {elapsed_time:.2f} seconds"
            )

            print(f"Successfully graded: {num_graded_items - num_failed_items}/{num_graded_items}")
            if num_already_graded_skipped > 0:
                print(f"Skipped {num_already_graded_skipped} notebook(s) that was already graded")
            if num_skipped_items > 0:
                print(f"Skipped: {num_skipped_items}/{num_graded_items} (using cached results)")
            if num_failed_items > 0:
                print(f"Failed to grade: {num_failed_items}/{num_graded_items}")

        if self.batch_config.export_csv:
            self.export_results_to_csv()

        return self.graded_results
