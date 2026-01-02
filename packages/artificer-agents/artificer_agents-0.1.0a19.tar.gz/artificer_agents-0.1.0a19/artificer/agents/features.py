"""AgentsFeature for Artificer CLI integration."""

from __future__ import annotations

import asyncio
import importlib
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import click
import questionary
from artificer.cli.feature import ArtificerFeature  # type: ignore[import-untyped]
from questionary import Style

from .registry import get_agent, list_agents

if TYPE_CHECKING:
    from artificer.cli.config import ArtificerConfig  # type: ignore[import-untyped]
    from pydantic_ai import Agent

_style = Style(
    [
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:cyan"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
    ]
)


def _get_agent_model(agent: Agent[Any, Any]) -> str:
    """Get a string representation of the agent's model."""
    model = agent.model
    if model is None:
        return "(default)"
    if isinstance(model, str):
        return model
    # Model object - try to get a useful representation
    return str(model)


def _get_agent_instructions(agent: Agent[Any, Any]) -> str:
    """Get the agent's instructions/system prompt."""
    # pydantic-ai uses _system_prompts internally
    if hasattr(agent, "_instructions") and agent._instructions:
        return str(agent._instructions)
    if hasattr(agent, "_system_prompts") and agent._system_prompts:
        prompts = agent._system_prompts
        if prompts:
            # Could be strings or callables
            parts = []
            for p in prompts:
                if isinstance(p, str):
                    parts.append(p)
                elif callable(p):
                    parts.append(f"<dynamic: {p.__name__}>")
            return "\n".join(parts)
    return "(none)"


def _get_output_type(agent: Agent[Any, Any]) -> str:
    """Get a string representation of the output type."""
    output_type = agent.output_type
    if output_type is str:
        return "str"
    if hasattr(output_type, "__name__"):
        return output_type.__name__
    return str(output_type)


def _get_tools_info(agent: Agent[Any, Any]) -> str:
    """Get info about the agent's tools."""
    tools = []

    # Check for function tools
    if hasattr(agent, "_function_tools") and agent._function_tools:
        for name in agent._function_tools:
            tools.append(name)

    # Check for toolsets (MCP servers, etc.)
    if hasattr(agent, "_toolsets") and agent._toolsets:
        for toolset in agent._toolsets:
            toolset_name = type(toolset).__name__
            tools.append(f"<{toolset_name}>")

    if not tools:
        return "(none)"
    return ", ".join(tools)


