'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-09-27 09:51:21 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-11-04 10:47:28 +0100
FilePath     : utils_yaml.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import os, sys
import yaml
from copy import deepcopy
import colorama
import warnings

from rich import print as rprint


import logging
from analysis_tool.utils.utils_logging import get_logger

# Check if running in Snakemake
is_snakemake = any('snakemake' in arg for arg in sys.argv)

if not is_snakemake:
    logger = get_logger(__name__, auto_setup_rich_logging=True)
else:
    logger = logging.getLogger(__name__)


from .utils_dict import update_config


# ----- Yaml part -----
def load_yaml(
    input_file_name: str,
    envParse: bool = False,
) -> dict:
    """
    Helper function to load a single YAML file.
    """
    # Check if the file exists before attempting to read
    if not os.path.exists(input_file_name):
        raise FileNotFoundError(f"{colorama.Fore.RED}the file {input_file_name} does not exist.{colorama.Style.RESET_ALL}")

    # read yaml file
    with open(input_file_name, "r") as f:
        if envParse:
            # Parse environment variables in configfile
            # Read file content
            content = f.read()
            # Replace environment variable placeholders
            content = os.path.expandvars(content)
            # Load YAML to dict
            yaml_loaded = yaml.safe_load(content)
        else:
            yaml_loaded = yaml.safe_load(f)

    logger.info(f"Loaded YAML file: {input_file_name}")

    return yaml_loaded


def read_yaml(
    input_file_name: str | list[str],
    mode: str | list[str] = None,
    envParse: bool = False,
) -> any:
    """
    Reads a YAML file, optionally parses environment variables, and extracts specific sections of the YAML file.

    Args:
        input_file_name (str): Path to the YAML file.
        mode (Union[str, List[str]], optional): Specifies the sections of the YAML to unfold. Can be a single section or a list of sections.
                                                 If a comma-separated string is provided, it will be split into a list.
        envParse (bool, optional): Whether to parse environment variables in the YAML file. Defaults to False.

    Returns:
        dict: The unfolded YAML content as a dictionary.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        KeyError: If a specified mode/section is not found in the YAML.
    """

    logger.info(f"Reading YAML file: {input_file_name}, mode: {mode}")

    # If input_file_name is a string, convert it to a list for consistency
    input_file_name = input_file_name if isinstance(input_file_name, list) else [str(input_file_name)]

    # Load and merge YAML files
    yaml_loaded = {}
    for f in input_file_name:
        yaml_content = load_yaml(f, envParse)
        yaml_loaded = update_config(yaml_loaded, yaml_content)

    # Deep copy the loaded YAML for further traversal
    yaml_unfolded = deepcopy(yaml_loaded)

    if mode is None:
        return yaml_unfolded

    # Convert mode into a list if it's a string with commas or ensure it's a list
    if isinstance(mode, str):
        mode = mode.split(',')  # Split by commas if mode is a comma-separated string
    mode = mode if isinstance(mode, list) else [mode]  # Ensure mode is always a list

    # Traverse through the specified sections (modes) of the YAML

    for m in mode:
        if m and m in yaml_unfolded:
            yaml_unfolded = yaml_unfolded[m]  # Traverse into the specified section
        else:
            raise KeyError(f"{colorama.Fore.RED}the section '{m}' was not found in the YAML file.{colorama.Style.RESET_ALL}")

    # Return the unfolded YAML content
    return yaml_unfolded


# def read_yaml(input_file_name: str, mode: str | list[str] = None, envParse: bool = False) -> dict:
#     """
#     Reads a YAML file, optionally parses environment variables, and extracts specific sections of the YAML file.

#     Args:
#         input_file_name (str): Path to the YAML file.
#         mode (Union[str, List[str]], optional): Specifies the sections of the YAML to unfold. Can be a single section or a list of sections.
#                                                  If a comma-separated string is provided, it will be split into a list.
#         envParse (bool, optional): Whether to parse environment variables in the YAML file. Defaults to False.

#     Returns:
#         dict: The unfolded YAML content as a dictionary.

#     Raises:
#         FileNotFoundError: If the specified file does not exist.
#         KeyError: If a specified mode/section is not found in the YAML.
#     """

#     # Check if the file exists before attempting to read
#     if not os.path.exists(input_file_name):
#         raise FileNotFoundError(f"{colorama.Fore.RED}the file {input_file_name} does not exist.{colorama.Style.RESET_ALL}")

#     # read yaml file
#     with open(input_file_name, "r") as f:
#         if envParse:
#             # Parse environment variables in configfile
#             # Read file content
#             content = f.read()
#             # Replace environment variable placeholders
#             content = os.path.expandvars(content)
#             # Load YAML to dict
#             yaml_loaded = yaml.safe_load(content)
#         else:
#             yaml_loaded = yaml.safe_load(f)

#     # Convert mode into a list if it's a string with commas or ensure it's a list
#     if isinstance(mode, str):
#         mode = mode.split(',')  # Split by commas if mode is a comma-separated string
#     mode = mode if isinstance(mode, list) else [mode]  # Ensure mode is always a list

#     # Deep copy the loaded YAML for further traversal
#     yaml_unfolded = deepcopy(yaml_loaded)

#     # Traverse through the specified sections (modes) of the YAML
#     for m in mode:
#         if m and m in yaml_unfolded:
#             yaml_unfolded = yaml_unfolded[m]  # Traverse into the specified section
#         else:
#             raise KeyError(f"{colorama.Fore.RED}the section '{m}' was not found in the YAML file.{colorama.Style.RESET_ALL}")

#     # Return the unfolded YAML content
#     return yaml_unfolded
