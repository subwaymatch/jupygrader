<p align="center">
  <img src="https://github.com/subwaymatch/jupygrader/blob/main/docs/images/logo_jupygrader_with_text_240.png?raw=true" alt="Jupygrader Logo" width="240"/>
</p>

[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/0ce9977cb9474fc0a2d7c531c988196b)](https://app.codacy.com/gh/subwaymatch/jupygrader/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

[![PyPI - Version](https://img.shields.io/pypi/v/jupygrader.svg)](https://pypi.org/project/jupygrader)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jupygrader.svg)](https://pypi.org/project/jupygrader)

---

## 📋 Table of Contents

- [📝 Summary](#-summary)
- [✨ Key Features](#-key-features)
- [📦 Installation](#-installation)
- [🔄 Update Jupygrader](#-update-jupygrader)
- [🚀 Usage](#-usage)
  - [Basic usage](#basic-usage)
  - [Specify the output directory](#specify-the-output-directory)
- [📒 Create an autogradable notebook](#-create-an-autogradable-notebook)
  - [Code cell for learners](#code-cell-for-learners)
  - [Graded test cases](#graded-test-cases)
  - [Manually graded items](#manually-graded-items)
  - [Obfuscate test cases](#obfuscate-test-cases)
  - [Add hidden test cases](#add-hidden-test-cases)
- [🤖 AI-Assisted Grading](#-ai-assisted-grading)
  - [Full AI grading](#full-ai-grading)
  - [Review failed test cases](#review-failed-test-cases)
  - [Grade manual items](#grade-manual-items)
  - [Grade both manual and failed items](#grade-both-manual-and-failed-items)
  - [Custom grading prompt](#custom-grading-prompt)
- [🔧 Utility functions](#-utility-functions)
  - [Replace test cases](#replace-test-cases)
- [📄 License](#-license)

## 📝 Summary

Jupygrader is a Python package for automated grading of Jupyter notebooks. It provides a framework to:

1. **Execute and grade Jupyter notebooks** containing student work and test cases
2. **Generate comprehensive reports** in multiple formats (JSON, HTML, TXT)
3. **Extract student code** from notebooks into separate Python files
4. **Verify notebook integrity** by computing hashes of test cases and submissions
5. **Grade with AI assistance** — use an LLM to grade manual items, review failures, or evaluate notebooks entirely without execution

## ✨ Key Features

- Executes notebooks in a controlled, temporary environment
- Preserves the original notebook while creating graded versions
- Adds grader scripts to notebooks to evaluate test cases
- Supports multiple grading modes:
  - Automatic grading via assertions and tests
  - Manual grading
  - Hybrid (automatic + manual)
  - AI-assisted grading (full or partial)
- Generates detailed grading results including:
  - Individual test case scores
  - Overall scores and summaries
  - Success/failure status of each test
- Produces multiple output formats for instructors to review:
  - Graded notebook (.ipynb)
  - HTML report
  - JSON result data
  - Plaintext summary
  - Extracted Python code
- Includes metadata like Python version, platform, and file hashes for verification

## 📦 Installation

```console
pip install jupygrader
```

## 🔄 Update Jupygrader

```console
pip install --upgrade jupygrader
```

## 🚀 Usage

### Basic usage

```python
from jupygrader import grade_notebooks

notebook_file_path = 'path/to/notebook.ipynb'
grade_notebooks([notebook_file_path])
```

Supplying a `pathlib.Path()` object is supported.

```python
from jupygrader import grade_notebooks
from pathlib import Path

notebook_path = Path('path/to/notebook.ipynb')
grade_notebooks([notebook_path])
```

If the `output_path` is not specified, the output files will be stored to the same directory as the notebook file.

During grading, Jupygrader preprocesses code cells and comments out lines that start with IPython shell/magic prefixes (`!` and `%`). This prevents notebook-only commands from causing syntax errors in the Python-based grading pipeline.

### Specify the output directory

```python
from jupygrader import grade_notebooks

grade_notebooks([{
    "notebook_path": 'path/to/notebook.ipynb',
    "output_path": 'path/to/output'
}])
```

## 📒 Create an autogradable notebook

The instructor authors only one "solution" notebook, which contains both the solution code and test cases for all graded parts.

Jupygrader provides a simple drag-and-drop interface to generate a student-facing notebook that removes the solution code and obfuscates test cases if required.

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

Mark a test case with `_grade_manually = True` to flag it for human (or AI) review instead of assertion-based grading.

```python
_test_case = 'explain-your-approach'
_points = 5
_grade_manually = True

# Students write a free-response answer here
```

### Obfuscate test cases

If you want to prevent learners from seeing the test case code, you can optionally set `_obfuscate = True` to base64-encode the test cases.

Note that this provides only basic obfuscation, and students can easily decode the string to reveal the original code.

We may introduce an encryption method in the future.

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

#### Converted (before obfuscation)

```python
_test_case = 'create-a-pandas-series'
_points = 2

if 'is_jupygrader_env' in globals():
    pd.testing.assert_series_equal(sample_series, pd.Series([-20, -10, 10, 20]))
```

## 🤖 AI-Assisted Grading

Jupygrader can use an OpenAI-compatible model to assist with grading. Set the `ai_mode` parameter to one of the following string values:

| `ai_mode` | Description |
|---|---|
| `"off"` | No AI grading (default) |
| `"full"` | AI grades all test cases based on notebook content — no execution required |
| `"manual_only"` | AI grades test cases marked `_grade_manually = True` |
| `"review_failed"` | AI reviews auto-graded test cases that failed |
| `"manual_and_failed"` | AI grades both manual items and failed test cases |

> **Note:** `openai_model` is required whenever `ai_mode` is not `"off"`. Omitting it raises a `ValueError`.

### Full AI grading

Use `ai_mode="full"` to have the AI evaluate every test case based solely on the notebook's content, without executing it. This is ideal for open-ended assignments, essay-style responses, or notebooks that include general instructions rather than assertion-based tests.

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

In `"full"` mode, test cases are parsed directly from the notebook's source cells (no execution). Notebooks without any test case cells are still processed and output artifacts are generated.

### Review failed test cases

Use `ai_mode="review_failed"` to have the AI explain why auto-graded test cases failed and optionally award partial credit.

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

### Grade manual items

Use `ai_mode="manual_only"` to have the AI grade items marked `_grade_manually = True` in the notebook.

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

### Grade both manual and failed items

Use `ai_mode="manual_and_failed"` to combine both workflows in a single pass.

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

### Custom grading prompt

Pass `custom_prompt` to give the AI model additional context or grading criteria. This works with all AI grading modes.

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
        "This is a data analysis assignment. "
        "Award full points if the student produces a correct result, even if the approach differs. "
        "Deduct points for hard-coded values."
    ),
)
```

## 🔧 Utility functions

### Replace test cases

If a test case needs to be updated before grading, use the `jupygrader.replace_test_case()` function.

This is useful when learners have already submitted their Jupyter notebooks, but the original notebook contains an incorrect test case.

```python
nb = nbformat.read(notebook_path, as_version=4)

jupygrader.replace_test_case(nb, 'q1', '_test_case = "q1"\n_points = 6\n\nassert my_var == 3')
```

Below is a sample code snippet demonstrating how to replace multiple test cases using a dictionary.

```python
nb = nbformat.read(notebook_path, as_version=4)

new_test_cases = {
    'test_case_01': '_test_case = "test_case_01"\n_points = 6\n\npass',
    'test_case_02': '_test_case = "test_case_02"\n_points = 3\n\npass'
}

for tc_name, new_tc_code in new_test_cases.items():
    jupygrader.replace_test_case(nb, tc_name, new_tc_code)
```

## 📄 License

`jupygrader` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
