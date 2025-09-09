# Using `jupygrader` as a CLI Tool

The CLI tool is work-in-progress.

```console
jupy --version
```

## jupy grade

Grade one or more notebooks or patterns.

### Usage

```
jupy grade NOTEBOOK_PATH... [OPTIONS]
```

- `NOTEBOOK_PATH` (required): One or more paths to notebooks, directories, or glob patterns.
  - If a file is given and ends with `.ipynb`, it is added directly.
  - If a directory is given, all top-level `.ipynb` files inside are included.
  - Otherwise, the argument is treated as a glob pattern and expanded recursively.

### Examples

#### Example 1: Grade a single notebook

```bash
jupy grade path/to/notebook.ipynb
```

#### Example 2: Grade multiple specific notebooks

```bash
jupy grade notebook1.ipynb notebook2.ipynb
```

#### Example 3: Grade all notebooks in a directory

```bash
jupy grade path/to/assignments/
```

#### Example 4: Grade notebooks using a glob pattern and save results to a specific folder

```bash
jupy grade "final-project/**/*.ipynb" --csv-output-path ./grading-results
```

#### Example 5: Regrade all notebooks, even if already graded, without creating a CSV:

```bash
jupy grade path/to/assignments/ --regrade-existing --no-export-csv
```

### Options

- `--verbose`  
  Enable verbose output. Defaults to `false`.

- `--export-csv / --no-export-csv`  
  Export results to CSV. Enabled by default.

- `--csv-output-path PATH`  
  Directory to write CSV output into (does not need to exist yet).  
  Must be a directory if provided.

- `--regrade-existing`  
  Regrade even if results already exist. Defaults to `false`.

### Behavior

- Prints the resolved list of notebooks to grade.
- Displays the effective option values.
- Calls the `grade_notebooks` function to run grading logic.

---

## jupy strip

Strip solution code and optionally outputs from a Jupyter Notebook.

### Usage

```bash
jupy strip NOTEBOOK_PATH [OPTIONS]
```

- `NOTEBOOK_PATH` (required): Path to a single Jupyter Notebook (`.ipynb` file).  
  Must exist and be readable.

### Examples

#### Example 1: Strip a notebook and a new default output file

This will create `assignment-1-stripped.ipynb`.

```bash
jupy strip assignment-1.ipynb
```

#### Example 2: Strip a notebook and specify the exact output file path:

```bash
jupy strip student-submission.ipynb -o student-version-for-release.ipynb
```

#### Example 3: Strip solution code but keep all cell outputs

```bash
jupy strip instructor-notebook.ipynb --no-clear-output -o student-notebook.ipynb
```

### Options

- `--output, -o PATH`  
  Path to save the stripped notebook.  
  Defaults to `[input]-stripped.ipynb`.  
  Must end with `.ipynb` if provided.

- `--clear-output / --no-clear-output`  
  Whether to also clear cell outputs and execution counts.  
  Enabled by default (`--clear-output`).

### Behavior

- Validates that both input and output files are `.ipynb`.
- Determines an output path (default or user-specified).
- Reads the notebook, removes solution code, and optionally clears outputs.
- Writes the processed notebook to the output path.
- Displays success or error messages.
