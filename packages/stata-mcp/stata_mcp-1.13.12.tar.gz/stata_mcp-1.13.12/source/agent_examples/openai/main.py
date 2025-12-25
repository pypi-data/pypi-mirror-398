#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : main.py

import os
import asyncio
from time import perf_counter
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled
from agents.mcp import MCPServerStdio


# If you are using Cloudflare AI Gateway to store the agent chat histories, you should disable the tracing.
# set_tracing_disabled(True)

mcp_server = MCPServerStdio(
    name="Stata-MCP",
    params={
        "command": "uvx",
        "args": [
            "stata-mcp"  # or you can use the local beta version with the git clone repo.
        ],
        "env": {
            "stata_cli": "stata-mp"  # alternative you can change your Stata path here
        }
    }
)

# It looks like the system prompt, you can change or add more information to instructions.
# I always figure that better instructions, better performance.
# Here is just an example of instructions, in the real task you should use a better one.
model_instructions = """
You are a helpful economics agent, you can help user to achieve their task with tools
"""

agent = Agent(
    name="Econ Assistant",
    instructions=model_instructions,
    mcp_servers=[mcp_server],  # If you hope to add other MCP servers, you can add them here.
    model=OpenAIChatCompletionsModel(  # If you have set environment of OPENAI_API_KEY, you can ignore arg `model`.
        model="deepseek-chat",  # As I am located in China, I use DeepSeek as model provider, you can change to OpenAI.
        openai_client=AsyncOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),  # "https://api.openai.com/v1"
            api_key=os.getenv("OPENAI_API_KEY")  # Suggest saving your API KEY in environment variables. IMPORTANT!
        )
    ),
)


async def main(msg: str):
    await mcp_server.connect()
    start = perf_counter()
    try:
        result = await Runner.run(agent, msg, max_turns=30)
        print(result.final_output)
    finally:
        elapsed = perf_counter() - start
        print(f"Total cost time: {elapsed:.2f} s")
        await mcp_server.cleanup()
    return result

# This task message is also an example, there is no research meaning.
task_message = """
Using the Stata default data, analysis the relationship between `mpg` and `price`, moreover add `weight` as a control.
"""


if __name__ == "__main__":
    asyncio.run(main(msg=task_message))
