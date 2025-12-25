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
from typing import Dict

# We suppose you have set the api_base and api_key.
# Note: The environment name is "OPENAI_API_BASE" and "OPENAI_API_KEY"
# os.environ["OPENAI_API_BASE"] = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
# os.environ["OPENAI_API_KEY"] = os.getenv("DEEPSEEK_API_KEY")

from langchain import hub
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent  # langgraph is more stable than langchain react agent


# Get the ReAct framework prompt here
prompt = hub.pull("hwchase17/react")

# You should set the stata_cli here, not in the client args
os.environ["stata_cli"] = "stata-mp"
client = MultiServerMCPClient(
    {
        "stata-mcp": {
            "command": "uvx",
            "args": ['stata-mcp'],
            "transport": "stdio",
        }
    }
)

# If you are setting other providers, you can set whatever model you want, visit official documents to change it.
model = init_chat_model(model="deepseek-chat", model_provider="openai")


async def main(msg: Dict[str, str]):
    tools = await client.get_tools()
    start = perf_counter()
    agent = create_react_agent(model, tools, prompt=prompt)
    result = await agent.ainvoke(msg)
    elapsed = perf_counter() - start
    print(result)
    print(f"Total cost time: {elapsed:.2f} s")
    return result


task: str = """
Using the Stata default data, analysis the relationship between `mpg` and `price`, moreover add `weight` as a control.
"""
task_messages = {"messages": task}

if __name__ == "__main__":
    asyncio.run(main(task_messages))
