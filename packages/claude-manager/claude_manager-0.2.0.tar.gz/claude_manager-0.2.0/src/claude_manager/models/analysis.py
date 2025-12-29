"""Pydantic models for AI-powered project analysis."""

from typing import Literal

from pydantic import BaseModel, Field


class DetectedTechnology(BaseModel):
    """A technology detected in the project."""

    name: str = Field(..., description="Name of the technology")
    category: Literal["language", "framework", "tool", "database", "infra", "testing", "auth"] = (
        Field(..., description="Category of the technology")
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ..., description="Confidence level of detection"
    )
    evidence: list[str] = Field(
        default_factory=list, description="Files/patterns that indicate this technology"
    )


class ProjectComplexity(BaseModel):
    """Assessment of project complexity."""

    level: Literal["simple", "medium", "complex"] = Field(
        ..., description="Overall complexity level"
    )
    factors: list[str] = Field(
        default_factory=list, description="Factors contributing to complexity"
    )


class AgentRecommendation(BaseModel):
    """A recommended agent with reasoning."""

    name: str = Field(..., description="Agent name from the library")
    reason: str = Field(..., description="Why this agent is recommended")
    priority: Literal["essential", "recommended", "optional"] = Field(
        ..., description="Priority level"
    )
    matched_technologies: list[str] = Field(
        default_factory=list, description="Technologies that triggered this recommendation"
    )


class MCPRecommendation(BaseModel):
    """A recommended MCP server with reasoning."""

    id: str = Field(..., description="MCP server ID from the catalog")
    reason: str = Field(..., description="Why this server is recommended")
    priority: Literal["essential", "recommended", "optional"] = Field(
        ..., description="Priority level"
    )
    matched_technologies: list[str] = Field(
        default_factory=list, description="Technologies that triggered this recommendation"
    )


class AnalysisResult(BaseModel):
    """Complete analysis result from Claude."""

    technologies: list[DetectedTechnology] = Field(
        default_factory=list, description="Detected technologies"
    )
    complexity: ProjectComplexity = Field(..., description="Project complexity assessment")
    special_considerations: list[str] = Field(
        default_factory=list, description="Special notes about the project"
    )
    recommended_agents: list[AgentRecommendation] = Field(
        default_factory=list, description="Recommended agents"
    )
    recommended_mcp: list[MCPRecommendation] = Field(
        default_factory=list, description="Recommended MCP servers"
    )
    summary: str = Field(..., description="Brief summary of the analysis")
    questions: list[str] = Field(
        default_factory=list, description="Clarifying questions if in interactive mode"
    )
