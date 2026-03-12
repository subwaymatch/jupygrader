import contextlib
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import tempfile
import textwrap
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union
from zoneinfo import ZoneInfo

import nbformat
import numpy as np
import openai
import pandas as pd
from bs4 import BeautifulSoup
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from nbformat import NotebookNode
from nbformat.v4 import new_code_cell, new_markdown_cell
from tzlocal import get_localzone_name

from ..__about__ import __version__ as jupygrader_version
from ..constants import GRADED_RESULT_ELEMENT_ID, GRADED_RESULT_JSON_FILENAME
from ..notebook_operations import (
    comment_out_magic_commands,
    does_cell_contain_test_case,
    extract_test_case_metadata_from_code,
    extract_user_code_from_notebook,
    get_test_cases_hash,
    is_manually_graded_test_case,
)
from ..utils import download_file, get_jupyter_cell_script, is_url
from .grading_dataclasses import (
    AIGradingMode,
    AIParsedResult,
    BatchGradingConfig,
    CopyFileItem,
    FileDict,
    FilePath,
    GradedResult,
    GradingItem,
)


class GradingTask:
    def __init__(
        self,
        item: GradingItem,
        batch_config: BatchGradingConfig,
        openai_client: Optional[openai.OpenAI] = None,
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

        self.openai_client = openai_client

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
            "Filename": graded_result.filename,
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
                test_case_link = f"<a href='#{anchor_id}'>{o.test_case_name}</a>"

                test_case_links.append(test_case_link)

            df_r = pd.DataFrame(
                [result.__dict__ for result in graded_result.test_case_results]
            )

            # replace test_case_name column with linked texts
            df_r["test_case_name"] = test_case_links

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

    def convert_test_case_using_grader_template(self, cell: NotebookNode) -> None:
        """Convert a test case cell to use the grader template.

        Transforms a test case cell by wrapping it with the appropriate grader template
        based on whether it's manually graded or automatically graded.

        Args:
            cell: The notebook cell containing a test case

        Returns:
            Modified source code with the test case wrapped in a grader template
        """
        if not does_cell_contain_test_case(cell):
            # do nothing if not a test case cell
            return

        source = cell.source

        if is_manually_graded_test_case(cell):
            grader_template_code = get_jupyter_cell_script("grader_manual_template.py")
            source = cell.source
        else:
            grader_template_code = get_jupyter_cell_script("grader_template.py")
            source = textwrap.indent(cell.source, "    ")

        converted_source = grader_template_code.replace(
            "# TEST_CASE_REPLACE_HERE", source
        )

        cell.source = converted_source

    def preprocess_test_case_cells(self) -> None:
        for cell in self.nb.cells:
            if does_cell_contain_test_case(cell):
                self.convert_test_case_using_grader_template(cell)

    def add_grader_scripts(self) -> None:
        prepend_cell = new_code_cell(
            get_jupyter_cell_script("prepend_to_start_of_notebook.py")
        )
        append_cell = new_code_cell(
            get_jupyter_cell_script("append_to_end_of_notebook.py")
        )

        self.nb.cells.insert(0, prepend_cell)
        self.nb.cells.append(append_cell)

    def remove_grader_scripts(self) -> None:
        # remove prepend, append cells added by Jupygrader before storing to HTML
        self.nb.cells.pop(0)  # first cell (added by Jupygrader)
        self.nb.cells.pop()  # last cell (added by Jupygrader)

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

            files = (
                [files]
                if isinstance(files, (str, Path)) and not is_url(files)
                else files
            )

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
            "jupygrader_" + str(uuid.uuid4())[:6]
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
        comment_out_magic_commands(self.nb)
        self.preprocess_test_case_cells()
        self.add_grader_scripts()

        client_kwargs = {
            "kernel_name": "python3",
            "allow_errors": True,
        }

        if self.execution_timeout is not None:
            client_kwargs["timeout"] = self.execution_timeout

        client = NotebookClient(self.nb, **client_kwargs)
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

        self.graded_result.submission_notebook_hash = self.submission_notebook_hash

        self.graded_result.grader_python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.graded_result.grader_platform = platform.platform()
        self.graded_result.jupygrader_version = jupygrader_version

        item_grading_end_time = time.time()
        local_zone = ZoneInfo(get_localzone_name())

        self.graded_result.grading_finished_at = datetime.fromtimestamp(
            item_grading_end_time, tz=local_zone
        ).strftime("%Y-%m-%d %I:%M %p %Z")
        self.graded_result.grading_duration_in_seconds = round(
            item_grading_end_time - self.grading_start_time, 2
        )

    def apply_partial_ai_grading(self) -> None:
        """
        Perform partial AI grading in a single request using the full notebook JSON.
        Uses responses.parse() for structured output.
        """
        if (
            self.batch_config.ai_mode == AIGradingMode.OFF
            or self.batch_config.ai_mode == AIGradingMode.FULL
        ) or self.openai_client is None:
            return

        mode = self.batch_config.ai_mode

        client = self.openai_client
        model = self.batch_config.openai_model or "gpt-5-mini"

        notebook_json = self.nb

        test_case_result_dicts = [
            tc.__dict__ for tc in self.graded_result.test_case_results
        ]

        test_cases_to_review = []

        MANUAL_GRADING_INSTRUCTION = 'Grade this part manually. Assign points and provide feedback. If the student\'s code or response is close to correct, assign `True` to "did_pass".'
        FAILED_TC_REVIEW_INSTRUCTION = 'Review this failed test case based on the error message. Explain why it failed. Provide partial points if the code was close to passing. But leave the "did_pass" field as `False`.'

        for tc in self.graded_result.test_case_results:
            if mode == AIGradingMode.MANUAL_ONLY and tc.grade_manually:
                test_cases_to_review.append(
                    {
                        "test_case_name": tc.test_case_name,
                        "instruction": MANUAL_GRADING_INSTRUCTION,
                    }
                )

            elif mode == AIGradingMode.REVIEW_FAILED and tc.did_pass is False:
                test_cases_to_review.append(
                    {
                        "test_case_name": tc.test_case_name,
                        "instruction": FAILED_TC_REVIEW_INSTRUCTION,
                    }
                )

            elif mode == AIGradingMode.MANUAL_AND_FAILED and (
                tc.grade_manually or tc.did_pass is False
            ):
                if tc.grade_manually:
                    instruction = MANUAL_GRADING_INSTRUCTION
                elif tc.did_pass is False:
                    instruction = FAILED_TC_REVIEW_INSTRUCTION

                test_cases_to_review.append(
                    {
                        "test_case_name": tc.test_case_name,
                        "instruction": instruction,
                    }
                )

        if not test_cases_to_review:
            return False

        payload = {
            "notebook": notebook_json,
            "test_cases": test_case_result_dicts,
            "cases_to_review": test_cases_to_review,
        }

        try:
            response = client.responses.parse(
                model=model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are grading a student's Jupyter notebook submission. "
                            'Evaluate only the requested test cases in "test_cases_to_review" and return results.'
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(payload),
                    },
                ],
                text_format=AIParsedResult,
            )
        except Exception as e:
            print(f"[AI grading error]: {e}")
            return False

        parsed: AIParsedResult = response.output_parsed
        print(parsed)

        has_modified_scores = False

        for result in parsed.results:
            tc = next(
                (
                    t
                    for t in self.graded_result.test_case_results
                    if t.test_case_name == result.test_case_name
                ),
                None,
            )

            if tc is None:
                continue

            tc.points = result.points
            tc.did_pass = result.did_pass
            tc.is_graded = True
            tc.ai_feedback = result.feedback

            has_modified_scores = True

        if has_modified_scores:
            self._recalculate_scores()

    def save_graded_notebook_to_html(self, html_title: str, html_path: str):
        """Save a graded notebook as HTML with enhanced navigation.

        Converts the notebook to HTML and adds a sidebar with links to test case results
        and back-to-top functionality. Also adds styling for the graded results.

        Args:
            nb: The notebook to convert
            html_title: Title for the HTML document
            output_path: Path where the HTML file will be saved
            graded_result: Grading results to use for the sidebar links
        """
        html_exporter = HTMLExporter()
        r = html_exporter.from_notebook_node(
            self.nb, resources={"metadata": {"name": html_title}}
        )

        # add in-page anchors for test case code cells
        soup = BeautifulSoup(r[0], "html.parser")
        elements = soup.find_all("div", class_="jp-CodeCell")

        tc_counts = {}

        for el in elements:
            cell_code = el.find("div", class_="jp-Editor").getText().strip()
            tc = extract_test_case_metadata_from_code(cell_code)
            if tc:
                tc_name_cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", tc.test_case_name)
                if tc_name_cleaned not in tc_counts:
                    tc_counts[tc_name_cleaned] = 0
                tc_counts[tc_name_cleaned] += 1

                anchor_id = f"{tc_name_cleaned}_id{tc_counts[tc_name_cleaned]}"

                # set div's ID so that we can create internal anchors
                el["id"] = anchor_id

        jupygrader_sidebar_container_el = soup.new_tag("div")
        jupygrader_sidebar_container_el["class"] = "jupygrader-sidebar-container"
        soup.body.append(jupygrader_sidebar_container_el)

        back_to_top_el = BeautifulSoup(
            "<a class='graded-item-link back-to-top' data-text='Scroll to Test Case Results Summary' href='#_graded_result'>•</a>",
            "html.parser",
        ).find("a")
        jupygrader_sidebar_container_el.append(back_to_top_el)

        tc_counts = {}

        for o in self.graded_result.test_case_results:
            tc_name_cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", o.test_case_name)
            if tc_name_cleaned not in tc_counts:
                tc_counts[tc_name_cleaned] = 0
            tc_counts[tc_name_cleaned] += 1

            anchor_id = f"{tc_name_cleaned}_id{tc_counts[tc_name_cleaned]}"
            item_status_classname = (
                "manual-grading-required"
                if o.grade_manually
                else "pass"
                if o.did_pass
                else "fail"
            )

            item_el = soup.new_tag("a")
            item_el.string = ""
            item_el["class"] = f"graded-item-link {item_status_classname}"
            item_el["href"] = f"#{anchor_id}"
            item_el["data-text"] = (
                ("Passed " if o.did_pass else "" if o.grade_manually else "Failed ")
                + o.test_case_name
                + (
                    " (manual grading required)"
                    if o.grade_manually
                    else f" ({o.points} out of {o.available_points})"
                )
            )
            jupygrader_sidebar_container_el.append(item_el)

        # insert css
        head = soup.head

        jupygrader_sidebar_css = """
   html {
    scroll-behavior: smooth;
    }
    .jupygrader-sidebar-container {
    font-family: var(--jp-content-font-family);
    position: fixed;
    top: 0;
    left: 0;
    width: 24px;
    height: calc(100% - 8px);
    display: flex;
    flex-direction: column;
    gap: 3px;
    z-index: 999;
    padding: 4px 0;
    }
    .graded-item-link {
    flex: 1;
    position: relative;
    color: white;
    background-color: #000;
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
    font-size: 12px;
    border-radius: 3px;
    margin: 0 4px 0 2px;
    }
    .graded-item-link:hover {
    position: relative;
    z-index: 1;
    }
    .graded-item-link.back-to-top {
    flex-grow: 0;
    padding: 2px 0;
    }
    .graded-item-link.back-to-top:hover {
    color: #ddd;
    background-color: #222;
    }
    .graded-item-link.pass {
    background-color: #4caf50;
    }
    .graded-item-link.pass:hover {
    background-color: #388e3c;
    }
    .graded-item-link.fail {
    background-color: #f44336;
    }
    .graded-item-link.fail:hover {
    background-color: #d32f2f;
    }
    .graded-item-link.manual-grading-required {
    background-color: #ffeb3b;
    }
    .graded-item-link.manual-grading-required:hover {
    background-color: #fdd835;
    }
    /* tooltip */
    .graded-item-link:before {
    content: attr(data-text);
    /* here's the magic */
    position: absolute;
    /* vertically center */
    top: 50%;
    transform: translateY(-50%);
    /* move to right */
    left: 100%;
    /* basic styles */
    width: 300px;
    padding: 8px 10px 10px 10px;
    background: #fff;
    color: #000;
    border: 4px solid #000;
    text-align: left;
    display: none;
    /* hide by default */
    }
    .graded-item-link.back-to-top:before {
    border-color: #000000;
    }
    .graded-item-link.pass:before {
    color: #4caf50;
    border-color: #4caf50;
    }
    .graded-item-link.fail:before {
    color: #f44336;
    border-color: #f44336;
    }
    .graded-item-link.manual-grading-required:before {
    color: #777;
    border-color: #ffeb3b;
    }
    .graded-item-link:hover:before {
    display: block;
    }
    """

        new_style = soup.new_tag("style", type="text/css")
        new_style.append(jupygrader_sidebar_css)

        head.append(new_style)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(soup.prettify())

    def generate_output_artifacts(
        self,
    ) -> None:
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

        with open(graded_notebook_path, mode="w", encoding="utf-8") as f:
            nbformat.write(self.nb, f)

        # Clean up the notebook by removing grader scripts
        self.remove_grader_scripts()
        # Add the graded result summary to the notebook metadata
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

    def grade(self) -> Optional[GradedResult]:
        self.error_message = None
        try:
            with self.use_temporary_grading_environment():
                # 1. Prepare and execute the notebook (read, preprocess, inject scripts)
                self.prepare_and_execute_notebook()

                # 2. Process results (read JSON, parse, add metadata)
                self.process_grading_results()

                # 3. Apply partial AI grading if enabled and recalculate scores if needed
                self.apply_partial_ai_grading()

                # 4. Generate output files (cleaned .ipynb, .html, .py, .txt, final .json)
                self.generate_output_artifacts()

            return self.graded_result
        except Exception as e:
            print(f"[Error in GradingTask.grade()]: {e}")
            self.error_message = str(e)
            return None
