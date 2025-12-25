"""
Python module for **nmk-base** venv tasks.
"""

import sys
from pathlib import Path

from nmk.model.builder import NmkTaskBuilder
from nmk.model.resolver import NmkListConfigResolver, NmkStrConfigResolver
from nmk.utils import run_pip


class ExeResolver(NmkStrConfigResolver):
    """
    Resolver class for **venvPython** config item
    """

    def get_value(self, name: str) -> list[str]:
        """
        Resolution logic: returns sys.executable
        """
        return sys.executable


class BinResolver(NmkStrConfigResolver):
    """
    Resolver class for **venvBin** config item
    """

    def get_value(self, name: str) -> list[str]:
        """
        Resolution logic: returns sys.executable parent folder
        """
        return str(Path(sys.executable).parent)


class FileDepsContentResolver(NmkListConfigResolver):
    """
    Resolver class for **venvFileDepsContent** config item
    """

    def get_value(self, name: str) -> list[str]:
        """
        Resolution logic: merge content from files listed in **venvFileDeps** config item
        """

        file_requirements = []

        # Merge all files content
        for req_file in map(Path, self.model.config["venvFileDeps"].value):
            with req_file.open() as f:
                # Append file content + one empty line
                file_requirements.extend(f.read().splitlines(keepends=False))
                file_requirements.append("")

        return file_requirements


class VenvUpdateBuilder(NmkTaskBuilder):
    """
    Builder for **py.venv** task
    """

    def build(self, pip_args: str = ""):
        """
        Build logic for **py.venv** task:
        calls **pip install** with generated requirements file, then **pip freeze** to list all dependencies in secondary output file.

        :param pip_args: Extra arguments to be used when invoking **pip install**
        """

        # Prepare outputs
        venv_folder = self.main_output
        venv_status = self.outputs[1]

        # Call pip and touch output folder
        run_pip(
            ["install"] + (["-r"] if self.main_input.suffix == ".txt" else []) + [str(self.main_input)],
            logger=self.logger,
            extra_args=pip_args + " " + self.model.pip_args,
        )
        venv_folder.touch()

        # Dump installed packages
        pkg_list = run_pip(["freeze"], logger=self.logger)
        with venv_status.open("w") as f:
            f.write(pkg_list)
