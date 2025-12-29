"""Pydantic models for agent templates."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentScope(str, Enum):
    """Scope of an agent (global or project-specific)."""

    GLOBAL = "global"
    PROJECT = "project"


class AgentModel(str, Enum):
    """Claude model to use for the agent."""

    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


class AgentTemplate(BaseModel):
    """Model representing an agent template from the library."""

    name: str = Field(..., description="Unique name of the agent")
    file: str = Field(..., description="Path to the agent file within the data directory")
    version: str = Field(default="1.0.0", description="Version of the agent template")
    description: str = Field(default="", description="Description of the agent's role")
    model: AgentModel = Field(default=AgentModel.SONNET, description="Claude model to use")
    tags: list[str] = Field(default_factory=list, description="Tags for detection matching")
    scope: AgentScope = Field(default=AgentScope.PROJECT, description="Scope of the agent")
    category: str | None = Field(default=None, description="Category (for project agents)")

    class Config:
        use_enum_values = True


class AgentFrontmatter(BaseModel):
    """Frontmatter structure for agent .md files."""

    name: str = Field(..., description="Agent name for Claude Code")
    description: str = Field(..., description="Description shown in Claude Code")
    tools: str = Field(
        default="Read, Glob, Grep, Bash, Edit, Write", description="Comma-separated tools"
    )
    model: AgentModel = Field(default=AgentModel.SONNET, description="Model to use")
    permission_mode: str = Field(
        default="plan",
        alias="permissionMode",
        description="Permission mode: plan or bypassPermissions",
    )

    class Config:
        use_enum_values = True


class DetectionRule(BaseModel):
    """Rule for detecting which agents to recommend for a project."""

    detector: str = Field(..., description="Detection pattern (e.g., 'pom.xml || build.gradle')")
    agents: list[str] = Field(..., description="Agent names to recommend if pattern matches")


class AgentsIndex(BaseModel):
    """Structure of the _index.yaml file for agents."""

    version: str = Field(default="1.0.0")
    global_agents: list[AgentTemplate] = Field(default_factory=list, alias="global")
    project: dict[str, Any] = Field(default_factory=dict)
    detection_rules: list[DetectionRule] = Field(default_factory=list)

    class Config:
        populate_by_name = True
