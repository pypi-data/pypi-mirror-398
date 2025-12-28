"""
Python version handling
"""

import platform
import re

from nmk.model.builder import NmkTaskBuilder
from nmk.model.resolver import NmkListConfigResolver, NmkStrConfigResolver

# Git version pattern
_GIT_VERSION_PATTERN = re.compile("([^-]+)(?:-([0-9]+))?(?:-(.+))?")


class PythonVersionResolver(NmkStrConfigResolver):
    """
    Python version resolver
    """

    def get_value(self, name: str) -> str:
        """
        Turn the git version in the Python way
        """
        git_version = self.model.config["gitVersion"].value
        m = _GIT_VERSION_PATTERN.match(git_version)
        if m is not None:
            # Build python version from git version segments
            out = m.group(1)
            if m.group(2) is not None:
                # Add commits count
                out += f".post{m.group(2)}"
            if m.group(3) is not None:
                # Add hash/dirty
                out += f"+{m.group(3)}".replace("-", ".")
            return out

        # Probably a simpler version (without segments)
        # Assume it is already compliant...
        return git_version


class PythonVersionRefresh(NmkTaskBuilder):
    """
    Python version builder
    """

    def build(self, version: str):
        """
        Simple python version dump
        """
        self.logger.info(self.task.emoji, self.task.description)
        with self.main_output.open("w") as f:
            f.write(version)


class PythonSupportedVersionsResolver(NmkListConfigResolver):
    """
    Supported python versions range resolver
    """

    def get_value(self, name: str) -> list[str]:
        """
        Returns supported python versions range

        :return: list of all python versions between min and max supported versions
        """

        def _split_version(v: str) -> list[int]:
            return list(map(int, v.split(".")))

        # Get min/max values, and verify consistency
        min_ver, max_ver = self.model.config["pythonMinVersion"].value, self.model.config["pythonMaxVersion"].value
        min_split, max_split = _split_version(min_ver), _split_version(max_ver)
        prefix = "Inconsistency in python min/max supported versions: "
        assert len(min_split) == len(max_split), prefix + "not the same segments count"
        assert len(min_split) == 2, prefix + "can only deal with X.Y versions (2 segments expected)"
        assert min_split[0] == max_split[0], prefix + "can't deal with different major versions"
        assert max_split[1] > min_split[1], prefix + "max isn't greater than min"

        # Also verifies current runtime is in range
        p_ver = platform.python_version()
        cur_split = _split_version(p_ver)
        assert cur_split[0] == max_split[0], prefix + f"current python major version ({p_ver}) doesn't match with supported versions range"
        assert min_split[1] <= cur_split[1] <= max_split[1], prefix + f"current python version ({p_ver}) is out of supported versions range"

        # Iterate and return versions range
        return [f"{min_split[0]}.{sub}" for sub in range(min_split[1], max_split[1] + 1)]
