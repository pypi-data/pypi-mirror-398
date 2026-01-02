from typing import Union, Literal

from pydantic import BaseModel, Field


class CMakeVersion(BaseModel):
    major: int = 3
    minor: int = 23
    patch: int = 0


class Condition(BaseModel):
    type: str
    lhs: str
    rhs: str


class CacheVariable(BaseModel):
    type: str
    value: str


class ConfigurePreset(BaseModel):
    name: str
    hidden: bool | None = None
    inherits: list[str] | None = None
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = None
    generator: str | None = None
    binary_dir: str | None = Field(default=None, alias="binaryDir")
    cache_variables: dict[str, Union[str, CacheVariable]] | None = Field(
        default=None, alias="cacheVariables"
    )
    environment: dict[str, str] | None = None
    condition: Condition | None = None


class BuildPreset(BaseModel):
    name: str
    configure_preset: str = Field(alias="configurePreset")
    inherit_configure_environment: bool | None = Field(
        default=None, alias="inheritConfigureEnvironment"
    )
    jobs: int | None = None
    targets: list[str] | None = Field(default=None)
    configuration: str | None = None
    clean_first: bool | None = Field(default=None, alias="cleanFirst")
    verbose: bool | None = None
    hidden: bool = Field(default=False)
    inherits: list[str] | None = Field(default=None)
    condition: Condition | None = None
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = Field(default=None)
    environment: dict[str, str] | None = Field(default=None)


class TestPreset(BaseModel):
    name: str
    configure_preset: str = Field(alias="configurePreset")
    inherit_configure_environment: bool | None = Field(
        default=None, alias="inheritConfigureEnvironment"
    )
    configuration: str | None = None
    hidden: bool = Field(default=False)
    inherits: list[str] | None = Field(default=None)
    condition: Condition | None = None
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = Field(default=None)
    environment: dict[str, str] | None = Field(default=None)


class PackagePreset(BaseModel):
    name: str
    hidden: bool = Field(default=False)
    inherits: list[str] | None = Field(default=None)
    condition: Condition | None = None
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = Field(default=None)
    environment: dict[str, str] | None = Field(default=None)
    configure_preset: str = Field(alias="configurePreset")
    inherit_configure_environment: bool | None = Field(
        default=None, alias="inheritConfigureEnvironment"
    )
    generators: list[str] | None = Field(default=None)
    configurations: list[str] | None = Field(default=None)
    variables: list[str] | None = Field(default=None)
    config_file: str | None = Field(default=None, alias="configFile")
    package_name: str | None = Field(default=None, alias="packageName")
    package_version: str | None = Field(default=None, alias="packageVersion")
    package_directory: str | None = Field(default=None, alias="packageDirectory")


class WorkflowStep(BaseModel):
    type: Literal["configure", "build", "test", "package"]
    name: str


class WorkflowPreset(BaseModel):
    name: str
    steps: list[WorkflowStep]
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = Field(default=None)


class CMakePresets(BaseModel):
    version: int = 9
    cmake_minimum_required: CMakeVersion = Field(
        default_factory=CMakeVersion, alias="cmakeMinimumRequired"
    )
    configure_presets: list[ConfigurePreset] | None = Field(
        default=None, alias="configurePresets"
    )
    build_presets: list[BuildPreset] | None = Field(default=None, alias="buildPresets")
    test_presets: list[TestPreset] | None = Field(default=None, alias="testPresets")
    package_presets: list[PackagePreset] | None = Field(
        default=None, alias="packagePresets"
    )
    workflow_presets: list[WorkflowPreset] | None = Field(
        default=None, alias="workflowPresets"
    )
