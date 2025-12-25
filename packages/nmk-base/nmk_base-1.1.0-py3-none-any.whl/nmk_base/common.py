"""
Python module for **nmk-base** utility classes.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Any, Union

from jinja2 import Environment, Template, meta
from nmk.model.builder import NmkTaskBuilder
from nmk.model.keys import NmkRootConfig
from nmk.utils import run_with_logs
from tomlkit import TOMLDocument, comment, loads
from tomlkit.toml_file import TOMLFile


class TemplateBuilder(NmkTaskBuilder):
    """
    Generic builder logic to generate files from templates
    """

    def relative_path(self, v: str) -> str:
        """
        Make an absolute path as project relative if possible

        :param v: Path string to be converted
        :return: Project relative path (if possible); unchanged input value otherwise
        """
        v_path = Path(str(v))
        if v_path.is_absolute():
            try:
                return v_path.relative_to(self.model.config[NmkRootConfig.PROJECT_DIR].value).as_posix()
            except ValueError:  # pragma: no cover
                # Simply ignore, non project -relative
                pass
        return v

    def config_value(self, config_name: str) -> Any:
        """
        Get config value by name & turn absolute paths to project relative ones (if possible)

        :param config_name: Config item name
        :return: Config item value
        """
        v = self.model.config[config_name].value

        # Value processing depends on type
        if isinstance(v, str):
            # Single string
            return self.relative_path(v)
        elif isinstance(v, list):
            # Potentially a list of string
            return [self.relative_path(p) for p in v]

        # Probably nothing to do with path, use raw value
        return v  # pragma: no cover

    def render_template(self, template: Path, kwargs: dict[str, str]) -> str:
        """
        Render template into a string, with provided keywords and config items

        :param template: Path to template file to be rendered
        :param kwargs: Map of keywords for templates rendering, indexed by name
        :return: Rendered template string
        :throw: AssertionError if unknown keyword is referenced in template
        """

        # Load template
        with template.open() as f:
            # Render it
            template_source = f.read()

        # Look for required config items
        required_items = meta.find_undeclared_variables(Environment().parse(template_source))
        unknown_items = list(filter(lambda x: x not in kwargs and x not in self.model.config, required_items))
        assert len(unknown_items) == 0, f"Unknown config items referenced from template {template}: {', '.join(unknown_items)}"

        # Render
        all_kw = {c: self.config_value(c) for c in filter(lambda x: x not in kwargs, required_items)}
        all_kw.update(kwargs)
        return Template(template_source).render(all_kw)

    def build_from_template(self, template: Path, output: Path, kwargs: dict[str, str]) -> str:
        """
        Generate file from template

        :param template: Path to template file to be rendered
        :param output: Path to output file to be generated
        :param kwargs: Map of keywords for templates rendering, indexed by name
        :return: Rendered template string
        :throw: AssertionError if unknown keyword is referenced in template
        """

        # By default, keep system-defined line endings
        line_endings = None
        if output.suffix is not None:  # pragma: no branch
            # Check for forced line endings
            suffix = output.suffix.lower()

            if suffix in self.model.config["linuxLineEndings"].value:
                # Always generate with Linux line endings
                line_endings = "\n"

            if suffix in self.model.config["windowsLineEndings"].value:
                # Always generate with Windows line endings
                line_endings = "\r\n"

        # Load template
        self.logger.debug(f"Generating {output} from template {template}")
        with output.open("w", newline=line_endings) as o:
            # Render it
            out = self.render_template(template, kwargs)
            o.write(out)
            return out

    def build(self, template: str, kwargs: dict[str, str] = None):
        """
        Default build behavior: generate main output file from provided template

        :param template: Path to the Jinja template to use for generation
        :param kwargs: Map of keywords for templates rendering, indexed by name
        """

        # Just build from template
        self.build_from_template(Path(template), self.main_output, kwargs if kwargs else {})


class TomlFileBuilder(TemplateBuilder):
    """
    Generic builder logic to generate TOML files from templates and contributed items
    """

    # Handle relative path for all contributions
    def _check_paths(self, value: Any):
        if isinstance(value, str):
            return self.relative_path(value)
        if isinstance(value, list):
            return list(map(self._check_paths, value))
        if isinstance(value, dict):
            return {k: self._check_paths(v) for k, v in value.items()}
        return value

    def _contribute(self, main: dict, update: dict):
        """
        Merge items from **update** dictionary into **main** one.
        Merge logic for existing items is:

        * for lists: new items are appended after existing ones
        * for dictionaries: existing dictionary is updated with new one content
        * for other types: existing values are replaces with new ones

        :param main: Settings dictionary to be updated
        :param update: Update dictionary to be merged into the existing one
        """

        for k, v in update.items():
            # Already exists in target model?
            if k in main:
                # List: extend
                if isinstance(v, list):
                    main[k].extend(self._check_paths(v))
                # Map: recursive contribution
                elif isinstance(v, dict) and len(v) > 0:
                    self._contribute(main[k], v)
                # Otherwise: replace
                else:
                    main[k] = self._check_paths(v)
            else:
                # New key
                if (isinstance(v, (list, dict))) and len(v) == 0:
                    # Ignore empty lists and dicts
                    continue
                main[k] = self._check_paths(v)

    def build(self, fragment_files: list[str], items: dict, plugin_name: str = "nmk-base", kwargs: dict[str, str] = None):
        """
        Generates toml file from fragments and items

        :param fragment_files: List of fragment files (processed as Jinja templates) to be merged
        :param items: Dict of toml items to be merged; only non-empty items are considered (no empty section will be added)
        :param plugin_name: Plugin name to be inserted in generated file heading comment
        :param kwargs: Map of keywords for templates rendering, indexed by name
        """

        # Merge fragments to generate final file
        toml_file = {}
        for f_path in map(Path, fragment_files):
            try:
                # Update document with rendered template
                fragment_doc = loads(self.render_template(f_path, kwargs if kwargs else {}))
            except Exception as e:
                # Propagate error with file name
                raise ValueError(f"While loading toml file template ({f_path}): {e}") from e
            self._contribute(toml_file, fragment_doc.unwrap())

        # Iterate on items contributed through yml project files (only ones contributing non-empty dicts)
        self._contribute(toml_file, {k: v for k, v in items.items() if (isinstance(v, dict) and len(v) > 0)})

        # Finally write config to output file
        doc = TOMLDocument()
        doc.add(comment(f"Please don't edit: generated by {plugin_name} plugin"))
        doc.update(toml_file)
        toml_output = TOMLFile(self.main_output)
        toml_output.write(doc)


class MkdirBuilder(NmkTaskBuilder):
    """
    Generic builder logic to create directory
    """

    def build(self):
        """
        Build logic:
        create specified directory (main output of the task)
        """

        # Create directory
        self.main_output.mkdir(parents=True, exist_ok=True)


class ProcessBuilder(NmkTaskBuilder):
    """
    Generic builder logic to call a sub-process
    """

    def build(self, cmd: Union[str, list[str]], verbose: bool = False):
        """
        Build logic:

        * call subprocess specified through **cmd** parameter; process is invoked in project directory
        * depending on the **verbose** parameter, redirect output to stdout (if True) or to nmk logs (if False)
        * touch the specified output file

        :param cmd: process command line; may be a string or a list of parameters
        :param verbose: states if the process output shall be displayed in stdout or saved in logs
        """

        # Split args if cmd is a string
        args = cmd if isinstance(cmd, list) else cmd.split(" ")

        if verbose:
            # Verbose: process output will go to stdout/stderr
            self.logger.debug(f"Running command: {args}")
            subprocess.run(args, cwd=self.model.config[NmkRootConfig.PROJECT_DIR].value, check=True)
        else:
            # Redirect output to logs
            run_with_logs(args, cwd=self.model.config[NmkRootConfig.PROJECT_DIR].value, check=True)

        # Touch main output file, if any
        if len(self.outputs):
            self.main_output.touch()


class CleanBuilder(NmkTaskBuilder):
    """
    Generic builder logic to clean a directory
    """

    def build(self, path: str):
        """
        Build logic: delete (recursively) provided directory, if it exists

        :param path: Directory to be deleted
        """

        # Check path
        to_delete = Path(path)
        if to_delete.is_dir():
            # Clean it
            self.logger.debug(f"Cleaning folder: {to_delete}")
            shutil.rmtree(to_delete)
        else:
            # Nothing to clean
            self.logger.debug(f"Nothing to clean (folder not found: {to_delete})")
