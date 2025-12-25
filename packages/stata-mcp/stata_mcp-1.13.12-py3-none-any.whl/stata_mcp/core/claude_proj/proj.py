#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : proj.py

from pathlib import Path

from .cwd_cfg import get_exp_cwd


class ClaudeProject:
    def __init__(self, cwd: str = "."):
        self.cwd = Path(get_exp_cwd(cwd))
        self.source_dir = self.cwd / "source"

    def init_project(self): ...

    def write_claude_md(self): ...

    def mk_data_dir(self):
        """
        创建一系列目录

        """
        data_dir = self.source_dir / "data"
        raw_data_dir = data_dir / "raw"
        middle_data_dir = data_dir / "middle"
        final_data_dir = data_dir / "final"

        self.mk_dir_exist(raw_data_dir)
        self.mk_dir_exist(middle_data_dir)
        self.mk_dir_exist(final_data_dir)

    @staticmethod
    def mk_dir_exist(path: str | Path) -> bool:
        """
        Create directory if it doesn't exist and return whether it exists.

        Args:
            path: Directory path to ensure exists

        Returns:
            bool: True if directory exists (or was successfully created), False if failed
        """
        path_obj = Path(path)
        if not path_obj.exists():
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
            except OSError:
                return False
        return path_obj.is_dir()
