#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : _cli.py

import argparse
import os
import sys
from importlib.metadata import version


def main() -> None:
    """Entry point for the command line interface."""
    parser = argparse.ArgumentParser(
        prog="stata-mcp",
        description="Stata-MCP command line interface",
        add_help=True)
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Stata-MCP version is {version('stata-mcp')}",
        help="show version information",
    )
    parser.add_argument(
        "-a", "--agent",
        nargs="?",
        const="./",
        help="run Stata-MCP as agent mode (default work dir: current working directory)",
    )
    parser.add_argument(
        "-c", "--client",
        nargs="?",
        const="cc",
        help="set the client mode (default for Claude Code)"
    )
    parser.add_argument(
        "--usable",
        action="store_true",
        help="check whether Stata-MCP could be used on this computer",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="install Stata-MCP to Claude Desktop")

    # mcp.run
    parser.add_argument(
        "-t",
        "--transport",
        choices=["stdio", "sse", "http", "streamable-http"],
        default=None,
        help="mcp server transport method (default: stdio)",
    )
    args = parser.parse_args()

    if args.usable:
        from ..utils.usable import usable
        sys.exit(usable())

    elif args.install:
        from ..utils.Installer import Installer
        Installer(sys_os=sys.platform).install()

    elif args.agent:
        from ..agent_as import REPLAgent
        agent = REPLAgent(work_dir=args.agent)
        agent.run()

    elif args.client:
        os.environ["STATA-MCP-CLIENT"] = "cc"

        from ..mcp_servers import stata_mcp as mcp

        mcp.run()

    else:
        from ..mcp_servers import stata_mcp as mcp

        print("Starting Stata-MCP...")

        # Use stdio if there is no transport argument
        transport = args.transport or "stdio"
        if transport == "http":
            transport = (
                "streamable-http"  # Default to streamable-http for HTTP transport
            )
        mcp.run(transport=transport)
