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
  - [Obfuscate test cases](#obfuscate-test-cases)
  - [Add hidden test cases](#add-hidden-test-cases)
- [🔧 Utility functions](#-utility-functions)
  - [Replace test cases](#replace-test-cases)
- [📄 License](#-license)

## 📝 Summary

Jupygrader is a Python package for automated grading of Jupyter notebooks. It provides a framework to:

1. **Execute and grade Jupyter notebooks** containing student work and test cases
2. **Generate comprehensive reports** in multiple formats (JSON, HTML, TXT)
3. **Extract student code** from notebooks into separate Python files
4. **Verify notebook integrity** by computing hashes of test cases and submissions

## ✨ Key Features

- Executes notebooks in a controlled, temporary environment
- Preserves the original notebook while creating graded versions
- Adds grader scripts to notebooks to evaluate test cases
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

Jupygrader is designed for educational settings where instructors need to grade student work in Jupyter notebooks, providing automated feedback while maintaining records of submissions and grading results.

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
import jupygrader

notebook_file_path = 'path/to/notebook.ipynb'
jupygrader.grade_notebooks(notebook_file_path)
```

Supplying a `pathlib.Path()` object is supported.

```python
import jupygrader
from pathlib import Path

notebook_path = Path('path/to/notebook.ipynb')
jupygrader.grade_notebooks(notebook_path)
```

If the `output_dir_path` is not specified, the output files will be stored to the same directory as the notebook file.

### Specify the output directory

```python
import jupygrader

jupygrader.grade_notebooks([{
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

### Obfuscate test cases

If you want to prevent learners from seeing the test case code, you can optionally set \_obfuscate = True to base64-encode the test cases.

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
