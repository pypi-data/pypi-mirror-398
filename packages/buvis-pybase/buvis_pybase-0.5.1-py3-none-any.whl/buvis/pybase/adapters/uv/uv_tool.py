import subprocess
from pathlib import Path

from buvis.pybase.adapters.console.console import console
from buvis.pybase.adapters.uv.uv import UvAdapter


class UvToolManager:
    @staticmethod
    def install_all(scripts_root: Path | None = None) -> None:
        """Install all projects in src/ as uv tools."""
        UvAdapter.ensure_uv()

        if scripts_root is None:
            scripts_root = Path.cwd()

        src_directory = scripts_root / "src"

        if src_directory.exists():
            for project_dir in src_directory.iterdir():
                if project_dir.is_dir() and (project_dir / "pyproject.toml").exists():
                    UvToolManager.install_tool(project_dir)

    @staticmethod
    def install_tool(project_path: Path) -> None:
        """Install a project as a uv tool."""
        pkg_name = project_path.name
        console.status(f"Installing {pkg_name} as uv tool...")

        try:
            # Use --force to overwrite existing tools, --editable for dev mode
            subprocess.run(
                ["uv", "tool", "install", "--force", "--editable", str(project_path)],
                check=True,
                capture_output=False,  # Let output show to user
            )
            console.success(f"Installed {pkg_name}")
        except subprocess.CalledProcessError as e:
            console.failure(f"Failed to install {pkg_name}: {e}")

    @staticmethod
    def update_all(scripts_root: Path | None = None) -> None:
        """Update all installed uv tools."""
        # uv tool upgrade --all might work if they were installed from registry,
        # but for editable local tools, re-installing or 'uv tool upgrade' works.
        # Since we use editable, they update automatically with code changes.
        # But we might want to update dependencies (lock file).

        if scripts_root is None:
            scripts_root = Path.cwd()

        src_directory = scripts_root / "src"

        if src_directory.exists():
            for project_dir in src_directory.iterdir():
                if project_dir.is_dir() and (project_dir / "pyproject.toml").exists():
                    UvToolManager.update_lock(project_dir)

    @staticmethod
    def update_lock(project_path: Path) -> None:
        """Update lock file for a project."""
        console.status(f"Updating lock file for {project_path.name}...")

        try:
            subprocess.run(
                ["uv", "lock", "--upgrade"],
                cwd=project_path,
                check=True,
                capture_output=True,
            )
            console.success(f"Updated lock file for {project_path.name}")
        except subprocess.CalledProcessError:
            console.failure(f"Failed to update lock file for {project_path.name}")
