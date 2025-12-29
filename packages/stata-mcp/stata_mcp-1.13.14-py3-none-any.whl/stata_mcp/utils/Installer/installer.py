#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : installer.py

import json
import os

from ...core.stata import StataFinder


class Installer:
    def __init__(self, sys_os, is_env=False):
        self.config_file_path: str = None
        if sys_os == "Darwin":
            self.config_file_path = os.path.expanduser(
                "~/Library/Application Support/Claude/claude_desktop_config.json"
            )
        elif sys_os == "Linux":
            print(
                "There is not a Linux version of Claude yet, please use the Windows or macOS version."
            )
        elif sys_os == "Windows":
            appdata = os.getenv(
                "APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
            self.config_file_path = os.path.join(
                appdata, "Claude", "claude_desktop_config.json"
            )

        os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)

        # Create an empty file if it does not already exist
        if not os.path.exists(self.config_file_path):
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                # Or write the default configuration
                f.write('{"mcpServers": {}}')

        stata_cli = StataFinder().STATA_CLI
        self.stata_mcp_config = {
            "stata-mcp": {
                "command": "uvx",
                "args": ["stata-mcp"],
                "env": {"STATA_CLI": stata_cli},
            }
        }

    def install(self):
        server_cfg = self.stata_mcp_config["stata-mcp"]
        stata_cli_path = server_cfg["env"]["STATA_CLI"]
        print("About to install the following MCP server into your Claude config:\n")
        print("  Server name:    stata-mcp")
        print(f"  Command:        {server_cfg['command']}")
        print(f"  Args:           {server_cfg['args']}")
        print(f"  STATA_CLI path: {stata_cli_path}\n")
        print(f"Configuration file to modify:\n  {self.config_file_path}\n")

        # Ask the user for confirmation
        choice = input(
            "Do you want to proceed and add this configuration? [y/N]: ")
        if choice.strip().lower() != "y":
            print("Installation aborted.")
            return

        # Read the now config
        try:
            with open(self.config_file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {"mcpServers": {}}

        # Update MCP_Config
        servers = config.setdefault("mcpServers", {})
        servers.update(self.stata_mcp_config)

        # Write it
        with open(self.config_file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(
            f"✅ Successfully wrote 'stata-mcp' configuration to: {self.config_file_path}"
        )
