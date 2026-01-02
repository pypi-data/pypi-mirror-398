import json
import logging
import pathlib
import shlex
import subprocess

import jinja2

from portal_tool.git_manager import GitManager
from portal_tool.models import PortalModule, PortDetails, PortalFramework


def enhance_portal_module(module: PortalModule) -> PortDetails:
    git_manager = GitManager()
    git_details = git_manager.to_details(subdirectory=module.short_name)
    version = git_manager.get_version(module.short_name)

    return PortDetails(
        name=module.name,
        version=version,
        short_name=module.short_name,
        description=module.description,
        license="MIT",  # TODO: get from repo
        git=git_details,
        options=module.options,
        dependencies=[dep.model_dump() for dep in module.dependencies],
        features=module.features,
    )


def make_vcpkg_json(changes: bool, port: PortDetails, json_path: pathlib.Path) -> None:
    old_vcpkg_json = json.loads(json_path.read_text() if json_path.exists() else "{}")

    json_details = {
        "name": port.name,
        "version": port.version,
        "description": port.description,
        "license": port.license,
        "dependencies": [
            {
                "name": dep.name,
                "features": dep.features,
                "version>=": dep.version,
            }
            for dep in port.dependencies
        ]
        + [
            {"name": "vcpkg-cmake", "host": True},
            {"name": "vcpkg-cmake-config", "host": True},
        ],
    }
    if port.features:
        json_details["features"] = {}
        for feature in port.features:
            feature_json = {"description": feature.description}
            if feature.dependencies:
                feature_json["dependencies"] = feature.dependencies
            json_details["features"][feature.name] = feature_json

    if changes and json_details["version"] == old_vcpkg_json.get("version"):
        json_details["port-version"] = old_vcpkg_json.get("port-version", 0) + 1

    json_path.write_text(json.dumps(json_details, indent=4))


def generate_vcpkg_port(details: PortDetails, output_path: pathlib.Path) -> None:
    env = jinja2.environment.Environment(
        loader=jinja2.PackageLoader("portal_tool", "templates/vcpkg"),
    )

    if details.features:
        cmake_template = env.get_template("portfile.cmake-features.j2")
    else:
        cmake_template = env.get_template("portfile.cmake.j2")

    cmake = cmake_template.render(port=details)
    usage_template = env.get_template("usage.j2")
    usage = usage_template.render(port=details)

    port_path = output_path / "ports" / details.name
    if not port_path.exists():
        port_path.mkdir(parents=True)

    logging.info(f"Generating vcpkg port at: {port_path}")

    port_file = port_path / "portfile.cmake"
    vcpkg_file = port_path / "vcpkg.json"
    usage_file = port_path / "usage"

    old_port_file_data = port_file.read_text() if port_file.exists() else ""
    changed_detected = old_port_file_data != cmake
    port_file.write_text(cmake)
    make_vcpkg_json(changed_detected, details, vcpkg_file)
    usage_file.write_text(usage)

    subprocess.check_output(shlex.split(f'vcpkg format-manifest "{vcpkg_file}"'))


GLOBAL_PORTS = [
    PortalModule(name="enchantum"),
    PortalModule(name="spdlog"),
    PortalModule(name="glaze"),
    PortalModule(name="llvm-adt"),
]


def generate_vcpkg_configuration(output_path: pathlib.Path, framework: PortalFramework):
    git_manager = GitManager()
    env = jinja2.environment.Environment(
        loader=jinja2.PackageLoader("portal_tool", "templates/vcpkg"),
    )
    template = env.get_template("vcpkg-configuration.json.j2")
    rendered = template.render(
        ports=framework.modules + GLOBAL_PORTS, registry_ref=git_manager.registry_commit
    )

    with open(output_path / "vcpkg-configuration.json", "w") as f:
        f.write(rendered)


def update_registry(output_path: pathlib.Path, framework: PortalFramework) -> None:
    logging.info(f"Updating vcpkg registry at: {output_path.absolute()}")
    GitManager().validate_modules_versions(framework.modules)
    for module in framework.modules:
        port = enhance_portal_module(module)
        generate_vcpkg_port(port, output_path)


def update_vcpkg_versions(output_path: pathlib.Path) -> None:
    output = subprocess.check_output(
        shlex.split(
            f'vcpkg --x-builtin-ports-root="{output_path / "ports"}" --x-builtin-registry-versions-dir="{output_path / "versions"}" x-add-version --all --verbose'
        )
    )
    print(output.decode())
