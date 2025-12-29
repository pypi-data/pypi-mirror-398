# Usage Guide
> Finding other language? Look here 👀
> - [English](#usage-guide)  
> - [中文](#使用指南)

Hope no [Star War](https://www.aeaweb.org/articles?id=10.1257/app.20150044) future. 

## Use in Python

The project provides interfaces for easy invocation in Python. Here are a few specific examples to help you quickly get started with using it in Python.

### OpenAI-Agents

Launch as MCP:

```python
# !uv pip install openai-agents
from agents import Agent, Runner
from agents.mcp import MCPServerStdio, MCPServerStdioParams

stata_mcp_server = MCPServerStdio(
    name="Stata-MCP",
    params=MCPServerStdioParams(
        command="uvx",
        args=["stata-mcp"]
    )
)

agent = Agent(
    name="Agent",
    instructions="You are a helpful agent.",
    mcp_servers=[stata_mcp_server]
)

result = await Runner.run(
    agent,
    input="Help me run a regression -> log(wage) ~ age, educ, exper with `nlsw88` data and report me the coefficients."
)

print(f"Result: \n> {result.final_output}")
```

Or, you can use our pre-defined Stata-Agent:

```python
# !uv pip install stata-mcp
from agents import Runner
from stata_mcp.agent_as import StataAgent

agent = StataAgent()
result = await Runner.run(
    agent,
    input="Help me run a regression -> log(wage) ~ age, educ, exper with `nlsw88` data and report me the coefficients."
)
print(f"Result: \n> {result.final_output}")
```

### Agent as Tool

Thanks to the agent-as-tool feature provided by OpenAI-Agents, we have pre-configured a Stata-Agent and exposed `as_tool`:

```python
# !uv pip install openai-agents stata-mcp
from agents import Agent
from stata_mcp.agent_as import StataAgent

agent = Agent(
    name="Scientist Agent",
    instructions="You are a helpful scientist.",
    tools=[StataAgent(max_turns=100).as_tool]
)
```

## Coding Agent

The project was initially designed for Claude Desktop and related products, so it may not be helpful for all agents. The following are only the agent configurations that have been tested. We also believe that MCP has been designed for agents from Day 0. The current coding agents are flourishing and overwhelming. We especially recommend using Claude Code and collaborating with other MCPs to complete your tasks.

### Claude Code

This is our most recommended coding agent solution and a basic usage solution for the project. If you want to use `Stata-MCP` in `Claude Code`, refer to the following configuration command:

```bash
claude mcp add stata-mcp -- uvx stata-mcp
```

If you want to manage your research as a project, here is a more suitable solution for you:

```bash
claude mcp add stata-mcp --env STATA_MCP_CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp
```

If you want to specify a specific version of `Stata-MCP`, add the corresponding version number:

```bash
claude mcp add stata-mcp --env STATA_MCP_CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp==1.13.0
```

Then you can try to use `claude mcp list` to check if the installation was successful.

To summarize, in your research directory, after initializing the project, you can freely configure MCP based on the project rather than global configuration. Of course, if you don't want global configuration, you can also remove the path-related parameters, which will not have any impact.

### Codex

If you want to use `Codex` in `VScode`, you need to modify the `~/.codex/config.toml` file. You can directly paste the following content at the end of the file:

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
```

### Cline

Open Cline's MCP configuration file `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/setting/cline_mcp_settings.json` and add the following content:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

### Cursor

`Cursor` performs slightly poorly. In our previous tests, we found that the MCP Server in `Cursor` seems unable to access the user's `Documents` directory. If you still want to use `Cursor`, we recommend you use the following configuration:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "--directory",
        "~/Documents/StataProj",
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP_CWD": "~/Documents/StataProj"
      }
    }
  }
}
```

If there are further errors, please solve them yourself. If you have any good solutions, you are also welcome to submit a PR to help others.

## LLMs Client

Most AI client configurations are similar. Claude Desktop is the most universal format. Taking Claude Desktop configuration as an example:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

Similarly, the configuration for other agents such as Cherry Studio is the same and will not be repeated here.


# 使用指南
> Finding other language? Look here 👀
> - [English](#usage-guide)  
> - [中文](#使用指南)

> Statement: Chinese documents is translated by machine as I am not good at Chinese, if there is any mistake, please let me know. Simultaneously, we recommend you read the English version of the Usage Guide. 

我们诚挚地希望经济学再无 🐒 reg monkey，不要再做无意义的研究！

## 在 Python 中使用
项目提供了容易在 Python 中调用的接口，这里是一些具体的例子来让你能在 python 中快速开始使用。

### OpenAI-Agents
以 MCP 形式启动：
```python
# !uv pip install openai-agents
from agents import Agent, Runner
from agents.mcp import MCPServerStdio, MCPServerStdioParams

stata_mcp_server = MCPServerStdio(
    name="Stata-MCP",
    params=MCPServerStdioParams(
        command="uvx",
        args=["stata-mcp"]
    )
)

agent = Agent(
    name="Agent",
    instructions="You are a helpful agent.",
    mcp_servers=[stata_mcp_server]
)

result = await Runner.run(
    agent,
    input="Help me run a regression -> log(wage) ~ age, educ, exper with `nlsw88` data and report me the coefficients."
)

print(f"Result: \n> {result.final_output}")
```

或者，你可以使用我们预定义的 Stata-Agent：
```python
# !uv pip install stata-mcp
from agents import Runner
from stata_mcp.agent_as import StataAgent

agent = StataAgent()
result = await Runner.run(
    agent,
    input="Help me run a regression -> log(wage) ~ age, educ, exper with `nlsw88` data and report me the coefficients."
)
print(f"Result: \n> {result.final_output}")

```

### Agent as tool
同时，得益于 OpenAI-Agents 提供的 agent-as-tool，我们预设置了一个 Stata-Agent 配置并预留了 `as_tool`：
```python
# !uv pip install openai-agents stata-mcp
from agents import Agent
from stata_mcp.agent_as import StataAgent

agent = Agent(
    name="Scientist Agent",
    instructions="You are a helpful scientist.",
    tools=[StataAgent(max_turns=100).as_tool]
)

```

## 在编码智能体中使用
这个项目最初设计目标是给 Claude Desktop 和相关产品使用的，可能不会为所有的智能体提供帮助，下面列出的只是被测试过的智能体配置。我们也认为 MCP 从 Day 0 开始就是为 Agent 服务的，现在的编码智能体也是各种各样让人类眼花缭乱，我们要特别推荐使用 Claude Code 并搭配其他 MCP 一起协作来完成你的任务。

### Claude Code
这是我们要最建议的编码智能体解决方案，这是一个项目基本的使用方案。如果你希望在 `Claude Code` 中使用`Stata-MCP`，参考下面的配置命令：
```bash
claude mcp add stata-mcp -- uvx stata-mcp
```

如果你希望用项目来管理你的研究，这里是更适合你的解决方案：
```bash
claude mcp add stata-mcp --env STATA_MCP_CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp
```

如果你希望指定特定版本的 `Stata-MCP`，加上对应的版本号：
```bash
claude mcp add stata-mcp --env STATA_MCP_CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp==1.13.0
```

然后你可以尝试使用 `claude mcp list` 去检查是否成功安装了。

总结来看，在你的研究目录下，初始化项目后你可以自由地根据项目进行配置MCP而非全局配置，当然如果你不希望全局配置也可以移除与路径有关的相关参数，这也不会产生影响。

### Codex
如果你希望使用 `VScode` 中的 `Codex`，你需要修改 `~/.codex/config.toml` 文件，可以直接把下面的内容粘贴到文件最后：
```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp"]
```

### Cline
打开 `Cline` 的 MCP 配置文件 `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/setting/cline_mcp_settings.json` 添加以下的内容：
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

### Cursor
`Cursor` 的表现有点糟糕，我们在之前的测试中就发现 `Cursor` 中的 MCP Server 似乎不能访问用户的 `Documents` 目录，如果你还是要使用 `Cursor`，我们推荐你使用下面的配置来使用：
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "--directory",
        "~/Documents/StataProj",
        "stata-mcp"
      ],
      "env": {
        "STATA_MCP_CWD": "~/Documents/StataProj"
      }
    }
  }
}
```
进一步如果有错误请自己解决，如果你有任何好的解决方案也欢迎你提交PR来帮助其他人。

## 在 AI 代理中使用
大多数的AI代理的配置都是相似的，Claude Desktop是最通用的格式，主要以 Claude Desktop 的配置作为例子：
```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

同样地，其他代理像Cherry Studio的配置也是相同的，这里不再重复。

