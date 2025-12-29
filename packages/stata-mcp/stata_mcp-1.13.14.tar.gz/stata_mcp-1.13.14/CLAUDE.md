# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stata-MCP is an MCP (Model Context Protocol) server that enables LLMs to execute Stata commands and perform regression analysis. It supports both MCP server mode and agent mode for interactive Stata analysis.

## Common Development Commands

### Environment Setup
```bash
# Install dependencies and create virtual environment
uv sync

# Install the package in development mode
uv pip install -e .

# Verify installation
stata-mcp --version
stata-mcp --usable
```

### Building and Distribution
```bash
# Build source distribution and wheels
uv build

# Build specific formats
uv build --sdist    # Source distribution only
uv build --wheel    # Wheel only

# Specify output directory
uv build --out-dir dist/
```

### Running the Application

#### MCP Server Mode (default)
```bash
# Start MCP server with stdio transport (default)
stata-mcp

# Start with specific transport
stata-mcp -t http    # HTTP transport
stata-mcp -t sse     # SSE transport
```

#### Agent Mode
```bash
# Run interactive agent mode
stata-mcp --agent

# Or use uvx for direct execution
uvx stata-mcp --agent
```

#### Utility Commands
```bash
# Check system compatibility
stata-mcp --usable

# Install to Claude Desktop
stata-mcp --install

# Check version
stata-mcp --version
```

### Development with uvx
```bash
# Run without local installation
uvx stata-mcp --version
uvx stata-mcp --agent
uvx stata-mcp --usable
```

## Architecture Overview

### Core Components

1. **MCP Server (`src/stata_mcp/__init__.py`)**
   - FastMCP-based server providing Stata tools and prompts
   - Main entry point for LLM interactions
   - Handles cross-platform Stata execution

2. **Stata Integration (`src/stata_mcp/core/stata/`)**
   - `StataFinder`: Locates Stata executable on different platforms
   - `StataController`: Manages Stata command execution
   - `StataDo`: Handles do-file execution with logging

3. **Agent Mode (`src/stata_mcp/mode/`)**
   - `StataAgent`: LangChain-based agent for autonomous analysis
   - Interactive conversational interface
   - Supports custom work directories and models

4. **Data Processing (`src/stata_mcp/core/data_info/`)**
   - `CsvDataInfo`: CSV file analysis and statistics
   - `DtaDataInfo`: Stata .dta file analysis
   - Automatic data type detection and summary statistics

5. **Sandbox System (`src/stata_mcp/sandbox/`)**
   - Secure execution environment
   - Jupyter kernel management for alternative execution
   - Result processing and file management

### MCP Tools Provided

- `help`: Get Stata command documentation
- `stata_do`: Execute Stata do-files
- `write_dofile`: Create Stata do-files from code
- `append_dofile`: Append code to existing do-files
- `get_data_info`: Analyze data files (CSV, DTA)
- `read_file`: Read file contents
- `ssc_install`: Install Stata packages from SSC
- `load_figure`: Load Stata-generated figures
- `mk_dir`: Create directories safely

### File Structure Conventions

```
~/Documents/stata-mcp-folder/
├── stata-mcp-log/      # Stata execution logs
├── stata-mcp-dofile/   # Generated do-files
├── stata-mcp-result/   # Analysis results
└── stata-mcp-tmp/      # Temporary files
```

### Cross-Platform Support

The project supports:
- **macOS**: Uses Stata MP from `/Applications/Stata/`
- **Windows**: Uses Stata MP from `Program Files`
- **Linux**: Uses `stata-mp` from system PATH

### Configuration

Environment variables:
- `lang`: Language setting ("en" or "cn")
- `documents_path`: Custom documents directory
- Stata executable path detection via `StataFinder`

## Git Commit Standards

Follow the project's git commit standards as defined in `source/docs/Rules/git_std_rule.md`:

- Use conventional commit format: `<type>(<scope>): <subject>`
- Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert
- Subject under 50 characters, imperative mood, lowercase
- Reference issues with `Closes #` or `Fixes #`
- No co-author information in commits (per user requirements)

## Important Notes

- All Python functions must have type annotations and English docstrings
- Use descriptive variable names
- Maintain proper code indentation
- The project requires a valid Stata license
- Default data output is in `~/Documents/stata-mcp-folder/`
- Agent mode supports multi-turn conversations with persistent data context
