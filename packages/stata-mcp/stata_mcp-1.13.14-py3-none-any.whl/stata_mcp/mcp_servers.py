#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : mcp_servers.py

import hashlib
import json
import logging
import logging.handlers
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP, Icon, Image

from .core.data_info import CsvDataInfo, DtaDataInfo
from .core.stata import StataDo, StataFinder
from .core.stata.builtin_tools import StataHelp as Help
from .core.stata.builtin_tools.ado_install import GITHUB_Install, NET_Install, SSC_Install
from .utils.Prompt import pmp

# Maybe somebody does not like logging.
# Whatever, left a controller switch `logging STATA_MCP_LOGGING_ON`. Turn off all logging with setting it as false.
# Default Logging Status: File (on), Console (off).
IS_DEBUG = False
if os.getenv("STATA_MCP_LOGGING_ON", 'true').lower() == 'true':
    # Configure logging
    logging_handlers = []

    if os.getenv("STATA_MCP_LOGGING_CONSOLE_HANDLER", 'false').lower() == 'true':
        # config logging in console.
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        logging_handlers.append(console_handler)

    if len(logging_handlers) == 0 or os.getenv("STATA_MCP_LOGGING_FILE_HANDLER", 'true').lower() == 'true':
        # If there is no handler, must add file-handler with rotation support.
        IS_DEBUG = True
        stata_mcp_dot_log_file_path = os.getenv(
            "STATA_MCP_LOG_FILE", None
        )
        if stata_mcp_dot_log_file_path:
            stata_mcp_dot_log_file_path = Path(stata_mcp_dot_log_file_path).expanduser().absolute()
        else:
            stata_mcp_dot_log_file_path = Path.home() / ".statamcp/stata_mcp_debug.log"
        stata_mcp_dot_log_file_path.parent.mkdir(exist_ok=True, parents=True)

        # Use RotatingFileHandler to limit file size and implement log rotation
        # Single file max size: 10MB, backup count: 5 (total 6 files including current)
        file_handler = logging.handlers.RotatingFileHandler(
            stata_mcp_dot_log_file_path,
            maxBytes=10_000_000,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        logging_handlers.append(file_handler)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=logging_handlers
    )
else:
    # I am not sure about whether this command would disable logging, and there is another suggestion
    # logging.basicConfig(level=logging.CRITICAL + 1)
    logging.disable()

# Initialize optional parameters
SYSTEM_OS = platform.system()

if SYSTEM_OS not in ["Darwin", "Linux", "Windows"]:
    # Here, if unknown system -> exit.
    sys.exit(f"Unknown System: {SYSTEM_OS}")

# Define IS_UNIX for cleaner conditional logic
IS_UNIX = SYSTEM_OS.lower() != "windows"
IS_SAVE_HELP = os.getenv("STATA_MCP_SAVE_HELP", 'true').lower() == "true"

# Set stata_cli
try:
    # find stata_cli, env first, then default path
    finder = StataFinder()
    STATA_CLI = finder.STATA_CLI
except FileNotFoundError as e:
    sys.exit(str(e))

cwd = os.getenv("STATA_MCP_CWD", os.getenv("STATA-MCP-CWD", None))  # Keep STATA-MCP-CWD for backward compatibility.
if not cwd:  # If there is no CWD config in environment, use `~/Documents` as working directory.
    cwd = Path.home() / "Documents"
else:
    cwd = Path(cwd)
    proj_name = cwd.name
    logging.info(f"Project name: {proj_name} in {cwd}") if IS_DEBUG else None  # Log project name if debug is enabled

# Use configured output path if available
output_base_path = cwd / "stata-mcp-folder"
output_base_path.mkdir(exist_ok=True, parents=True)  # make sure this folder exists

# Create a series of folder
log_base_path = output_base_path / "stata-mcp-log"
log_base_path.mkdir(exist_ok=True)
dofile_base_path = output_base_path / "stata-mcp-dofile"
dofile_base_path.mkdir(exist_ok=True)
result_doc_path = output_base_path / "stata-mcp-result"
result_doc_path.mkdir(exist_ok=True)
tmp_base_path = output_base_path / "stata-mcp-tmp"
tmp_base_path.mkdir(exist_ok=True)

