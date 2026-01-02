import logging
import os
import re
import subprocess

import pathlib

import typer

from portal_tool.installer.configurators.configurator import Configurator


class WindowsConfigurator(Configurator):
    def __init__(self, yes: bool):
        logging.info("Running Windows 11 configurator")

    def _try_install_vcpkg_dependencies(self) -> None:
        pass

    def _install_package(self, packages: list[str]) -> None:
        raise NotImplementedError

    def _validate_compilers(self) -> None:
        typer.echo("Validating compilers...")

        clang_valid = False
        msvc_valid = False

        try:
            result = subprocess.run(
                ["clang", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                match = re.search(r"clang version (\d+)\.(\d+)", result.stdout)
                installation_path = re.search("InstalledDir: (.*)", result.stdout)
                if match:
                    major = int(match.group(1))
                    if major >= 19:
                        path_info = (
                            f" ({installation_path.group(1)})"
                            if installation_path
                            else ""
                        )
                        typer.echo(f"Clang {major}.{match.group(2)} found{path_info}")
                        clang_valid = True
                    else:
                        typer.echo(
                            f"Clang {major}.{match.group(2)} found, but version 19+ is required"
                        )
        except (subprocess.SubprocessError, FileNotFoundError):
            typer.echo("Clang not found")

        try:
            program_files_x86_path = os.environ.get("ProgramFiles(x86)", "")
            vs_where_path = (
                pathlib.Path(program_files_x86_path)
                / "Microsoft Visual Studio"
                / "Installer"
                / "vswhere.exe"
            )

            result = subprocess.run(
                [vs_where_path], capture_output=True, text=True, timeout=5
            )

            output = result.stdout + result.stderr
            match = re.search(r"installationVersion: (\d+)\.(\d+).(\d+)\.(\d+)", output)
            installation_path = re.search("installationPath: (.*)", output)
            if match:
                major = int(match.group(1))
                minor = int(match.group(2))
                version_str = f"{major}.{minor}"
                if major >= 17:
                    path_info = (
                        f" ({installation_path.group(1)})" if installation_path else ""
                    )
                    typer.echo(f"MSVC {version_str} found{path_info}")
                    msvc_valid = True
                else:
                    typer.echo(f"MSVC {version_str} found, but version 17+ is required")
        except (subprocess.SubprocessError, FileNotFoundError):
            typer.echo("MSVC not found")

        if not clang_valid and not msvc_valid:
            typer.echo("\nNo valid compiler found!")
            typer.echo("Please install at least one of the following:")
            typer.echo("  - Clang 19 or later")
            typer.echo("        can be installed from here https://releases.llvm.org/")
            typer.echo("  - MSVC 17 or later")
            typer.echo(
                "        can be installed from here https://visualstudio.microsoft.com/downloads/"
            )
            raise typer.Abort("Compiler validation failed")

        typer.echo("Compiler validation successful!")

    def _validate_uv(self) -> None:
        # Check for a valid uv version
        proceed = False
        try:
            subprocess.check_output(["uv", "--version"])
            typer.echo("UV found, skipping installation")
            proceed = False
        except (subprocess.SubprocessError, FileNotFoundError):
            proceed = typer.confirm(
                "UV not found, would you like to install it?", abort=True
            )

        if proceed:
            typer.echo("Installing UV...")
            subprocess.run(
                [
                    "powershell",
                    "-ExecutionPolicy",
                    "ByPass",
                    "-c",
                    "irm https://astral.sh/uv/install.ps1 | iex",
                ],
                check=True,
            )
            typer.echo("UV installation successful")

    def _get_script_extension(self) -> str:
        return "bat"

    def _get_executable_extension(self) -> str:
        return ".exe"

    def _validate_dependencies(self) -> None:
        # Windows does not have any dependencies that need validating
        typer.echo("No dependencies to validate!")
