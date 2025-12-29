from stata_mcp.mcp_servers import stata_mcp as mcp


def main(transport: str = "stdio"):
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
