from .grading_dataclasses import (
    FilePath,
    FileDict,
    GradingItem,
    CopyFileItem,
    BatchGradingConfig,
    GradedResult,
)
from ..__about__ import __version__ as jupygrader_version
from ..constants import GRADED_RESULT_JSON_FILENAME
from .grading_task import GradingTask
from ..notebook_operations import (
    get_test_cases_hash,
    extract_user_code_from_notebook,
)
from ..utils import download_file
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Union, Dict, Any, Tuple, TypedDict, Iterator
from pathlib import Path
import nbformat
from nbformat import NotebookNode
from nbclient import NotebookClient
import shutil
import json
import os
import tempfile
import pandas as pd
import contextlib
import hashlib
import sys
from datetime import datetime
import time
import uuid
import platform


class BatchGradingManager:
    def __init__(
        self,
        grading_items: Union[
            FilePath, GradingItem, List[Union[FilePath, GradingItem, dict]]
        ],
        batch_config: BatchGradingConfig,
    ):
        self.verbose = batch_config.verbose
        self.batch_config: BatchGradingConfig = batch_config
        self.grading_items: List[GradingItem] = self.normalize_grading_items(
            grading_items
        )
        self.graded_results: List[GradedResult] = []

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

    def export_results_to_csv(
        self,
    ) -> None:
        """Exports the list of GradedResult objects to a CSV file."""
        if not self.graded_results:
            if self.verbose:
                print("No results to export to CSV.")
            return

        # Create timestamp for CSV filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"graded_results_{timestamp}.csv"

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

        # Extract main attributes from GradedResult objects
        data = []
        for result in self.graded_results:
            # Create a dictionary with selected attributes
            result_dict = {
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
            }
            data.append(result_dict)

        # Create DataFrame and export to CSV
        try:
            df = pd.DataFrame(data)
            # Ensure the directory exists
            csv_resolved_path.parent.mkdir(parents=True, exist_ok=True)
            # Export to CSV
            df.to_csv(csv_resolved_path, index=False, encoding="utf-8")
            if self.verbose:
                print(f"Results exported to CSV: {csv_resolved_path}")
        except Exception as e:
            print(f"Error exporting results to CSV: {e}")

    def grade(
        self,
    ) -> List[GradedResult]:
        num_items = len(self.grading_items)
        num_failed_grading = 0

        if self.verbose:
            print(
                f"Starting grading of {num_items} notebook(s) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

        start_time = time.time()

        for idx, item in enumerate(self.grading_items, start=1):
            try:
                notebook_path = item.notebook_path
                notebook_name = Path(notebook_path).name

                if self.verbose:
                    print("-" * 70)
                    print(
                        f"[{idx}/{num_items}] Grading: {notebook_name} ... ",
                    )

                batch_config = BatchGradingConfig(
                    base_files=self.batch_config.base_files,
                    verbose=self.verbose,
                    export_csv=self.batch_config.export_csv,
                    csv_output_path=self.batch_config.csv_output_path,
                )

                grading_task = GradingTask(item, batch_config)

                graded_result = grading_task.grade()

                # Add to results list
                self.graded_results.append(graded_result)

                if self.verbose:
                    score = graded_result.learner_autograded_score
                    max_score = graded_result.max_autograded_score
                    print(f"Done. Score: {score}/{max_score}")

            except Exception as e:
                num_failed_grading += 1

                if self.verbose:
                    print(f"Error: {str(e)}")
                    print(f"Failed to grade notebook: {item.notebook_path}")

            finally:
                if self.verbose:
                    print(f"Progress: {round(idx / num_items * 100, 1)}%")

        elapsed_time = time.time() - start_time

        if self.verbose:
            print("-" * 70)
            print(
                f"Completed grading {num_items} notebook(s) in {elapsed_time:.2f} seconds"
            )

            print(f"Successfully graded: {num_items - num_failed_grading}/{num_items}")
            if num_failed_grading > 0:
                print(f"Failed to grade: {num_failed_grading}/{num_items}")

        # Export results to CSV if requested
        if self.batch_config.export_csv:
            self.export_results_to_csv()

        return self.graded_results
