from portal_tool.installer.configurator_factory import ConfiguratorFactory


class Installer:
    def __init__(self, examples_url: str, registry_url: str, yes: bool):
        self.examples_url = examples_url
        self.registry_url = registry_url
        self.yes = yes

    def install(self, vcpkg: bool, environment: bool) -> None:
        configurator = ConfiguratorFactory().create(self.yes)

        if vcpkg:
            configurator.configure_vcpkg()

        if environment:
            configurator.configure_build_environment()
