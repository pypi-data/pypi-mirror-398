"""JSON schemas for Claude Code structured output."""

ANALYSIS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "technologies": {
            "type": "array",
            "description": "List of detected technologies",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Technology name"},
                    "category": {
                        "type": "string",
                        "enum": [
                            "language",
                            "framework",
                            "tool",
                            "database",
                            "infra",
                            "testing",
                            "auth",
                        ],
                        "description": "Technology category",
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Detection confidence",
                    },
                    "evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Files/patterns that indicate this",
                    },
                },
                "required": ["name", "category", "confidence"],
            },
        },
        "complexity": {
            "type": "object",
            "description": "Project complexity assessment",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["simple", "medium", "complex"],
                    "description": "Complexity level",
                },
                "factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Contributing factors",
                },
            },
            "required": ["level", "factors"],
        },
        "special_considerations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Special notes about the project",
        },
        "recommended_agents": {
            "type": "array",
            "description": "Recommended Claude Code agents",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Agent name from library"},
                    "reason": {"type": "string", "description": "Why recommended"},
                    "priority": {
                        "type": "string",
                        "enum": ["essential", "recommended", "optional"],
                        "description": "Priority level",
                    },
                    "matched_technologies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Matched technologies",
                    },
                },
                "required": ["name", "reason", "priority"],
            },
        },
        "recommended_mcp": {
            "type": "array",
            "description": "Recommended MCP servers",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "MCP server ID from catalog"},
                    "reason": {"type": "string", "description": "Why recommended"},
                    "priority": {
                        "type": "string",
                        "enum": ["essential", "recommended", "optional"],
                        "description": "Priority level",
                    },
                    "matched_technologies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Matched technologies",
                    },
                },
                "required": ["id", "reason", "priority"],
            },
        },
        "summary": {"type": "string", "description": "Brief analysis summary"},
        "questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Clarifying questions for interactive mode",
        },
    },
    "required": [
        "technologies",
        "complexity",
        "recommended_agents",
        "recommended_mcp",
        "summary",
    ],
}
