#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : sandbox_manager.py

from ..jupyter_manager import KernelManager, KernelPool


class SandboxManager:
    def __init__(self):
        self.kernel_pool = KernelPool()
        self.kernel = KernelManager('stata')
