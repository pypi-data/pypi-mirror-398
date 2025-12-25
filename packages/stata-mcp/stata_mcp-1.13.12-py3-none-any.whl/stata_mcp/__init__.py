from importlib.metadata import version

__version__ = version("stata-mcp")
__author__ = "Song Tan <sepine@statamcp.com>"


if __name__ == "__main__":
    print(f"Hello Stata-MCP@version{__version__}")
