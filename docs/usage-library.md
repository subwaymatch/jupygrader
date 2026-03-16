# Using `jupygrader` as a Python Library

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

Use the `grade_notebooks()` function to grade Jupyter notebooks. You can pass a list of notebook paths or a list of dictionaries for a more detailed configuration.

Before execution, Jupygrader preprocesses code cells and comments out lines beginning with `!` or `%` so IPython shell/magic commands do not break Python-based grading.

```python
from jupygrader import grade_notebooks

# Grade a list of notebooks
graded_results = grade_notebooks(["path/to/notebook1.ipynb", "path/to/notebook2.ipynb"])
```

!!! info "Custom Output Path and File Copying"

    You can specify the output path and copy files to the working directory for each notebook by passing a dictionary for each notebook.

    See the example below.

```python
from jupygrader import grade_notebooks

item1 = {
    "notebook_path": "path/to/notebook1.ipynb",
    "output_path": "path/to/output1",
    "copy_files": ["data1.csv"],
}
item2 = {
    "notebook_path": "path/to/notebook2.ipynb"
    # Use default output_path and do not copy files
}

graded_results = grade_notebooks([item1, item2])
```

You can also specify a dictionary for `copy_files` to place them in specific locations.

The key is the source file and the value is the destination path.

The destination path is relative to the working directory of the Jupyter notebook.

```python
from jupygrader import grade_notebooks

item1 = {
    "notebook_path": "path/to/notebook1.ipynb",
    "copy_files": {"my_data.parquet": "my_data.parquet"},
}

item2 = {
    "notebook_path": "path/to/notebook2.ipynb",
    "copy_files": {
        "data/population.csv": "another/path/population.csv",
        "titanic.db": "databases/titanic.db",
    },
}

graded_results = grade_notebooks([item1, item2])

```

If your assignment has base files that should be copied to every notebook's workspace, you can specify them in the `base_files` parameter of the `grade_notebooks` function. This will copy those files to the working directory of each notebook being graded.

```python
from jupygrader import grade_notebooks

graded_results = grade_notebooks(
    ["notebook1.ipynb", "notebook2.ipynb"],
    base_files={
        # Copy from the URL to data/my_data.csv in the working directory relative to the notebook
        "https://example.com/path/to/base_file.csv": "data/my_data.csv",
        # Local files are also supported
        "local-data/another_file.key": "openai_api_key.key",
    },
)
```

If a notebook has been already graded, it will skip grading and return the cached result. This is useful for large assignments where you want to avoid re-grading notebooks that have not changed.

```python
from jupygrader import grade_notebooks

graded_results1 = grade_notebooks(
    ["notebook1.ipynb", "notebook2.ipynb", "notebook3.ipynb"]
)

# The second call will skip re-grading for all three notebooks if they have not changed, and the jupygrader version is the same
graded_results2 = grade_notebooks(
    ["notebook1.ipynb", "notebook2.ipynb", "notebook3.ipynb"]
)

```

To force a regrade, use `regrade_existing=True` parameter. This will re-grade all specified notebooks regardless of whether they have been previously graded or not.

```python
graded_results2 = grade_notebooks(
    ["notebook1.ipynb", "notebook2.ipynb", "notebook3.ipynb"], regrade_existing=True
)
```

You can also control the verbosity of the output and whether to export the graded results to a CSV file. By default, verbose output is enabled and the graded results are exported to a CSV file named `graded_results_{%Y%m%d_%H%M%S}.csv` in the current working directory.

```python
from jupygrader import grade_notebooks

graded_results = grade_notebooks(
    ["notebook1.ipynb", "notebook2.ipynb", "notebook3.ipynb"],
    verbose=True,  # Default, set to False to disable verbose output
    export_csv=True,  # Default, set to False to disable CSV export
    csv_output_path="path/to/output/graded_results.csv",  # Optional: specify a custom path for the CSV output,
)
```

---

## 🤖 AI-Assisted Grading

Jupygrader can use an OpenAI-compatible model to assist with grading. Pass an `openai_client`, an `openai_model`, and set `ai_mode` to activate AI grading.

