# A Simple Autograder for Jupyter Notebooks

<p align="center">
  <img src="https://github.com/subwaymatch/jupygrader/blob/main/docs/images/logo_jupygrader_with_text_240.png?raw=true" alt="Jupygrader Logo" width="240"/>
</p>

[![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/0ce9977cb9474fc0a2d7c531c988196b)](https://app.codacy.com/gh/subwaymatch/jupygrader/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

[![PyPI - Version](https://img.shields.io/pypi/v/jupygrader.svg)](https://pypi.org/project/jupygrader)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jupygrader.svg)](https://pypi.org/project/jupygrader)

Easily grade Jupyter notebooks using test cases and generate detailed reports.

## Sample Usage

```python
import glob
from jupygrader import grade_notebooks

# Select all Jupyter notebooks in the "submissions" folder
notebooks = glob.glob('submissions/*.ipynb')

# Grade notebooks
graded_results = grade_notebooks(notebooks)
```

Creating an autogradable item is as simple as adding a cell with a test case name (`_test_case`) and points ( `_points` ) to the notebook.

Assume your student is tasked to calculate the sum of odd numbers in `my_list1` and store it to a new variable named `odd_sum`.

```python
# Task: Calculate the sum of odd numbers
# in `my_list1` and store it
# to a new variable named `odd_sum`.

my_list1 = [1, 2, 3, 4, 5]

# YOUR CODE BEGINS
odd_sum = 0
for x in my_list1:
    if x % 2 != 0:
        odd_sum += x
# YOUR CODE ENDS
```

Add a cell with the following content after the code cell for the student.

```python
_test_case = "calculate-odd-sum"
_points = 2

assert odd_sum == 9
```

For each test case, Jupygrader will mark the test case as ==pass== if the test case cell does not throw an exception. Otherwise, it will mark the test case as ==fail==.

Here is a sample `TestCaseResult` object shown as JSON for the above test case.

```json
{
  "test_case_name": "calculate-odd-sum",
  "points": 2,
  "available_points": 2,
  "did_pass": true,
  "grade_manually": false,
  "message": ""
},
```

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
