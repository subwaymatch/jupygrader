import contextlib
import hashlib
import html
import json
import os
import platform
import re
import shutil
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from nbformat import NotebookNode
from nbformat.v4 import new_markdown_cell
from tzlocal import get_localzone_name

from ..__about__ import __version__ as jupygrader_version
from ..constants import GRADED_RESULT_ELEMENT_ID
from ..html_export import save_graded_notebook_to_html
from ..models.config import BatchGradingConfig, CopyFileItem, FileDict, FilePath, GradingItem
from ..models.results import GradedResult
from ..notebook_operations import extract_user_code_from_notebook
from ..utils import download_file, is_url


def sanitize_for_markdown_table(value: object) -> str:
    """Escape untrusted text before embedding it in a Markdown/HTML report cell.

    Test case names, error messages, and AI feedback can contain arbitrary
    student- or model-controlled text. Notebook Markdown cells render raw HTML,
    so unescaped content would allow script injection in the graded HTML report.
    """
    if value is None:
        return ""
    text = html.escape(str(value))
    text = text.replace("|", "\\|")
    text = text.replace("\r\n", "\n").replace("\n", "<br>")
    return text


class BaseGradingTask(ABC):
    def __init__(
        self,
        item: GradingItem,
        batch_config: BatchGradingConfig,
    ):
        self.item = item

        self.notebook_path, self.output_path = self.validate_paths(
            item.notebook_path, item.output_path
        )

        with open(self.notebook_path, "rb") as f:
            self.submission_notebook_hash = hashlib.md5(f.read()).hexdigest()

        self.filename_base = self.notebook_path.stem
        self.batch_config = batch_config
        self.verbose = batch_config.verbose
        self.copy_files = item.copy_files
        self.base_files = batch_config.base_files
        self.temp_workdir_path = None
        self.temp_notebook_path = None
        self.nb: NotebookNode = None
        self.graded_result: GradedResult = None
        self.grading_start_time = time.time()
        self.execution_timeout = batch_config.execution_timeout
        self.error_message: Optional[str] = None

    def get_existing_graded_result(self) -> Optional[GradedResult]:
        graded_result_json_filename = f"{self.filename_base}-graded-result.json"
        graded_result_json_path = self.output_path / graded_result_json_filename

        if not graded_result_json_path.exists():
            return None

        with open(graded_result_json_path, "r", encoding="utf-8") as f:
            graded_result_data = json.load(f)

        graded_result = GradedResult.from_dict(graded_result_data)

        if (
            graded_result
            and graded_result.submission_notebook_hash == self.submission_notebook_hash
            and graded_result.jupygrader_version == jupygrader_version
        ):
            return graded_result

        return None

    def add_graded_result_to_notebook(self) -> None:
        graded_result = self.graded_result

        gr_cells = []

        # add result summary
        gr_cells.append(
            new_markdown_cell(
                '<div style="text-align: center;"><img src="https://github.com/subwaymatch/jupygrader/blob/main/docs/images/logo_jupygrader_with_text_240.png?raw=true" alt="Jupygrader Logo" width="120"/></div>'
            )
        )

        learner_score_in_percentage = (
            f" ({round(graded_result.learner_autograded_score / graded_result.max_autograded_score * 100, 2)}%)"
            if graded_result.max_autograded_score != 0
            else ""
        )

        gr_dict_for_df = {
            "**Autograded Score**": f"**{graded_result.learner_autograded_score} out of {graded_result.max_autograded_score}** {learner_score_in_percentage}",
            "Autograded Test Cases": f"Passed {graded_result.num_passed_cases} out of {graded_result.num_autograded_cases} cases",
            "Pending Test Cases": f"⌛ {graded_result.num_manually_graded_cases} item{'s' if graded_result.num_manually_graded_cases > 1 else ''} worth a total of {graded_result.max_manually_graded_score} point{'s' if graded_result.max_manually_graded_score > 1 else ''} require manual grading",
            "Total Available Points": graded_result.max_total_score,
            "Filename": sanitize_for_markdown_table(graded_result.filename),
            "Autograder Finished At": graded_result.grading_finished_at,
            "Autograder Duration": f"{graded_result.grading_duration_in_seconds} second{'' if graded_result.grading_duration_in_seconds == 0 else 's'}",
            "Test Cases Checksum": graded_result.test_cases_hash,
            "Submission File Checksum": graded_result.submission_notebook_hash,
            "Autograder Python Version": f"Python {graded_result.grader_python_version}",
            "Autograder Platform": graded_result.grader_platform,
            "Jupygrader Version": graded_result.jupygrader_version,
        }

        if graded_result.num_manually_graded_cases == 0:
            del gr_dict_for_df["Pending Test Cases"]

        df_metadata = pd.DataFrame(
            {"item": gr_dict_for_df.keys(), "description": gr_dict_for_df.values()}
        )
        gr_cells.append(new_markdown_cell(df_metadata.to_markdown(index=False)))

        if (
            graded_result.num_autograded_cases + graded_result.num_manually_graded_cases
            == 0
        ):
            gr_cells.append(
                new_markdown_cell(
                    "Jupygrader did not detect any test cases in this notebook."
                )
            )
        else:
            gr_cells.append(
                new_markdown_cell(
                    f'<h2 id="{GRADED_RESULT_ELEMENT_ID}">Test Case Results</h2>'
                )
            )

            tc_counts = {}
            test_case_links = []

            for o in graded_result.test_case_results:
                tc_name_cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", o.test_case_name)
                if tc_name_cleaned not in tc_counts:
                    tc_counts[tc_name_cleaned] = 0
                tc_counts[tc_name_cleaned] += 1
                anchor_id = f"{tc_name_cleaned}_id{tc_counts[tc_name_cleaned]}"
                test_case_link = f"<a href='#{anchor_id}'>{html.escape(o.test_case_name)}</a>"

                test_case_links.append(test_case_link)

            df_r = pd.DataFrame(
                [result.__dict__ for result in graded_result.test_case_results]
            )

            # replace test_case_name column with linked texts
            df_r["test_case_name"] = test_case_links

            # escape untrusted text so it cannot inject HTML into the report
            for untrusted_column in ("error_message", "ai_feedback"):
                if untrusted_column in df_r.columns:
                    df_r[untrusted_column] = df_r[untrusted_column].apply(
                        sanitize_for_markdown_table
                    )

            df_r.loc[~df_r["is_graded"], "points"] = np.nan
            df_r["available_points"] = df_r["available_points"].astype(str)

            # inner function to generate a human-readable result
            def get_human_readable_result(row):
                if not row["is_graded"]:
                    return "⌛ Requires manual grading"
                else:
                    return "✔️ Pass" if row["did_pass"] else "❌ Fail"

            df_r["did_pass"] = df_r.apply(get_human_readable_result, axis=1)
            df_r.rename(
                columns={
                    "available_points": "max_score",
                    "pass": "result",
                    "points": "learner_score",
                },
                inplace=True,
            )
            df_r["learner_score"] = df_r["learner_score"].apply(
                lambda x: (
                    "Pending"
                    if pd.isna(x)
                    else str(int(x))
                    if float(x).is_integer()
                    else str(x)
                )
            )

            df_r.drop(columns=["grade_manually", "is_graded"], inplace=True)

            gr_cells.append(new_markdown_cell(df_r.to_markdown()))
            gr_cells.append(new_markdown_cell("\n---\n"))

        self.nb.cells = gr_cells + self.nb.cells

    @staticmethod
    def validate_paths(notebook_path, output_path) -> Tuple[Path, Path]:
        resolved_notebook_path = Path(notebook_path).resolve()
        if not resolved_notebook_path.exists():
            raise FileNotFoundError(
                f"Notebook file not found: {resolved_notebook_path}"
            )

        if output_path is None:
            resolved_output_path = resolved_notebook_path.parent
        else:
            resolved_output_path = Path(output_path).resolve()

        if not resolved_output_path.exists():
            resolved_output_path.mkdir(parents=True, exist_ok=True)
        elif not resolved_output_path.is_dir():
            raise NotADirectoryError(
                f"Output path is not a directory: {resolved_output_path}"
            )

        return resolved_notebook_path, resolved_output_path

    def _resolve_dest_within_workdir(self, dest: FilePath, label: str) -> Path:
        """Resolve a destination path and ensure it stays inside the grading workdir.

        Destination paths may come from user-supplied configuration; without this
        check, an absolute path or a ``..`` component could write outside the
        temporary grading directory.
        """
        workdir = self.temp_workdir_path.resolve()
        resolved_dest = (workdir / dest).resolve()

        if resolved_dest != workdir and not resolved_dest.is_relative_to(workdir):
            raise ValueError(
                f"Invalid {label} destination outside the grading directory: {dest}"
            )

        resolved_dest.parent.mkdir(parents=True, exist_ok=True)
        return resolved_dest

    def copy_required_files(self) -> None:
        """Copy notebook and any additional required files to the temporary directory."""
        filename = self.notebook_path.name
        temp_notebook_path = self.temp_workdir_path / filename

        # Copy the notebook itself
        shutil.copy2(self.notebook_path, temp_notebook_path)

        def process_files(
            files: Optional[Union[FilePath, List[FilePath], FileDict]],
            label: str = "files",
        ) -> None:
            if not files:
                return

            copy_file_items: List[CopyFileItem] = []

            if isinstance(files, (str, Path)):
                files = [files]

            if isinstance(files, list):
                for src in files:
                    if is_url(src):
                        # URLs in list form are downloaded into the workdir root,
                        # named after the last path segment of the URL
                        url_filename = (
                            os.path.basename(urlsplit(str(src)).path)
                            or "downloaded_file"
                        )
                        resolved_dest = self._resolve_dest_within_workdir(
                            url_filename, label
                        )
                        copy_file_items.append(
                            CopyFileItem(src=src, dest=resolved_dest, is_url=True)
                        )
                        continue

                    resolved_src = Path(src).resolve()

                    try:
                        relative_path = resolved_src.relative_to(
                            self.notebook_path.parent
                        )
                    except ValueError:
                        relative_path = Path(resolved_src.name)

                    resolved_dest = self._resolve_dest_within_workdir(
                        relative_path, label
                    )

                    copy_file_items.append(
                        CopyFileItem(
                            src=resolved_src,
                            dest=resolved_dest,
                            is_url=False,
                        )
                    )

            elif isinstance(files, dict):
                for src, dest in files.items():
                    resolved_dest = self._resolve_dest_within_workdir(dest, label)

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
                if copy_item.is_url:
                    if not download_file(str(copy_item.src), copy_item.dest):
                        print(
                            f"Warning: failed to download {label} from {copy_item.src}, skipping copy"
                        )
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
        """Context manager for setting up and cleaning up the grading environment.

        Exceptions raised inside the managed block are NOT suppressed here — they
        must propagate to the caller so that grading failures are reported with
        their actual error message instead of being silently swallowed.
        """
        filename = self.notebook_path.name

        # Create a temporary random directory for grading (mkdtemp is race-free)
        self.temp_workdir_path = Path(tempfile.mkdtemp(prefix="jupygrader_"))
        self.temp_notebook_path = self.temp_workdir_path / filename

        original_cwd = os.getcwd()

        try:
            # Copy notebook and other files, including base_files
            self.copy_required_files()

            # Change the current working directory to the temporary directory
            os.chdir(self.temp_workdir_path)

            yield

        finally:
            # Change back to the original working directory
            os.chdir(original_cwd)

            # Clean up the temporary working directory
            shutil.rmtree(self.temp_workdir_path, ignore_errors=True)

    def _populate_graded_result_metadata(self) -> None:
        """Fill in system/environment metadata on self.graded_result."""
        self.graded_result.filename = self.notebook_path.name
        self.graded_result.submission_notebook_hash = self.submission_notebook_hash
        self.graded_result.grader_python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.graded_result.grader_platform = platform.platform()
        self.graded_result.jupygrader_version = jupygrader_version

        item_grading_end_time = time.time()
        try:
            local_zone = ZoneInfo(get_localzone_name())
        except Exception:
            # Containers and minimal environments may not expose a local timezone
            local_zone = timezone.utc

        self.graded_result.grading_finished_at = datetime.fromtimestamp(
            item_grading_end_time, tz=local_zone
        ).strftime("%Y-%m-%d %I:%M %p %Z")
        self.graded_result.grading_duration_in_seconds = round(
            item_grading_end_time - self.grading_start_time, 2
        )

    def save_graded_notebook_to_html(self, html_title: str, html_path: str) -> None:
        save_graded_notebook_to_html(self.nb, self.graded_result, html_title, html_path)

    def generate_output_artifacts(self) -> None:
        """Cleans the notebook and saves all output files."""
        graded_notebook_filename = f"{self.filename_base}-graded.ipynb"
        graded_notebook_path = self.output_path / graded_notebook_filename

        # Add graded result metadata to notebook metadata
        self.nb.metadata["jupygrader"] = {
            "graded": True,
            "version": jupygrader_version,
            "grading_finished_at": self.graded_result.grading_finished_at,
            "grading_duration_in_seconds": self.graded_result.grading_duration_in_seconds,
            "learner_autograded_score": self.graded_result.learner_autograded_score,
            "max_autograded_score": self.graded_result.max_autograded_score,
            "max_manually_graded_score": self.graded_result.max_manually_graded_score,
            "max_total_score": self.graded_result.max_total_score,
            "num_autograded_cases": self.graded_result.num_autograded_cases,
            "num_passed_cases": self.graded_result.num_passed_cases,
            "num_failed_cases": self.graded_result.num_failed_cases,
            "num_manually_graded_cases": self.graded_result.num_manually_graded_cases,
            "num_total_test_cases": self.graded_result.num_total_test_cases,
            "submission_notebook_hash": self.graded_result.submission_notebook_hash,
            "test_cases_hash": self.graded_result.test_cases_hash,
            "grader_python_version": self.graded_result.grader_python_version,
            "grader_platform": self.graded_result.grader_platform,
            "test_case_results": [
                tc.__dict__ for tc in self.graded_result.test_case_results
            ],
        }

        import nbformat

        with open(graded_notebook_path, mode="w", encoding="utf-8") as f:
            nbformat.write(self.nb, f)

        # Clean up the notebook by removing grader scripts (subclass hook)
        self._pre_annotate_cleanup()
        # Add the graded result summary to the notebook
        self.add_graded_result_to_notebook()

        # Extract and Save User Code (.py)
        extracted_user_code = extract_user_code_from_notebook(self.nb)
        extracted_code_filename = f"{self.filename_base}_user_code.py"
        extracted_code_path = self.output_path / extracted_code_filename
        with open(extracted_code_path, "w", encoding="utf-8") as f:
            f.write(extracted_user_code)
        self.graded_result.extracted_user_code_file = str(extracted_code_path.resolve())

        # Save Graded HTML Report
        graded_html_filename = f"{self.filename_base}-graded.html"
        graded_html_path = self.output_path / graded_html_filename
        self.save_graded_notebook_to_html(
            html_title=f"{self.filename_base}", html_path=graded_html_path
        )
        self.graded_result.graded_html_file = str(graded_html_path.resolve())

        # Save Text Summary
        text_summary_filename = f"{self.filename_base}-graded-result-summary.txt"
        text_summary_file_path = self.output_path / text_summary_filename
        with open(text_summary_file_path, "w", encoding="utf-8") as f:
            f.write(self.graded_result.text_summary)
        self.graded_result.text_summary_file = str(text_summary_file_path.resolve())

        # Save Final Graded Result JSON
        graded_result_json_filename = f"{self.filename_base}-graded-result.json"
        graded_result_json_path = self.output_path / graded_result_json_filename
        self.graded_result.graded_result_json_file = str(
            graded_result_json_path.resolve()
        )
        with open(graded_result_json_path, "w", encoding="utf-8") as f:
            json.dump(self.graded_result.to_dict(), f, indent=2)

    def _pre_annotate_cleanup(self) -> None:
        """Hook called just before add_graded_result_to_notebook().

        Subclasses that inject cells into the notebook during execution
        (e.g. ExecutionGradingTask) should override this to remove those cells
        before the result summary is prepended.
        """

    def _recalculate_scores(self) -> None:
        """Recalculates overall scores based on potentially updated test case results."""
        self.graded_result.num_passed_cases = sum(
            1
            for tc in self.graded_result.test_case_results
            if tc.is_graded and tc.did_pass
        )
        self.graded_result.num_failed_cases = sum(
            1
            for tc in self.graded_result.test_case_results
            if tc.is_graded and tc.did_pass is False
        )
        self.graded_result.num_autograded_cases = sum(
            1 for tc in self.graded_result.test_case_results if tc.is_graded
        )
        self.graded_result.num_manually_graded_cases = sum(
            1 for tc in self.graded_result.test_case_results if not tc.is_graded
        )

        self.graded_result.learner_autograded_score = sum(
            tc.points for tc in self.graded_result.test_case_results if tc.is_graded
        )

        self.graded_result.max_autograded_score = sum(
            tc.available_points
            for tc in self.graded_result.test_case_results
            if tc.is_graded
        )
        self.graded_result.max_manually_graded_score = sum(
            tc.available_points
            for tc in self.graded_result.test_case_results
            if not tc.is_graded
        )
        self.graded_result.max_total_score = (
            self.graded_result.max_autograded_score
            + self.graded_result.max_manually_graded_score
        )

    @abstractmethod
    def grade(self) -> Optional[GradedResult]:
        """Execute the grading pipeline and return the result."""
