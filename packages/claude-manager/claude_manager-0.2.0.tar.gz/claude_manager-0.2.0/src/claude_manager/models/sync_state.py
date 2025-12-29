"""Pydantic models for synchronization state tracking."""

from datetime import datetime

from pydantic import BaseModel, Field


class AgentInstallation(BaseModel):
    """Tracking information for an installed agent."""

    library_version: str = Field(..., description="Version from the library")
    content_hash: str = Field(..., description="SHA256 hash of the content")
    installed_at: datetime = Field(
        default_factory=datetime.now, description="Installation timestamp"
    )
    last_synced: datetime | None = Field(default=None, description="Last sync check timestamp")


class MCPInstallation(BaseModel):
    """Tracking information for an installed MCP server."""

    version: str = Field(..., description="Installed version")
    source_type: str = Field(..., description="Source type (npm, github, etc.)")
    source_location: str = Field(..., description="Source location (package name or repo)")
    installed_at: datetime = Field(
        default_factory=datetime.now, description="Installation timestamp"
    )
    last_checked: datetime | None = Field(default=None, description="Last update check timestamp")


class CommandInstallation(BaseModel):
    """Tracking information for an installed command."""

    library_version: str = Field(..., description="Version from the library")
    content_hash: str = Field(..., description="SHA256 hash of the content")
    installed_at: datetime = Field(
        default_factory=datetime.now, description="Installation timestamp"
    )


class HookInstallation(BaseModel):
    """Tracking information for an installed hook."""

    library_version: str = Field(..., description="Version from the library")
    content_hash: str = Field(..., description="SHA256 hash of the content")
    installed_at: datetime = Field(
        default_factory=datetime.now, description="Installation timestamp"
    )
    hook_type: str = Field(..., description="Hook type: UserPromptSubmit, PreToolUse, PostToolUse")


class GlobalSyncState(BaseModel):
    """State tracking for global installations (~/.claude/)."""

    version: str = Field(default="1.0.0", description="State file format version")
    library_version: str = Field(default="", description="Library version used for sync")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last state update")
    agents: dict[str, AgentInstallation] = Field(default_factory=dict)
    commands: dict[str, CommandInstallation] = Field(default_factory=dict)
    hooks: dict[str, HookInstallation] = Field(default_factory=dict)
    mcp_servers: dict[str, MCPInstallation] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DetectedTechnologies(BaseModel):
    """Technologies detected in a project."""

    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


class ProjectSyncState(BaseModel):
    """State tracking for project installations (./.claude/)."""

    version: str = Field(default="1.0.0", description="State file format version")
    project_path: str = Field(..., description="Absolute path to the project")
    analyzed_at: datetime = Field(
        default_factory=datetime.now, description="Last analysis timestamp"
    )
    detected: DetectedTechnologies = Field(default_factory=DetectedTechnologies)
    agents: dict[str, AgentInstallation] = Field(default_factory=dict)
    commands: dict[str, CommandInstallation] = Field(default_factory=dict)
    mcp_servers: dict[str, MCPInstallation] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
