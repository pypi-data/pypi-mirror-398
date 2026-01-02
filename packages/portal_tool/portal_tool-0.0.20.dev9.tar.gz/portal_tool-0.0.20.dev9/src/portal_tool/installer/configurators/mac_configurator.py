import logging

import typer

from portal_tool.installer.configurators.configurator import Configurator


class MacConfigurator(Configurator):
    def __init__(self, yes: bool):
        logging.info("Running MacOs configurator")

    def _try_install_vcpkg_dependencies(self) -> None:
        pass

    def _install_package(self, packages: list[str]) -> None:
        raise NotImplementedError

    def _validate_compilers(self) -> None:
        typer.echo("Missing compiler validation, skipping...")

    def get_script_extension(self) -> str:
        return "sh"

    def get_executable_extension(self) -> str:
        return ""

    def _validate_dependencies(self) -> None:
        typer.echo("No dependencies to validate!")
