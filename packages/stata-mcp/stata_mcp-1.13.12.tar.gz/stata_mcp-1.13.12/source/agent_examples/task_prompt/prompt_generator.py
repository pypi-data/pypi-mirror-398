#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : prompt_generator.py

import os
import string
import textwrap
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, Callable, Optional, Literal

DEFAULT_ROOT: str = os.path.expanduser("~/Downloads/StataAgent")
AgentProvider = Literal["openai", "langchain"]


class TemplateName(str, Enum):
    ReAct = "ReAct"
    # CoT = "CoT"
    Common = "Common"


class PromptGeneratorBase(ABC):
    DEFAULT_ROOT: str = DEFAULT_ROOT

    def __init__(self,
                 provider: str = "openai",
                 language: str = "English",
                 **kwargs):
        self.provider = provider.lower()
        self.language = language

        if self.provider == "langchain":  # I am not sure how to config OpenAI agent on tools of prompt
            self.tools_setting = """
            You have access to the following tools: 
            {tools}
            """
            self.action_setting = "Action: the action to take, should be one of [{tool_names}]"
        else:
            self.tools_setting = ""
            self.action_setting = "Action: the action to take, should be one of tools"


    @abstractmethod
    def instructions_generate(self, *args, **kwargs) -> str: ...

    @abstractmethod
    def tasks_generate(self, *args, **kwargs) -> str: ...


class _ReAct_PromptGenerator(PromptGeneratorBase):
    def instructions_generate(self, *args, **kwargs) -> str:
        """
        Generate the instruction prompt string for the ReAct template.

        Args:
            **kwargs: Optional keyword arguments.
                - default_root (str, optional): if not -> self.DEFAULT_ROOT
                    set the default root path for global output files.

        Returns:
            str: The instructions prompt for ReAct Agent

        Copyrights:
            This template is sourced by hwchase17/react on Langchain, raw source copyright is belong to @hwchase17.
            Based on that, I made improvements to make it more suitable for empirical economics research agent (Stata).
            If you want to find the source prompt, visit on https://smith.langchain.com/hub/hwchase17/react
            or, with python script as following:
            ```python
            from langchain import hub
            prompt = hub.pull("hwchase17/react")
            ```
        """
        default_root: str = kwargs.get("default_root", None) or self.DEFAULT_ROOT
        os.makedirs(default_root, exist_ok=os.path.exists(default_root))

        instructions = f"""
        Answer the following questions as best you can. 
        {self.tools_setting}
        Use the following format:
        Question: the input question you must answer
        Thought: you should always think about what to do
        {self.action_setting}
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
            if not, use {default_root} as the global output path.
            
            Important:
                1. All of the table, figure, tmp-data should be save in the global output path.
                2. Do not use a deeper path as avoiding the PathExistError

        Stata Command Suggestion:
            0. if you are not sure about a command, try to use `help` tools
            1. use `sum2docx` to generate a summary table.
            2. use `outreg2` to save regression table.
            3. the regression table should saved with formatting `.doc`, `.rtf`, and `.tex` 
                (in exploring environment, only tex for easier get the table for LLMs; at final, try to save all)

        All the response use {self.language}
        Let's Begin!
        """
        instructions = textwrap.dedent(instructions).strip()
        return instructions

    def tasks_generate(self, *args, **kwargs) -> str:
        """

        """
        datas: Optional[str] = kwargs.get("datas", None)
        aims: Optional[str] = kwargs.get("aims", None)

        if datas is None:
            raise ValueError("You must provide the data information at least the path.")
        if aims is None:
            raise ValueError("You must provide the aims (or we can say the tasks) information.")

        datas_describe: str = "Data describes: "
        datas_describe += kwargs.get("datas_describe") or (
            "is None, but you can use `sum` and `describe` command in Stata "
            "and read the log file to find out the structure and data describe"
        )

        default_deliverables = (
            "Finally, you should list all of the dofile path and log-file path in the final chat message. "
            "Mainly, you should report the core result in the final chat message which is necessary"
        )
        deliverables: str = kwargs.get("deliverables", default_deliverables)

        additional: str = ""
        root = kwargs.get("root", None)
        if root:
            additional += f"Global output path: {root}; "
        for k, v in kwargs.items():
            if k not in ["datas", "datas_describe", "aims", "deliverables", "root"]:
                additional += f"{k}: {v}; "

        tasks_prompt = f"""
        Now, I will give you some information about the tasks, all of them are chunked to three part:
        
        Datas: {datas}
        {datas_describe}
        
        Tasks Aims: {aims}
        
        Finally Deliverables: {deliverables}
        
        {additional}
        """
        tasks_prompt = textwrap.dedent(tasks_prompt).strip()
        return tasks_prompt