# Config gitignore in STATA_MCP_FOLDER
if not (GITIGNORE_FILE := output_base_path / ".gitignore").exists():
    with open(GITIGNORE_FILE, "w", encoding="utf-8") as f:
        f.write("*")


# Initialize MCP Server, avoiding FastMCP server timeout caused by Icon src fetch
instructions = ("Stata-MCP provides a set of tools to operate Stata locally. "
                "Typically, it writes code to do-file and executes them. "
                "The minimum operation unit should be the do-file; there is no session config.")
try:
    stata_mcp = FastMCP(
        name="stata-mcp",
        instructions=instructions,
        website_url="https://www.statamcp.com",
        icons=[Icon(
            src="https://r2.statamcp.com/android-chrome-512x512.png",
            mimeType="image/png",
            sizes=["512x512"]
        )]
    )
except Exception:
    stata_mcp = FastMCP(
        name="stata-mcp",
        instructions=instructions,
        website_url="https://www.statamcp.com",
    )

IS_PROMPT = os.getenv("STATA_MCP_PROMPT", 'true').lower() == 'true'


@stata_mcp.prompt()
def stata_assistant_role(lang: str = None) -> str:
    """
    Return the Stata assistant role prompt content.

    This function retrieves a predefined prompt that defines the role and capabilities
    of a Stata analysis assistant. The prompt helps set expectations and context for
    the assistant's behavior when handling Stata-related tasks.

    Args:
        lang (str, optional): Language code for localization of the prompt content.
            If None, returns the default language version. Defaults to None.
            Examples: "en" for English, "cn" for Chinese.

    Returns:
        str: The Stata assistant role prompt text in the requested language.

    Examples:
        >>> stata_assistant_role()  # Returns default language version
        "I am a Stata analysis assistant..."

        >>> stata_assistant_role(lang="en")  # Returns English version
        "I am a Stata analysis assistant..."

        >>> stata_assistant_role(lang="cn")  # Returns Chinese version
        "我是一个Stata分析助手..."
    """
    return pmp.get_prompt(prompt_id="stata_assistant_role", lang=lang)


@stata_mcp.prompt()
def stata_analysis_strategy(lang: str = None) -> str:
    """
    Return the Stata analysis strategy prompt content.

    This function retrieves a predefined prompt that outlines the recommended
    strategy for conducting data analysis using Stata. The prompt includes
    guidelines for data preparation, code generation, results management,
    reporting, and troubleshooting.

    Args:
        lang (str, optional): Language code for localization of the prompt content.
            If None, returns the default language version. Defaults to None.
            Examples: "en" for English, "cn" for Chinese.

    Returns:
        str: The Stata analysis strategy prompt text in the requested language.

    Examples:
        >>> stata_analysis_strategy()  # Returns default language version
        "When conducting data analysis using Stata..."

        >>> stata_analysis_strategy(lang="en")  # Returns English version
        "When conducting data analysis using Stata..."

        >>> stata_analysis_strategy(lang="cn")  # Returns Chinese version
        "使用Stata进行数据分析时，请遵循以下策略..."
    """
    return pmp.get_prompt(prompt_id="stata_analysis_strategy", lang=lang)


if IS_UNIX:
    # Config help class
    help_cls = Help(STATA_CLI)

    # As AI-Client does not support Resource at a board yet, we still keep the prompt
    @stata_mcp.resource(
        uri="help://stata/{cmd}",
        name="help",
        description="Get help for a Stata command"
    )
    @stata_mcp.prompt(name="help", description="Get help for a Stata command")
    @stata_mcp.tool(name="help", description="Get help for a Stata command")
    def help(cmd: str) -> str:
        """
        Execute the Stata 'help' command and return its output.

        Args:
            cmd (str): The name of the Stata command to query, e.g., "regress" or "describe".

        Returns:
            str: The help text returned by Stata for the specified command,
                 or a message indicating that no help was found.
        """
        help_file = (tmp_base_path / f"help__{cmd}.txt")
        try:
            with open(help_file, "r", encoding="utf-8") as f:
                content = f.read()
            if content:
                logging.info(f"Successfully retrieved help for command: {cmd} from local storage.")
                return content
        except FileNotFoundError:
            pass
        try:
            help_result = help_cls.help(cmd)
            logging.info(f"Successfully retrieved help for command: {cmd} from Stata.")
            if IS_SAVE_HELP:
                with open(help_file, "w", encoding="utf-8") as help_file:
                    help_file.write(help_result)
                help_result = help_result + f"\n{cmd} help file: {help_file}"
            return help_result
        except Exception as e:
            logging.error(f"Failed to retrieve help for command: {cmd}.")
            logging.debug(str(e))
            return f"No help found for command: {cmd}"


