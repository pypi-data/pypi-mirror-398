# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`artificer-agents` is a lightweight Python library that provides a simple, deterministic agent runtime. It is part of the Artificer ecosystem alongside `artificer-cli` and `artificer-workflows`.

Its sole responsibility is to:
- Run a small agent loop
- Call a configured language model
- Invoke MCP tools
- Optionally invoke subagents
- Return structured results

It does **not** define workflows, user interaction, or orchestration semantics.

## Development Commands

This project uses `uv` for package management and requires Python 3.13+.

```bash
# Install dependencies (including dev)
uv sync

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_file.py::test_name

# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Lint and auto-fix
uv run ruff check . --fix

# Type check
uv run mypy artificer

# Build the package
uv build
```

## Design Principles

- Minimal surface area
- Model-agnostic
- MCP-first
- Stateless agents
- Typed input/output (Pydantic models)
- No chat assumptions
- Runtime over framework

## Architecture

### Module Structure

This project uses namespace packages to coexist with `artificer-cli` and `artificer-workflows`:

```
artificer/                   # Namespace package (no __init__.py)
    agents/
        __init__.py          # Exports Agent, StringInput, StringOutput
        agent.py             # Agent base class
        actions.py           # Action type for model responses
        context.py           # WorkingMemory for tool/subagent results
        runtime.py           # run_agent() async loop
        models/
            __init__.py      # Exports Model, OpenAIModel, Tool
            base.py          # Model ABC and Tool type
            openai.py        # OpenAI implementation
        mcp/
            __init__.py      # Exports MCPClient
            client.py        # MCPClient wrapper around fastmcp
```

### Agent Definition

Agents are defined as subclasses with class attributes:

```python
from pydantic import BaseModel
from artificer.agents import Agent
from artificer.agents.mcp import MCPClient
from artificer.agents.models import OpenAIModel


class MyInput(BaseModel):
    query: str


class MyOutput(BaseModel):
    result: str


class MyAgent(Agent):
    system_prompt = "You are a helpful assistant."
    model = OpenAIModel(model="gpt-4o-mini")
    mcp_client = MCPClient(["path/to/server.py"])  # optional
    tools = ["web"]           # Namespace allowlist (empty = all tools)
    subagents = []            # Optional nested agents
    max_iterations = 50
    _input_schema = MyInput
    _output_schema = MyOutput
```

Key features:
- Name auto-derived from class name (`MyAgent` → `"my"`)
- Set `_input_schema` and `_output_schema` for typed I/O
- Default `StringInput`/`StringOutput` for simple str → str agents
- Agents auto-register by name when defined

### Runtime Loop

The `agent.run()` method executes the agent loop:

1. Build prompt (system + input + context + tools + response format instructions)
2. Call model → get text response → parse JSON into Action
3. Execute action:
   - `CALL_TOOL` → invoke MCP tool, store result
   - `SPAWN_SUBAGENT` → recursive run call
   - `DONE` → validate output, return
4. Update context
5. Repeat until DONE or max_iterations

The design is model-agnostic: any model that can follow instructions and return JSON can be used. The prompt includes instructions for the model to respond with a JSON action object.

### Usage Example

```python
import asyncio
from pydantic import BaseModel
from artificer.agents import Agent
from artificer.agents.mcp import MCPClient
from artificer.agents.models import OpenAIModel


class MyInput(BaseModel):
    query: str


class MyOutput(BaseModel):
    result: str


class MyAgent(Agent):
    system_prompt = "You are a helpful assistant."
    model = OpenAIModel(model="gpt-4o-mini")
    mcp_client = MCPClient(["path/to/server.py"])
    _input_schema = MyInput
    _output_schema = MyOutput


async def main():
    agent = MyAgent()

    async with agent.mcp_client:
        result = await agent.run(MyInput(query="Hello"), verbose=True)
        print(result.result)

asyncio.run(main())
```

### Simple String Agents

For simple agents that just take a string and return a string:

```python
class SimpleAgent(Agent):
    system_prompt = "Answer questions concisely."
    model = OpenAIModel(model="gpt-4o-mini")

result = await SimpleAgent().run("What is Python?")
print(result.output)  # StringOutput has .output field
```

## Code Style

- Type hints for all function parameters and return values
- Prefer simple, direct solutions over complex abstractions
