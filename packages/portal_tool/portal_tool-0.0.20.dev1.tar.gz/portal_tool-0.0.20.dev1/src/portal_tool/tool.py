import logging
import pathlib
from typing import Annotated

import appdirs
import typer
from pydantic_settings import BaseSettings

from portal_tool.installer.repo.repo_maker import RepoMaker
from portal_tool.installer.installer import Installer
from portal_tool.git_manager import GitManager
from portal_tool.models import PortalFramework
from portal_tool.vcpkg_port import (
    update_registry,
    generate_vcpkg_configuration,
    update_vcpkg_versions,
)

global_working_directory = pathlib.Path.cwd()
framework: PortalFramework


class Settings(BaseSettings):
    registry_url: str = "github.com:JonatanNevo/portal-vcpkg-registry"
    examples_url: str = "github.com:JonatanNevo/portal-examples"


def registry_start(
    working_dir: Annotated[
        pathlib.Path,
        typer.Option(
            "-d", "--working-dir", help="The working directory of the project"
        ),
    ] = pathlib.Path.cwd(),
    framework_path: Annotated[
        pathlib.Path | None,
        typer.Option(
            "-f", "--framework-path", help="The path to the framework.json file"
        ),
    ] = None,
    force_update_framework: Annotated[
        bool,
        typer.Option(
            "-u", "--force-update-framework", help="Force update the framework"
        ),
    ] = False,
):
    global framework
    global global_working_directory
    global_working_directory = working_dir

    user_data_path = pathlib.Path(appdirs.user_data_dir("portal-tool"))

    if framework_path is not None:
        framework = PortalFramework.model_validate_json(framework_path.read_text())
    elif (working_dir / "framework.json").exists() and not force_update_framework:
        framework = PortalFramework.model_validate_json(
            (working_dir / "framework.json").read_text()
        )
    elif (user_data_path / "framework.json").exists() and not force_update_framework:
        framework = PortalFramework.model_validate_json(
            (user_data_path / "framework.json").read_text()
        )
    else:
        # TODO: get from git as well?
        raise FileNotFoundError(
            "No framework.json found in working directory or user data directory"
        )

    GitManager().init_repo(framework)


def registry_end(*args, **kwargs) -> None:
    user_data_path = pathlib.Path(appdirs.user_data_dir("portal-tool"))
    (user_data_path / "framework.json").write_text(framework.model_dump_json(indent=4))


registry = typer.Typer(callback=registry_start, result_callback=registry_end)


@registry.command()
def update() -> None:
    update_registry(global_working_directory, framework)


@registry.command()
def update_versions() -> None:
    update_vcpkg_versions(global_working_directory)


@registry.command()
def create_config() -> None:
    generate_vcpkg_configuration(global_working_directory, framework)


app = typer.Typer()
app.add_typer(registry, name="registry", help="Commands for managing the registry")


@app.command()
def install(
    dependencies_only: Annotated[
        bool,
        typer.Option(
            "--only-dependencies",
            help="Only installs the dependencies, skips all other stages",
        ),
    ] = False,
    auto_yes: Annotated[
        bool,
        typer.Option(
            "-y",
            "--yes",
            help="Automatically answer yes to all questions.",
        ),
    ] = False,
) -> None:
    installer = Installer(Settings().examples_url, Settings().registry_url, auto_yes)

    if dependencies_only:
        installer.install(False, True)
    else:
        installer.install(True, True)


@app.command()
def init(
    directory: Annotated[
        pathlib.Path,
        typer.Option("-d", "--dir", help="The directory to initialize the project in"),
    ] = pathlib.Path.cwd(),
) -> None:
    RepoMaker(directory)


@app.callback()
def main():
    logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    app()
