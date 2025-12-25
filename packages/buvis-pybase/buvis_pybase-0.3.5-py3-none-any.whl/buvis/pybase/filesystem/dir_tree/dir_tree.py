from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from buvis.pybase.filesystem.dir_tree.delete_by_extension import delete_by_extension
from buvis.pybase.filesystem.dir_tree.lowercase_file_extensions import (
    lowercase_file_extensions,
)
from buvis.pybase.filesystem.dir_tree.merge_mac_metadata import (
    merge_mac_metadata,
)
from buvis.pybase.filesystem.dir_tree.remove_empty_directories import (
    remove_empty_directories,
)
from buvis.pybase.filesystem.dir_tree.rename_equivalent_extensions import (
    rename_equivalent_extensions,
)

if TYPE_CHECKING:
    from pathlib import Path


class DirTree:
    @staticmethod
    def count_files(directory: Path) -> int:
        """
        Count the number of files in the directory and its subdirectories.

        :param directory: Path to the directory to process
        :type directory: :class:`Path`
        :return: Number of files in the directory and its subdirectories
        :rtype: int
        """
        return sum(1 for _ in directory.rglob("*") if _.is_file())

    @staticmethod
    def get_max_depth(directory: Path) -> int:
        """
        Determine the maximum depth of the directory tree.

        :param directory: Path to the directory to process
        :type directory: :class:`Path`
        :return: Maximum depth of the directory tree
        :rtype: int
        """
        return max(len(p.relative_to(directory).parts) for p in directory.rglob("*"))

    @staticmethod
    def delete_by_extension(directory: Path, extensions_to_delete: list[str]) -> None:
        """
        Delete files with specific extensions in the given directory.

        :param directory: Path to the directory to process
        :type directory: :class:`Path`
        :param extensions_to_delete: List of file extensions to delete
        :type extensions_to_delete: list[str]
        :return: None. The function modifies the <directory> in place.
        """
        delete_by_extension(directory, extensions_to_delete)

    @staticmethod
    def normalize_file_extensions(directory: Path) -> None:
        """
        Normalize file extensions in the given directory:
        1) lowercase the extensions
        2) replace equivalents

        :param directory: Path to the directory to process
        :type directory: :class:`Path`
        :return: None. The function modifies the <directory> in place.
        """
        lowercase_file_extensions(directory)

        # TODO: this should be configurable
        equivalent_extensions = [
            ["jpg", "jpeg", "jfif"],
            ["mp3", "mp2"],
            ["flac", "fla"],
        ]
        rename_equivalent_extensions(directory, equivalent_extensions)

    @staticmethod
    def remove_empty_directories(directory: Path) -> None:
        remove_empty_directories(directory)

    @staticmethod
    def merge_mac_metadata(directory: Path) -> None:
        merge_mac_metadata(directory)
