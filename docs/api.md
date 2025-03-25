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
    from jupygrader import grade_notebooks, GradingItemConfig

    # Grade with GradingItemConfig for more options
    item1 = GradingItemConfig(
        notebook_path='path/to/notebook1.ipynb',
        output_path='path/to/output1',
        copy_files=['data1.csv']
    )

    item2 = GradingItemConfig(
        notebook_path='path/to/notebook2.ipynb',
        output_path=None, # Will output to the same path as the notebook2.ipynb file
        copy_files={
            'data/population.csv': 'another/path/population.csv'
        }
    )

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
    from jupygrader import grade_single_notebook, GradeingItemConfig

    # Grade with detailed configuration
    config = GradingItemConfig(
        notebook_path='path/to/notebook.ipynb',
        output_path='path/to/output',
        copy_files=['data.csv']
    )
    graded_result = grade_single_notebook(config)
    ```

::: jupygrader.grade_single_notebook

---

## 📦 @dataclasses

---

### `jupygrader.GradingItemConfig`

::: jupygrader.GradingItemConfig

---

### `jupygrader.types.TestCaseMetadata`

::: jupygrader.types.TestCaseMetadata

---

### `jupygrader.types.TestCaseResult`

::: jupygrader.types.TestCaseResult

---

### `jupygrader.types.GradedResult`

::: jupygrader.types.GradedResult

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

---

### `jupygrader.remove_comments()`

::: jupygrader.remove_comments

---

### `jupygrader.get_test_cases_hash()`

::: jupygrader.get_test_cases_hash
