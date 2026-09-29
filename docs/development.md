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

Releases are published by the `.github/workflows/publish.yml` workflow when a GitHub release is published. It uses PyPI trusted publishing, so no API token is needed.

### One-time setup

On [pypi.org](https://pypi.org/manage/project/jupygrader/settings/publishing/), open the `jupygrader` project's **Publishing** settings and add a GitHub publisher:

- Owner: `subwaymatch`
- Repository name: `jupygrader`
- Workflow name: `publish.yml`
- Environment name: `pypi`

### Release a new version

1. Update `__version__` in `src/jupygrader/__about__.py`. Bump the patch version (for example, `0.5.1` to `0.5.2`) for fixes and behavior changes. Bump the minor version only when the public API changes.
2. Merge the change into `main`.
3. On GitHub, create a release from `main` with a tag that matches the version, such as `v0.5.2`.

The workflow checks that the tag matches `__version__`, builds the package, and uploads it to PyPI. Follow its progress in the repository's **Actions** tab.

### Publish manually

To publish from your own computer instead, build the package and run:

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
