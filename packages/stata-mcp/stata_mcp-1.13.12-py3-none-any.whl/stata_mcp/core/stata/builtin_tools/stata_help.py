#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : stata_help.py

from ..stata_controller import StataController


class StataHelp:
    def __init__(self, stata_cli: str):
        self.controller = StataController(stata_cli)

    def help(self, cmd: str) -> str:
        std_error_msg = (
            f"help {cmd}\r\n"
            f"help for {cmd} not found\r\n"
            f"try help contents or search {cmd}"
        )
        help_result = self.controller.run(f"help {cmd}")

        if help_result != std_error_msg:
            return help_result
        else:
            raise Exception("No help found for the command in Stata ado locally: " + cmd)

    def check_command_exist_with_help(self, cmd: str) -> bool:
        std_error_msg = (
            f"help {cmd}\r\n"
            f"help for {cmd} not found\r\n"
            f"try help contents or search {cmd}"
        )
        help_result = self.controller.run(f"help {cmd}")
        if help_result != std_error_msg:
            return True
        else:
            return False
