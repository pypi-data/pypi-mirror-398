"""Pydantic models for MCP server definitions."""

from enum import Enum

from pydantic import BaseModel, Field


class MCPSourceType(str, Enum):
    """Type of MCP server source."""

    NPM = "npm"
    GITHUB = "github"
    UVX = "uvx"
    PIP = "pip"


class MCPSource(BaseModel):
    """Source definition for an MCP server."""

    type: MCPSourceType = Field(..., description="Source type (npm, github, uvx, pip)")
    package: str | None = Field(default=None, description="Package name (for npm, uvx, pip)")
    repo: str | None = Field(default=None, description="Repository (for github: owner/repo)")
    install_cmd: str | None = Field(default=None, description="Custom install command")

    class Config:
        use_enum_values = True


class MCPConfigTemplate(BaseModel):
    """Configuration template for an MCP server."""

    command: str = Field(..., description="Command to run the server")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")


class MCPServer(BaseModel):
    """Model representing an MCP server from the catalog."""

    id: str = Field(..., description="Unique ID of the server")
    name: str = Field(..., description="Display name")
    description: str = Field(default="", description="Description of the server")
    source: MCPSource = Field(..., description="Source definition")
    config_template: MCPConfigTemplate = Field(..., description="Configuration template")
    tags: list[str] = Field(default_factory=list, description="Tags for detection matching")
    scope: str = Field(default="project", description="Scope: global or project")


class MCPDetectionRule(BaseModel):
    """Rule for detecting which MCP servers to recommend."""

    detector: str = Field(..., description="Detection pattern")
    servers: list[str] = Field(..., description="Server IDs to recommend")


class MCPCatalog(BaseModel):
    """Structure of the _catalog.yaml file for MCP servers."""

    version: str = Field(default="1.0.0")
    global_servers: list[MCPServer] = Field(default_factory=list, alias="global")
    project_servers: list[MCPServer] = Field(default_factory=list, alias="project")
    detection_rules: list[MCPDetectionRule] = Field(default_factory=list)

    class Config:
        populate_by_name = True
