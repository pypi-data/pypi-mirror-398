"""Claude Code subprocess analyzer for project analysis."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from claude_manager.agent.prompts.analyze import (
    ANALYSIS_SYSTEM_PROMPT,
    ANALYSIS_USER_PROMPT,
    INTERACTIVE_SUFFIX,
)
from claude_manager.library.loader import LibraryLoader
from claude_manager.models.analysis import AnalysisResult


class AnalysisError(Exception):
    """Base exception for analysis errors."""

    pass


class ClaudeNotFoundError(AnalysisError):
    """Claude CLI not found in PATH."""

    pass


class AnalysisTimeoutError(AnalysisError):
    """Analysis took too long."""

    pass


class OutputParseError(AnalysisError):
    """Failed to parse Claude's output."""

    pass


class ClaudeAnalyzer:
    """Invokes Claude Code to analyze a project and return structured insights."""

    def __init__(
        self,
        project_path: Path,
        interactive: bool = False,
        model: str = "sonnet",
        timeout: int = 300,
        loader: LibraryLoader | None = None,
    ) -> None:
        """Initialize the analyzer.

        Args:
            project_path: Path to the project to analyze
            interactive: Whether to include clarifying questions
            model: Claude model to use (haiku, sonnet, opus)
            timeout: Timeout in seconds for the analysis
            loader: LibraryLoader instance (created if not provided)
        """
        self.project_path = project_path.resolve()
        self.interactive = interactive
        self.model = model
        self.timeout = timeout
        self.loader = loader or LibraryLoader()

    def analyze(self) -> AnalysisResult:
        """Run the analysis and return structured results.

        Returns:
            AnalysisResult with technologies, recommendations, etc.

        Raises:
            ClaudeNotFoundError: If claude CLI is not found
            AnalysisTimeoutError: If analysis times out
            OutputParseError: If output parsing fails
            AnalysisError: For other errors
        """
        # Check Claude CLI availability
        if not shutil.which("claude"):
            raise ClaudeNotFoundError(
                "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )

        cmd = self._build_command()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.project_path,
            )
        except subprocess.TimeoutExpired as e:
            raise AnalysisTimeoutError(f"Analysis timed out after {self.timeout}s") from e

        if result.returncode != 0:
            raise AnalysisError(f"Claude analysis failed: {result.stderr}")

        return self._parse_output(result.stdout)

    def _build_command(self) -> list[str]:
        """Build the Claude CLI command."""
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt()

        cmd = [
            "claude",
            "--print",
            "--output-format",
            "json",
            "--model",
            self.model,
            "--permission-mode",
            "plan",
            "--allowedTools",
            "Read,Glob,Grep,Bash(git status:git log:git diff:ls:find:head:tail)",
            "--add-dir",
            str(self.project_path),
            "--system-prompt",
            system_prompt,
            user_prompt,
        ]

        return cmd

    def _get_system_prompt(self) -> str:
        """Return the system prompt for analysis."""
        return ANALYSIS_SYSTEM_PROMPT

    def _get_user_prompt(self) -> str:
        """Return the user prompt with context."""
        agents_context = self._get_available_agents_context()
        mcp_context = self._get_available_mcp_context()

        prompt = ANALYSIS_USER_PROMPT.format(
            project_path=self.project_path,
            available_agents_context=agents_context,
            available_mcp_context=mcp_context,
        )

        if self.interactive:
            prompt += INTERACTIVE_SUFFIX

        return prompt

    def _get_available_agents_context(self) -> str:
        """Generate context about available agents for the prompt."""
        agents_index = self.loader.get_agents_index()

        lines = ["## Available Agents", ""]

        # Global agents
        lines.append("### Global Agents (always useful)")
        for agent in agents_index.get("global", []):
            desc = agent.get("description", "")
            model = agent.get("model", "sonnet")
            lines.append(f"- **{agent['name']}**: {desc} (model: {model})")

        # Project agents by category
        lines.append("")
        lines.append("### Project Agents (context-specific)")
        project = agents_index.get("project", {})
        categories = project.get("categories", {})

        for category, agents in categories.items():
            lines.append(f"\n#### {category}")
            for agent in agents:
                tags = ", ".join(agent.get("tags", []))
                desc = agent.get("description", "")
                lines.append(f"- **{agent['name']}**: {desc} [tags: {tags}]")

        return "\n".join(lines)

    def _get_available_mcp_context(self) -> str:
        """Generate context about available MCP servers for the prompt."""
        catalog = self.loader.get_mcp_catalog()

        lines = ["## Available MCP Servers", ""]

        # Global MCP servers
        for server in catalog.get("global", []):
            tags = ", ".join(server.get("tags", []))
            desc = server.get("description", "")
            lines.append(f"- **{server['id']}** ({server['name']}): {desc} [tags: {tags}]")

        # Project MCP servers
        for server in catalog.get("project", []):
            tags = ", ".join(server.get("tags", []))
            desc = server.get("description", "")
            lines.append(f"- **{server['id']}** ({server['name']}): {desc} [tags: {tags}]")

        return "\n".join(lines)

    def _parse_output(self, output: str) -> AnalysisResult:
        """Parse Claude's JSON output into structured result.

        Args:
            output: Raw JSON output from Claude

        Returns:
            Parsed AnalysisResult

        Raises:
            OutputParseError: If parsing fails
        """
        try:
            # Claude --print --output-format json returns a JSON object
            # with a "result" field containing the conversation result
            data = json.loads(output)

            # Handle different output formats
            if isinstance(data, dict):
                # If it's the full response object, extract the result
                if "result" in data:
                    result_text = data["result"]
                    # The result might be a JSON string that needs parsing
                    if isinstance(result_text, str):
                        # Try to find JSON in the result
                        result_data = self._extract_json(result_text)
                    else:
                        result_data = result_text
                else:
                    # Direct JSON response
                    result_data = data
            else:
                raise OutputParseError(f"Unexpected output format: {type(data)}")

            return AnalysisResult.model_validate(result_data)

        except json.JSONDecodeError as e:
            # Try to extract JSON from the output
            try:
                result_data = self._extract_json(output)
                return AnalysisResult.model_validate(result_data)
            except Exception:
                raise OutputParseError(f"Failed to parse JSON output: {e}") from e
        except Exception as e:
            raise OutputParseError(f"Failed to parse analysis output: {e}") from e

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON object from text that may contain other content.

        Args:
            text: Text potentially containing JSON

        Returns:
            Parsed JSON dict

        Raises:
            OutputParseError: If no valid JSON found
        """
        # Try to find JSON block in markdown code fence
        import re

        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
        if json_match:
            result: dict[str, Any] = json.loads(json_match.group(1))
            return result

        # Try to find raw JSON object
        brace_start = text.find("{")
        if brace_start != -1:
            # Find matching closing brace
            depth = 0
            for i, char in enumerate(text[brace_start:], brace_start):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        json_str = text[brace_start : i + 1]
                        result = json.loads(json_str)
                        return result

        raise OutputParseError("No valid JSON found in output")
