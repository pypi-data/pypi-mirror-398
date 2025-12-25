"""
Python module for base resolvers (to be used by other plugins).
"""

from abc import abstractmethod
from pathlib import Path

from nmk.model.resolver import NmkListConfigResolver


class FilesResolver(NmkListConfigResolver):
    """
    Base resolver class helping for files resolution.
    """

    @property
    @abstractmethod
    def folder_config(self) -> str:  # pragma: no cover
        """
        Must be overridden by sub-classes. This property is used to identify the config item identifying the folder(s) where to search files.

        :return: Name of the config item holding the folder(s) to be searched for files
        """
        pass

    @property
    def extension(self) -> str:  # pragma: no cover
        """
        Can be overridden by sub-classes. This property is used to identify the extension of files to be searched

        :return: Extension to be searched in folder(s); Default is "*.*"
        """
        return "*.*"

    def get_value(self, name: str) -> list[Path]:
        """
        Files resolution logic:
        iterate on provided folders (from config item name), and filter on provided extension.

        :return: List of found files
        """

        # Locate paths to be browsed
        path_config = self.model.config[self.folder_config].value
        path_to_browse = path_config if isinstance(path_config, list) else [path_config]

        # Iterate on paths, and find all files
        return [file for path in map(Path, path_to_browse) for file in filter(lambda f: f.is_file(), path.rglob(self.extension))]
