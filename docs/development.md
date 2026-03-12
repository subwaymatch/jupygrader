This page describes how to develop and contribute to `jupygrader`.

- `hatch` is used as the build system.
- `pytest` is used as the test runner.
- `mkdocs` is used for the documentation site.

## Test project

All tests are defined in the `tests/` directory. To run all tests, you can use the following command:

```console
hatch test
```

`hatch` uses `pytest` as the test runner. You can parallelize the tests to speed up the testing process by using the `-p` flag (shorthand for `--parallel`), which will distribute the tests across multiple workers.

```console
hatch test -p
```

Print a code coverage table by using the `--cover` flag.

```console
hatch test --cover
```

### Tests that require an OpenAI API key

Test cases that require OpenAI API key and may incur costs are marked with the `@pytest.mark.ai` marker. By default, these tests are not run when you execute `hatch test`. To include these tests in the test run, use the `-m ai` option with `hatch run pytest`.

```console
hatch run pytest -m ai
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

## Previewing documentation in development mode

```sh
hatch run docs:serve
```

## Building documentation

```sh
hatch run docs:build
```

## Deploy Docs to GitHub Pages

This is automated by GitHub Actions, but can be used to manually deploy changes without pushing to the main branch.

```sh
hatch run docs:deploy
```
