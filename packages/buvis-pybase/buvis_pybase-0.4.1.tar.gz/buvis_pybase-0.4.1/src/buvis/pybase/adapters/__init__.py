import os

if os.name == "nt":
    from .outlook_local.outlook_local import OutlookLocalAdapter

from .console.console import console, logging_to_console
from .jira.jira import JiraAdapter
from .poetry.poetry import PoetryAdapter
from .shell.shell import ShellAdapter
from .uv.uv import UvAdapter
from .uv.uv_tool import UvToolManager

__all__ = [
    "JiraAdapter",
    "PoetryAdapter",
    "ShellAdapter",
    "UvAdapter",
    "UvToolManager",
    "console",
    "logging_to_console",
]
