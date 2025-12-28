"""
Python package build module
"""

import shutil
import sys
from logging import Logger
from pathlib import Path

from nmk.model.builder import NmkTaskBuilder
from nmk.model.keys import NmkRootConfig
from nmk.model.resolver import NmkListConfigResolver, NmkStrConfigResolver
from nmk.utils import is_windows, run_pip, run_with_logs
from nmk_base.venvbuilder import VenvUpdateBuilder
from tomlkit import loads
from tomlkit.toml_file import TOMLFile


# Install filter for Windows
def _can_install(name: str, logger: Logger) -> bool:
    # On Windows, refuse to install nmk package while running nmk (wont' work)
    if is_windows() and name == "nmk":
        logger.warning("Can't install nmk while running nmk!")
        return False
    return True


class PackageBuilder(NmkTaskBuilder):
    """
    Python package builder
    """

    def build(self, project_file: str, version_file: str, source_dirs: list[str], artifacts_dir: str, build_dir: str, extra_resources: dict[str, str]):
        """
        Delegate to python build module, from a temporary build folder

        :param project_file: path to python project file
        :param version_file: path to generated version file
        :param source_dirs: list of source folders for this wheel
        :param artifacts_dir: output folder for built wheel
        :param build_dir: temporary build folder
        :param extra_resources: dictionary of extra resources mapping (original path -> target path)
        """

        # Prepare build folder
        build_path = Path(build_dir)
        if build_path.is_dir():
            shutil.rmtree(build_path)
        build_path.mkdir(exist_ok=True, parents=True)

        # Copy source folders and various project files
        project_root = Path(self.model.config[NmkRootConfig.PROJECT_DIR].value)
        for source_dir in map(Path, source_dirs):
            shutil.copytree(source_dir, build_path / source_dir.relative_to(project_root))
        for candidate in filter(lambda p: p.is_file(), map(Path, [project_file, version_file, project_root / "README.md", project_root / "LICENSE"])):
            shutil.copyfile(candidate, build_path / candidate.name)

        # Update project file with version
        build_project = build_path / Path(project_file).name
        build_version = build_path / Path(version_file).name
        with build_project.open() as f:
            project_doc = loads(f.read())
        dyn_table = project_doc.get("tool").get("setuptools").get("dynamic")
        dyn_table["version"] = {"file": build_version.name}
        project_output = TOMLFile(build_project)
        project_output.write(project_doc)

        # Handle extra resources
        for src, dst in extra_resources.items():
            src_path, dst_path = Path(src), Path(dst)
            if not src_path.is_absolute():  # pragma: no branch
                src_path = project_root / src_path
            if not dst_path.is_absolute():  # pragma: no branch
                dst_path = project_root / dst_path
            assert src_path.exists(), f"Required extra resource path not found: {src_path}"
            dst_path = build_path / dst_path.relative_to(project_root)
            dst_path.mkdir(exist_ok=True, parents=True)
            if src_path.is_file():
                # Single file copy
                self.logger.debug(f"Copy extra resource file: {src_path} --> {dst_path}")
                shutil.copyfile(src_path, dst_path / src_path.name)
            else:
                # Directory copy
                self.logger.debug(f"Copy extra resource tree: {src_path} --> {dst_path}")
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

        # Prepare artifacts folder
        artifacts_path = Path(artifacts_dir)
        artifacts_path.mkdir(exist_ok=True, parents=True)
        for wheel in artifacts_path.glob("*.whl"):
            wheel.unlink()

        # Delegate to build module
        run_with_logs(
            [sys.executable, "-m", "build", "--wheel", "--skip-dependency-check", "--no-isolation"],
            self.logger,
            cwd=build_path,
        )

        # Copy wheel to artifacts folder
        target_wheel = self.main_output
        built_wheel = build_path / "dist" / target_wheel.name
        assert built_wheel.is_file(), f"Expected built wheel not found: {built_wheel}"
        shutil.copyfile(built_wheel, target_wheel)


class PythonModuleResolver(NmkStrConfigResolver):
    """
    Python module name resolver
    """

    def get_value(self, name: str) -> str:
        """
        Return module name from package (i.e. wheel) name
        """
        return self.model.config["pythonPackage"].value.replace("-", "_")


class Installer(VenvUpdateBuilder):
    """
    Install built wheel in venv
    """

    def build(self, name: str, pip_args: list[str], to_remove: str):
        """
        Install wheel in venv

        :param name: wheel name to be installed
        :param pip_args: pip command line arguments
        :param to_remove: stamp file to be removed
        """

        # Check if wheel can be installed
        if _can_install(name, self.logger):
            # Install wheel in current venv
            super().build(" ".join(pip_args))

            # Remove stamp file
            Path(to_remove).unlink(missing_ok=True)


class Uninstaller(NmkTaskBuilder):
    """
    Uninstall current project wheel from venv
    """

    def build(self, name: str):
        """
        Uninstall wheel from venv

        Note that task won't fail if the wheel is not installed

        :param name: wheel name to be uninstalled
        """

        # Simply delegate to pip
        run_pip(["uninstall", "--yes", name], logger=self.logger)


class EditableBuilder(NmkTaskBuilder):
    """
    Install python project in editable mode
    """

    def build(self, pip_args: list[str]):
        """
        Install project in venv as editable package

        :param pip_args: pip command line arguments
        """

        # Check if project can be installed in editable mode
        if _can_install(self.model.config["pythonPackage"].value, self.logger):
            # Delegate to pip
            run_pip(["install", "-e", "."], logger=self.logger, extra_args=" ".join(pip_args))

            # Touch stamp file
            self.main_output.touch()


class PythonOptionalDepsResolver(NmkListConfigResolver):
    """
    Python optional deps resolver
    """

    def get_value(self, name: str, groups: dict[str, list[str]]) -> list[str]:
        """
        Turn dependency options deps dict into a merged list of dependencies
        """
        return sorted(list(set(dependency for deps in groups.values() for dependency in deps)))
