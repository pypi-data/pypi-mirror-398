"""Simple registry for pydantic-ai agents."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic_ai import Agent

# Global registry mapping names to agents
_agents: dict[str, Agent[Any, Any]] = {}


def _to_kebab_case(name: str) -> str:
    """Convert CamelCase to kebab-case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s1).lower()


def agent(cls_or_name: type | str | None = None) -> Any:
    """Decorator to register a pydantic-ai Agent class with the CLI.

    Usage:
        @agent  # registers as 'my-agent' (from class name)
        class MyAgent(Agent):
            ...

        @agent("custom-name")  # explicit name
        class MyAgent(Agent):
            ...
    """

    def decorator(cls: type) -> type:
        # Determine the name
        if isinstance(cls_or_name, str):
            name = cls_or_name
        else:
            name = _to_kebab_case(cls.__name__)

        # Instantiate and register
        instance = cls()
        register_agent(name, instance)
        return cls

    # Called as @agent (no parentheses)
    if isinstance(cls_or_name, type):
        return decorator(cls_or_name)

    # Called as @agent("name") or @agent()
    return decorator


def register_agent(name: str, agent: Agent[Any, Any]) -> Agent[Any, Any]:
    """Register an agent with the CLI.

    Args:
        name: The name to register the agent under.
        agent: A pydantic-ai Agent instance.

    Returns:
        The agent (for decorator-style usage).

    Example:
        from pydantic_ai import Agent
        from artificer.agents import register_agent

        my_agent = Agent('openai:gpt-4o', instructions='Be helpful.')
        register_agent('my-agent', my_agent)

        # Or as a decorator-style pattern:
        register_agent('helper', Agent('openai:gpt-4o'))
    """
    _agents[name] = agent
    return agent


def get_agent(name: str) -> Agent[Any, Any] | None:
    """Get a registered agent by name."""
    return _agents.get(name)


def list_agents() -> dict[str, Agent[Any, Any]]:
    """Get all registered agents."""
    return _agents.copy()


def clear_registry() -> None:
    """Clear all registered agents (useful for testing)."""
    _agents.clear()
