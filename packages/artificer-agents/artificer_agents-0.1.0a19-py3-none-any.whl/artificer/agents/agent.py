"""WorkflowAgent - pydantic-ai Agent with workflow instructions."""

from __future__ import annotations

from typing import Any

from pydantic_ai import Agent

WORKFLOW_INSTRUCTIONS = """You drive workflows using MCP tools.

CRITICAL - Only use these workflow tools (with DOUBLE underscore __):
- <WorkflowName>__start_workflow - Start the workflow
- <WorkflowName>__complete_step - Complete each step

Process:
1. Call __start_workflow to begin
2. Follow the step's instructions
3. Call __complete_step with workflow_id, step_id, status="SUCCESS", and output
4. Repeat until workflow_status is "COMPLETED"
"""


class WorkflowAgent(Agent[Any, Any]):
    model: Any = None
    instructions: Any = None

    def __init__(self, **kwargs: Any) -> None:
        cls = self.__class__

        # Get instructions from kwargs (if provided), otherwise from class
        if "instructions" in kwargs:
            instructions = kwargs.pop("instructions")
        else:
            instructions = cls.instructions

        # Prepend workflow instructions
        full_instructions: Any
        if instructions is None:
            full_instructions = WORKFLOW_INSTRUCTIONS
        elif isinstance(instructions, str):
            full_instructions = f"{WORKFLOW_INSTRUCTIONS}\n\n{instructions}"
        else:
            full_instructions = [WORKFLOW_INSTRUCTIONS, instructions]

        # Pass output_type if defined directly on this class (not inherited)
        init_kwargs: dict[str, Any] = {"instructions": full_instructions}
        if "output_type" in cls.__dict__ and cls.__dict__["output_type"] is not None:
            init_kwargs["output_type"] = cls.__dict__["output_type"]

        # Merge with remaining kwargs
        init_kwargs.update(kwargs)

        super().__init__(cls.model, **init_kwargs)
