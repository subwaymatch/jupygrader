This page describes how to develop and contribute to `jupygrader`.

- `hatch` is used as the build system.
- `pytest` is used as the test runner.
- `mkdocs` is used for the documentation site.

## Test project

`hatch` uses `pytest` as the test runner. All tests are defined in the `tests/` directory.

```console
hatch test
```

Print a code coverage table by using the `--cover` flag.

```console
hatch test --cover
```

## Generate a code coverage report

```console
hatch run test:cov-html

# Output:
# Wrote HTML report to htmlcov\index.html
```

## Build artifact

This creates a distribution package, which can be uploaded to PyPI.

- Source distribution (sdist): `dist\jupygrader-...tar.gz`
- Wheel distribution (wheel): `dist\jupygrader-...-py3-none-any.whl`

```console
hatch build
```

## Install the built package locally

```console
pip install dist\jupygrader-...-py3-none-any.whl
```

## Publish to PyPI

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

## Updating Documentation

```sh
hatch run docs-serve # Serve docs
hatch run docs-build # Build docs
```

## Deploy Docs to GitHub Pages

This is automated by GitHub Actions, but can be used to manually deploy changes without pushing to the main branch.

```sh
hatch run mkdocs gh-deploy
```