@stata_mcp.tool(
    name="read_file",
    description="Reads a file and returns its content as a string"
)
def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    Reads the content of a file and returns it as a string.

    Args:
        file_path (str): The full path to the file to be read.
        encoding (str, optional): The encoding used to decode the file. Defaults to "utf-8".

    Returns:
        str: The content of the file as a string.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"The file at {file_path} does not exist.")

    try:
        with open(path, "r", encoding=encoding) as file:
            log_content = file.read()
        logging.info(f"Successfully read file: {file_path}")
        return log_content
    except IOError as e:
        logging.error(f"Failed to read file {file_path}: {str(e)}")
        raise IOError(f"An error occurred while reading the file: {e}")


@stata_mcp.tool(
    name="get_data_info",
    description="Get descriptive statistics for the data file"
)
def get_data_info(data_path: str | Path,
                  vars_list: Optional[List[str]] = None,
                  encoding: str = "utf-8") -> str:
    """
    Get descriptive statistics for the data file.

    Args:
        data_path (str): the data file's absolutely path.
            Current, only allow [dta, csv] file.
        vars_list (Optional[List[str]]): the vars you want to get info (default is None, means all vars).
        encoding (str): data file encoding method (dta file is not supported this arg),
            if you do not know your data ignore this arg, for most of the data files are `UTF-8`.

    Returns:
        str: the return result is a type <str> but looks like a type <dict>, including the `info_filter` as keys.
            there is a more details which saved all the information about the data, visit the value of `saved_path`.

    Examples:
        >>> get_data_info("/Applications/Stata/auto.dta")
        {
            'overview': {'obs': 74, 'var_numbers': 12},
            'vars_detail': {
                'make': {'type': 'str', 'obs': 74, 'value_list': ['Buick Skylark', 'Chev. Chevette', ...]},
                'price': {'type': 'float', 'obs': 74,
                          'summary': {'mean': 6165.257, 'se': np.float64(342.872), 'min': 3291.0, 'max': 15906.0}},
                'mpg': {'type': 'float', 'obs': 74,
                        'summary': {'mean': 21.297, 'se': np.float64(0.673), 'min': 12.0, 'max': 41.0}},
                'rep78': {'type': 'float', 'obs': 69,
                          'summary': {'mean': 3.406, 'se': np.float64(0.119), 'min': 1.0, 'max': 5.0}},
                'headroom': {'type': 'float', 'obs': 74,
                             'summary': {'mean': 2.993, 'se': np.float64(0.098), 'min': 1.5, 'max': 5.0}},
                'trunk': {'type': 'float', 'obs': 74,
                          'summary': {'mean': 13.757, 'se': np.float64(0.497), 'min': 5.0, 'max': 23.0}},
                'weight': {'type': 'float', 'obs': 74,
                           'summary': {'mean': 3019.459, 'se': np.float64(90.347), 'min': 1760.0, 'max': 4840.0}},
                'length': {'type': 'float', 'obs': 74,
                           'summary': {'mean': 187.932, 'se': np.float64(2.588), 'min': 142.0, 'max': 233.0}},
                'turn': {'type': 'float', 'obs': 74,
                         'summary': {'mean': 39.649, 'se': np.float64(0.511), 'min': 31.0, 'max': 51.0}},
                'displacement': {'type': 'float', 'obs': 74,
                                 'summary': {'mean': 197.297, 'se': np.float64(10.676), 'min': 79.0, 'max': 425.0}},
                'gear_ratio': {'type': 'float', 'obs': 74,
                               'summary': {'mean': 3.015, 'se': np.float64(0.053), 'min': 2.190, 'max': 3.890}},
                'foreign': {'type': 'float', 'obs': 74,
                            'summary': {'mean': 0.297, 'se': np.float64(0.053), 'min': 0.0, 'max': 1.0}}},
            'saved_path': '/Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-tmp/auto.json'
        }
    """
    # Config the allowed class
    CLASS_MAPPING = {
        "dta": DtaDataInfo,
        "csv": CsvDataInfo,
    }

    data_path = Path(data_path).expanduser().resolve()
    data_name = data_path.stem
    data_extension = data_path.suffix.lower().strip(".")

    # Calculate content hash for cache identification
    HASH_LENGTH = os.getenv("HASH_LENGTH", 12)
    content_hash = hashlib.md5(data_path.read_bytes()).hexdigest()[:HASH_LENGTH]

    # Build cache file path based on filename and content hash
    # This ensures: same filename + same content = same cache file
    saved_file_path = (
        tmp_base_path / f"data_info__{data_name}_{data_extension}__hash_{content_hash}.json"
    )

    # Try to load from cache first
    try:
        with open(saved_file_path, "r", encoding="utf-8") as f:
            cached_result = json.load(f)
        logging.info(f"Successfully loaded cached data info for: {data_name}")
        # Return cached result as JSON string to match expected format
        return json.dumps(cached_result, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        logging.info(f"No cache found for {data_name}.")
        # Cache not found, proceed with file type check and data processing
    except json.JSONDecodeError as e:
        logging.warning(f"Cache file corrupted for {data_name}: {e}")
        # Cache corrupted, proceed with regeneration
    except Exception as e:
        logging.warning(f"Error reading cache for {data_name}: {e}.")
        # Other error, proceed with regeneration

    # Only check file type and process if cache was not found/loaded
    data_info_cls = CLASS_MAPPING.get(data_extension, None)

    if not data_info_cls:
        logging.error(f"Unsupported file extension: {data_extension} for data file: {data_path}")
        return f"Unsupported file extension now: {data_extension}"

    summary_result = data_info_cls(
        data_path=data_path,
        vars_list=vars_list,
        encoding=encoding
    ).summary(saved_file_path)

    # filter的部分有一些问题，等后续再改吧。
    # 相关注释和实现
    # info_filter: Optional[List[str]] = None,
    # info_filter (Optional[List[str]]): the part what you want to reach, (default is None, means all parts).
    #     for the arg, suggest to use None,
    #     at present, parts including ["overview", "vars_detail"]

    # # default_filter是所有存在的key
    # default_filter = ["overview", "vars_detail"]
    #
    # if info_filter is None:
    #     _filter = default_filter
    # else:
    #     _filter = [filter_i for filter_i in info_filter if filter_i in default_filter]
    # filtered_summary = {key: value for key, value in summary_result.items() if key in _filter}

    logging.info(f"Successfully generated data summary for {data_path}, saved to {saved_file_path}")
    return str(summary_result)


@stata_mcp.prompt()
def results_doc_path() -> str:
    """
    Generate and return a result document storage path based on the current timestamp.

    This function performs the following operations:
    1. Gets the current system time and formats it as a '%Y%m%d%H%M%S' timestamp string
    2. Concatenates this timestamp string with the preset result_doc_path base path to form a complete path
    3. Creates the directory corresponding to that path (no error if directory already exists)
    4. Returns the complete path string of the newly created directory

    Returns:
        str: The complete path of the newly created result document directory, formatted as:
            `<result_doc_path>/<YYYYMMDDHHMMSS>`,
            where the timestamp portion is generated from the system time when the function is executed

    Notes:
        (The following content is not needed for LLM to understand)
        - Using the `exist_ok=True` parameter, no exception will be raised when the target directory already exists
        - The function uses the walrus operator (:=) in Python 3.8+ to assign a variable within an expression
        - The returned path is suitable for use as the output directory for Stata commands such as `outreg2`
        - In specific Stata code, you can set the file output path at the beginning.
    """
    path = result_doc_path / datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")
    path.mkdir(exist_ok=True)
    return path.as_posix()


@stata_mcp.tool(
    name="write_dofile",
    description="write the stata-code to dofile"
)
def write_dofile(content: str, encoding: str = None) -> str:
    """
    Write stata code to a dofile and return the do-file path.

    Args:
        content (str): The stata code content which will be writen to the designated do-file.
        encoding (str): The encoding method for the dofile, default -> 'utf-8'

    Returns:
        the do-file path

    Notes:
        Please be careful about the first command in dofile should be use data.
        For avoiding make mistake, you can generate stata-code with the function from `StataCommandGenerator` class.
        Please avoid writing any code that draws graphics or requires human intervention for uncertainty bug.
        If you find something went wrong about the code, you can use the function from `StataCommandGenerator` class.

    Enhancement:
        If you have `outreg2`, `esttab` command for output the result,
        you should use the follow command to get the output path.
        `results_doc_path`, and use `local output_path path` the path is the return of the function `results_doc_path`.
        If you want to use the function `write_dofile`, please use `results_doc_path` before which is necessary.

    """
    file_path = dofile_base_path / f"{datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')}.do"
    encoding = encoding or "utf-8"
    try:
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        logging.info(f"Successful write dofile to {file_path}")
    except Exception as e:
        logging.error(f"Failed to write dofile to {file_path}: {str(e)}")
    return file_path.as_posix()


@stata_mcp.tool(
    name="append_dofile",
    description="append stata-code to an existing dofile or create a new one",
)
def append_dofile(original_dofile_path: str, content: str, encoding: str = None) -> str:
    """
    Append stata code to an existing dofile or create a new one if the original doesn't exist.

    Args:
        original_dofile_path (str): Path to the original dofile to append to.
            If empty or invalid, a new file will be created.
        content (str): The stata code content which will be appended to the designated do-file.
        encoding (str): The encoding method for the dofile, default -> 'utf-8'

    Returns:
        The new do-file path (either the modified original or a newly created file)

    Notes:
        When appending to an existing file, the content will be added at the end of the file.
        If the original file doesn't exist or path is empty, a new file will be created with the content.
        Please be careful about the syntax coherence when appending code to an existing file.
        For avoiding mistakes, you can generate stata-code with the function from `StataCommandGenerator` class.
        Please avoid writing any code that draws graphics or requires human intervention for uncertainty bug.
        If you find something went wrong about the code, you can use the function from `StataCommandGenerator` class.

    Enhancement:
        If you have `outreg2`, `esttab` command for output the result,
        you should use the follow command to get the output path.
        `results_doc_path`, and use `local output_path path` the path is the return of the function `results_doc_path`.
        If you want to use the function `append_dofile`, please use `results_doc_path` before which is necessary.
    """
    # Set encoding if None
    encoding = encoding or "utf-8"

    # Create a new file path for the output
    new_file_path = dofile_base_path / f"{datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')}.do"

    # Check if original file exists and is valid
    original_exists = False
    original_content = ""
    if original_dofile_path and Path(original_dofile_path).exists():
        try:
            with open(original_dofile_path, "r", encoding=encoding) as f:
                original_content = f.read()
            original_exists = True
        except Exception:
            # If there's any error reading the file, we'll create a new one
            original_exists = False

    # Write to the new file (either copying original content + new content, or
    # just new content)
    with open(new_file_path, "w", encoding=encoding) as f:
        if original_exists:
            f.write(original_content)
            # Add a newline if the original file doesn't end with one
            if original_content and not original_content.endswith("\n"):
                f.write("\n")
            logging.info(f"Successfully appended content to {new_file_path} from {original_dofile_path}")
        else:
            logging.info(f"Created new dofile {new_file_path} with content (original file not found)")
        f.write(content)

    logging.info(f"Successfully wrote dofile to {new_file_path}")
    return new_file_path.as_posix()


@stata_mcp.tool(name="ado_package_install", description="Install ado package from ssc or github")
def ado_package_install(package: str,
                        source: str = "ssc",
                        is_replace: bool = True,
                        package_source_from: str = None) -> str:
    """
    Install a package from SSC or GitHub

    Args:
        package (str): The name of the package to be installed.
                       for SSC, use package name;
                       for GitHub, use "username/reponame" format.
        source (str): The source to install from. Options are "ssc" (default) or "GitHub".
        is_replace (bool): Whether to force replacement of an existing installation. Defaults to True.
        package_source_from (str): The directory or url of the package from, only works if source == 'net'

    Returns:
        str: The execution log returned by Stata after running the installation.

    Examples:
        >>> ado_package_install(package="outreg2", source="ssc")
        >>> # this would install outreg2 from ssc
        >>> ado_package_install(package="sepinetam/texiv", source="github")
        >>> # this would install texiv from https://github.com/sepinetam/texiv
        -------------------------------------------------------------------------------
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012185447.log
        log type:  text
        opened on:  12 Oct 2025, 18:54:47

        . do "/Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-dofile/20251012185447.do"

        . ssc install outreg2, replace
        checking outreg2 consistency and verifying not already installed...
        all files already exist and are up to date.

        .
        end of do-file

        . log close
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012185447.log
        log type:  text
        closed on:  12 Oct 2025, 18:54:55
        -------------------------------------------------------------------------------

        >>> ado_package_install(command="a_fake_command")
        -------------------------------------------------------------------------------
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012190159.log
        log type:  text
        opened on:  12 Oct 2025, 19:01:59

        . do "/Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-dofile/20251012190159.do"

        . ssc install a_fake_command, replace
        ssc install: "a_fake_command" not found at SSC, type search a_fake_command
        (To find all packages at SSC that start with a, type ssc describe a)
        r(601);

        end of do-file

        r(601);

        . log close
        name:  <unnamed>
        log:  /Users/sepinetam/Documents/stata-mcp-folder/stata-mcp-log/20251012190159.log
        log type:  text
        closed on:  12 Oct 2025, 19:02:00
        -------------------------------------------------------------------------------

    Notes:
        Avoid using this tool unless strictly necessary, as SSC installation can be time-consuming
        and may not be required if the package is already present.
    """
    if IS_UNIX:
        SOURCE_MAPPING: Dict = {
            "github": GITHUB_Install,
            "net": NET_Install,
            "ssc": SSC_Install
        }
        installer = SOURCE_MAPPING.get(source, SSC_Install)

        logging.info(f"Try to use {installer.__name__} to install {package}.")

        # set the args for the special cases
        args = [package, package_source_from] if source == "net" else [package]
        install_msg = installer(STATA_CLI, is_replace).install(*args)

        if installer.check_installed_from_msg(install_msg):
            logging.info(f"{package} is installed successfully.")
        else:
            logging.error(f"{package} installation failed.")
            logging.debug(f"Full installation message: {install_msg}")

        return install_msg
    else:
        from_message = f"from({package_source_from})" if (package_source_from and source == "net") else ""
        replace_str = "replace" if is_replace else ""
        tmp_file = write_dofile(f"{source} install {package}, {replace_str} {from_message}")
        return stata_do(tmp_file, is_read_log=True).get("log_content")


@stata_mcp.tool(name="load_figure")
def load_figure(figure_path: str) -> Image:
    """
    Load figure from device

    Args:
        figure_path (str): the figure file path, only support png and jpg format

    Returns:
        Image: the figure thumbnail
    """
    if not Path(figure_path).exists():
        logging.error(f"Try to load figure {figure_path} but not found.")
        raise FileNotFoundError(f"{figure_path} not found")

    logging.info(f"Successfully loaded figure from {figure_path}")
    return Image(figure_path)


@stata_mcp.tool(name="mk_dir")
def mk_dir(path: str) -> bool:
    """
    Safely create a directory using pathvalidate for security validation.

    Args:
        path (str): the path you want to create

    Returns:
        bool: the state of the new path,
              if True -> the path exists now;
              else -> not success

    Raises:
        ValueError: if path is invalid or contains unsafe components
        PermissionError: if insufficient permissions to create directory
    """
    from pathvalidate import ValidationError, sanitize_filepath

    # Input validation
    if not path or not isinstance(path, str):
        raise ValueError("Path must be a non-empty string")

    try:
        # Use pathvalidate to sanitize and validate path
        safe_path = sanitize_filepath(path, platform="auto")

        # Get absolute path for further validation
        absolute_path = Path(safe_path).resolve()

        # Check if directory already exists
        if absolute_path.exists():
            logging.info(f"Directory already exists: {absolute_path}")
        else:
            # Create directory with reasonable permissions
            absolute_path.mkdir(mode=0o755, exist_ok=True, parents=True)
            logging.info(f"Successfully created directory: {absolute_path}")

        # Verify successful creation
        success = absolute_path.exists() and absolute_path.is_dir()
        if success:
            logging.info(f"Directory creation verified: {absolute_path}")
        else:
            logging.error(f"Directory creation failed: {absolute_path}")

        return success

    except ValidationError as e:
        logging.error(f"Invalid path for directory creation: {path} - {str(e)}")
        raise ValueError(f"Invalid path detected: {e}")
    except PermissionError:
        logging.error(f"Permission denied when creating directory: {path}")
        raise PermissionError(f"Insufficient permissions to create directory: {path}")
    except OSError as e:
        logging.error(f"OS error when creating directory {path}: {str(e)}")
        raise OSError(f"Failed to create directory {path}: {str(e)}")


@stata_mcp.tool(name="stata_do", description="Run a stata-code via Stata")
def stata_do(dofile_path: str,
             log_file_name: str = None,
             is_read_log: bool = True) -> Dict[str, Union[str, None]]:
    """
    Execute a Stata do-file and return the log file path with optional log content.

    This function runs a Stata do-file using the configured Stata executable and
    generates a log file. It supports cross-platform execution (macOS, Windows, Linux).

    Args:
        dofile_path (str): Absolute or relative path to the Stata do-file (.do) to execute.
        log_file_name (str, optional): Set log file name without a time-string. If None, using nowtime as filename
        is_read_log (bool, optional): Whether to read and return the log file content.
                                    Defaults to True.

    Returns:
        Dict[str, Union[str, None]]: A dictionary containing:
            - "log_file_path" (str): Path to the generated Stata log file
            - "log_content" (str, optional): Content of the log file if is_read_log is True

    Raises:
        FileNotFoundError: If the specified do-file does not exist
        RuntimeError: If Stata execution fails or log file cannot be generated
        PermissionError: If there are insufficient permissions to execute Stata or write log files

    Example:
        >>> do_file_path: str | Path = ...
        >>> result = stata_do(do_file_path, is_read_log=True)
        >>> print(result[log_file_path])
        /path/to/logs/analysis.log
        >>> print(result[log_content])
        Stata log content...

        >>> result = stata_do(do_file_path, log_file_name="experience")  # Not suggest to use log_file_name arg.
        >>> print(result[log_file_path])
        /log/file/base/experience.log

        >>> not_exist_dofile = ...
        >>> result = stata_do(not_exist_dofile)
        >>> print(result)
        {"error": "error content..."}

    Note:
        - The log file is automatically created in the configured log_file_path directory
        - Supports multiple operating systems through the StataDo executor
        - Log file naming follows Stata conventions with .log extension
    """
    # Initialize Stata executor with system configuration
    stata_executor = StataDo(
        stata_cli=STATA_CLI,  # Path to Stata executable
        log_file_path=str(log_base_path),  # Directory for log files
        dofile_base_path=str(dofile_base_path),  # Base directory for do-files
        sys_os=SYSTEM_OS  # Operating system identifier
    )

    # Execute the do-file and get log file path
    logging.info(f"Try to running file {dofile_path}")

    try:
        log_file_path = stata_executor.execute_dofile(dofile_path, log_file_name)
        logging.info(f"{dofile_path} is executed successfully. Log file path: {log_file_path}")
    except Exception as e:
        logging.error(f"Failed to execute {dofile_path}. Error: {str(e)}")
        return {"error": str(e)}

    # Return log content based on user preference
    log_content = stata_executor.read_log(log_file_path) if is_read_log else "Not read log"
    return {
        "log_file_path": log_file_path,
        "log_content": log_content
    }


__all__ = [
    "stata_mcp",

    # Functions (Core)
    "get_data_info",
    "stata_do",
    "write_dofile",
    "append_dofile",

    # Utilities
    "mk_dir",
    "load_figure",
    "read_file",
    "ado_package_install",
]

if IS_UNIX:
    __all__.extend([
        "help"
    ])
