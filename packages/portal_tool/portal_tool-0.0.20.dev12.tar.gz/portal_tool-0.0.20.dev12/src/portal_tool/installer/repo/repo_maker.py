import importlib
import importlib.util
import json
import os
import pathlib
import platform
import shlex
import shutil
import subprocess
import zipimport

import typer
from cookiecutter.main import cookiecutter

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
        self.base_path = pathlib.Path(
            typer.prompt(f"Base Location (will create a folder named {self.name.lower().replace(' ', '_')})",
                         default=path))
        self.project_path = self.base_path / self.name.lower().replace(' ', '_')

        self.vcpkg_toolchain_location = "{}/scripts/buildsystems/vcpkg.cmake"
        self.use_global = False
        self.vcpkg_exec_location = pathlib.Path("")

        self._create_repo_from_template()
        self._configure_git()
        self._setup_vcpkg()
        self._configure_build_system()

    def _find_pacakge_path(self) -> pathlib.Path:
        source_path = "templates/repo/bootstrap"
        spec = importlib.util.find_spec("portal_tool")
        assert spec is not None, "An import spec was not found for the package."
        loader = spec.loader
        assert loader is not None, "A loader was not found for the package."

        if isinstance(loader, zipimport.zipimporter):
            self._archive = loader.archive
            pkgdir = next(iter(spec.submodule_search_locations))  # type: ignore
            template_root = os.path.join(pkgdir, source_path).rstrip(os.path.sep)
        else:
            roots: list[str] = []

            # One element for regular packages, multiple for namespace
            # packages, or None for single module file.
            if spec.submodule_search_locations:
                roots.extend(spec.submodule_search_locations)
            # A single module file, use the parent directory instead.
            elif spec.origin is not None:
                roots.append(os.path.dirname(spec.origin))

            if not roots:
                raise ValueError(
                    f"The portal_tool package was not installed in a"
                    " way that PackageLoader understands."
                )

            for root in roots:
                root = os.path.join(root, source_path)

                if os.path.isdir(root):
                    template_root = root
                    break
            else:
                raise ValueError(
                    f"PackageLoader could not find a {source_path!r} directory"
                    f" in the portal_tool package."
                )
        return pathlib.Path(template_root)

    def _create_repo_from_template(self) -> None:
        if self.project_path.exists():
            proceed = typer.confirm(
                "Found existing project, would you like to continue? (delete folder)"
            )
            if not proceed:
                raise typer.Abort("Aborting repo creation.")
            return

        cookiecutter(
            self._find_pacakge_path().as_posix(),
            no_input=True,
            extra_context={"project_name": self.name},
            output_dir=self.base_path.as_posix(),
        )

    def _configure_git(self) -> None:
        typer.echo(f"Initializing git repo in: {self.project_path}")
        subprocess.check_output(shlex.split(f'git -C "{self.project_path}" init'))

    def _setup_vcpkg(self) -> None:
        vcpkg_root, found_using_env = self.configurator.find_vcpkg_root()

        self.use_global = False
        if vcpkg_root:
            self.use_global = typer.confirm(
                f"Found global vcpkg, [{vcpkg_root}] would you like to use? (if not, a local submodule will be created)"
            )

        if not self.use_global:
            typer.echo(f"Creating vcpkg submodule in: {self.project_path / 'vcpkg'}")
            try:
                subprocess.check_output(
                    shlex.split(
                        f'git -C "{self.project_path}" submodule add https://github.com/microsoft/vcpkg "{"vcpkg"}"'
                    )
                )
                subprocess.check_output(f'{self.project_path.as_posix()}/vcpkg/bootstrap-vcpkg.{self.configurator.get_script_extension()}', shell=True)
                self.vcpkg_exec_location = self.project_path / "vcpkg" / f"vcpkg{self.configurator.get_executable_extension()}"
            except subprocess.CalledProcessError:
                typer.echo("Failed to add submodule, please add it manually.")
        else:
            self.vcpkg_exec_location = vcpkg_root / f"vcpkg{self.configurator.get_executable_extension()}"

        self.vcpkg_toolchain_location = self.vcpkg_toolchain_location.format(
            (
                "$env{VCPKG_ROOT}"
                if found_using_env
                else (pathlib.Path(os.path.expanduser("~")) / ".vcpkg").as_posix()
            )
            if self.use_global
            else "${sourceDir}/vcpkg"
        )

    def _configure_build_system(self) -> None:
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

        # TODO: support clang
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
                name="debug", configure_preset=ninja_multi.name, configuration="Debug"
            ),
            BuildPreset(
                name="development",
                configure_preset=ninja_multi.name,
                configuration="RelWithDebInfo",
            ),
            BuildPreset(
                name="release",
                configure_preset=ninja_multi.name,
                configuration="Release",
            ),
        ]

        (self.project_path / "CMakePresets.json").write_text(
            self.presets.model_dump_json(indent=4, exclude_none=True, by_alias=True)
        )

        vcpkg_config = {
            "registries": [
                {
                    "kind": "git",
                    "repository": "https://github.com/JonatanNevo/portal-vcpkg-registry",
                    "reference": "main",
                    "baseline": "07f01155c58797765efee4f55a4acaf621cee5da",
                    "packages": ["portal-core", "portal-application", "portal-input", "portal-networking",
                                 "portal-serialization", "portal-engine", "enchantum", "spdlog", "glaze", "llvm-adt"]
                }
            ]
        }

        (self.project_path / "vcpkg_configuration.json").write_text(json.dumps(vcpkg_config, indent=4))

        subprocess.check_output(shlex.split(f"{self.vcpkg_exec_location.as_posix()} x-update-baseline"))
