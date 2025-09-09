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

## jupy strip

Strip solution code and optionally outputs from a Jupyter Notebook.

### Usage

```
jupy strip NOTEBOOK_PATH [OPTIONS]
```

- `NOTEBOOK_PATH` (required): Path to a single Jupyter Notebook (`.ipynb` file).  
  Must exist and be readable.

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
