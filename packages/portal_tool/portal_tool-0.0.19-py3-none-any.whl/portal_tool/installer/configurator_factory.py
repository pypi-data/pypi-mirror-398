import platform
from dataclasses import dataclass

from portal_tool.installer.configurators.configurator import Configurator
from portal_tool.installer.configurators.linux_configurator import LinuxConfigurator
from portal_tool.installer.configurators.mac_configurator import MacConfigurator
from portal_tool.installer.configurators.windows_configurator import WindowsConfigurator


@dataclass(frozen=True)
class PlatformDetails:
    name: str
    version: str


class ConfiguratorFactory:
    def __init__(self):
        self.configurators = {
            "Windows": WindowsConfigurator,
            "Linux": LinuxConfigurator,
            "Darwin": MacConfigurator,
        }

    def create(self, yes: bool) -> Configurator:
        local_details = PlatformDetails(platform.system(), str(platform.version()))

        system_configurator = self.configurators.get(local_details.name)
        if system_configurator is None:
            raise ValueError(f"Unsupported platform: {local_details.name}")

        return system_configurator(yes)
