from pydantic import BaseModel, Field


class GitDetails(BaseModel):
    repo: str
    ref: str
    sha: str
    head_ref: str
    subdirectory: str


class Dependency(BaseModel):
    name: str
    version: str
    features: list[str] = Field(default_factory=list)


class Feature(BaseModel):
    name: str
    description: str
    dependencies: list[str] = Field(default_factory=list)


class PortDetails(BaseModel):
    name: str
    short_name: str
    version: str
    description: str
    license: str = Field(default="MIT")
    git: GitDetails = Field(default_factory=GitDetails)
    options: list[str] = Field(default_factory=list)
    dependencies: list[Dependency] = Field(default_factory=list)
    features: list[Feature] = Field(default_factory=list)


class PortalModule(BaseModel):
    name: str
    short_name: str = ""
    target_override: str | None = None
    version: str = ""
    description: str = ""
    options: list[str] = Field(default_factory=list)
    dependencies: list[Dependency] = Field(default_factory=list)
    features: list[Feature] = Field(default_factory=list)


class PortalFramework(BaseModel):
    repo: str
    repo_branch: str | None = None
    vcpkg_registry_repo: str
    modules: list[PortalModule] = Field(default_factory=list)


class GitStatus(BaseModel):
    repo: str | None = None
    branch: str | None = None
    commit: str | None = None
    sha: str | None = None


class LocalStatus(BaseModel):
    framework: GitStatus = Field(default_factory=GitStatus)
    registry: GitStatus = Field(default_factory=GitStatus)
