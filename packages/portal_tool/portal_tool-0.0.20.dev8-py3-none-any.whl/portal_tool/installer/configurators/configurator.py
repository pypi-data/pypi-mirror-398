import abc
import os

import pathlib
import shlex
import shutil
import subprocess

import typer


class Configurator(metaclass=abc.ABCMeta):
    def configure_vcpkg(self) -> None:
        typer.echo("Configuring vcpkg...")
        root, _ = self.find_vcpkg_root()
        if root is None:
            typer.echo("Failed to find global vcpkg.")
            self._try_install_vcpkg()
        else:
            typer.echo(f"Global vcpkg found at: {root}")

    def find_vcpkg_root(self) -> tuple[pathlib.Path, bool] | tuple[None, None]:
        value = os.environ.get("VCPKG_ROOT")
        if value is None:
            installed_vcpkg = pathlib.Path(os.path.expanduser("~")) / ".vcpkg"
            if (
                installed_vcpkg.exists()
                and (
                    installed_vcpkg / f"vcpkg{self.get_executable_extension()}"
                ).exists()
            ):
                return installed_vcpkg, False
        return (pathlib.Path(value), True) if value else (None, None)

    def configure_build_environment(self) -> None:
        typer.echo("Configuring build environment...")
        self._validate_compilers()
        self._validate_cmake()
        self._validate_dependencies()

    def _try_install_vcpkg(self) -> None:
        install_vcpkg = typer.confirm("Would you like to install vcpkg?")
        if not install_vcpkg:
            raise typer.Abort(
                "No vcpkg installation, please install it manually and try again."
            )

        self._try_install_vcpkg_dependencies()

        installation_directory = pathlib.Path(
            typer.prompt(
                "Choose installation directory:",
                default=os.path.join(os.path.expanduser("~"), ".vcpkg"),
            )
        )
        if installation_directory.exists():
            override = typer.confirm("Folder exists, overwrite?")
            if not override:
                raise typer.Abort("Installation aborted.")
            shutil.rmtree(installation_directory)

        subprocess.check_output(
            shlex.split(
                f'git clone https://github.com/microsoft/vcpkg "{installation_directory}"'
            )
        )
        typer.echo("Bootstrap vcpkg...")
        subprocess.check_output(
            shlex.split(
                f"{installation_directory}/bootstrap-vcpkg.{self.get_script_extension()}"
            )
        )
        typer.echo(f"Vcpkg installed successfully to: {installation_directory}")

    def _validate_cmake(self) -> None:
        pass

    @abc.abstractmethod
    def _validate_dependencies(self) -> None:
        pass

    @abc.abstractmethod
    def _try_install_vcpkg_dependencies(self) -> None:
        pass

    @abc.abstractmethod
    def get_script_extension(self) -> str:
        pass

    @abc.abstractmethod
    def get_executable_extension(self) -> str:
        pass

    @abc.abstractmethod
    def _install_package(self, packages: list[str]) -> None:
        pass

    @abc.abstractmethod
    def _validate_compilers(self) -> None:
        pass