### AI grading modes

| `ai_mode` | Description |
|---|---|
| `"off"` | No AI grading (default) |
| `"full"` | AI grades all test cases based on notebook content — no execution required |
| `"manual_only"` | AI grades test cases marked `_grade_manually = True` |
| `"review_failed"` | AI reviews auto-graded test cases that failed |
| `"manual_and_failed"` | AI grades both manual items and failed test cases |

!!! warning "openai_model is required"

    You must always specify `openai_model` when using any AI grading mode. Omitting it raises a `ValueError` before any grading begins.

---

### Full AI grading (`"full"`)

Use `ai_mode="full"` to have the AI evaluate every test case based solely on the notebook's content, **without executing the notebook**. This is ideal for:

- Open-ended or essay-style assignments
- Rubric-based grading with general instructions
- Notebooks that don't rely on assertion-based tests

```python
import openai
from jupygrader import grade_notebooks

client = openai.OpenAI(api_key="your-api-key")

results = grade_notebooks(
    ["submissions/student1.ipynb", "submissions/student2.ipynb"],
    ai_mode="full",
    openai_client=client,
    openai_model="gpt-4o",
)
```

In `"full"` mode, test cases are parsed directly from the notebook's source cells. The notebook is never executed — the AI grades each test case by reading the notebook content. Notebooks without any test case cells are still processed and all output artifacts are generated.

**Notebook structure for full AI grading**

Test cases in your notebook don't need assertion code — they just need a name and point value. The AI uses the surrounding notebook context to decide whether the student's work meets the criteria.

```python
# Cell 1: student work area
_test_case = "question-1"
_points = 5
_grade_manually = True

# Students write their free-response answer above this cell
```

You can also have a notebook with general instructions (no test cases). In that case, grading completes and artifacts are generated, but no AI call is made since there are no cases to evaluate.

---

### Grade manual items only (`"manual_only"`)

Use `ai_mode="manual_only"` to have the AI grade test cases marked with `_grade_manually = True`. The notebook is still executed first; only manual items are sent to the AI.

```python
import openai
from jupygrader import grade_notebooks

client = openai.OpenAI(api_key="your-api-key")

results = grade_notebooks(
    ["submissions/student1.ipynb", "submissions/student2.ipynb"],
    ai_mode="manual_only",
    openai_client=client,
    openai_model="gpt-4o",
)
```

**Notebook test case example**

```python
_test_case = "explain-your-approach"
_points = 5
_grade_manually = True

# Students write a free-response answer in the cell above
```

---

### Review failed test cases (`"review_failed"`)

Use `ai_mode="review_failed"` to have the AI explain why auto-graded test cases failed and optionally award partial credit. The notebook is still executed; the AI receives the error messages for failed cases.

```python
import openai
from jupygrader import grade_notebooks

client = openai.OpenAI(api_key="your-api-key")

results = grade_notebooks(
    ["submissions/student1.ipynb", "submissions/student2.ipynb"],
    ai_mode="review_failed",
    openai_client=client,
    openai_model="gpt-4o",
)
```

The AI can award partial points for failed test cases but keeps `did_pass` as `False`.

---

### Grade both manual and failed items (`"manual_and_failed"`)

Use `ai_mode="manual_and_failed"` to combine both workflows in a single pass — the AI grades manual items and reviews failed test cases.

```python
import openai
from jupygrader import grade_notebooks

client = openai.OpenAI(api_key="your-api-key")

results = grade_notebooks(
    ["submissions/student1.ipynb", "submissions/student2.ipynb"],
    ai_mode="manual_and_failed",
    openai_client=client,
    openai_model="gpt-4o",
)
```

---

### Custom grading prompt

Pass `custom_prompt` to give the AI additional context, assignment-specific criteria, or grading rubric details. This works with all AI grading modes.

