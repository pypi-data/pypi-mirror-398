#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : kernel_manager.py

import logging
import sys
from typing import Dict

from jupyter_client.kernelspec import KernelSpecManager


class KernelManager:
    def __init__(self,
                 kernel_name: str = "stata"):
        self.kernel_name = kernel_name
        self.kernel_path = self.find_kernel()

    def find_kernel(self,
                    kernel_name: str = None) -> str:
        if not kernel_name:
            kernel_name = self.kernel_name

        kernels_dict: Dict[str, str] = KernelSpecManager().find_kernel_specs()

        if kernel_name in set(kernels_dict.keys()):
            return kernels_dict.get(kernel_name)
        else:
            logging.warning(
                "Kernel not found, please install it.\n"
                "You can run `pip install stata_kernel` to deal it")
            sys.exit(1)


if __name__ == '__main__':
    # list jupyter kernel
    ksm = KernelSpecManager()
    print(ksm.find_kernel_specs())

    print(KernelManager().find_kernel())
