# Agent Examples
Here is some examples of how to use Stata-MCP in agents.

> If you are finding how to make the agent perform better, read file: [How to write a task prompt](task_prompt/README.md)

## Catalog
- [OpenAI-Agent](#openai-agent)
- [Langchain-ReAct-Agent](#langchain-react-agent)

## OpenAI-Agent
The OpenAI-Agent is the most traditional agent here (I think), it's also the most simple one.  
If you just hope to find out that there is something AI could do, have a try here, it is a good start.

You can `cd` to the `OpenAI-Agent` directory and run `main.py` to start the agent.
```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

# If you did not make your environment, make one.
# uv sync

uv run agent_examples/openai/main.py  # before that, you can change your task message, just provide the minimal task description, and don’t forget to include your data path and the output path.
```

If there is timeout error, do not worry, you can install it before running the agent, like this:
```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

pip install -e .
# You can find whether it is installed successfully by:
stata-mcp --version
```
and, edit the agent file `agent_examples/openai/main.py`, from
```python
mcp_server = MCPServerStdio(
    name="Stata-MCP",
    params={
        "command": "uvx",
        "args": [
            "stata-mcp"
        ],
        "env": {
            "stata_cli": "stata-mp"
        }
    }
)
```
to
```python
mcp_server = MCPServerStdio(
    name="Stata-MCP",
    params={
        "command": "stata-mcp",
        "args": [],
        "env": {"stata_cli": "stata-mp"}
    }
)
```

## Langchain-ReAct-Agent
Similar to the OpenAI-Agent, the Langchain-ReAct-Agent is also a simple agent.  
With ReAct framework, it could perform better than the common Agent.  
More information could read this paper: [ReAct: Synergizing Reasoning and Acting in Language Models](http://arxiv.org/abs/2210.03629).

How to run?
```bash
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp
uv run agent_examples/langchain/main.py
```

