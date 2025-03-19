# Usage

## 📦 Installation

```console
pip install jupygrader
```

## 🔄 Update Jupygrader

```console
pip install --upgrade jupygrader
```

## Grade Notebooks

---

### Grade multiple notebooks

Use the `grade_notebooks` function to grade Jupyter notebooks. You can pass a list of notebook paths or `GradingItemConfig` objects for more detailed configuration.

```python
from jupygrader import grade_notebooks

# Grade a list of notebooks
graded_results = grade_notebooks(['path/to/notebook1.ipynb', 'path/to/notebook2.ipynb'])
```

You can specify the output path and copy files to the working directory for each notebook by using a `GradingItemConfig` dataclass.

```python
from jupygrader import grade_notebooks, GradingItemConfig

# Grade with GradingItemConfig for more options
item1 = GradingItemConfig(
    notebook_path='path/to/notebook1.ipynb',
    output_path='path/to/output1',
    copy_files=['data1.csv']
)

# You can also specify a dictionary for copy_files to place them in specific locations
# The key is the source file and the value is the destination path
# The destination path is relative to the working directory of the Jupyter notebook
item2 = GradingItemConfig(
    notebook_path='path/to/notebook2.ipynb',
    output_path=None, # Will output to the same path as the notebook2.ipynb file
    copy_files={
        'data/population.csv': 'another/path/population.csv',
        'titanic.db': 'databases/titanic.db'
    }
)

graded_results = grade_notebooks([item1, item2])
```

---

### Grade a single notebook

You can grade a single notebook using the `grade_single_notebook` function.

!!! note

    The `grade_single_notebook` function is a wrapper around the `grade_notebooks` function. It is provided for convenience.

=== "Basic"

    ```python
    from jupygrader import grade_single_notebook

    # Grade a single notebook by path
    graded_result = grade_single_notebook('path/to/notebook.ipynb')
    ```

=== "With Configuration"

    ```python
    from jupygrader import grade_single_notebook, GradeingItemConfig

    # Grade with custom output path and file copying
    config = GradingItemConfig(
        notebook_path='path/to/notebook.ipynb',
        output_path='path/to/output',
        copy_files=['data.csv']
    )
    graded_result = grade_single_notebook(config)
    ```
