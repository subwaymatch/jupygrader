<p align="center">
  <img src="https://github.com/subwaymatch/jupygrader/blob/main/docs/images/logo_jupygrader_with_text_240.png?raw=true" alt="Jupygrader Logo" width="240"/>
</p>

[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)

[![PyPI - Version](https://img.shields.io/pypi/v/jupygrader.svg)](https://pypi.org/project/jupygrader)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jupygrader.svg)](https://pypi.org/project/jupygrader)

---

## 📋 Table of Contents

- [Summary](#summary)
- [Key Features](#key-features)
- [Installation](#installation)
- [Update Jupygrader](#update-jupygrader)
- [Usage](#usage)
  - [Specifying the output directory](#specifying-the-output-directory)
- [Development](#development)
  - [Test project](#test-project)
  - [Build artifact](#build-artifact)
  - [Publish to PyPI](#publish-to-pypi)
- [License](#license)

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
jupygrader.grade_notebook(notebook_file_path)
```

Supplying a `pathlib.Path()` object is supported.

```python
import jupygrader
from pathlib import Path

notebook_path = Path('path/to/notebook.ipynb')
jupygrader.grade_notebook(notebook_path)
```

If the `output_dir_path` is not specified, the output files will be stored to the same directory as the notebook file.

### Specifying the output directory

```python
import jupygrader

notebook_path = 'path/to/notebook.ipynb'
output_path = 'path/to/output'

jupygrader.grade_notebook(
    notebook_path=notebook_path,
    output_path=output_path
)
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

### Graded test cases

A graded test case requires a test case name and an assigned point value.

- The `_test_case` variable should store the name of the test case.
  The `_points` variable should store the number of points, either as an integer or a float.

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

## 💻 Development

### Test project

`hatch` uses `pytest` as the test runner. All tests are defined in the `tests/` directory.

```console
hatch test
```

Print a code coverage table by using the `--cover` flag.

```console
hatch test --cover
```

### Generate a code coverage report

```console
hatch run test:cov-html

# Output:
# Wrote HTML report to htmlcov\index.html
```

### Build artifact

This creates a distribution package, which can be uploaded to PyPI.

- Source distribution (sdist): `dist\jupygrader-...tar.gz`
- Wheel distribution (wheel): `dist\jupygrader-...-py3-none-any.whl`

```console
hatch build
```

### Installing the built package locally

```console
pip install dist\jupygrader-...-py3-none-any.whl
```

### Publish to PyPI

```console
hatch publish

# username: __token__
# password: [your-token-value]
```

Alternatively, you can create a `~/.pypirc` file with the token credentials.

`~/.pypirc`

```plaintext
[pypi]
username = __token__
password = [your-token-value]
```

## 📄 License

`jupygrader` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
