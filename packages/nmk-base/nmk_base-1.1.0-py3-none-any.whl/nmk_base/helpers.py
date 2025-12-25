"""
Python module for **nmk-base** helper tasks.
"""

from nmk import __version__
from nmk.model.builder import NmkTaskBuilder
from rich.emoji import Emoji


class InfoBuilder(NmkTaskBuilder):
    """
    Common implementation for information display tasks
    """

    def display_info(self, info: dict[str, str]):
        """
        Iterate on information dictionnary content, and display it with aligned colons

        :param info: Information dictionnary
        """

        # Prepare spaces padding
        max_len = max([len(n) for n in info])

        # Display all information
        for name, version in info.items():
            self.logger.info(self.task.emoji, f" {Emoji('backhand_index_pointing_right')} {name}{' ' * (max_len - len(name))}: {version}")


class VersionBuilder(InfoBuilder):
    """
    Builder implementation for **version** task
    """

    def build(self, plugins: dict[str, str]):
        """
        Build logic for **version** task:
        iterate on provided plugins version map and display them.

        :param plugins: Map of plugins versions
        """

        # Display all versions
        all_versions = {"nmk": __version__}
        all_versions.update(plugins)
        self.display_info(all_versions)


class HelpBuilder(InfoBuilder):
    """
    Builder implementation for **help** task
    """

    def build(self, links: dict[str, str]):
        """
        Build logic for **help** task:
        iterate on provided plugins help links map and display them.

        :param links: Map of plugins help links
        """

        # Displays all online help links
        all_links = {"nmk": "https://nmk.readthedocs.io/"}
        all_links.update(links)
        self.display_info(all_links)


class TaskListBuilder(InfoBuilder):
    """
    Builder implementation for **tasks** task
    """

    def build(self):
        """
        Build logic for **tasks** task:
        iterate on build model tasks, and display them (with their emoji and description text)
        """

        # Iterate on all model tasks
        all_tasks = {k: f"{self.model.tasks[k].emoji} - {self.model.tasks[k].description}" for k in sorted(self.model.tasks.keys())}
        self.display_info(all_tasks)
