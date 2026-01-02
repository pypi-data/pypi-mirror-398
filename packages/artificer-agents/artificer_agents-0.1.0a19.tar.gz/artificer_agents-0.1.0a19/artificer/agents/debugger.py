"""Interactive debugger for pydantic-ai agents using agent.iter()."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import questionary

if TYPE_CHECKING:
    from pydantic_ai import Agent
    from pydantic_ai.agent import AgentRunResult


def _format_node(node: Any) -> str:
    """Format a node for display."""
    node_type = type(node).__name__

    if hasattr(node, "model_dump"):
        data = node.model_dump()
        return f"{node_type}:\n{json.dumps(data, indent=2, default=str)}"

    return f"{node_type}: {node}"


def _format_messages(messages: list[Any]) -> str:
    """Format messages for display."""
    output = []
    for i, msg in enumerate(messages):
        if hasattr(msg, "model_dump"):
            data = msg.model_dump()
        else:
            data = msg

        role = data.get("role", "unknown") if isinstance(data, dict) else "unknown"
        output.append(f"[{i}] {str(role).upper()}")
        output.append("-" * 40)
        output.append(json.dumps(data, indent=2, default=str))
        output.append("")
    return "\n".join(output)


async def _save_to_file(
    node: Any,
    messages: list[Any],
    step: int,
) -> None:
    """Sub-menu for saving debug data to files."""
    choices = ["Save current node", "Save all messages", "Save both", "Back"]

    choice = await questionary.select(
        "What would you like to save?",
        choices=choices,
    ).ask_async()

    if choice == "Back":
        return

    # Get filename
    default_name = f"debug_step{step}"
    filename = await questionary.text(
        "Filename (without extension):",
        default=default_name,
    ).ask_async()

    if not filename:
        return

    base_path = Path(filename)

    if choice in ("Save current node", "Save both"):
        path = base_path.with_suffix(".node.json")
        if hasattr(node, "model_dump"):
            data = node.model_dump()
        else:
            data = {"type": type(node).__name__, "repr": repr(node)}
        path.write_text(json.dumps(data, indent=2, default=str))
        print(f"Saved node to {path}")

    if choice in ("Save all messages", "Save both"):
        path = base_path.with_suffix(".messages.json")
        messages_data = []
        for msg in messages:
            if hasattr(msg, "model_dump"):
                messages_data.append(msg.model_dump())
            else:
                messages_data.append(msg)
        path.write_text(json.dumps(messages_data, indent=2, default=str))
        print(f"Saved messages to {path}")


async def debug_step(
    step: int,
    node: Any,
    messages: list[Any],
    *,
    agent_name: str = "",
) -> bool:
    """Interactive debug breakpoint for a single step.

    Args:
        step: Current step number (0-indexed).
        node: The current node from agent.iter().
        messages: The current message history.
        agent_name: Name of the agent being debugged.

    Returns:
        True to continue execution, False to abort.
    """
    node_type = type(node).__name__

    if agent_name:
        title = f"{agent_name} | step {step + 1} | {node_type}"
    else:
        title = f"step {step + 1} | {node_type}"

    width = max(len(title) + 4, 50)
    print(f"\n┌{'─' * width}┐")
    print(f"│ {title:<{width - 2}} │")
    print(f"└{'─' * width}┘")

    while True:
        choices = [
            "View current node",
            "View message history",
            "Save to file...",
            "Continue",
            "Abort",
        ]

        choice = await questionary.select(
            "What would you like to do?",
            choices=choices,
        ).ask_async()

        if choice is None:
            # User pressed Ctrl+C
            return False

        if choice == "View current node":
            print("\n" + _format_node(node))

        elif choice == "View message history":
            print("\n" + _format_messages(messages))

        elif choice == "Save to file...":
            await _save_to_file(node, messages, step)

        elif choice == "Continue":
            return True

        elif choice == "Abort":
            return False


async def run_with_debug(
    agent: Agent[Any, Any],
    prompt: str,
    *,
    verbose: bool = False,
) -> AgentRunResult[Any]:
    """Run an agent with interactive debugging at each step.

    Uses agent.iter() to step through the agent execution,
    pausing at each node to allow inspection.

    Args:
        agent: The pydantic-ai agent to run.
        prompt: The input prompt.
        verbose: If True, print extra info during execution.

    Returns:
        The final AgentRunResult.

    Raises:
        RuntimeError: If the user aborts execution.
    """
    from pydantic_graph.nodes import End

    step = 0

    async with agent.iter(prompt) as agent_run:
        async for node in agent_run:
            # Get current messages from the agent run
            messages = list(agent_run.all_messages())

            if verbose:
                node_type = type(node).__name__
                print(f"[step {step + 1}] {node_type}")

            # Skip End nodes for debugging (nothing interesting to show)
            if isinstance(node, End):
                if verbose:
                    print("[completed]")
                continue

            # Show debug menu
            should_continue = await debug_step(
                step,
                node,
                messages,
                agent_name="",  # Could extract from agent if available
            )

            if not should_continue:
                raise RuntimeError("Execution aborted by user")

            step += 1

        # Return the final result
        if agent_run.result is None:
            raise RuntimeError("Agent did not produce a result")

        return agent_run.result
