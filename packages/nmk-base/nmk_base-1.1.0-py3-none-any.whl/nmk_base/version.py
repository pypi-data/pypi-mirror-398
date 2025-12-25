"""
Python module for **nmk-base** version resolvers.
"""

from abc import abstractmethod

from nmk.model.resolver import NmkStrConfigResolver

import nmk_base


class VersionResolver(NmkStrConfigResolver):
    """
    Base class for nmk plugins version resolvers
    """

    @abstractmethod
    def get_version(self) -> str:  # pragma: no cover
        """
        Abstract method (to be overridden by subclasses), called by resolver to get plugin version.

        :returns: Plugin version string
        """
        pass

    def get_value(self, name: str) -> str:
        """
        Returns version string (returned by **get_version** method)

        :param name: Config item name (unused)
        :returns: Version string
        """
        return self.get_version()


class NmkBaseVersionResolver(VersionResolver):
    """
    Resolver for **nmkBasePluginVersion** config item
    """

    def get_version(self) -> str:
        """
        Returns **nmk_base** module version

        :returns: Module version
        """
        return nmk_base.__version__