class _CoT_PromptGenerator(PromptGeneratorBase):
    # TODO: achieve the CoT prompt generator
    def instructions_generate(self, *args, **kwargs) -> str: ...

    def tasks_generate(self, *args, **kwargs) -> str: ...


class _Common_PromptGenerator(PromptGeneratorBase):
    # TODO: achieve the common prompt generator
    def __int__(self,
                provider: str = "openai",
                language: str = "English",
                **kwargs):
        super().__init__(provider, language, **kwargs)
        self.instructions_template = kwargs.get("instructions_template", None)
        self.tasks_template = kwargs.get("tasks_template", None)

        if (self.instructions_template is None) or (self.tasks_template is None):
            raise ValueError("You must provide the template for instructions and tasks.")

        formatter = string.Formatter()
        self.field_of_instructions = [fname for _, fname, _, _ in formatter.parse(self.instructions_template) if fname]
        self.field_of_tasks = [fname for _, fname, _, _ in formatter.parse(self.tasks_template) if fname]

    def instructions_generate(self, *args, **kwargs) -> str: ...

    def tasks_generate(self, *args, **kwargs) -> str: ...


class PromptGenerator:
    DEFAULT_ROOT: str = DEFAULT_ROOT
    _generator_mapping: Dict[TemplateName, Callable] = {
        TemplateName.ReAct: _ReAct_PromptGenerator,
        # TemplateName.CoT: _CoT_PromptGenerator,
        TemplateName.Common: _Common_PromptGenerator,
    }

    def __init__(self,
                 template_name: str | TemplateName = TemplateName.ReAct,
                 language: str = "English",  # any string, like "English", "Chinese", "zh-CN", "中文", "Español" ...
                 ROOT: str | Path = None,
                 agent_provider: AgentProvider | str = "openai",  # now only support "openai" and "langchain"
                 *,  # the following args is not supported now
                 is_diy: bool = False,
                 instructions_template: str = None,
                 tasks_template: str = None):
        if isinstance(template_name, str):
            template_name = TemplateName(template_name)
        self.ROOT: str = self.ensure_path(ROOT)

        self.template_name: TemplateName = template_name
        self.generator = self._generator_mapping.get(self.template_name)(
            provider=agent_provider, 
            language=language
        )

        if is_diy and (template_name == TemplateName.Common) and False:  # TODO: Achieve DIY, temporary disable
            self.generator = self._generator_mapping.get(TemplateName.Common)(
                instructions_template, 
                tasks_template
            )

    def ensure_path(self, path=None) -> str:
        if path is None:
            path = self.DEFAULT_ROOT
        abs_path = os.path.abspath(os.path.expanduser(path))
        os.makedirs(abs_path, exist_ok=True)
        return abs_path

    def instructions(self, root: str = None,  **kwargs) -> str:
        return self.generator.instructions_generate(
            default_root=self.ensure_path(root),
            **kwargs
        )

    def tasks(self,
              datas: str,
              aims: str,
              root: str | Path = None,  # Optional, there is a default root setting: "~/Downloads/StataAgent"
              datas_describe: str = None,  # Optional
              **kwargs) -> str:
        root = self.ensure_path(root)
        return self.generator.tasks_generate(
            datas=datas, aims=aims, root=root, datas_describe=datas_describe, **kwargs
        )


if __name__ == "__main__":
    generator = PromptGenerator()
