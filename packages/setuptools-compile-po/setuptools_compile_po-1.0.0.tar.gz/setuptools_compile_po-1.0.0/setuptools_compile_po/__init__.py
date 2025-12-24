import os
from shutil import which

from setuptools import Command
from setuptools.command.build import build
from setuptools.command.sdist import log
from setuptools.config.pyprojecttoml import load_file
from setuptools.dist import Distribution
from setuptools.errors import ExecError


class compile_po_mixin:
    """Compile po mixin."""

    def init_build_mo_directory(self):
        self.build_mo_directory = self.distribution.build_mo_directory
        if self.build_mo_directory is None:
            self.build_mo_directory = os.path.join(self.distribution.packages[0], "locale")

    def initialize_options(self):
        super().initialize_options()
        self.build_mo_directory = None

    def finalize_options(self):
        super().finalize_options()
        self.init_build_mo_directory()

    def create_mo(self, po: str) -> str:
        raise NotImplementedError()

    def run(self):
        """Run msgfmt for each language."""
        msgfmt = self.distribution.msgfmt
        if which(msgfmt) is None:
            raise ExecError(f"Command '{msgfmt}' was not found. Please install gettext.")
        for root, _dirs, files in os.walk(self.build_mo_directory):
            for name in files:
                ext = name.split(".")[-1]
                if ext == "po":
                    po = os.path.join(root, name)
                    mo = self.create_mo(po)
                    self.spawn([msgfmt, "-o", mo, po])


class build_mo(compile_po_mixin, build):
    """Subcommand of build command: build_mo."""

    description = "Compile po files to mo files."

    def create_mo(self, po: str) -> str:
        return os.path.join(self.build_lib, po[:-3]) + ".mo"


class sdist_mo(compile_po_mixin, Command):
    """Source distribution mo files."""

    description = "Source distribution mo files."

    def initialize_options(self):
        self.build_mo_directory = None

    def finalize_options(self):
        self.init_build_mo_directory()

    def create_mo(self, po: str) -> str:
        filepath = os.path.join(self.distribution.get_fullname(), po[:-3]) + ".mo"
        folders = os.path.dirname(filepath)
        if not os.path.isdir(folders):
            log.info("creating %s", folders)
            os.makedirs(folders)
        return filepath


def set_subcommands(dist: Distribution) -> None:
    filename = "pyproject.toml"
    params = load_file(filename).get("tool", {}).get("setuptools_compile_po", {}) if os.path.isfile(filename) else {}
    dist.msgfmt = params.get("msgfmt", "msgfmt")
    dist.build_mo_directory = params.get("directory")
    build = dist.get_command_class("build")
    sdist = dist.get_command_class("sdist")
    build.sub_commands.append(("build_mo", lambda x: True))
    sdist.sub_commands.append(("sdist_mo", lambda x: True))
