# API Reference

## 📌 Grader Functions

---

### `jupygrader.grade_notebooks()`

The primary entry point for grading. All functionality is accessible through this single function.

=== "Basic"

    ```python
    from jupygrader import grade_notebooks

    # Grade a list of notebooks
    graded_results = grade_notebooks(["path/to/notebook1.ipynb", "path/to/notebook2.ipynb"])
    ```

=== "With Configuration"

    ```python
    from jupygrader import grade_notebooks

    item1 = {
        "notebook_path": "path/to/notebook1.ipynb",
        "output_path": "path/to/output1",
        "copy_files": ["data1.csv"],
    }

    item2 = {
        "notebook_path": "path/to/notebook2.ipynb",
        "output_path": None,  # Will default to the notebook's parent directory
        "copy_files": {
            "data/population.csv": "another/path/population.csv",
        },
    }

    graded_results = grade_notebooks(
        [item1, item2],
        execution_timeout=300  # Allow up to 300 seconds (5 minutes) per cell
    )
    ```

=== "Full AI Grading"

    ```python
    import openai
    from jupygrader import grade_notebooks

    client = openai.OpenAI(api_key="your-api-key")

    # Grade based on notebook content — no execution
    results = grade_notebooks(
        ["submissions/student1.ipynb", "submissions/student2.ipynb"],
        ai_mode="full",
        openai_client=client,
        openai_model="gpt-4o",
    )
    ```

=== "Partial AI Grading"

    ```python
    import openai
    from jupygrader import grade_notebooks

    client = openai.OpenAI(api_key="your-api-key")

    # Execute notebooks, then send manual and failed cases to AI
    results = grade_notebooks(
        ["submissions/student1.ipynb", "submissions/student2.ipynb"],
        ai_mode="manual_and_failed",
        openai_client=client,
        openai_model="gpt-4o",
        custom_prompt="Award partial credit for correct reasoning even if the final answer is wrong.",
    )
    ```

#### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `grading_items` | `list` | — | Notebook paths (strings/Paths), dicts, or `GradingItem` objects |
| `base_files` | `str`, `Path`, `list`, or `dict` | `None` | Files copied to every notebook's working directory |
| `verbose` | `bool` | `True` | Print progress and diagnostic information |
| `export_csv` | `bool` | `True` | Export results to a timestamped CSV file |
| `csv_output_path` | `str` or `Path` | `None` | Custom path for the CSV export |
| `regrade_existing` | `bool` | `False` | Re-grade notebooks even if cached results exist |
| `execution_timeout` | `int` or `None` | `600` | Max seconds allowed per cell execution (not total notebook runtime); `None` disables timeout |
| `ai_mode` | `str` | `"off"` | AI grading mode — see table below |
| `openai_client` | `openai.OpenAI` | `None` | OpenAI client instance; required when `ai_mode` is not `"off"` |
| `openai_model` | `str` | `None` | Model name (e.g. `"gpt-4o"`); **required** when `ai_mode` is not `"off"` |
| `custom_prompt` | `str` | `None` | Additional grading instructions appended to the AI system prompt |

#### AI grading modes

| `ai_mode` | Description |
|---|---|
| `"off"` | No AI grading (default) |
| `"full"` | AI grades all test cases based on notebook content — notebook is **not** executed |
| `"manual_only"` | AI grades test cases marked `_grade_manually = True` |
| `"review_failed"` | AI reviews failed auto-graded test cases |
| `"manual_and_failed"` | AI grades both manual items and failed test cases |

::: jupygrader.grade_notebooks

---

## 📦 @dataclasses

---

### `jupygrader.GradedResult`

::: jupygrader.GradedResult

### `jupygrader.TestCaseResult`

::: jupygrader.TestCaseResult

---

---

## 📌 Notebook Operations

---

### `jupygrader.extract_test_case_metadata_from_code()`

::: jupygrader.extract_test_case_metadata_from_code

---

### `jupygrader.extract_test_cases_metadata_from_notebook()`

::: jupygrader.extract_test_cases_metadata_from_notebook

---

### `jupygrader.does_cell_contain_test_case()`

::: jupygrader.does_cell_contain_test_case

---

### `jupygrader.is_manually_graded_test_case()`

::: jupygrader.is_manually_graded_test_case

---

### `jupygrader.extract_user_code_from_notebook()`

::: jupygrader.extract_user_code_from_notebook

### `jupygrader.remove_code_cells_that_contain()`

::: jupygrader.remove_code_cells_that_contain

---

### `jupygrader.remove_comments()`

::: jupygrader.remove_comments

---

### `jupygrader.get_test_cases_hash()`

::: jupygrader.get_test_cases_hash
