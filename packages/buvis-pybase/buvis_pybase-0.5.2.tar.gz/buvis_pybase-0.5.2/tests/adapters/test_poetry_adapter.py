import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from buvis.pybase.adapters.poetry.poetry import PoetryAdapter


@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_runpy_run_path():
    with patch("runpy.run_path") as mock_run_path:
        yield mock_run_path


@pytest.fixture
def mock_importlib_import_module():
    with patch("importlib.import_module") as mock_import_module:
        yield mock_import_module


def test_run_script(
    mock_subprocess_run, mock_runpy_run_path, mock_importlib_import_module
):
    launcher = Path("script_launcher")
    arguments = ["arg1", "arg2"]
    pkg_name = "script_launcher"

    mock_activator = MagicMock(spec=Path)
    mock_activator.is_file.return_value = True

    mock_launcher_module = MagicMock()
    mock_importlib_import_module.return_value = mock_launcher_module

    with patch.object(PoetryAdapter, "get_activator_path", return_value=mock_activator):
        PoetryAdapter.run_script(launcher, arguments)

    # run_script() should NOT call subprocess.run for poetry install/update
    # Those calls are in update_script(), not run_script()
    
    mock_runpy_run_path.assert_called_once_with(str(mock_activator))
    mock_importlib_import_module.assert_called_once_with(f"{pkg_name}.cli")
    mock_launcher_module.cli.assert_called_once_with(arguments)


def test_update_script(mock_subprocess_run):
    """Test the update_script method which actually does the poetry install/update."""
    launcher = Path("script_launcher")
    pkg_name = "script_launcher"
    pkg_src = Path(launcher, "../../src/", pkg_name).resolve()

    PoetryAdapter.update_script(launcher)

    mock_subprocess_run.assert_any_call(
        ["poetry", "--directory", pkg_src, "install"],
        capture_output=True,
        check=False,
    )
    mock_subprocess_run.assert_any_call(
        ["poetry", "--directory", pkg_src, "update"],
        capture_output=True,
        check=False,
    )


def test_run_script_activator_not_found(mock_subprocess_run, capsys):
    launcher = Path("script_launcher")
    arguments = ["arg1", "arg2"]
    pkg_name = "script_launcher"
    pkg_src = Path(launcher, "../../src/", pkg_name).resolve()

    mock_activator = MagicMock(spec=Path)
    mock_activator.is_file.return_value = False

    with patch.object(PoetryAdapter, "get_activator_path", return_value=mock_activator):
        PoetryAdapter.run_script(launcher, arguments)

    captured = capsys.readouterr()
    assert (
        captured.out.strip()
        == f"Script preparation failed. Make sure `poetry install` can complete successfully in {pkg_src}."
    )


def test_get_activator_path_posix(mock_subprocess_run):
    directory = Path("/path/to/project")
    venv_dir = Path("/path/to/venv")
    activator_posix = Path(venv_dir, "bin", "activate_this.py")

    mock_subprocess_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=str(venv_dir).encode("utf-8"),
    )

    with patch("pathlib.Path.is_file", return_value=True):
        result = PoetryAdapter.get_activator_path(directory)

    assert result == activator_posix


def test_get_activator_path_win(mock_subprocess_run):
    directory = Path("C:\\path\\to\\project")
    venv_dir = Path("C:\\path\\to\\venv")
    activator_posix = Path(venv_dir, "bin", "activate_this.py")
    activator_win = Path(venv_dir, "Scripts", "activate_this.py")

    mock_subprocess_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=str(venv_dir).encode("utf-8"),
    )

    with patch("pathlib.Path.is_file", side_effect=[False, True]):
        result = PoetryAdapter.get_activator_path(directory)

    assert result == activator_win


def test_get_activator_path_not_found(mock_subprocess_run):
    directory = Path("/path/to/project")
    venv_dir = Path("/path/to/venv")

    mock_subprocess_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=str(venv_dir).encode("utf-8"),
    )

    result = PoetryAdapter.get_activator_path(directory)

    assert result == Path.cwd()
