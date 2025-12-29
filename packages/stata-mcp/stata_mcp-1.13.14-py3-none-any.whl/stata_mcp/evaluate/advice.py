#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : advice.py

from abc import ABC
from typing import Dict, List

from openai import OpenAI

from ._model import DEFAULT_CLIENT, THINKING_MODEL


class AdviceModelBase(ABC):
    CLIENT: OpenAI = DEFAULT_CLIENT
    MODEL: str = THINKING_MODEL

    INSTRUCTION: str
    RULE: str

    def __init__(self, client: OpenAI = None, model: str = None):
        self.client = client or self.CLIENT
        self._model = model

    @property
    def model(self) -> str:
        return self._model or self.MODEL

    @property
    def instruction(self) -> str:
        return self.INSTRUCTION

    def _set_reference_answer(self, reference_answer: str):
        self.reference_answer = reference_answer

    def advice(self, task: str, processer: str | List[str], reference_answer: str = None) -> str:
        if isinstance(processer, str):
            pass
        elif isinstance(processer, list):
            processer = "\n".join(processer)

        # 设置reference_answer，如果提供了的话
        if reference_answer is not None:
            self._set_reference_answer(reference_answer)

        msg: List = [
            {
                "role": "system",
                "content": self.instruction
            },
            {
                "role": "user",
                "content": "Here is the task information: " + task
            },
            {
                "role": "assistant",
                "content": "I have known this reference_answer, now please give me reference answer."
            },
            {
                "role": "user",
                "content": self.reference_answer or self.RULE
            },
            {
                "role": "assistant",
                "content": "I have known this reference_answer, now please give me the process information"
            },
            {
                "role": "user",
                "content": processer
            }
        ]
        resp = self.client.chat.completions.create(
            model=self.MODEL,
            messages=msg,
        )
        return resp.choices[0].message.content


class AdvicePositiveCN(AdviceModelBase):
    INSTRUCTION = """
    ## 任务说明：
    根据提供的规则和信息，给出积极的评价。请确保你的评价是客观的，并且避免打分或做任何主观评判。
    评价应该集中在对信息或行为中的正面方面进行描述，突出任务在完成过程中表现好的地方。

    ## 具体要求：
    1. 在评价时，聚焦于信息或行为的积极方面。比如，表扬其创新性、有效性、合作性等。
    2. 避免任何负面或中立的描述。若无法找到完全正面的内容，可以尽可能强调其潜力或已有的成就。
    3. 使用清晰且专业的语言，确保评价简洁且不带任何偏见。
    4. 不需要给出分数、等级或排名。
    5. 确保评价中的措辞不会引起误解或误导，保持客观和公正。
    """


class AdviceNegativeCN(AdviceModelBase):
    INSTRUCTION = """
    ## 任务说明：
    根据提供的规则和信息，给出消极的评价。请确保你的评价是客观的，并且避免打分或做任何主观评判。
    评价应该集中在对信息或行为中的不足之处进行描述，突出任务在完成过程中存在的问题或需改进的地方。

    ## 具体要求：
    1. 在评价时，聚焦于信息或行为的不足方面。比如，指出其目标偏差、有效性不足、协作不充分等。
    2. 避免任何正面或中立的描述。若无法确定具体问题，可以尽可能指出潜在风险或尚未覆盖的环节。
    3. 使用清晰且专业的语言，确保评价简洁且不带任何偏见。
    4. 不需要给出分数、等级或排名。
    5. 确保评价中的措辞不会引起误解或误导，保持客观和公正。
    """


class AdvicePositive(AdviceModelBase):
    INSTRUCTION = """
    ## Task Description:
    Provide positive feedback based on the given reference_answers and information. Ensure the evaluation is objective and avoid assigning scores or making any subjective judgments.
    The feedback should focus on describing the positive aspects of the information or behavior, highlighting what was done well during the task.

    ## Specific Requirements:
    1. Focus on the positive aspects of the information or behavior, such as praising its innovativeness, effectiveness, or collaboration.
    2. Avoid any negative or neutral descriptions. If purely positive aspects cannot be found, emphasize its potential or existing achievements as much as possible.
    3. Use clear and professional language to ensure the feedback is concise and unbiased.
    4. No scores, grades, or rankings are needed.
    5. Ensure that the wording will not cause misunderstanding or mislead, maintaining objectivity and fairness.
    """


class AdviceNegative(AdviceModelBase):
    INSTRUCTION = """
    ## Task Description:
    Provide negative feedback based on the given reference_answers and information. Ensure the evaluation is objective and avoid assigning scores or making any subjective judgments.
    The feedback should focus on describing the shortcomings of the information or behavior, highlighting the problems or areas needing improvement during the task.

    ## Specific Requirements:
    1. Focus on the shortcomings of the information or behavior, such as pointing out goal deviations, lack of effectiveness, or insufficient collaboration.
    2. Avoid any positive or neutral descriptions. If specific problems cannot be identified, highlight potential risks or uncovered aspects as much as possible.
    3. Use clear and professional language to ensure the feedback is concise and unbiased.
    4. No scores, grades, or rankings are needed.
    5. Ensure that the wording will not cause misunderstanding or mislead, maintaining objectivity and fairness.
    """


LANG_MAPPING: Dict[str, dict] = {
    "cn": {
        "positive": AdvicePositiveCN,
        "negative": AdviceNegativeCN
    },
    "en": {
        "positive": AdvicePositive,
        "negative": AdviceNegative
    },
}
