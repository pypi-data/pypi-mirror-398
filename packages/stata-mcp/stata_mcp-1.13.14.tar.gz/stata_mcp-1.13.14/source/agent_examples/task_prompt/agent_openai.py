#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : agent_openai.py

"""
All the file structure is same as agent_examples/openai/main.py
The difference is only prompt setting.
"""

import os
import asyncio
from time import perf_counter
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled
from agents.mcp import MCPServerStdio

from prompt_generator import PromptGenerator


set_tracing_disabled(True)

generator = PromptGenerator(template_name="ReAct", language="English", agent_provider="openai")

mcp_server = MCPServerStdio(
    name="Stata-MCP",
    params={
        "command": "stata-mcp",
        "args": [],
        # "command": "uvx",
        # "args": [
        #     "stata-mcp"  # or you can use the local beta version with the git clone repo.
        # ],
        "env": {
            "stata_cli": "stata-mp"  # alternative you can change your Stata path here
        }
    }
)

model_instructions = generator.instructions()

agent = Agent(
    name="Econ Assistant",
    instructions=model_instructions,
    mcp_servers=[mcp_server],  # If you hope to add other MCP servers, you can add them here.
    model=OpenAIChatCompletionsModel(  # If you have set environment of OPENAI_API_KEY, you can ignore arg `model`.
        model="deepseek-chat",  # As I am located in China, I use DeepSeek as model provider, you can change to OpenAI.
        openai_client=AsyncOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),  # of whatever providers' base url
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


task_message = generator.tasks(
    datas="The default data of Stata",
    aims="Get the data structure and know the relationship between mpg and price",
)


if __name__ == "__main__":
    asyncio.run(main(msg=task_message))
