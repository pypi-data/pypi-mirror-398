"""
File resolvers sub-module
"""

from pathlib import Path

from nmk.model.keys import NmkRootConfig
from nmk.model.resolver import NmkListConfigResolver


class ProtoFilesFinder(NmkListConfigResolver):
    """
    Input proto files resolver
    """

    def get_value(self, name: str, folder: str) -> list[Path]:
        """
        List all proto files found in input folder

        :param name: config item name
        :param folder: root proto folder
        :return: list of input proto files
        """

        # Iterate on source paths, and find all proto files
        return list(filter(lambda f: f.is_file(), Path(folder).rglob("*.proto")))


class ProtoAllSubDirsFinder(NmkListConfigResolver):
    """
    Proto subfolders list resolver
    """

    def get_value(self, name: str, folder: str, input_files: list[Path]) -> list[Path]:
        """
        List all proto sub-folders (one per file)

        :param name: config item name
        :param folder: root proto folder
        :param input_files: list of all input proto files
        :return: list of proto sub-folders
        """

        # All sub-folders, relative to proto folder (exactly one per proto file)
        root = Path(folder)
        return [p.parent.relative_to(root) for p in input_files]


class ProtoUniqueSubDirsFinder(NmkListConfigResolver):
    """
    Proto subfolders set resolver
    """

    def get_value(self, name: str, input_subdirs: list[Path]) -> list[Path]:
        """
        List all proto sub-folders (no duplicates)

        :param name: config item name
        :param input_subdirs: list of all subdirs relative to proto root folder
        :return: set of proto sub-folders
        """
        # Set filtered subfolders
        return sorted(list(set(input_subdirs)))


class ProtoPathOptionsBuilder(NmkListConfigResolver):
    """
    Paths options list resolver
    """

    def _make_relative(self, p: Path) -> Path:
        # Make it project relative if possible
        if p.is_absolute():  # pragma: no branch
            try:
                return p.relative_to(self.model.config[NmkRootConfig.PROJECT_DIR].value)
            except ValueError:  # pragma: no cover
                # Simply ignore, non project-relative
                pass
        return p  # pragma: no cover

    def get_value(self, name: str, folder: str, deps: list[str]) -> list[str]:
        """
        Build path options list for protoc command

        :param name: config item name
        :param folder: root proto folder
        :param deps: list of extra proto paths for generation
        :return: list of path options
        """

        # Return a list of protoc path options
        out = []
        root = Path(folder)
        for p in map(self._make_relative, [root] + [Path(d) for d in deps]):
            out.extend(["--proto_path", p.as_posix()])
        return out
