"""
Python related resolvers and builders sub-module
"""

import importlib.resources
import re
import shutil
import sys
from pathlib import Path

from nmk.model.builder import NmkTaskBuilder
from nmk.model.keys import NmkRootConfig
from nmk.model.model import NmkModel
from nmk.model.resolver import NmkListConfigResolver
from nmk.utils import create_dir_symlink, run_with_logs
from nmk_base.common import TemplateBuilder

_ERROR_LINE_PATTERN = re.compile("^([^ ]+Error: )(.*)")


# Grab some config items
def _get_python_src_folder(model: NmkModel) -> Path:
    return Path(model.config["pythonSrcFolders"].value[0])


class OutputFoldersFinder(NmkListConfigResolver):
    """
    Generated python module folders resolver
    """

    def get_value(self, name: str, input_subdirs: list[str]) -> list[str]:
        """
        List all generated python module folders

        :param name: config item name
        :param input_subdirs: list of unique input subdirs
        :return: list of generated python module folders
        """

        # Do we have a python source folder?
        if "pythonSrcFolders" in self.model.config:
            target_src = _get_python_src_folder(self.model)

            # Rework list to add intermediate (empty) python packages
            whole_set = set()
            for p in input_subdirs:
                parts = list(Path(p).parts)
                for i in range(1, len(parts) + 1):
                    new_path = Path(*parts[:i])
                    whole_set.add(new_path)
            whole_list = sorted(list(whole_set))

            # Return all folder relative to python folder
            return [str(target_src / p) for p in whole_list]
        else:
            return []


class OutputPythonFilesFinder(NmkListConfigResolver):
    """
    Generated python files resolver
    """

    def get_value(self, name: str, folder: str, input_files: list[str], src_folders: list[str]) -> list[str]:
        """
        List all generated python files names

        :param name: config item name
        :param folder: root proto folder
        :param input_files: list of all input proto files
        :param src_folders: list of python generated source folders
        :return: list of generated files names
        """

        # Do we have python output folders
        if len(src_folders):
            # Grab some variables values
            target_src, proto_src = (_get_python_src_folder(self.model), Path(folder))

            # Convert source proto file names to python ones
            return [
                str(target_src / f"{str(p_file)[: -len(p_file.suffix)]}{suffix}.py")
                for p_file in [Path(p).relative_to(proto_src) for p in input_files]
                for suffix in ["_pb2", "_pb2_grpc"]
            ] + [str(Path(p) / "__init__.py") for p in src_folders]
        else:
            return []


class OutputProtoFilesFinder(NmkListConfigResolver):
    """
    Copied proto files resolver
    """

    def get_value(self, name: str, folder: str, input_files: list[str], src_folders: list[str]) -> list[str]:
        """
        List all names of proto files copied in python source directory

        :param name: config item name
        :param folder: root proto folder
        :param input_files: list of all input proto files
        :param src_folders: list of python generated source folders
        :return: list of copied proto files names
        """

        # Do we have python output folders
        if len(src_folders):
            # Grab some variables values
            target_src, proto_src = (_get_python_src_folder(self.model), Path(folder))

            # Copied proto file in python folder
            return [str(target_src / p_file) for p_file in [Path(p).relative_to(proto_src) for p in input_files]]
        else:
            return []


class OutputFoldersFinderWithWildcard(OutputFoldersFinder):
    """
    Generated python module wildcards resolver
    """

    def get_value(self, name: str, input_subdirs: list[str]) -> list[str]:
        """
        List all generated python module folders, with appended '/*' wildcard

        :param name: config item name
        :param input_subdirs: list of unique input subdirs
        :return: list of generated python module wildcards
        """

        # Same than parent, with a "*" wildcard
        return [f"{p}/*" for p in super().get_value(name, input_subdirs)]


class ProtoLinkBuilder(NmkTaskBuilder):
    """
    proto.link silent task builder
    """

    def build(self):
        """
        Create local project symbolic link to venv root
        """

        # Only if link is not created yet
        if not self.main_output.exists():
            # Source path: check for root folder of Jinja module
            src_path = Path(importlib.resources.files("jinja2")).parent

            # Prepare output parent if not exists yet
            self.main_output.parent.mkdir(exist_ok=True, parents=True)

            # Ready to create symlink
            create_dir_symlink(src_path, self.main_output)


class ProtoPythonBuilder(TemplateBuilder):
    """
    proto.gen.py task builder
    """

    def _make_absolute(self, option: str) -> Path:
        if not option.startswith("--") and not Path(option).is_absolute():
            return str(Path(self.model.config[NmkRootConfig.PROJECT_DIR].value) / option)
        return option

    def build(self, init_template: str, all_input_subdirs: list[str], options: list[str], src_folders: list[str], extra_args: list[str]):
        """
        Generate python files from input proto ones

        Iterates on input proto files, and call protoc tool to generate python files.
        Also generate __init__.py files for all generated modules, from provided template.

        :param init_template: path to __init__.py file template
        :param all_input_subdirs: list of all input subdirs (one per found proto file)
        :param options: list of proto paths options
        :param src_folders: list of python generated source folders
        :param extra_args: list of extra arguments for protoc command
        """

        # Grab some config items
        target_src, sub_folders = (_get_python_src_folder(self.model), all_input_subdirs)

        # Clean and re-create target folders
        for output_dir in src_folders:
            candidate_dir = target_src / output_dir
            if candidate_dir.is_dir():
                shutil.rmtree(candidate_dir)
            candidate_dir.mkdir(parents=True, exist_ok=True)

        # Build proto paths list
        proto_paths = [self._make_absolute(o) for o in options]

        # Iterate on inputs (proto files)
        for proto_file, target_subdir in zip(self.inputs, sub_folders, strict=True):
            # Delegate to protoc
            run_with_logs(
                [sys.executable, "-m", "grpc_tools.protoc"]
                + proto_paths
                + ["--python_out", str(target_src), "--pyi_out", str(target_src), "--grpc_python_out", str(target_src)]
                + extra_args
                + [str(proto_file)]
            )

            # Also simply copy proto file to output
            shutil.copyfile(proto_file, target_src / target_subdir / proto_file.name)

        # Reorder output files
        importable_files = {Path(out_folder).relative_to(target_src): [] for out_folder in src_folders}
        for candidate in [p.relative_to(target_src) for p in filter(lambda f: f.name.endswith("_pb2.py"), self.outputs)]:
            importable_files[candidate.parent].append(candidate.as_posix()[: -len(candidate.suffix)].replace("/", "."))

        # Browse importable packages
        for p, modules in importable_files.items():
            # Generate init file
            self.build_from_template(Path(init_template), target_src / p / "__init__.py", {"modules": modules})


class ProtoPythonChecker(NmkTaskBuilder):
    """
    proto.check.py task builder
    """

    def build(self, src_folders: list[str]):
        """
        Check generated python files import

        Verifies (for all generated python modules folders) that importing all generated
        files at once works well (typically to make sure there are no enum naming conflicts).

        :param src_folders: list of python module folders to be checked
        """

        target_src = _get_python_src_folder(self.model)
        for p in map(Path, src_folders):
            # Try to import, to verify any name overlap
            cp = run_with_logs([sys.executable, "-c", f"from {p.relative_to(target_src).as_posix().replace('/', '.')} import *"], check=False)
            if cp.returncode != 0:
                # Just print meaningfull error
                raise AssertionError(next(filter(lambda m: m is not None, map(_ERROR_LINE_PATTERN.match, cp.stderr.splitlines()))).group(2))
