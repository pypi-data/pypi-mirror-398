#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : cwd_cfg.py

from pathlib import Path


# TODO: Add the save guard for relative path like "../../"
def get_exp_cwd(path: str | Path = ".") -> Path:
    """
    Config the current working directory
    """
    path_obj = Path(path).expanduser()  # solve the problem like Path("~/Documents").is_absolute()
    if path_obj.is_absolute():
        try:
            path_obj.mkdir(parents=True, exist_ok=True)
            return path_obj
        except OSError as e:
            raise e
    else:
        TERMINAL_CURRENT_PATH = Path.cwd()
        combined_path = (TERMINAL_CURRENT_PATH / path_obj).resolve()
        combined_path.mkdir(parents=True, exist_ok=True)
        return combined_path
