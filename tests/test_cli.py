from pathlib import Path

from jupygrader.cli import _get_unique_default_strip_output_path


def test_get_unique_default_strip_output_path_without_collision(tmp_path: Path):
    notebook_path = tmp_path / "assignment.ipynb"

    write_path = _get_unique_default_strip_output_path(str(notebook_path))

    assert write_path == str(tmp_path / "assignment-stripped.ipynb")


def test_get_unique_default_strip_output_path_with_collision(tmp_path: Path):
    notebook_path = tmp_path / "assignment.ipynb"

    (tmp_path / "assignment-stripped.ipynb").touch()
    (tmp_path / "assignment-stripped(1).ipynb").touch()

    write_path = _get_unique_default_strip_output_path(str(notebook_path))

    assert write_path == str(tmp_path / "assignment-stripped(2).ipynb")
