from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


class PoetryAdapter:
    """
    A class to handle running scripts within a Poetry-managed project environment.
    """

    @classmethod
    def run_script(cls, script_path: str, args: list):
        script_file = Path(script_path)
        pkg_name = script_file.stem

        # Find the corresponding project directory
        scripts_root = script_file.parent.parent
        project_dir = scripts_root / "src" / pkg_name

        if project_dir.exists() and (project_dir / "pyproject.toml").exists():
            # Run using the project's virtual environment
            import subprocess

            cmd = [
                "poetry",
                "run",
                "python",
                "-c",
                f"import sys; sys.path.insert(0, '{project_dir}'); "
                f"from {pkg_name}.cli import main; main({args!r})",
            ]
            subprocess.run(cmd, cwd=project_dir)
        else:
            # Fallback to current behavior
            launcher_module = importlib.import_module(f"{pkg_name}.cli")
            launcher_module.main(args)

    @staticmethod
    def update_script(launcher: Path) -> None:
        pkg_name = Path(launcher).stem.replace("-", "_")
        pkg_src = Path(launcher, "../../src/", pkg_name).resolve()

        sys.path.insert(0, str(pkg_src))
        subprocess.run(  # noqa: S603
            ["poetry", "--directory", pkg_src, "install"],  # noqa: S607
            capture_output=True,
            check=False,
        )
        subprocess.run(  # noqa: S603
            ["poetry", "--directory", pkg_src, "update"],  # noqa: S607
            capture_output=True,
            check=False,
        )

    @staticmethod
    def get_activator_path(directory: Path) -> Path:
        """
        Get the path to the virtual environment activator script.

        :param directory: The directory of the Poetry project.
        :type directory: Path
        :return: The path to the activator script, or the current working directory if not found.
        :rtype: Path
        """
        venv_dir_stdout = subprocess.run(  # noqa: S603
            ["poetry", "--directory", directory, "env", "info", "--path"],  # noqa: S607
            stdout=subprocess.PIPE,
            check=False,
        )
        venv_dir = Path(venv_dir_stdout.stdout.decode("utf-8").strip())
        activator_posix = Path(venv_dir, "bin", "activate_this.py")
        activator_win = Path(venv_dir, "Scripts", "activate_this.py")

        if activator_posix.is_file():
            return activator_posix

        if activator_win.is_file():
            return activator_win

        return Path.cwd()

    @classmethod
    def update_all_scripts(cls, scripts_root: Path = None):
        """Update all scripts in bin/ and all Poetry projects in src/."""

        if scripts_root is None:
            scripts_root = Path.cwd()

        # Update bin scripts using existing method

        bin_directory = scripts_root / "bin"

        if bin_directory.exists():
            for file_path in bin_directory.iterdir():
                if file_path.is_file() and cls._contains_poetry_adapter(file_path):
                    cls.update_script(str(file_path))

        # Update individual script projects in src/

        src_directory = scripts_root / "src"

        if src_directory.exists():
            for project_dir in src_directory.iterdir():
                if project_dir.is_dir() and (project_dir / "pyproject.toml").exists():
                    cls._update_poetry_project(project_dir)

    @staticmethod
    def _contains_poetry_adapter(file_path: Path) -> bool:
        try:
            return (
                "from buvis.pybase.adapters import PoetryAdapter"
                in file_path.read_text()
            )

        except UnicodeDecodeError:
            return False

    @staticmethod
    def _update_poetry_project(project_path: Path):
        import subprocess

        try:
            subprocess.run(
                ["poetry", "update"], cwd=project_path, check=True, capture_output=True
            )

        except subprocess.CalledProcessError:
            pass  # Silently continue on failure
