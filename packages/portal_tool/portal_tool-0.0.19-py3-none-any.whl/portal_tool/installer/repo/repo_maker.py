import os
import pathlib
import platform
import shlex
import subprocess

import typer

from portal_tool.installer.configurator_factory import ConfiguratorFactory
from portal_tool.installer.repo.build_models import (
    CMakePresets,
    ConfigurePreset,
    BuildPreset,
)


class RepoMaker:
    """
    A repo consists of:
    - vcpkg (either submodule or globally installed)
    - src
    - resources
    - vcpkg configuration
    - cmake configuration
    """

    def __init__(self, path: pathlib.Path):
        self.configurator = ConfiguratorFactory().create(False)
        self.presets = CMakePresets()

        self.name = typer.prompt("Project Name")
        self.base_path = pathlib.Path(typer.prompt("Project Location", default=path))

        self.vcpkg_toolchain_location = "{}/scripts/buildsystems/vcpkg.cmake"

        self._configure_git()
        self._setup_vcpkg()
        self._create_repo_from_template()
        self._configure_build_system()

    def _configure_git(self) -> None:
        if (self.base_path / ".git").exists():
            proceed = typer.confirm(
                "Found existing git repo, would you like to continue?"
            )
            if not proceed:
                raise typer.Abort("Aborting repo creation.")
            return

        typer.echo(f"Initializing git repo in: {self.base_path}")
        subprocess.check_output(shlex.split(f'git -C "{self.base_path}" init'))

    def _setup_vcpkg(self) -> None:
        vcpkg_root, found_using_env = self.configurator.find_vcpkg_root()

        use_global = False
        if vcpkg_root:
            use_global = typer.confirm(
                f"Found global vcpkg, [{vcpkg_root}] would you like to use? (if not, a local submodule will be created)"
            )

        if not use_global:
            typer.echo(f"Creating vcpkg submodule in: {self.base_path / 'vcpkg'}")
            try:
                subprocess.check_output(
                    shlex.split(
                        f'git -C "{self.base_path}" submodule add https://github.com/microsoft/vcpkg "{"vcpkg"}"'
                    )
                )
            except subprocess.CalledProcessError:
                typer.echo("Failed to add submodule, please add it manually.")

        self.vcpkg_toolchain_location = self.vcpkg_toolchain_location.format(
            (
                "$env{VCPKG_ROOT}"
                if found_using_env
                else (pathlib.Path(os.path.expanduser("~")) / ".vcpkg").as_posix()
            )
            if use_global
            else "${sourceDir}/vcpkg"
        )

    def _create_repo_from_template(self) -> None:
        base = ConfigurePreset(
            name="base",
            hidden=True,
            binary_dir="${sourceDir}/build/${presetName}",
            cache_variables={
                "CMAKE_TOOLCHAIN_FILE": self.vcpkg_toolchain_location,
                "CMAKE_CONFIGURATION_TYPES": "Debug;RelWithDebInfo;Release",
            },
        )

        # TODO: determine generator (ninja-multi, xcode, vs)
        ninja_multi = ConfigurePreset(
            name="ninja-multi", inherits=[base.name], generator="Ninja Multi-Config"
        )

        if platform.system() == "Linux":
            ninja_multi.environment = {
                "CC": "clang",
                "CXX": "clang++",
                "VCPKG_KEEP_ENV_VARS": "CC;CXX",
                **(ninja_multi.environment if ninja_multi.environment else {}),
            }

        self.presets.configure_presets = [base, ninja_multi]

        self.presets.build_presets = [
            BuildPreset(
                name="debug", configurePreset=ninja_multi.name, configuration="Debug"
            ),
            BuildPreset(
                name="development",
                configurePreset=ninja_multi.name,
                configuration="RelWithDebInfo",
            ),
            BuildPreset(
                name="release",
                configurePreset=ninja_multi.name,
                configuration="Release",
            ),
        ]

        (self.base_path / "CMakePresets.json").write_text(
            self.presets.model_dump_json(indent=4, exclude_none=True)
        )

    def _configure_build_system(self) -> None:
        pass
