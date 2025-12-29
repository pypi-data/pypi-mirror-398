#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : _model.py

import os

from openai import OpenAI

DEFAULT_CLIENT = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini-2025-08-07")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-5-mini-2025-08-07")
THINKING_MODEL = os.getenv("THINKING_MODEL")

print(DEFAULT_MODEL, CHAT_MODEL, THINKING_MODEL)
