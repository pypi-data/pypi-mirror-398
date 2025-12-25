"""
Python module for system dependencies check
"""

import shutil

from nmk.model.builder import NmkTaskBuilder


class SystemDepsCheckBuilder(NmkTaskBuilder):
    """
    Builder logic for **sys.deps** task
    """

    def build(self, deps: dict[str, dict[str, str]]):
        """
        Verify system dependencies

        Iterate on required dependencies, check them, and stop with install instructions if they're not found

        :param deps: Map of system requirements + install instructions
        """

        # Collect missing dependencies
        missing_deps = {i[0]: i[1] for i in filter(lambda t: shutil.which(t[0]) is None, deps.items())}

        # Something missing?
        if missing_deps:  # pragma: no branch
            # List missing commands
            self.logger.warning(f"Missing system dependencies: {', '.join(list(missing_deps.keys()))}")

            # Just verify if current system has apt
            has_apt = shutil.which("apt") is not None

            # Also inform about install instructions ...
            apt_packages = set()
            urls_map = {}
            for command, instructions in missing_deps.items():
                # ... with apt
                if "apt" in instructions and has_apt:  # pragma: no cover
                    apt_packages = apt_packages.union(instructions["apt"])

                # ... with simple URLs
                if "url" in instructions:  # pragma: no branch
                    urls_map[command] = instructions["url"]
            assert apt_packages or urls_map, "Detected missing dependencies, but no install instructions are provided..."

            # Display instructions
            self.logger.warning("Install instructions:")
            if apt_packages:  # pragma: no cover
                self.logger.warning(f'* for global system install, use this command: "sudo apt install {" ".join(apt_packages)}"')
            for cmd, url in urls_map.items():
                self.logger.warning(f'* for "{cmd}" manual user install: see {url}')

            # Stop here
            raise RuntimeError("Please install missing system dependencies (see above)")