class AgentsFeature(ArtificerFeature):  # type: ignore[misc]
    """Feature providing CLI commands for agent management."""

    @classmethod
    def register(cls, cli: click.Group, config: "ArtificerConfig") -> None:
        """Register agent commands with the CLI."""
        cls._import_agent_modules(config)

        @cli.group()
        def agents() -> None:
            """Manage and run agents."""
            pass

        @agents.command(name="list")
        def list_cmd() -> None:
            """List all available agents."""
            registered = list_agents()
            if not registered:
                click.echo("No agents registered.")
                return

            # Check if we're in an interactive terminal
            if not sys.stdin.isatty():
                # Non-interactive: just list agents
                click.echo("Available agents:")
                for name, agent in registered.items():
                    model = _get_agent_model(agent)
                    click.echo(f"  {name} [model: {model}]")
                return

            # Build choices for selection
            choices = []
            for name, agent in registered.items():
                model = _get_agent_model(agent)
                display = f"{name} [model: {model}]"
                choices.append(questionary.Choice(title=display, value=name))

            selected = questionary.select(
                "Select an agent:",
                choices=choices,
                style=_style,
                use_shortcuts=False,
                use_indicator=True,
            ).ask()

            if selected is None:
                return

            # Show options for the selected agent
            action = questionary.select(
                f"What would you like to do with '{selected}'?",
                choices=[
                    questionary.Choice(title="Describe", value="describe"),
                    questionary.Choice(title="Run", value="run"),
                    questionary.Choice(title="Cancel", value="cancel"),
                ],
                style=_style,
                use_shortcuts=False,
                use_indicator=True,
            ).ask()

            if action == "describe":
                cls._describe_agent(selected)
            elif action == "run":
                cls._run_agent_interactive(selected)

        @agents.command(name="describe")
        @click.argument("agent_name", required=False)
        def describe_cmd(agent_name: str | None) -> None:
            """Show detailed information about an agent."""
            if agent_name is None:
                agent_name = cls._select_agent("Select an agent to describe:")
                if agent_name is None:
                    return

            cls._describe_agent(agent_name)

        @agents.command(name="run")
        @click.argument("agent_name", required=False)
        @click.argument("prompt", required=False)
        @click.option(
            "-d", "--debug", is_flag=True, help="Enable interactive debug mode"
        )
        @click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
        def run_cmd(
            agent_name: str | None,
            prompt: str | None,
            debug: bool,
            verbose: bool,
        ) -> None:
            """Run an agent with the given prompt.

            PROMPT is the text input to send to the agent.
            If not provided, will prompt for input interactively.
            """
            if agent_name is None:
                agent_name = cls._select_agent("Select an agent to run:")
                if agent_name is None:
                    return

            cls._run_agent_interactive(agent_name, prompt, debug=debug, verbose=verbose)

    @classmethod
    def _select_agent(cls, message: str) -> str | None:
        """Show interactive agent selection."""
        registered = list_agents()
        if not registered:
            click.echo("No agents registered.")
            return None

        # Non-interactive: can't select
        if not sys.stdin.isatty():
            click.echo("No agent specified and not in interactive mode.", err=True)
            return None

        choices = []
        for name, agent in registered.items():
            model = _get_agent_model(agent)
            display = f"{name} [model: {model}]"
            choices.append(questionary.Choice(title=display, value=name))

        result = questionary.select(
            message,
            choices=choices,
            style=_style,
            use_shortcuts=False,
            use_indicator=True,
        ).ask()
        return cast(str | None, result)

    @classmethod
    def _describe_agent(cls, agent_name: str) -> None:
        """Show detailed information about an agent."""
        agent = get_agent(agent_name)
        if agent is None:
            available = list(list_agents().keys())
            click.echo(f"Unknown agent: {agent_name}", err=True)
            if available:
                click.echo(f"Available: {', '.join(available)}", err=True)
            raise SystemExit(1)

        click.echo(f"Agent: {agent_name}")
        click.echo(f"Model: {_get_agent_model(agent)}")
        click.echo(f"Output Type: {_get_output_type(agent)}")
        click.echo(f"Tools: {_get_tools_info(agent)}")
        click.echo()
        click.echo("Instructions:")
        click.echo(_get_agent_instructions(agent))

    @classmethod
    def _run_agent_interactive(
        cls,
        agent_name: str,
        prompt: str | None = None,
        *,
        debug: bool = False,
        verbose: bool = False,
    ) -> None:
        """Run an agent, prompting for input if needed."""
        agent = get_agent(agent_name)
        if agent is None:
            available = list(list_agents().keys())
            click.echo(f"Unknown agent: {agent_name}", err=True)
            if available:
                click.echo(f"Available: {', '.join(available)}", err=True)
            raise SystemExit(1)

        # Get prompt
        if prompt is None:
            if not sys.stdin.isatty():
                click.echo("No prompt provided and not in interactive mode.", err=True)
                raise SystemExit(1)

            prompt = questionary.text(
                "Enter prompt:",
                style=_style,
            ).ask()
            if prompt is None:
                return

        # Run the agent
        result = asyncio.run(
            cls._run_agent_async(agent, prompt, debug=debug, verbose=verbose)
        )

        # Output result
        if isinstance(result, dict) and "error" in result:
            click.echo(f"Error: {result['error']}", err=True)
            raise SystemExit(1)

        # Pretty print the result
        if isinstance(result, str):
            click.echo(result)
        else:
            click.echo(json.dumps(result, indent=2, default=str))

    @classmethod
    async def _run_agent_async(
        cls,
        agent: Agent[Any, Any],
        prompt: str,
        *,
        debug: bool = False,
        verbose: bool = False,
    ) -> Any:
        """Run an agent and return the result."""
        from .debugger import run_with_debug

        try:
            if debug:
                result = await run_with_debug(agent, prompt, verbose=verbose)
            else:
                async with agent:
                    result = await agent.run(prompt)

            # Extract the output
            output = result.output

            # Convert to serializable format
            if hasattr(output, "model_dump"):
                return output.model_dump()
            return output
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def _import_agent_modules(cls, config: "ArtificerConfig") -> None:
        """Import agent modules to register agents."""
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        pyproject_path = Path.cwd() / "pyproject.toml"
        if not pyproject_path.exists():
            return

        with open(pyproject_path, "rb") as f:
            pyproject: dict[str, Any] = tomllib.load(f)

        agents_config: dict[str, Any] = (
            pyproject.get("tool", {}).get("artificer", {}).get("agents", {})
        )

        # Add cwd to path so local agent modules can be imported
        cwd = str(Path.cwd())
        if cwd not in sys.path:
            sys.path.insert(0, cwd)

        agent_modules: list[str] = agents_config.get("agents", [])
        for module_path in agent_modules:
            try:
                importlib.import_module(module_path)
            except ImportError as e:
                click.echo(
                    f"Warning: Could not import agent module '{module_path}': {e}",
                    err=True,
                )
