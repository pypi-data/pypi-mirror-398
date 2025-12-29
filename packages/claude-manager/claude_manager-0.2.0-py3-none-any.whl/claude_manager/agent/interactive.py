"""Interactive Claude analyzer with Q&A support."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from claude_manager.agent.prompts.analyze import (
    ANALYSIS_SYSTEM_PROMPT,
    ANALYSIS_USER_PROMPT,
    INTERACTIVE_SUFFIX,
)
from claude_manager.library.loader import LibraryLoader
from claude_manager.models.analysis import AnalysisResult


class InteractiveAnalyzer:
    """Handles interactive analysis with Claude asking clarifying questions."""

    def __init__(
        self,
        project_path: Path,
        model: str = "sonnet",
        timeout: int = 300,
        loader: LibraryLoader | None = None,
    ) -> None:
        """Initialize the interactive analyzer.

        Args:
            project_path: Path to the project to analyze
            model: Claude model to use (haiku, sonnet, opus)
            timeout: Timeout in seconds for each interaction
            loader: LibraryLoader instance (created if not provided)
        """
        self.project_path = project_path.resolve()
        self.model = model
        self.timeout = timeout
        self.loader = loader or LibraryLoader()
        self.console = Console()

    def run(self) -> AnalysisResult:
        """Run interactive analysis session.

        Returns:
            AnalysisResult with technologies, recommendations, etc.
        """
        from claude_manager.agent.analyzer import ClaudeNotFoundError

        # Check Claude CLI availability
        if not shutil.which("claude"):
            raise ClaudeNotFoundError(
                "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )

        self.console.print("\n[bold]Mode interactif[/bold]")
        self.console.print(
            "[dim]L'IA peut poser des questions pour affiner les recommandations.[/dim]\n"
        )

        # First pass: initial analysis
        result = self._run_analysis_pass()

        # Handle questions if any
        while result.questions:
            self.console.print("\n[bold yellow]Questions de clarification:[/bold yellow]")
            answers = []

            for i, question in enumerate(result.questions, 1):
                self.console.print(f"\n[yellow]{i}. {question}[/yellow]")
                answer = typer.prompt("Votre réponse")
                answers.append(f"Q: {question}\nA: {answer}")

            # Run another pass with the answers
            result = self._run_analysis_pass(additional_context="\n\n".join(answers))

        return result

    def _run_analysis_pass(self, additional_context: str = "") -> AnalysisResult:
        """Run a single analysis pass.

        Args:
            additional_context: Additional context from previous Q&A

        Returns:
            AnalysisResult from this pass
        """
        from claude_manager.agent.analyzer import AnalysisError

        cmd = self._build_command(additional_context)

        with self.console.status("[bold]Analyse en cours...[/bold]"):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=self.project_path,
                )
            except subprocess.TimeoutExpired as e:
                raise AnalysisError(f"Analysis timed out after {self.timeout}s") from e

        if result.returncode != 0:
            raise AnalysisError(f"Claude analysis failed: {result.stderr}")

        return self._parse_output(result.stdout)

    def _build_command(self, additional_context: str = "") -> list[str]:
        """Build the Claude CLI command.

        Args:
            additional_context: Additional context to include in the prompt

        Returns:
            Command list for subprocess
        """
        system_prompt = ANALYSIS_SYSTEM_PROMPT
        user_prompt = self._get_user_prompt(additional_context)

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

    def _get_user_prompt(self, additional_context: str = "") -> str:
        """Build the user prompt with context.

        Args:
            additional_context: Additional context from Q&A

        Returns:
            Complete user prompt
        """
        agents_context = self._get_available_agents_context()
        mcp_context = self._get_available_mcp_context()

        prompt = ANALYSIS_USER_PROMPT.format(
            project_path=self.project_path,
            available_agents_context=agents_context,
            available_mcp_context=mcp_context,
        )

        prompt += INTERACTIVE_SUFFIX

        if additional_context:
            prompt += f"\n\n## Previous Q&A Context\n\n{additional_context}"
            prompt += "\n\nPlease incorporate these answers into your analysis. If you have more questions, include them. Otherwise, provide the final recommendations."

        return prompt

    def _get_available_agents_context(self) -> str:
        """Generate context about available agents."""
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
        """Generate context about available MCP servers."""
        catalog = self.loader.get_mcp_catalog()

        lines = ["## Available MCP Servers", ""]

        for server in catalog.get("global", []):
            tags = ", ".join(server.get("tags", []))
            desc = server.get("description", "")
            lines.append(f"- **{server['id']}** ({server['name']}): {desc} [tags: {tags}]")

        for server in catalog.get("project", []):
            tags = ", ".join(server.get("tags", []))
            desc = server.get("description", "")
            lines.append(f"- **{server['id']}** ({server['name']}): {desc} [tags: {tags}]")

        return "\n".join(lines)

    def _parse_output(self, output: str) -> AnalysisResult:
        """Parse Claude's JSON output into structured result.

        Args:
            output: Raw output from Claude

        Returns:
            Parsed AnalysisResult
        """
        from claude_manager.agent.analyzer import OutputParseError

        try:
            data = json.loads(output)

            # Handle different output formats
            if isinstance(data, dict):
                if "result" in data:
                    result_text = data["result"]
                    if isinstance(result_text, str):
                        result_data = self._extract_json(result_text)
                    else:
                        result_data = result_text
                else:
                    result_data = data
            else:
                raise OutputParseError(f"Unexpected output format: {type(data)}")

            return AnalysisResult.model_validate(result_data)

        except json.JSONDecodeError as e:
            try:
                result_data = self._extract_json(output)
                return AnalysisResult.model_validate(result_data)
            except Exception:
                raise OutputParseError(f"Failed to parse JSON output: {e}") from e
        except Exception as e:
            raise OutputParseError(f"Failed to parse analysis output: {e}") from e

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON object from text that may contain other content."""
        import re

        # Try to find JSON block in markdown code fence
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
        if json_match:
            result: dict[str, Any] = json.loads(json_match.group(1))
            return result

        # Try to find raw JSON object
        brace_start = text.find("{")
        if brace_start != -1:
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

        from claude_manager.agent.analyzer import OutputParseError

        raise OutputParseError("No valid JSON found in output")
