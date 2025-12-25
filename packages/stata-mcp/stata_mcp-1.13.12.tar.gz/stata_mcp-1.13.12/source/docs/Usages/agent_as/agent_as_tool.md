# Agent as Tool

Often we want to use Agents to accomplish specific tasks, but sometimes configuring Agents, including writing prompts that require repeated debugging, can be challenging. This project provides a simpler solution to use Agents as tools, which can achieve excellent results with default prompts. Of course, if you want to customize your prompts and tool descriptions, the project also provides corresponding interfaces.

## Quickly Start
If you have never install `stata-mcp`, `openai` and `openai-agents`, install them first, `pip` and `uv` are allowed.

```bash
pip install stata-mcp
```

or

```bash
uv add stata-mcp
```

Here is an example for use `stata-mcp` as a tool.

```python
import asyncio

from agents import Agent
from stata_mcp.agent_as.agent_as_tool import StataAgent

# init stata agent and set as tool
stata_agent = StataAgent()
sa_tool = stata_agent.as_tool()

# Create main Agent
agent = Agent(
    ...,
    tools=[sa_tool],
)


# Then run the agent as usual.
async def main():
    ...


if __name__ == "__main__":
    asyncio.run(main())

```

## Other Model Provider
You can use any other model provider but `openai`, use the function `set_model` for change it, also you can use the model in ANY OPENAI-AGENT registry.

Here is an example for using `DeepSeek` as model provider

```python
import os

from agents import Agent
from stata_mcp.agent_as.agent_as_tool import StataAgent, set_model

deepseek_model = set_model(
    model_name="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
)

stata_agent = StataAgent(model=deepseek_model)

agent = Agent(
    ...,
    tools=[stata_agent.as_tool, ...],
)

```
