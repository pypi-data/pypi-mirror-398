# artificer-agents

A lightweight Python library for running deterministic agent loops with MCP tools.

## Installation

```bash
pip install artificer-agents

# With OpenAI support
pip install artificer-agents[openai]
```

Requires Python 3.13+.

## Usage

Define agents as classes:

```python
import asyncio
from pydantic import BaseModel
from artificer.agents import Agent
from artificer.agents.mcp import MCPClient
from artificer.agents.models import OpenAIModel


class Input(BaseModel):
    query: str


class Output(BaseModel):
    result: str


class MyAgent(Agent):
    system_prompt = "You are a helpful assistant."
    model = OpenAIModel(model="gpt-4o-mini")
    mcp_client = MCPClient(["path/to/mcp-server.py"])  # optional
    _input_schema = Input
    _output_schema = Output


async def main():
    agent = MyAgent()

    async with agent.mcp_client:
        result = await agent.run(Input(query="Hello"), verbose=True)
        print(result.result)

asyncio.run(main())
```

## Simple String Agents

For simple str -> str agents, no schemas needed:

```python
class SimpleAgent(Agent):
    system_prompt = "Answer questions concisely."
    model = OpenAIModel(model="gpt-4o-mini")

result = await SimpleAgent().run("What is Python?")
print(result.output)  # StringOutput with .output field
```

## Subagents

Agents can spawn other agents:

```python
class ResearcherAgent(Agent):
    system_prompt = "Research the topic and return findings."
    model = model
    mcp_client = mcp_client
    _input_schema = ResearchInput
    _output_schema = ResearchOutput


class OrchestratorAgent(Agent):
    system_prompt = "Use the researcher subagent to gather info."
    model = model
    subagents = [ResearcherAgent()]
    _input_schema = Input
    _output_schema = Output
```

## Development

```bash
uv sync                    # Install dependencies
./scripts/check.sh         # Run all checks (lint, format, typecheck, tests)
./scripts/test.sh          # Run tests only
./scripts/format.sh        # Format code
```

## License

MIT
