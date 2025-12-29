#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : score_it.py

import uuid
from typing import List, Literal

from ._model import CHAT_MODEL, DEFAULT_CLIENT
from .advice import LANG_MAPPING


class ScoreModel:
    client = DEFAULT_CLIENT
    model = CHAT_MODEL
    print(model)

    instruction = """
    ## Role
    You are an evaluation and scoring model. When the user asks you to provide a score, you should evaluate the work based on the dialogue history. The full score is 100 points.  

    ## Workflow
    When the user requests scoring, you should follow the workflow below. Each part is worth 20 points, and you should assign scores accordingly:

    1. **Task Understanding**: Understand the user’s task and expectations based on the request and dialogue context.  
    2. **Result Evaluation**: Compare the user’s actual output with the reference or ideal result to measure task completion.  
    3. **Process Analysis**: Evaluate the task process from four dimensions (Agent’s reasoning, tool usage, error handling, and planning/organization).  
    4. **Score Generation**: Provide the Result Score and the Processer Score separately, with reasons for each.  
    5. **Final Score Summary**: Add the two parts together to obtain the final total score (FinalScore), and output it in the specified format.  

    ## Scoring Dimensions
    The scoring should be conducted from the following five dimensions:

    0. **Task Completion (Result)**: The gap between the actual output and the reference or ideal result.  
    1. **Reasoning**: Whether the Agent’s reasoning process is clear, coherent, and without major gaps or omissions.  
    2. **Tool Usage**: Whether tools are actively and correctly used to assist in completing the task, and whether the usage is efficient.  
    3. **Error Handling**: Whether errors, exceptions, or incomplete information are reasonably handled and corrected.  
    4. **Planning & Organization**: Whether the steps in the task execution are designed reasonably, showing structured planning and overall control.  

    ## Example
    ```
    <meta>
    TaskID: C1_C2
    Language: EN
    </meta>
    <score>
    <score_from_results>
    Result Score: 20 / 20
    Reason: ... (A example (it should be langer): This work result match to the reference result, and there is no matter about it.)
    </score_from_results>
    <score_from_processer>
    Processer Score: 68 / 80
    Reason: from 4 dim to describing the reason for this score ...
    <detail>
    <agent_reasoning>
    Score: 19 / 20
    Reason: ...
    </agent_reasoning>
    <tool_usage>
    Score: 17 / 20
    Reason: ...
    </tool_usage>
    <error_handling>
    Score: 12 / 20
    Reason: ...
    </error_handling>
    <planning>
    Score: 20 / 20
    Reason: ...
    </planning>

    </detail>
    </score_from_processer>
    <final_score>
    FinalScore: 88 = 20 + 68
    </final_score>
    </score>
    ```

    ## Some Information for example
    Please remember, ths sign "`" is should not be return.
    The language is describe the language of task, processer and results' language, you can choose "zh-CN", "EN".
    The total score will equal to sum up of each one.
    And the type of score must be int.
    The 4 dimensions refer to [Agent’s reasoning, tool usage, error handling, planning & organization].
    """

    def __init__(self,
                 task: str,
                 reference_answer: str,
                 processer: str,
                 results: str,
                 task_id: str = None,
                 lang: Literal["en", "cn"] = "en"):
        self.task = task
        self.task_id = task_id or uuid.uuid4().__str__()
        self.reference_answer = reference_answer
        self.processer = processer
        self.results = results

        self.lang = lang

    @property
    def advice_models(self) -> dict:
        return LANG_MAPPING[self.lang]

    @property
    def positive_advice_model(self):
        return self.advice_models["positive"]

    @property
    def negative_advice_model(self):
        return self.advice_models["negative"]

    def score_it(self) -> str:
        print("========== Start Score it ==========")
        positive_advice = self.positive_advice_model().advice(self.task, self.processer, self.reference_answer)
        negative_advice = self.negative_advice_model().advice(self.task, self.processer, self.reference_answer)

        msg: List = [
            {"role": "system", "content": self.instruction},

            {
                "role": "user",
                "content":
                    "Here is the task: " + self.task +
                    "\nAnd task id is: " + self.task_id
            },
            {
                "role": "user",
                "content":
                    "Here is the adjust rule or we can say it is the reference answer, "
                    "(but please note that it is not the certain answer):\n" + self.reference_answer
            },
            {
                "role": "assistant",
                "content":
                    "I have known about the task and the score rule! "
                    "Please give me the processer and the result."
            },

            {"role": "user", "content": "Here is the processer: "+self.processer},
            {"role": "user", "content": "Here is the result: "+self.results},

            {"role": "assistant", "content": "OK! I have got the information, what should we do now?"},

            {"role": "user", "content": "please give the positive advice without score"},
            {"role": "assistant", "content": positive_advice},
            {"role": "user", "content": "please give the negative advice without score"},
            {"role": "assistant", "content": negative_advice},

            {"role": "user", "content": "Now please give me the finial score and the details"},
        ]
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=msg
        )
        final_score_str = resp.choices[0].message.content

        return final_score_str
