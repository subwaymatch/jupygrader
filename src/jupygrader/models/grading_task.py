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
from ..notebook_operations import (
    preprocess_test_case_cells,
    get_test_cases_hash,
    add_grader_scripts,
    remove_grader_scripts,
    add_graded_result_to_notebook,
    extract_user_code_from_notebook,
    save_graded_notebook_to_html,
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
import copy
import uuid
import platform


class GradingTask:
    def __init__(self, item: GradingItem, batch_config: BatchGradingConfig):
        self.item = item

        self.notebook_path = None
        self.output_path = None

        self.validate_paths()

        self.batch_config = batch_config
        self.verbose = batch_config.verbose
        self.copy_files = item.copy_files
        self.base_files = batch_config.base_files
        self.temp_workdir_path = None
        self.temp_notebook_path = None
        self.nb: NotebookNode = None
        self.graded_result: GradedResult = None
        self.grading_start_time = time.time()

    def validate_paths(self) -> None:
        self.notebook_path = Path(self.item.notebook_path).resolve()
        if not self.notebook_path.exists():
            raise FileNotFoundError(f"Notebook file not found: {self.notebook_path}")

        if self.item.output_path is None:
            self.output_path = self.notebook_path.parent
        else:
            self.output_path = Path(self.item.output_path).resolve()

        if not self.output_path.exists():
            self.output_path.mkdir(parents=True, exist_ok=True)
        elif not self.output_path.is_dir():
            raise NotADirectoryError(
                f"Output path is not a directory: {self.output_path}"
            )

    def copy_required_files(self) -> None:
        """Copy notebook and any additional required files to the temporary directory."""
        filename = self.notebook_path.name
        temp_notebook_path = self.temp_workdir_path / filename

        # Copy the notebook itself
        shutil.copy2(self.notebook_path, temp_notebook_path)

        def is_url(path: Union[str, Path]) -> bool:
            """Check if the path starts with http or https."""
            return str(path).lower().startswith(("http://", "https://"))

        def process_files(
            files: Optional[Union[FilePath, List[FilePath], FileDict]],
            label: str = "files",
        ) -> None:
            if not files:
                return

            copy_file_items: List[CopyFileItem] = []

            files = [files] if isinstance(files, (str, Path)) else files

            if isinstance(files, list):
                for src in files:
                    resolved_src = Path(src).resolve()

                    try:
                        relative_path = resolved_src.relative_to(
                            self.notebook_path.parent
                        )
                    except ValueError:
                        relative_path = Path(resolved_src.name)

                    resolved_dest = self.temp_workdir_path / relative_path
                    resolved_dest.parent.mkdir(parents=True, exist_ok=True)

                    copy_file_items.append(
                        CopyFileItem(
                            src=resolved_src,
                            dest=resolved_dest,
                            is_url=False,
                        )
                    )

            elif isinstance(files, dict):
                for src, dest in files.items():
                    resolved_dest = self.temp_workdir_path / dest
                    resolved_dest.parent.mkdir(parents=True, exist_ok=True)

                    if is_url(src):
                        copy_file_items.append(
                            CopyFileItem(
                                src=src,
                                dest=resolved_dest,
                                is_url=True,
                            )
                        )

                    else:
                        resolved_src = Path(src).resolve()

                        copy_file_items.append(
                            CopyFileItem(
                                src=resolved_src, dest=resolved_dest, is_url=False
                            )
                        )

            else:
                raise ValueError(f"Invalid type for {label}: {type(files)}")

            for copy_item in copy_file_items:
                if self.verbose:
                    print(f"Copying {label}: {copy_item.src} → {copy_item.dest}")

                if copy_item.is_url:
                    download_file(str(copy_item.src), copy_item.dest)
                elif copy_item.src.exists():
                    if copy_item.src.is_file():
                        shutil.copy2(copy_item.src, copy_item.dest)
                    elif copy_item.src.is_dir():
                        shutil.copytree(
                            copy_item.src, copy_item.dest, dirs_exist_ok=True
                        )
                else:
                    print(
                        f"Warning: {label} source not found, skipping copy: {copy_item.src}"
                    )

        # First, copy base_files
        process_files(self.base_files, label="base_file")

        # Then, copy copy_files
        process_files(self.copy_files, label="copy_file")

    @contextlib.contextmanager
    def use_temporary_grading_environment(
        self,
    ) -> Iterator[None]:
        """Context manager for setting up and cleaning up the grading environment."""
        filename = self.notebook_path.name

        # Create a temporary random directory for grading
        self.temp_workdir_path = Path(tempfile.gettempdir()) / (
            "jupygrader_" + str(uuid.uuid4())[:8]
        )
        self.temp_workdir_path.mkdir(parents=True, exist_ok=False)
        self.temp_notebook_path = self.temp_workdir_path / filename

        original_cwd = os.getcwd()

        try:
            # Copy notebook and other files, including base_files
            self.copy_required_files()

            # Change the current working directory to the temporary directory
            os.chdir(self.temp_workdir_path)

            yield

        except Exception as e:
            print(f"[Error in use_temporary_grading_environment()]: {e}")

        finally:
            # Change back to the original working directory
            os.chdir(original_cwd)

            # Clean up the temporary working directory
            if self.temp_workdir_path.exists() and self.temp_workdir_path.is_dir():
                shutil.rmtree(self.temp_workdir_path, ignore_errors=True)

    def prepare_and_execute_notebook(self) -> None:
        self.nb = nbformat.read(self.temp_notebook_path, as_version=4)
        preprocess_test_case_cells(self.nb)
        add_grader_scripts(self.nb)

        client = NotebookClient(
            self.nb, timeout=600, kernel_name="python3", allow_errors=True
        )
        client.execute()

    def process_grading_results(self) -> None:
        results_json_path = Path(GRADED_RESULT_JSON_FILENAME)

        if not results_json_path.exists():
            raise FileNotFoundError(
                f"Graded results JSON file not found: {results_json_path}"
            )

        with open(results_json_path, "r", encoding="utf-8") as f:
            graded_result_data = json.load(f)

        self.graded_result = GradedResult.from_dict(graded_result_data)

        self.graded_result.filename = self.notebook_path.name
        self.graded_result.test_cases_hash = get_test_cases_hash(self.nb)

        with open(self.temp_notebook_path, "rb") as f:
            self.graded_result.submission_notebook_hash = hashlib.md5(
                f.read()
            ).hexdigest()

        self.graded_result.grader_python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.graded_result.grader_platform = platform.platform()
        self.graded_result.jupygrader_version = jupygrader_version

        item_grading_end_time = time.time()

        self.graded_result.grading_finished_at = datetime.fromtimestamp(
            item_grading_end_time
        ).strftime("%Y-%m-%d %I:%M %p %Z")
        self.graded_result.grading_duration_in_seconds = round(
            item_grading_end_time - self.grading_start_time, 2
        )

    def generate_output_artifacts(
        self,
    ) -> None:
        filename_base = self.notebook_path.stem  # Name without extension

        """Cleans the notebook and saves all output files."""
        # --- Save Graded Notebook (.ipynb) ---
        graded_notebook_filename = f"{filename_base}-graded.ipynb"
        graded_notebook_path = self.output_path / graded_notebook_filename
        with open(graded_notebook_path, mode="w", encoding="utf-8") as f:
            nbformat.write(self.nb, f)

        # Clean up the notebook by removing grader scripts
        remove_grader_scripts(self.nb)
        # Add the graded result summary to the notebook metadata
        add_graded_result_to_notebook(self.nb, self.graded_result)

        # --- Extract and Save User Code (.py) ---
        extracted_user_code = extract_user_code_from_notebook(self.nb)
        extracted_code_filename = f"{filename_base}_user_code.py"
        extracted_code_path = self.output_path / extracted_code_filename
        with open(extracted_code_path, "w", encoding="utf-8") as f:
            f.write(extracted_user_code)
        self.graded_result.extracted_user_code_file = str(extracted_code_path.resolve())

        # --- Save Graded HTML Report ---
        graded_html_filename = f"{filename_base}-graded.html"
        graded_html_path = self.output_path / graded_html_filename
        save_graded_notebook_to_html(
            self.nb,
            html_title=f"{filename_base}.ipynb",  # Use original-like name for title
            output_path=graded_html_path,
            graded_result=self.graded_result,
        )
        self.graded_result.graded_html_file = str(graded_html_path.resolve())

        # --- Save Text Summary ---
        text_summary_filename = f"{filename_base}-graded-result-summary.txt"
        text_summary_file_path = self.output_path / text_summary_filename
        with open(text_summary_file_path, "w", encoding="utf-8") as f:
            f.write(self.graded_result.text_summary)
        self.graded_result.text_summary_file = str(text_summary_file_path.resolve())

        # --- Save Final Graded Result JSON ---
        graded_result_json_filename = f"{filename_base}-graded-result.json"
        graded_result_json_path = self.output_path / graded_result_json_filename
        with open(graded_result_json_path, "w", encoding="utf-8") as f:
            json.dump(self.graded_result.to_dict(), f, indent=2)

    def grade(self) -> GradedResult:
        """Grade a single notebook based on a GradingItem. (Orchestrator)"""
        original_notebook_path = Path(self.item.notebook_path).resolve()

        with self.use_temporary_grading_environment():
            if self.verbose:
                print(
                    f"Grading {original_notebook_path.name} in {self.temp_notebook_path.parent}"
                )

            # 1. Prepare and execute the notebook (read, preprocess, inject scripts)
            self.prepare_and_execute_notebook()

            # 2. Process results (read JSON, parse, add metadata)
            self.process_grading_results()

            # 3. Generate output files (cleaned .ipynb, .html, .py, .txt, final .json)
            self.generate_output_artifacts()

            if self.verbose:
                print(f"Finished grading {self.notebook_path.name}")

        return self.graded_result
