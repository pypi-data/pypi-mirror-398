#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : claude_cfg.py

import platform
import shutil
import subprocess
import webbrowser
from typing import Dict


def check_claude_code(claude_cmd: str = "claude") -> bool:
    return shutil.which(claude_cmd) is not None


def guide_for_install_claude_code(base_doc_url: str = None):
    if base_doc_url is None:
        base_doc_url = "https://docs.statamcp.com/guide_claude_code.html"

    CURRENT_OS = platform.system()
    os_mapping = {
        "Darwin": "macos",
        "Windows": "windows",
        "Linux": "linux"
    }
    url = f"{base_doc_url}#{os_mapping.get(CURRENT_OS, '')}"

    webbrowser.open(url)
    return None


def install_stata_mcp_for_claude_code(cwd: str) -> bool:
    try:
        # Execute claude mcp command to install stata-mcp
        command = [
            "claude", "mcp", "add", "stata-mcp",
            "--env", f"STATA_MCP_CWD={cwd}",
            "--", "uvx", "stata-mcp"
        ]

        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60  # Add timeout to prevent hanging
        )

        # Return True if command executed successfully
        return result.returncode == 0

    except subprocess.TimeoutExpired:
        return False
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def claude_mcp_list(cwd: str = None) -> Dict[str, dict]:
    """
    Parse the output of 'claude mcp list' command and return a structured dictionary.

    Terminal output example:
    Checking MCP server health...

    github: https://api.githubcopilot.com/mcp (HTTP) - ✓ Connected
    context7: npx -y @upstash/context7-mcp --api-key xxxxx-xxxxx-xxxxx-xxxxx - ✓ Connected
    markitdown: /Users/sepinetam/my_local_mcp/mkitdown-mcp/.venv/bin/markitdown-mcp  - ✓ Connected

    Expected return format:
    {
        "github": {
            "cfg": "https://api.githubcopilot.com/mcp (HTTP)",
            "state": True
        },
        "context7": {
            "cfg": "npx -y @upstash/context7-mcp --api-key xxxxx-xxxxx-xxxxx-xxxxx",
            "state": True
        },
        "markitdown": {
            "cfg": "/Users/sepinetam/my_local_mcp/mkitdown-mcp/.venv/bin/markitdown-mcp",
            "state": True
        },
    }

    If there is no mcp config, the expected output like:
    No MCP servers configured. Use `claude mcp add` to add a server.

    At this, return {}
    """
    try:
        command = ["claude", "mcp", "list"]

        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return {}

        output = result.stdout.strip()

        # Check for no MCP servers configured
        if not output or "No MCP servers configured" in output:
            return {}

        mcp_servers: Dict[str, dict] = {}
        lines = output.split('\n')

        for line in lines:
            line = line.strip()

            # Skip empty lines and health check messages
            if not line or line.startswith("Checking MCP server health"):
                continue

            # Skip "No MCP servers configured" message
            if "No MCP servers configured" in line:
                return {}

            # Parse server configuration lines
            if ':' in line:
                # Split by first colon to get server name and config
                parts = line.split(':', 1)
                if len(parts) < 2:
                    continue

                server_name = parts[0].strip()
                config_part = parts[1].strip()

                # Check connection status
                is_connected = "✓ Connected" in config_part

                # Extract configuration by removing the connection status part
                if " - ✓ Connected" in config_part:
                    config = config_part.replace(" - ✓ Connected", "").strip()
                elif " - ✗" in config_part:
                    config = config_part.split(" - ✗")[0].strip()
                elif "Failed" in config_part:
                    # Handle cases like "Failed to connect" or similar error messages
                    config = config_part.split(" -")[0].strip()
                else:
                    config = config_part.strip()

                # Add to result dictionary
                mcp_servers[server_name] = {
                    "cfg": config,
                    "state": is_connected
                }

        return mcp_servers

    except subprocess.TimeoutExpired:
        return {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


if __name__ == "__main__":
    print(claude_mcp_list("/Users/sepinetam/Documents/Github/stata-mcp"))
