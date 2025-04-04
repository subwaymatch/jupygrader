# API Reference

## 📌 Grader Functions

---

### `jupygrader.grade_notebooks()`

=== "Basic"

    ```python
    from jupygrader import grade_notebooks

    # Grade a list of notebooks
    graded_results = grade_notebooks(['path/to/notebook1.ipynb', 'path/to/notebook2.ipynb'])
    ```

=== "With Configuration"

    ```python
    from jupygrader import grade_notebooks, GradingItem

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

    graded_results = grade_notebooks([item1, item2])
    ```

::: jupygrader.grade_notebooks

---

### `jupygrader.grade_single_notebook()`

=== "Basic"

    ```python
    from jupygrader import grade_single_notebook

    # Grade a single notebook by path
    graded_result = grade_single_notebook('path/to/notebook.ipynb')
    ```

=== "With Configuration"

    ```python
    from jupygrader import grade_single_notebook

    # Grade with detailed configuration
    item1 = {
        "notebook_path": "path/to/notebook1.ipynb",
        "output_path": "path/to/output1",
        "copy_files": ["data1.csv"],
    }
    graded_result = grade_single_notebook(item)
    ```

::: jupygrader.grade_single_notebook

---

## 📦 @dataclasses

---

### `jupygrader.TestCaseResult`

::: jupygrader.TestCaseResult

---

### `jupygrader.GradedResult`

::: jupygrader.GradedResult

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
