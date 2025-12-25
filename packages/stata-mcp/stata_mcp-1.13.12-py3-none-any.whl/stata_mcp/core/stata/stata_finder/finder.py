#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : finder.py

import glob
import logging
import os
import platform
from typing import Optional

from .linux import FinderLinux
from .macos import FinderMacOS
from .windows import FinderWindows, get_available_drives, windows_stata_match


class StataFinder:
    FINDER_MAPPING = {
        "Darwin": FinderMacOS,
        "Windows": FinderWindows,
        "Linux": FinderLinux,
    }

    def __init__(self, stata_cli: str = None):
        finder_cls = self.FINDER_MAPPING.get(platform.system())
        self.finder = finder_cls(stata_cli)

    @property
    def STATA_CLI(self) -> str | None:
        try:
            return self.finder.find_stata()
        except (FileNotFoundError, AttributeError):
            return None


class StataFinderOLD:
    """A class to find Stata CLI installations across different operating systems."""

    FINDER_MAPPING = {
        "Darwin": FinderMacOS,
        "Windows": FinderWindows,
        "Linux": FinderLinux,
    }

    def __init__(self, stata_cli: str = None):
        """
        Initialize the StataFinder.

        Args:
            stata_cli (str): the user updates stata_cli file path
        """
        self.current_os = platform.system()
        self._os_finders = {
            "Darwin": self._find_stata_macos,
            "Windows": self._find_stata_windows,
            "Linux": self._find_stata_linux,
        }
        self.finder = self._os_finders.get(self.current_os, None)
        # TODO: Change the original finder to the newer
        # self.finder = self.FINDER_MAPPING.get(self.current_os)(stata_cli = stata_cli)

    # @property
    # def STATA_CLI(self) -> str:  # 等前面的都改好了，就可以只保留这个了
    #     return self.finder.find_stata()

    def _stata_version_windows(self, driver: str = "C:\\") -> list:
        """Find Stata installations on Windows."""
        stata_paths = []
        common_patterns = [
            os.path.join(driver, "Program Files", "Stata*", "*.exe"),
            os.path.join(driver, "Program Files(x86)", "Stata*", "*.exe"),
        ]

        for pattern in common_patterns:
            try:
                matches = glob.glob(pattern)
                for match in matches:
                    if "stata" in match.lower() and match.lower().endswith(".exe"):
                        stata_paths.append(match)

                if not stata_paths:
                    for root, dirs, files in os.walk(driver):
                        if root.count(os.sep) - driver.count(os.sep) > 3:
                            dirs.clear()
                            continue

                        for file in files:
                            if (
                                file.lower().endswith(".exe")
                                and "stata" in file.lower()
                            ):
                                stata_paths.append(os.path.join(root, file))

            except Exception as e:
                logging.warn(e)

        return stata_paths

    def _find_stata_macos(self) -> Optional[str]:
        return self.finder.find_stata()

    def _default_stata_cli_path_windows(self) -> Optional[str]:
        """Get default Stata CLI path on Windows."""
        drives = get_available_drives()
        stata_cli_path_list = []

        for drive in drives:
            stata_cli_path_list += self._stata_version_windows(drive)

        if len(stata_cli_path_list) == 0:
            return None
        elif len(stata_cli_path_list) == 1:
            return stata_cli_path_list[0]
        else:
            for path in stata_cli_path_list:
                if windows_stata_match(path):
                    return path
            return stata_cli_path_list[0]

    def _find_stata_windows(self) -> Optional[str]:
        """Find Stata CLI on Windows systems."""
        return self._default_stata_cli_path_windows()

    def _default_stata_cli_path_linux(self) -> Optional[str]:
        """Get default Stata CLI path on Linux."""
        # TODO: Implement Linux-specific logic
        return None

    def _find_stata_linux(self) -> Optional[str]:
        """Find the Stata CLI path on Linux systems.

        For Linux users, this function attempts to locate the Stata CLI executable.

        Returns:
            The path to the Stata CLI executable, or None if not found.
        """
        return self._default_stata_cli_path_linux()

    def find_stata(self,
                   os_name: Optional[str] = None,
                   is_env: bool = True) -> Optional[str]:
        """Find Stata CLI installation.

        Args:
            os_name: Operating system name. If None, uses current system.
            is_env: Whether to check environment variables first.

        Returns:
            Path to Stata CLI executable, or None if not found.

        Raises:
            RuntimeError: If the operating system is not supported.
        """
        if is_env:
            stata_cli = os.getenv("stata_cli", None) or os.getenv("STATA_CLI", None)
            if stata_cli:
                return stata_cli

        target_os = os_name or self.current_os
        finder = self._os_finders.get(target_os)

        if not finder:
            raise RuntimeError(f"Unsupported OS: {target_os!r}")

        return finder()

    def get_supported_os(self) -> list:
        """Get list of supported operating systems."""
        return list(self._os_finders.keys())

    def is_stata_available(
        self, os_name: Optional[str] = None, is_env: bool = True
    ) -> bool:
        """Check if Stata is available on the system.

        Args:
            os_name: Operating system name. If None, uses current system.
            is_env: Whether to check environment variables first.

        Returns:
            True if Stata is found, False otherwise.
        """
        try:
            stata_path = self.find_stata(os_name=os_name, is_env=is_env)
            return stata_path is not None
        except RuntimeError:
            return False
