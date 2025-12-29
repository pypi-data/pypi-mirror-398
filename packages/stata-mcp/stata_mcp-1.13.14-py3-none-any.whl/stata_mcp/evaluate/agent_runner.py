#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : agent_runner.py

import asyncio
from typing import Any, Dict, List

from agents import Agent, OpenAIChatCompletionsModel, Runner
from agents.mcp import MCPServer, MCPServerStdio, MCPServerStdioParams
from openai import AsyncOpenAI

from .score_it import ScoreModel


class AgentRunner:
    instructions: str = """
    Answer the following questions as best you can. 

    Use the following format:
    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of tools

    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Some advice about Stata:
        When you write dofile, you must add the header meta information.
        Header should contain file animation, data, author (your name), like:
        ```Stata
        /*
        aim: to explore the relationship between a and b
        date: 2025.05.20, Tues.
        author: Econ Agent & username ...
        */
        ```

        Then, at all of the dofile should contain the global output path.
        All of the output file should in the path, user will tell you the path, 
        if not, use {default_root -> `~/Downloads/stata_mcp_cwd`} as the global output path.

        Important:
            1. All of the table, figure, tmp-data should be save in the global output path.
            2. Do not use a deeper path as avoiding the PathExistError

    Stata Command Suggestion:
        0. if you are not sure about a command, try to use `help` tools
        1. use `sum2docx` to generate a summary table.
        2. use `outreg2` to save regression table.
        3. the regression table should saved with formatting `.doc`, `.rtf`, and `.tex` 
            (in exploring environment, only tex for easier get the table for LLMs; at final, try to save all)

    All the response use English. If user spoke other language, answer with their language.
    Let's Begin!
    """

    STATA_MCP_CFG = MCPServerStdio(
        name="Stata-MCP",
        params=MCPServerStdioParams(
            command="uvx",
            args=["stata-mcp"]
        ),
        client_session_timeout_seconds=60.0,
        cache_tools_list=True,
    )

    def __init__(self,
                 model: str,
                 api_key: str,
                 base_url: str = "https://api.openai.com/v1"):
        self.openai_model = OpenAIChatCompletionsModel(
            model=model,
            openai_client=AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )
        )
        self.agent = Agent(
            name="Social Science Research Agent",
            instructions=self.instructions,
            model=self.openai_model,
            mcp_servers=[self.STATA_MCP_CFG]
        )

    def _update_agent(self, agent: Agent):
        self.agent = agent

    def add_mcp(self, mcp_server: MCPServer):
        self.agent.mcp_servers.append(mcp_server)

    def run(self, task: str, max_turns: int = 30):
        result = asyncio.run(Runner.run(self.agent, task, max_turns=max_turns))
        return result

    @staticmethod
    def get_processer(result) -> List[Dict[str, Any]]:
        """
        Extract the complete conversation process from the agent runner result.
        Returns a list of conversation items in standard format.

        Args:
            result: The result returned by Runner.run()

        Returns:
            List[Dict[str, Any]]: List of conversation items with role and content

        Example:
            >>> conversation = AgentRunner.get_processer(result)
            >>> print(conversation)
            [
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": "Use tool to tell me 1 + 1 equal to?"
                },
                {
                    "role": "assistant",
                    "content": "I need to use tools to solve this problem."
                },
                {
                    "role": "tool",
                    "content": "Tool execution result: 2"
                },
                {
                    "role": "assistant",
                    "content": "The answer is 2."
                }
            ]
        """
        try:
            # Get the complete conversation history using to_input_list()
            conversation_items = result.to_input_list()

            # Convert to standard format
            processed_conversation = []

            for item in conversation_items:
                if hasattr(item, 'role') and hasattr(item, 'content'):
                    # Standard message format
                    processed_item = {
                        "role": item.role,
                        "content": item.content
                    }
                    processed_conversation.append(processed_item)
                elif isinstance(item, dict):
                    # Dictionary format
                    processed_item = {
                        "role": item.get("role", "unknown"),
                        "content": item.get("content", "")
                    }
                    processed_conversation.append(processed_item)
                else:
                    # Handle other item types (tool calls, etc.)
                    if hasattr(item, 'type'):
                        processed_item = {
                            "role": item.type,
                            "content": str(item)
                        }
                        processed_conversation.append(processed_item)

            return processed_conversation

        except Exception as e:
            # Fallback: try to extract basic information
            try:
                # Try to get final output as fallback
                final_output = getattr(result, 'final_output', str(result))
                return [
                    {
                        "role": "assistant",
                        "content": final_output
                    }
                ]
            except Exception:
                # Last resort: return the result as string
                return [
                    {
                        "role": "system",
                        "content": f"Error processing conversation: {str(e)}. Raw result: {str(result)}"
                    }
                ]

    @staticmethod
    def get_final_result(result) -> str:
        """
        Extract the final AI response from the agent runner result.

        Args:
            result: The result returned by Runner.run()

        Returns:
            str: The final output/message from the agent

        Example:
            >>> final_message = AgentRunner.get_final_result(result)
            >>> print(final_message)
            "The answer is 2."
        """
        try:
            # Try to get the final_output attribute first
            if hasattr(result, 'final_output'):
                return result.final_output
            # Fallback to string conversion
            return str(result)
        except Exception as e:
            # Return error information if extraction fails
            return f"Error extracting final result: {str(e)}"

    def evaluate(self, task: str, reference_answer: str, is_display: bool = False):
        """
        Evaluate the agent's performance on a given task using ScoreModel.

        Args:
            task (str): The task description to evaluate
            reference_answer (str): The reference answer for evaluation
            is_display (bool): Whether to print the evaluation score, default False

        Returns:
            str: The evaluation score and detailed feedback from ScoreModel
        """
        # Run the agent task
        result = self.run(task)

        # Get the conversation process as list
        processer_list = self.get_processer(result)

        # Convert the processer list to string format for ScoreModel
        processer_str = str(processer_list)

        # Get the final result as string
        results_str = self.get_final_result(result)

        # Create and run the ScoreModel
        score_model = ScoreModel(
            task=task,
            reference_answer=reference_answer,
            processer=processer_str,
            results=results_str
        )

        # Get the evaluation score
        score_result = score_model.score_it()

        # Display the result if requested
        if is_display:
            print(score_result)

        # Return the evaluation score
        return score_result
