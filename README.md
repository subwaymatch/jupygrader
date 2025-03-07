# Jupygrader

[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)

[![PyPI - Version](https://img.shields.io/pypi/v/jupygrader.svg)](https://pypi.org/project/jupygrader)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jupygrader.svg)](https://pypi.org/project/jupygrader)

---

## Table of Contents

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

## Summary

Jupygrader is a Python package for automated grading of Jupyter notebooks. It provides a framework to:

1. **Execute and grade Jupyter notebooks** containing student work and test cases
2. **Generate comprehensive reports** in multiple formats (JSON, HTML, TXT)
3. **Extract student code** from notebooks into separate Python files
4. **Verify notebook integrity** by computing hashes of test cases and submissions

## Key Features

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

## Installation

```console
pip install jupygrader
```

## Update Jupygrader

```console
pip install --upgrade jupygrader
```

## Usage

### Basic usage

```python
import jupygrader

notebook_file_path = 'path/to/notebook.ipynb'
jupygrader.grade_notebook(notebook_file_path)
```

### Specifying the output directory

```python
import jupygrader

notebook_file_path = 'path/to/notebook.ipynb'
output_dir_path = 'path/to/output'

jupygrader.grade_notebook(
    notebook_path=notebook_file_path,
    output_path=output_dir_path
)
```

## Development

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

### Build artifcat

```console
hatch build
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

## License

`jupygrader` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