```python
import openai
from jupygrader import grade_notebooks

client = openai.OpenAI(api_key="your-api-key")

results = grade_notebooks(
    ["submissions/student1.ipynb"],
    ai_mode="full",
    openai_client=client,
    openai_model="gpt-4o",
    custom_prompt=(
        "This is a data analysis assignment using pandas. "
        "Award full points if the student arrives at the correct result, "
        "even if the approach differs from the expected solution. "
        "Deduct 50% of points if the student hard-codes values instead of computing them."
    ),
)
```

```python
import openai
from jupygrader import grade_notebooks

client = openai.OpenAI(api_key="your-api-key")

results = grade_notebooks(
    ["submissions/student1.ipynb"],
    ai_mode="manual_only",
    openai_client=client,
    openai_model="gpt-4o",
    custom_prompt=(
        "Grade the free-response questions based on clarity of explanation, "
        "correct use of terminology, and depth of reasoning. "
        "Award partial credit for partially correct answers."
    ),
)
```

---

## 📒 Create an autogradable notebook

The instructor authors only one "solution" notebook, which contains both the solution code and test cases for all graded parts.

### Code cell for learners

Any code between `# YOUR CODE BEGINS` and `# YOUR CODE ENDS` are stripped in the student version.

```python
import pandas as pd

# YOUR CODE BEGINS
sample_series = pd.Series([-20, -10, 10, 20])
# YOUR CODE ENDS

print(sample_series)
```

nbgrader syntax (`### BEGIN SOLUTION`, `### END SOLUTION`) is also supported.

```python
import pandas as pd

### BEGIN SOLUTION
sample_series = pd.Series([-20, -10, 10, 20])
### END SOLUTION

print(sample_series)
```

In the student-facing notebook, the code cell will look like:

```python
import pandas as pd

# YOUR CODE BEGINS

# YOUR CODE ENDS

print(sample_series)
```

### Grader-only cells

To keep setup notes or helper code in the instructor notebook only, start any cell with one of the following markers. The full cell will be removed in the generated student version:

- `# GRADER_ONLY` (case-insensitive)
- `# grader_only` (case-insensitive)
- `! grader_only` (case-insensitive)
- `_grader_only = True` (case-sensitive; whitespace is ignored)

### Graded test cases

A graded test case requires a test case name and an assigned point value.

- The `_test_case` variable should store the name of the test case.
- The `_points` variable should store the number of points, either as an integer or a float.

```python
_test_case = 'create-a-pandas-series'
_points = 2

pd.testing.assert_series_equal(sample_series, pd.Series([-20, -10, 10, 20]))
```

### Manually graded items

Mark a test case with `_grade_manually = True` to flag it for human or AI review instead of assertion-based grading.

```python
_test_case = 'explain-your-approach'
_points = 5
_grade_manually = True

# Students write a free-response answer in the cell above
```

### Obfuscate test cases (Work-in-progress)

If you want to prevent learners from seeing the test case code, you can optionally set `_obfuscate = True` to base64-encode the test cases.

!!! warning

    This provides only basic obfuscation, and students with technical knowledge can easily decode the string to reveal the original code. Supporting a password-based encryption method is planned for future releases.

**Instructor notebook**

```python
_test_case = 'create-a-pandas-series'
_points = 2
_obfuscate = True

pd.testing.assert_series_equal(sample_series, pd.Series([-20, -10, 10, 20]))
```

**Student notebook**

```python
# DO NOT CHANGE THE CODE IN THIS CELL
_test_case = 'create-a-pandas-series'
_points = 2
_obfuscate = True

import base64 as _b64
_64 = _b64.b64decode('cGQudGVzdGluZy5hc3NlcnRfc2VyaWVzX2VxdWFsKHNhbXBsZV9zZXJpZXMsIHBkLlNlcmllcyhbLT\
IwLCAtMTAsIDEwLCAyMF0pKQ==')
eval(compile(_64, '<string>', 'exec'))
```

### Add hidden test cases

Hidden test cases only run while grading.

#### Original test case

```python
_test_case = 'create-a-pandas-series'
_points = 2

### BEGIN HIDDEN TESTS
pd.testing.assert_series_equal(sample_series, pd.Series([-20, -10, 10, 20]))
### END HIDDEN TESTS
```
