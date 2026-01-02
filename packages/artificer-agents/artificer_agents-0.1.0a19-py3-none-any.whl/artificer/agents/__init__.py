"""Agent CLI integration for Artificer.

This module provides:
- @agent decorator for registering pydantic-ai agents with the CLI
- WorkflowAgent for agents that drive artificer-workflows
- CLI commands for managing and running agents

Example usage:

    from pydantic_ai import Agent
    from artificer.agents import agent, WorkflowAgent

    # Simple agent with CLI registration
    @agent
    class MyAgent(Agent):
        model = 'openai:gpt-4o'
        instructions = 'You are a helpful assistant.'

    # Workflow-aware agent
    @agent
    class MyWorkflowAgent(WorkflowAgent):
        model = 'openai:gpt-4o'
        instructions = 'Drive the BuildFeature workflow.'

Then use the CLI:

    artificer agents list
    artificer agents run my-agent "Hello!"
"""

from artificer.agents.agent import WORKFLOW_INSTRUCTIONS, WorkflowAgent
from artificer.agents.debugger import run_with_debug
from artificer.agents.features import AgentsFeature
from artificer.agents.registry import (
    agent,
    clear_registry,
    get_agent,
    list_agents,
    register_agent,
)

__all__ = [
    "AgentsFeature",
    "WORKFLOW_INSTRUCTIONS",
    "WorkflowAgent",
    "agent",
    "clear_registry",
    "get_agent",
    "list_agents",
    "register_agent",
    "run_with_debug",
]
