'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-07-10 17:47:25 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-12-02 03:29:57 +0100
FilePath     : utils_ROOT.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

# Import the necessary modules
import os
import sys
import glob
from pathlib import Path
import colorama
import warnings
from typing import List, Tuple, Optional, Union, Set, Dict, Any
import random
import re
from collections import defaultdict
import shutil

import numpy as np

import ROOT as r
from ROOT import (
    vector,
    gInterpreter,
    RDataFrame,
    TObject,
    std,
    gErrorIgnoreLevel,
    kPrint,
    kInfo,
    kWarning,
    kError,
    kBreak,
    kSysError,
    kFatal,
    RDF,
    TFile,
    TChain,
    TCanvas,
    TLegend,
    TGraph,
    gStyle,
    TH1,
    TH2,
    TH3,
    TH1D,
    TH2D,
    TH3D,
)

from rich import print as rprint

# Use rich backend for logging
import logging
from rich.logging import RichHandler

# Check if running in Snakemake
is_snakemake = any('snakemake' in arg for arg in sys.argv)

# Configure rich logging globally
if not is_snakemake:
    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%x %X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )  # or "DEBUG"/"WARNING" as needed
logger = logging.getLogger(__name__)


def check_root_file(input_file_name: str, obj_name: str = None) -> bool:
    """
    Checks if a ROOT file exists, contains a specified object, and validates it appropriately based on object type.

    Parameters:
        input_file_name (str): The path to the input ROOT file.
        obj_name (str): The name of the object to check in the ROOT file. If None, the function will only check if the file exists.

    Returns:
        bool: True if the file exists, contains the object, and the object passes validation. False otherwise.
    """
    input_file_name: str = Path(input_file_name).resolve().as_posix()

    # Step 1: Check if the file exists
    if not Path(input_file_name).exists():
        logger.error(f'File does not exist: [bold red]{input_file_name}[/]', extra={"markup": True})
        return False

    # Step 2: Open the ROOT file
    try:
        root_file = TFile.Open(input_file_name, "READ")
        if not root_file or root_file.IsZombie():
            logger.error(f'Cannot open ROOT file: [bold red]{input_file_name}[/]', extra={"markup": True})
            return False
    except Exception as e:
        logger.error(f'Error opening file: [bold red]{e}[/]', extra={"markup": True})
        return False

    if obj_name is None:
        return True

    # Step 3: Check if the specified object exists
    list_of_keys = root_file.GetListOfKeys()
    if not ((list_of_keys.Contains(obj_name)) or (list_of_keys.Contains(obj_name.split('/')[0]))):
        logger.error(f'Object [bold red]{obj_name}[/] does not exist in file [bold red]{input_file_name}[/]', extra={"markup": True})
        root_file.Close()
        return False

    # Step 4: Access the object and validate based on type
    obj = root_file.Get(obj_name)
    if not obj:
        logger.error(f'Error retrieving object: [bold red]{obj_name}[/]', extra={"markup": True})
        root_file.Close()
        return False

    # Determine object type and validate accordingly
    obj_class = obj.ClassName()

    # For tree-like objects, check entries
    if obj_class.startswith('TTree') or obj_class.startswith('TNtuple') or 'tree' in obj_name.lower():
        num_entries = obj.GetEntries()
        if num_entries > 0:
            logger.info(f"Tree '{obj_name}' in file '{input_file_name}' has {num_entries} entries.")
            root_file.Close()
            return True
        else:
            logger.error(f'Tree has zero entries: [bold red]{obj_name}[/]', extra={"markup": True})
            root_file.Close()
            return False

    # For histogram-like objects, just verify they exist (already done above)
    elif obj_class.startswith('TH') or obj_class.startswith('TProfile'):
        logger.info(f"Histogram '{obj_name}' (class: {obj_class}) found in file '{input_file_name}'.")
        root_file.Close()
        return True

    # For other objects, just verify they exist
    else:
        logger.info(f"Object '{obj_name}' (class: {obj_class}) found in file '{input_file_name}'.")
        root_file.Close()
        return True


# Load the cpp files
GLOBAL_LOADED_CPP_FILES: list[Path] = []


def load_cpp_file(cpp_file_paths: Union[str, List[str]]) -> Tuple[bool, List[Path]]:
    """
    Load C++ function files into ROOT's interpreter (gInterpreter).

    This function loads one or more C++ files into ROOT's CINT/Cling interpreter,
    making the functions and classes defined in those files available for use in
    ROOT analysis. It handles various input formats including single files,
    directories, wildcard patterns, and comma-separated lists.

    Parameters:
        cpp_file_paths (Union[str, List[str]]): Input specification for C++ files to load.
            Can be:
            - Single file path: "analysis.cpp"
            - Directory path: "cpp_functions/" (loads all .cpp files)
            - Wildcard pattern: "functions/*.cpp"
            - Comma-separated list: "file1.cpp,file2.cpp,dir/"
            - List of paths: ["file1.cpp", "file2.cpp"]

    Returns:
        Tuple[bool, List[Path]]:
            - bool: True if at least one file was successfully loaded, False otherwise
            - List[Path]: Complete list of all C++ files loaded in this session

    Raises:
        ValueError: If input type is not string or list

    Global Variables:
        Modifies GLOBAL_LOADED_CPP_FILES: Tracks all C++ files loaded in this session

    Example:
        >>> # Load a single file
        >>> success, loaded_files = load_cpp_file("analysis_functions.cpp")
        >>> if success:
        ...     print(f"Loaded {len(loaded_files)} files total")

        >>> # Load all .cpp files from a directory
        >>> success, loaded_files = load_cpp_file("cpp_utilities/")

        >>> # Load multiple files with different methods
        >>> success, loaded_files = load_cpp_file([
        ...     "analysis.cpp",
        ...     "helpers/",
        ...     "utils/*.cpp"
        ... ])

        >>> # Load comma-separated files
        >>> success, loaded_files = load_cpp_file("file1.cpp,file2.cpp,helpers/")
    """

    # ========================================
    # Access global tracking variable
    # ========================================

    global GLOBAL_LOADED_CPP_FILES

    # ========================================
    # Input validation
    # ========================================

    # Check if input is provided
    if not cpp_file_paths:
        logger.warning('No input file provided, no action taken.')
        return (False, GLOBAL_LOADED_CPP_FILES)

    # ========================================
    # Parse and normalize input paths
    # ========================================

    # Convert input to standardized list format
    normalized_input_paths: List[str] = []

    if isinstance(cpp_file_paths, str):
        # Handle comma-separated string input
        normalized_input_paths = [file_path.strip() for file_path in cpp_file_paths.split(',')]
    elif isinstance(cpp_file_paths, list):
        # Handle list input
        normalized_input_paths = [file_path.strip() for file_path in cpp_file_paths]
    else:
        raise ValueError(f'Invalid input type: {type(cpp_file_paths)}. Expected str or List[str]')

    # ========================================
    # Discover all C++ files to load
    # ========================================

    cpp_files_to_load: List[str] = []  # List of resolved file paths

    for input_path_str in normalized_input_paths:
        # Skip empty strings from splitting
        if not input_path_str:
            continue

        input_path = Path(input_path_str).resolve()

        # ========================================
        # Handle different input types
        # ========================================

        if input_path.is_dir():
            # Directory: load all .cpp files within it
            directory_cpp_files = [str(cpp_file) for cpp_file in input_path.glob('*.cpp')]
            cpp_files_to_load.extend(directory_cpp_files)
            logger.debug(f'Found {len(directory_cpp_files)} .cpp files in directory: {input_path}')

        elif '*' in input_path_str:
            # Wildcard pattern: use glob to find matching files
            pattern_matches = glob.glob(input_path_str)
            cpp_pattern_matches = [file_path for file_path in pattern_matches if file_path.endswith('.cpp')]
            cpp_files_to_load.extend(cpp_pattern_matches)
            logger.debug(f'Found {len(cpp_pattern_matches)} .cpp files matching pattern: {input_path_str}')

        elif input_path_str.endswith('.cpp'):
            # Specific .cpp file
            cpp_files_to_load.append(str(input_path))
            logger.debug(f'Added specific .cpp file: {input_path}')

        else:
            # Invalid input - not a directory, pattern, or .cpp file
            logger.warning(f'No valid .cpp files found for input: {input_path_str}')

    # ========================================
    # Validate discovery results
    # ========================================

    if not cpp_files_to_load:
        logger.warning('No valid .cpp files found in provided input')
        return (False, GLOBAL_LOADED_CPP_FILES)

    # ========================================
    # Load each discovered C++ file
    # ========================================

    logger.info(f'Attempting to load {len(cpp_files_to_load)} .cpp files')
    logger.debug(f'Files to load: {cpp_files_to_load}')

    files_loaded_this_session = 0

    for cpp_file_path_str in cpp_files_to_load:
        cpp_file_path = Path(cpp_file_path_str).resolve()

        # ========================================
        # Check if file was already loaded
        # ========================================

        if cpp_file_path in GLOBAL_LOADED_CPP_FILES:
            logger.warning(f'Already loaded [bold yellow]{cpp_file_path}[/], skipping to avoid duplicate loading.', extra={"markup": True})
            continue

        # ========================================
        # Verify file exists before loading
        # ========================================

        if not cpp_file_path.exists():
            logger.error(f'C++ file does not exist: [bold red]{cpp_file_path}[/]', extra={"markup": True})
            continue

        # ========================================
        # Load the C++ file into ROOT interpreter
        # ========================================

        try:
            # Use ROOT's gROOT.LoadMacro which returns meaningful values
            # Returns 0 on success, -1 on error
            load_result = r.gROOT.LoadMacro(str(cpp_file_path))
            # gInterpreter.LoadMacro(str(cpp_file_path)) # This function do not have return value

            # Check if loading was successful (0 = success)
            if load_result == 0:
                logger.info(f'Successfully loaded: [bold green]{cpp_file_path}[/]', extra={"markup": True})

                # Add to global tracking list
                GLOBAL_LOADED_CPP_FILES.append(cpp_file_path)
                files_loaded_this_session += 1

            else:
                logger.error(f'Failed to load C++ file: [bold red]{cpp_file_path}[/] (error code: {load_result})', extra={"markup": True})

        except Exception as e:
            logger.error(f'Exception while loading [bold red]{cpp_file_path}[/]: {str(e)}', extra={"markup": True})

    # ========================================
    # Report loading results
    # ========================================

    success = files_loaded_this_session > 0

    if success:
        logger.info(f'Successfully loaded {files_loaded_this_session} new C++ files. ' f'Total files loaded this session: {len(GLOBAL_LOADED_CPP_FILES)}')
    else:
        logger.warning('No new C++ files were loaded')

    return (success, GLOBAL_LOADED_CPP_FILES)


def create_event_intervals(input_file_path: str, max_event_interval: int, input_tree_name: str = 'DecayTree') -> List[int]:
    """
    Split samples into intervals based on maximum event count per interval.

    Args:
        input_file_path: Path to the ROOT file
        max_event_interval: Maximum number of events per interval
        input_tree_name: Name of the tree in the ROOT file

    Returns:
        List of intervals, each interval is a tuple of (start_event, end_event), starting from 0.

    Raises:
        RuntimeError: If file cannot be opened or is invalid
        ValueError: If max_event_interval is invalid
    """

    # Validate input parameters
    if max_event_interval <= 0:
        raise ValueError(f"max_event_interval must be positive, got {max_event_interval}")

    # Check if the input file is a valid ROOT file with the given tree name
    if not check_root_file(input_file_path, input_tree_name):
        raise RuntimeError(f"{colorama.Fore.RED}cannot open file {input_file_path}{colorama.Style.RESET_ALL}")

    # Get total number of events in the input file
    rd = RDataFrame(input_tree_name, input_file_path)
    total_events = rd.Count().GetValue()

    # Handle empty file case
    if total_events == 0:
        return []

    # Calculate the number of intervals
    num_intervals = total_events // max_event_interval
    last_interval_remainder = total_events % max_event_interval

    # Split the events into intervals, which stores the event indexes
    intervals_map: List[Tuple[int, int]] = []

    # Create full intervals
    for i in range(num_intervals):
        intervals_map.append((i * max_event_interval, (i + 1) * max_event_interval))

    # Only add the last partial interval if there are remaining events
    if last_interval_remainder > 0:
        intervals_map.append((num_intervals * max_event_interval, num_intervals * max_event_interval + last_interval_remainder))

    return intervals_map


# * Check if two branches are identical
def get_overlapped_branches(dataframe_1: RDataFrame, dataframe_2: RDataFrame) -> Set[str]:
    """
    Get branch names that exist in both RDataFrames.

    Args:
        dataframe_1: First RDataFrame to compare
        dataframe_2: Second RDataFrame to compare

    Returns:
        Set of branch names that exist in both RDataFrames

    Example:
        >>> rdf1 = RDataFrame("tree1", "file1.root")
        >>> rdf2 = RDataFrame("tree2", "file2.root")
        >>> common_branches = get_overlapped_branches(rdf1, rdf2)
        >>> print(f"Common branches: {common_branches}")
    """
    branches_1 = set(dataframe_1.GetColumnNames())
    branches_2 = set(dataframe_2.GetColumnNames())
    return branches_1 & branches_2


def are_branches_identical(
    dataframe_1: RDataFrame,
    dataframe_2: RDataFrame,
    branch_name_1: str,
    branch_name_2: str,
    tolerance: float = 1e-10,
) -> Tuple[bool, str]:
    """
    Check if two branches from different RDataFrames contain identical values.

    This function handles different data types appropriately:
    - Floating point numbers: compared with tolerance using np.allclose
    - Integers, booleans, strings: exact comparison using np.array_equal

    Args:
        dataframe_1: First RDataFrame containing branch_name_1
        dataframe_2: Second RDataFrame containing branch_name_2
        branch_name_1: Name of branch in first RDataFrame
        branch_name_2: Name of branch in second RDataFrame
        tolerance: Relative and absolute tolerance for floating point comparison

    Returns:
        Tuple containing:
        - bool: True if branches are identical, False otherwise
        - str: Error message if branches differ, empty string if identical

    Example:
        >>> rdf1 = RDataFrame("tree", "file1.root")
        >>> rdf2 = RDataFrame("tree", "file2.root")
        >>> is_same, error_msg = are_branches_identical(rdf1, rdf2, "mass", "mass")
        >>> if not is_same:
        >>>     print(f"Branches differ: {error_msg}")
    """
    try:
        # ========================================
        # Extract data as numpy arrays
        # ========================================

        data_1: dict[str, np.ndarray] = dataframe_1.AsNumpy([branch_name_1])
        data_2: dict[str, np.ndarray] = dataframe_2.AsNumpy([branch_name_2])

        values_1: np.ndarray = data_1[branch_name_1]
        values_2: np.ndarray = data_2[branch_name_2]

        # ========================================
        # Check if array lengths match
        # ========================================

        if len(values_1) != len(values_2):
            error_message = f"Different array lengths: {len(values_1)} vs {len(values_2)}"
            logger.warning(f"[bold yellow]{error_message}[/]", extra={"markup": True})
            return False, error_message

        # ========================================
        # Handle floating point data types (float, complex)
        # ========================================

        if values_1.dtype.kind in 'fc':
            # Use tolerance-based comparison for floating point values
            are_close = np.allclose(values_1, values_2, rtol=tolerance, atol=tolerance, equal_nan=True)
            if not are_close:
                max_difference = np.max(np.abs(values_1 - values_2))
                error_message = f"Floating point values differ (max diff: {max_difference:.2e}, tolerance: {tolerance:.2e})"
                logger.warning(f"[bold yellow]{error_message}[/]", extra={"markup": True})
                return False, error_message
        else:
            # ========================================
            # Exact comparison for integers, booleans, strings, etc.
            # ========================================

            if not np.array_equal(values_1, values_2):
                # Find first differing entry for debugging
                different_indices = np.where(values_1 != values_2)[0]
                if len(different_indices) > 0:
                    first_diff_index = different_indices[0]
                    error_message = f"Values differ at entry {first_diff_index}: " f"{values_1[first_diff_index]} vs {values_2[first_diff_index]}"
                    logger.warning(f"[bold yellow]{error_message}[/]", extra={"markup": True})
                    return False, error_message

        return True, ""
    except Exception as exception:
        # ========================================
        # Handle errors
        # ========================================

        error_message = f"Error comparing branches: {str(exception)}"
        logger.error(f"[bold red]{error_message}[/]", extra={"markup": True})
        return False, error_message


def check_file_branch_compatibility(
    file_path_1: str,
    file_path_2: str,
    branches_to_check: list[str],
    tree_name_1: str = "DecayTree",
    tree_name_2: str = "DecayTree",
    tolerance: float = 1e-10,
) -> bool:
    """
    Check if overlapping branches between two ROOT files are identical.

    This function:
    1. Opens both ROOT files and creates RDataFrames
    2. Finds branches that exist in both files
    3. Compares values in each overlapping branch
    4. Returns True only if ALL overlapping branches are identical

    Args:
        file_path_1: Path to first ROOT file
        file_path_2: Path to second ROOT file
        branches_to_check: List of branches to check for compatibility (default: None)
        tree_name_1: Name of tree in first file (default: "DecayTree")
        tree_name_2: Name of tree in second file (default: "DecayTree")
        tolerance: Tolerance for floating point comparisons (default: 1e-10)
    Returns:
        bool: True if all overlapping branches are identical, False otherwise

    Example:
        >>> compatible = check_file_branch_compatibility(
        ...     "data1.root", "data2.root",
        ...     tree_name_1="Events", tree_name_2="Events"
        ... )
        >>> if compatible:
        ...     print("Files can be safely merged")
        ... else:
        ...     print("Files have conflicting branch values")
    """

    if not branches_to_check:
        raise ValueError("No branches to check, got an empty list")

    logger.info("Checking branch compatibility between:")
    logger.info(f"  File 1: {file_path_1} (tree: {tree_name_1})")
    logger.info(f"  File 2: {file_path_2} (tree: {tree_name_2})")

    # Create RDataFrames from ROOT files
    dataframe_1 = RDataFrame(tree_name_1, file_path_1)
    dataframe_2 = RDataFrame(tree_name_2, file_path_2)

    # ========================================
    # Check the branches to be checked exist in the files
    # ========================================

    for branch_name in branches_to_check:
        if branch_name not in dataframe_1.GetColumnNames():
            raise ValueError(f"Branch {branch_name} not found in file {file_path_1}")
        if branch_name not in dataframe_2.GetColumnNames():
            raise ValueError(f"Branch {branch_name} not found in file {file_path_2}")

    # ========================================
    # Check each overlapping branch for identical values
    # ========================================

    all_branches_identical = True
    for branch_name in branches_to_check:
        logger.info(f"Comparing branch: {branch_name}")

        is_identical, error_message = are_branches_identical(dataframe_1, dataframe_2, branch_name, branch_name, tolerance)

        if not is_identical:
            logger.warning(f"[bold yellow]Branch '{branch_name}' differs between files: {error_message}[/]", extra={"markup": True})
            all_branches_identical = False
        else:
            logger.info(f"[bold green]Branch '{branch_name}' is identical[/]", extra={"markup": True})

    if all_branches_identical:
        logger.info("[bold green]All overlapping branches are identical - files are compatible[/]", extra={"markup": True})
    else:
        logger.warning("[bold yellow]Some branches differ - files are NOT compatible[/]", extra={"markup": True})

    return all_branches_identical


def reset_tree_reshuffled_bit(tree: r.TTree) -> r.TTree:
    # ========================================
    # Unset the kEntriesReshuffled bit
    # ========================================

    if tree.TestBit(r.TTree.kEntriesReshuffled):
        tree.ResetBit(r.TTree.kEntriesReshuffled)
        logger.warning('Unset the kEntriesReshuffled bit, be careful with this option, it may cause chaos in branch order.')
    return tree


def rdfMergeFriends(
    input_file_nominal: str,
    input_file_friends: Union[str, List[str]],
    tree_nominal: str,
    tree_friends: Union[str, List[str]],
    output_file_name: str,
    output_tree_name: str = 'DecayTree',
    output_branches: Optional[Union[List[str], str]] = None,
    build_index_names: Optional[List[str]] = None,  # [major_name, minor_name = '0']
    strict_entry_size_check: bool = True,
    ignore_k_entries_reshuffled: bool = False,
    check_branch_compatibility: bool = True,
    skip_compatibility_check_branches: Optional[List[str]] = None,
    remove_overlapped_branches: bool = True,
) -> str:
    """
    Merge ROOT trees by adding friend trees to a nominal tree and save the result.

    This function creates friend relationships between ROOT trees, allowing access to
    branches from multiple trees as if they were a single tree. The trees are merged
    based on entry index (row-by-row matching) or custom indexing.

    Parameters:
        input_file_nominal (str): Path to the nominal ROOT file
        input_file_friends (Union[str, List[str]]): Path(s) to friend ROOT file(s)
        tree_nominal (str): Name of the tree in the nominal file
        tree_friends (Union[str, List[str]]): Name(s) of tree(s) in friend file(s)
        output_file_name (str): Path for the output merged ROOT file
        output_tree_name (str, optional): Name for the output tree. Defaults to 'DecayTree'
        output_branches (Optional[Union[List[str], str]], optional):
            Branches to save in output. 'ALL' saves all branches, None saves unique branches.
        build_index_names (Optional[List[str]], optional):
            [major_branch, minor_branch] for building tree index. Required for multithreading.
        strict_entry_size_check (bool, optional):
            If True, raises error when trees have different entry counts. Defaults to True.
        ignore_k_entries_reshuffled (bool, optional):
            If True, ignores reshuffled tree warning (use with caution). Defaults to False.
        check_branch_compatibility (bool, optional):
            If True, verifies overlapping branches have identical values. Defaults to True.
        skip_compatibility_check_branches (Optional[List[str]], optional):
            Branches to skip during compatibility check. Defaults to None.
        remove_overlapped_branches (bool, optional):
            If True, removes duplicate branches (e.g. {TreeName}_{index}_{branchName} that are created by tree merging)
            Defaults to True.

    Returns:
        str: Path to the output file

    Raises:
        ValueError: If multithreading is enabled but build_index_names is not provided
        AssertionError: If trees have different entry counts and strict_entry_size_check is True
        RuntimeError: If branch compatibility check fails or reshuffled trees are detected

    Example:
        >>> # Basic usage - merge two trees
        >>> output_file = rdfMergeFriends(
        ...     input_file_nominal="data.root",
        ...     input_file_friends="weights.root",
        ...     tree_nominal="Events",
        ...     tree_friends="WeightTree",
        ...     output_file_name="merged.root"
        ... )

        >>> # Advanced usage with indexing for multithreading
        >>> output_file = rdfMergeFriends(
        ...     input_file_nominal="data.root",
        ...     input_file_friends=["weights.root", "systematics.root"],
        ...     tree_nominal="Events",
        ...     tree_friends=["WeightTree", "SystTree"],
        ...     output_file_name="merged.root",
        ...     build_index_names=["event_id", "0"],
        ...     output_branches=["pt", "eta", "weight", "syst_up"]
        ... )
    """

    # ========================================
    # Input validation and normalization
    # ========================================

    # Convert single friend file/tree to lists for uniform processing
    friend_file_list = input_file_friends if isinstance(input_file_friends, list) else [input_file_friends]
    friend_tree_list = tree_friends if isinstance(tree_friends, list) else [tree_friends] * len(friend_file_list)

    # Validate build_index_names format and check multithreading compatibility
    build_index_names = build_index_names if isinstance(build_index_names, list) and len(build_index_names) == 2 else [None, '0']
    if build_index_names[0] is None and r.ROOT.IsImplicitMTEnabled():
        raise ValueError(
            f'You are using {colorama.Fore.RED}r.ROOT.EnableImplicitMT(){colorama.Style.RESET_ALL} '
            f'but you did not specify the {colorama.Fore.RED}build_index_names{colorama.Style.RESET_ALL}. '
            f'This will result in a crash. Please specify the {colorama.Fore.RED}build_index_names{colorama.Style.RESET_ALL}.'
        )

    # ========================================
    # Load and prepare nominal tree
    # ========================================

    # Check if nominal file and tree exist
    if not check_root_file(input_file_nominal, tree_nominal):
        raise FileNotFoundError(f'The nominal file {input_file_nominal} does not contain the tree {tree_nominal}')

    # Open nominal file and get tree
    nominal_file = TFile(input_file_nominal)
    nominal_tree = nominal_file.Get(tree_nominal)

    # Extract branch names from nominal tree
    nominal_branches = [branch.GetName() for branch in nominal_tree.GetListOfBranches()]
    nominal_rdf = RDataFrame(nominal_tree)

    # Initialize list of branches to save (starts with nominal branches)
    unique_branches_to_save = nominal_branches.copy()

    # ========================================
    # Handle reshuffled entries in nominal tree
    # ========================================

    # Check if nominal tree has been reshuffled (entries reordered)
    if nominal_tree.TestBit(r.TTree.kEntriesReshuffled):
        logger.warning('The nominal tree has been reshuffled')
        if ignore_k_entries_reshuffled:
            logger.warning('Here we will try to reset the status bit and add the friend tree, but please take your own risk')
            reset_tree_reshuffled_bit(nominal_tree)
        else:
            raise RuntimeError(f'Please check the file: {input_file_nominal}:{tree_nominal} - reshuffled entries detected')

    # ========================================
    # Process each friend tree
    # ========================================
    # Check if friend file and tree exist
    for friend_file_path, friend_tree_name in zip(friend_file_list, friend_tree_list):
        if not check_root_file(friend_file_path, friend_tree_name):
            raise FileNotFoundError(f'The friend file {friend_file_path} does not contain the tree {friend_tree_name}')

    # Store the overlapped branches for each friend tree
    overlapped_branches_dict: Dict[str, List[str]] = {}
    for friend_index, (friend_file_path, friend_tree_name) in enumerate(zip(friend_file_list, friend_tree_list)):
        logger.info(f'Adding friend: {friend_file_path}:{friend_tree_name}')

        # Open friend file and get tree
        friend_file = TFile(friend_file_path)
        friend_tree = friend_file.Get(friend_tree_name)

        # ========================================
        # Validate entry count consistency
        # ========================================

        # Check if friend tree has same number of entries as nominal tree
        nominal_entries = nominal_tree.GetEntries()
        friend_entries = friend_tree.GetEntries()

        if nominal_entries != friend_entries:
            if strict_entry_size_check:
                raise AssertionError(
                    f'{colorama.Fore.RED}The friend tree {friend_file_path}:{friend_tree_name} '
                    f'has {friend_entries} entries but the nominal tree {input_file_nominal}:{tree_nominal} '
                    f'has {nominal_entries} entries{colorama.Style.RESET_ALL}'
                )
            else:
                logger.warning(
                    f'The friend tree [bold yellow]{friend_file_path}:{friend_tree_name}[/] '
                    f'has {friend_entries} entries but the nominal tree '
                    f'[bold yellow]{input_file_nominal}:{tree_nominal}[/] has {nominal_entries} entries',
                    extra={"markup": True},
                )

        # ========================================
        # Branch compatibility checking
        # ========================================

        # Get branch names from friend tree
        friend_tree_column_names = [branch.GetName() for branch in friend_tree.GetListOfBranches()]

        # Check if overlapping branches have identical values
        overlapped_branches = list(set(nominal_branches) & set(friend_tree_column_names))
        if overlapped_branches:

            # Update the overlapped branches dictionary
            overlapped_branches_dict[f'{friend_file_path}:{friend_tree_name}'] = overlapped_branches

            if check_branch_compatibility:

                # Create a RDataFrame from the friend tree
                friend_rdf = RDataFrame(friend_tree)
                skip_compatibility_check_branches = skip_compatibility_check_branches or []

                # Check each overlapping branch for identical values
                for branch_name in overlapped_branches:
                    if branch_name in skip_compatibility_check_branches:
                        continue

                    is_identical, error_message = are_branches_identical(nominal_rdf, friend_rdf, branch_name, branch_name)

                    if not is_identical:
                        raise RuntimeError(
                            f'Branch compatibility check failed for branch "{branch_name}" '
                            f'between nominal tree {input_file_nominal}:{tree_nominal} '
                            f'and friend tree {friend_file_path}:{friend_tree_name}. '
                            f'Error: {error_message}'
                        )

        # ========================================
        # Build index for efficient merging
        # ========================================

        # Build index if specified (required for multithreading)
        if build_index_names[0] is not None:
            if build_index_names[0] not in friend_tree_column_names:
                raise AssertionError(f'The friend tree {friend_file_path}:{friend_tree_name} ' f'does not have the branch {build_index_names[0]} required for indexing')

            logger.info(f'Building index: {build_index_names[0]}:{build_index_names[1]}')
            friend_tree.BuildIndex(build_index_names[0], build_index_names[1])

        # ========================================
        # Handle reshuffled entries in friend tree
        # ========================================

        # Check if friend tree has been reshuffled
        if friend_tree.TestBit(r.TTree.kEntriesReshuffled):
            logger.warning(f'The friend tree {friend_file_path}:{friend_tree_name} has been reshuffled')
            if ignore_k_entries_reshuffled:
                logger.warning('Here we will try to reset the status bit, but please take your own risk')
                reset_tree_reshuffled_bit(friend_tree)
            else:
                raise RuntimeError(f'Please check the file - reshuffled entries detected in friend tree')

        # ========================================
        # Add friend tree to nominal tree
        # ========================================

        # Add friend with unique alias to avoid naming conflicts
        friend_alias = f'{friend_tree_name}_{friend_index}'
        nominal_tree.AddFriend(friend_tree, friend_alias)

        # Add friend tree branches to the list of branches to save
        unique_branches_to_save.extend([branch.GetName() for branch in friend_tree.GetListOfBranches()])

    # ========================================
    # Save merged tree to output file
    # ========================================

    # Remove duplicate branch names
    unique_branches_to_save = list(set(unique_branches_to_save))

    # Create output directory if it doesn't exist
    Path(output_file_name).parent.mkdir(parents=True, exist_ok=True)

    # The temporary file to store the merged tree
    temp_merged_file: str = str(Path(output_file_name).parent / f"{Path(output_file_name).stem}_tmp.root")
    if Path(temp_merged_file).exists():
        Path(temp_merged_file).unlink()

    # Create RDataFrame from the merged tree (nominal + friends)
    merged_rdf = RDataFrame(nominal_tree)

    # Save the merged tree with specified branches to the temporary file
    if isinstance(output_branches, str) and output_branches.upper() == 'ALL':
        logger.info(f'Saving all branches to {temp_merged_file}')
        merged_rdf.Snapshot(output_tree_name, temp_merged_file)
        rprint(f'Saved all branches to {temp_merged_file}')
    else:
        # Use specified branches or all unique branches if none specified
        branches_to_save = output_branches or unique_branches_to_save
        logger.info(f'Saving {len(branches_to_save)} branches to {temp_merged_file}')
        logger.debug(f'Branches to save: {branches_to_save}')
        merged_rdf.Snapshot(output_tree_name, temp_merged_file, branches_to_save)
        rprint(f'Saved {len(branches_to_save)} branches to {temp_merged_file}')

    # Remove the overlapped branches from the temporary file
    # Note: overlapped_branches_dict serves as a flag indicating that indexed branches
    # (e.g., DecayTree_0_branchName) may have been created during merging
    if remove_overlapped_branches and overlapped_branches_dict:

        # Remove the overlapped branches from the temporary file
        rprint(f'Removing the overlapped branches from the temporary file {temp_merged_file} and saving to {output_file_name}')
        clean_merged_tree_branches(
            input_file_path=temp_merged_file,
            input_tree_name=output_tree_name,
            output_file_path=output_file_name,
            check_duplicate_branches=True,
        )
        Path(temp_merged_file).unlink()
        rprint(f'The overlapped branches have been removed from the temporary file and saved to {output_file_name}')
        rprint(f'The temporary file {temp_merged_file} has been removed')

    else:
        shutil.move(temp_merged_file, output_file_name)
        rprint(f'No overlapped branches found in the temporary file, so the temporary file {temp_merged_file} has been moved to {output_file_name}')

    return output_file_name


def clean_merged_tree_branches(
    input_file_path: str,
    input_tree_name: str,
    output_file_path: str,
    output_tree_name: Optional[str] = None,
    check_duplicate_branches: bool = True,
    tolerance: float = 1e-10,
    strict_check: bool = True,
) -> str:
    """
    Clean up duplicate branches created by tree merging and verify their consistency.

    When trees are merged with AddFriend, overlapping branches get renamed to
    {TreeName}_{index}_{branchName}. This function:
    1. Identifies all such indexed branches using regex pattern
    2. Verifies they contain identical values across all indices
    3. Removes the indexed branches, keeping only the original non-indexed versions

    Parameters:
        input_file_path (str): Path to input ROOT file
        input_tree_name (str): Name of the tree in the input file
        output_file_path (str): Path for output ROOT file with cleaned branches
        output_tree_name (Optional[str]): Name for output tree (defaults to input_tree_name)
        tolerance (float): Tolerance for floating point comparisons (default: 1e-10)
        strict_check (bool): If True, raises error when indexed branches differ (default: True)

    Returns:
        str: Path to the output file

    Raises:
        RuntimeError: If indexed branches have different values (when strict_check=True)
        FileNotFoundError: If input file doesn't exist or doesn't contain the tree

    Example:
        >>> # Clean a merged tree with indexed branches
        >>> output_file = clean_merged_tree_branches(
        ...     input_file_path="merged.root",
        ...     input_tree_name="DecayTree",
        ...     output_file_path="cleaned.root"
        ... )
    """

    # Set output tree name
    output_tree_name = output_tree_name or input_tree_name

    # Validate input file using existing helper
    if not check_root_file(input_file_path, input_tree_name):
        raise FileNotFoundError(f'The input file {input_file_path} does not contain the tree {input_tree_name}')

    logger.info(f'Processing tree "{input_tree_name}" from {input_file_path}')

    # ========================================
    # Get all branch names using existing helper
    # ========================================

    all_branches = get_branch_names(input_file_path, input_tree_name)
    logger.info(f'Found {len(all_branches)} total branches')

    # ========================================
    # Identify indexed branches using regex
    # Pattern: {TreeName}_{index}_{branchName}
    # ========================================

    pattern = re.compile(rf'^{re.escape(input_tree_name)}_(\d+)_(.+)$')

    # Group indexed branches by their base name
    indexed_branches_map: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
    non_indexed_branches: List[str] = []

    for branch_name in all_branches:
        match = pattern.match(branch_name)
        if match:
            index = int(match.group(1))
            base_name = match.group(2)
            indexed_branches_map[base_name].append((branch_name, index))
        else:
            non_indexed_branches.append(branch_name)

    logger.info(f'Found {len(indexed_branches_map)} base branches with indexed versions')
    logger.info(f'Found {len(non_indexed_branches)} non-indexed branches')

    # ========================================
    # Verify indexed branches have identical values
    # ========================================

    if check_duplicate_branches and indexed_branches_map:
        logger.info('Checking consistency of indexed branches...')

        # Create RDataFrame once for all comparisons
        rdf = RDataFrame(input_tree_name, input_file_path)

        all_consistent = True
        inconsistent_branches = []

        for base_name, indexed_versions in indexed_branches_map.items():
            if len(indexed_versions) <= 1:
                continue

            # Sort by index for consistent comparison
            indexed_versions.sort(key=lambda x: x[1])
            logger.info(f'  Checking base branch: {base_name} ({len(indexed_versions)} versions)')

            # Compare each version against the first one
            reference_branch = indexed_versions[0][0]

            for i in range(1, len(indexed_versions)):
                compare_branch = indexed_versions[i][0]

                # Use existing helper function for comparison
                is_identical, error_message = are_branches_identical(rdf, rdf, reference_branch, compare_branch, tolerance)

                if not is_identical:
                    all_consistent = False
                    inconsistent_branches.append(base_name)
                    logger.error(f'[bold red]Inconsistent values for base branch "{base_name}":[/]\n' f'    {reference_branch} != {compare_branch}\n' f'    {error_message}', extra={"markup": True})
                    break

        # Handle inconsistencies
        if not all_consistent:
            error_msg = f'Found {len(inconsistent_branches)} base branch(es) with inconsistent indexed versions:\n' f'  {inconsistent_branches}\n' f'Cannot proceed with cleaning.'
            if strict_check:
                raise RuntimeError(error_msg)
            else:
                logger.warning(f'[bold yellow]{error_msg}[/]', extra={"markup": True})
        else:
            logger.info('[bold green]All indexed branches are consistent[/]', extra={"markup": True})

    # ========================================
    # Determine branches to save
    # ========================================

    branches_to_save = non_indexed_branches.copy()

    # If base branch doesn't exist, keep the first indexed version
    for base_name, indexed_versions in indexed_branches_map.items():
        if base_name not in non_indexed_branches:
            indexed_versions.sort(key=lambda x: x[1])
            first_version = indexed_versions[0][0]
            logger.warning(f'[bold yellow]Base branch "{base_name}" not found in non-indexed branches. ' f'Keeping indexed version: {first_version}[/]', extra={"markup": True})
            branches_to_save.append(first_version)

    logger.info(f'Will save {len(branches_to_save)} branches to output file')

    # ========================================
    # Save cleaned tree to output file
    # ========================================

    # Create output directory if needed
    Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)

    # Create RDataFrame and save with selected branches
    rdf_output = RDataFrame(input_tree_name, input_file_path)
    rdf_output.Snapshot(output_tree_name, output_file_path, branches_to_save)

    logger.info(f'[bold green]Successfully saved cleaned tree to {output_file_path}[/]', extra={"markup": True})

    return output_file_path


def apply_cut_to_rdf(rdf: RDataFrame, cut_str: str = 'NONE') -> RDataFrame:
    # ========================================
    # Apply the cut_str
    # ========================================

    cut_str = '' if cut_str.upper().replace(' ', '') in {'NONE', '1>0', '(1>0)'} else cut_str

    if cut_str:
        if rdf.Count().GetValue() > 0:
            logger.info(f'Applying cut: {cut_str}, the number of entries before applying the cut is {rdf.Count().GetValue()}')
            rdf = rdf.Filter(cut_str)
            logger.info(f'The number of entries after applying the cut is {rdf.Count().GetValue()}')
        else:
            logger.warning(f'The dataframe is empty before applying the cut: [bold yellow]{cut_str}[/]', extra={"markup": True})

    return rdf


def add_tmp_var_to_rdf(rdf: RDataFrame, var_expression: str, var_name: Optional[str] = None) -> Tuple[RDataFrame, str]:
    # ========================================
    # Define the temporary variable
    # ========================================

    # Define the temporary variable
    var_name = var_name or '__var'
    __variable = var_name

    # Check if the variable name already exists in the dataframe
    n_random_number = 0
    while __variable in rdf.GetColumnNames():
        __variable = f'{__variable}_random{n_random_number}'
        n_random_number += 1

    if n_random_number > 0:
        logger.warning(
            f'The variable name [bold yellow]{var_name}[/] already exists in the dataframe. A random number is added as suffix. The new variable name is [bold yellow]{__variable}[/]',
            extra={"markup": True},
        )

    # Define the variable
    rdf = rdf.Define(__variable, var_expression)

    # Return the dataframe and the temporary variable name
    return rdf, __variable


def add_tmp_weight_to_rdf(
    rdf: RDataFrame,
    weight_expr: str = 'NONE',
    output_weight_name: Optional[str] = None,
) -> Tuple[RDataFrame, str]:
    # ========================================
    # Prepare the weight variable
    # ========================================

    # Define the temporary weight variable
    output_weight_name = output_weight_name or '__weight'
    __weight_name = output_weight_name

    if (weight_expr) and (weight_expr.replace(' ', '').upper() not in {'NONE', 'ONE', '1'}):
        # Parse the weight string
        weight_expr = weight_expr
    else:
        weight_expr = '1.0'

    # Check if the weight name already exists in the dataframe
    n_random_number = 0
    while __weight_name in rdf.GetDefinedColumnNames():
        __weight_name = f'{__weight_name}_random{n_random_number}'
        n_random_number += 1

    if n_random_number > 0:
        logger.warning(
            f'The weight name [bold yellow]{output_weight_name}[/] already exists in the dataframe. A random number is added as suffix. The new weight name is [bold yellow]{__weight_name}[/]',
            extra={"markup": True},
        )

    # Define the weight variable
    rdf = rdf.Define(__weight_name, weight_expr)

    # Return the dataframe and the temporary weight variable name
    return rdf, __weight_name


def get_sum_weight(rdf: RDataFrame, weight_expr: str, cut: str = 'None') -> float:
    # Apply the cut
    rdf = apply_cut_to_rdf(rdf, cut)

    # Define the temporary weight variable
    __weight_name = '__weight'
    rdf, __weight_name = add_tmp_weight_to_rdf(rdf, weight_expr, __weight_name)

    # Return the sum of the weight
    return rdf.Sum(__weight_name).GetValue()


def get_branch_names(input_file_path: str, input_tree_name: str) -> List[str]:
    """
    Function to get the names of all the branches (columns) in a ROOT TTree.

    Parameters:
    - input_file_path: Path to the input ROOT file.
    - input_tree_name: Name of the TTree in the ROOT file.

    Returns:
    - List of branch (column) names.
    """

    # Check if the input file is a valid ROOT file with the given tree name
    if not check_root_file(input_file_path, input_tree_name):
        raise RuntimeError(f"{colorama.Fore.RED}cannot open file {input_file_path}{colorama.Style.RESET_ALL}")

    # Open the ROOT file
    tfile = TFile.Open(input_file_path)

    # Get the TTree from the file
    ttree = tfile.Get(input_tree_name)

    # Get the list of branch names
    branches = ttree.GetListOfBranches()
    branch_names = [branch.GetName() for branch in branches]

    tfile.Close()

    return branch_names


def get_rdf_with_branches(
    input_file_path: str | list[str],
    input_tree_name: str,
    branches_to_read: str | list[str],
    fill_missing_branches: bool = True,
    n_entries_max: int = -1,
) -> RDataFrame:
    """
    Function to create an RDataFrame with specified branches from a ROOT file.
    If a branch is missing, it sets that branch to 0 if `fill_missing_branches` is True.

    Parameters:
    - input_file_path: Path or list of paths to the input ROOT files.
    - input_tree_name: Name of the TTree in the ROOT file.
    - branches_to_read: List or single branch name to read.
    - fill_missing_branches: If True, missing branches are set to 0. If False, missing branches are ignored.
    - n_entries_max: Maximum number of entries to read. If <= 0, all entries are read.

    Returns:
    - RDataFrame: A dataframe with the requested branches.
    """

    # ========================================
    # Convert the input to a list if it's a single string
    # ========================================

    input_file_path = input_file_path if isinstance(input_file_path, list) else [input_file_path]

    # ========================================
    # Check if the input file with the given tree name exists
    # ========================================

    for input_file in input_file_path:
        check_root_file(input_file, input_tree_name)

    # ========================================
    # Convert the input to a list if it's a single string
    # ========================================

    branches_to_read = branches_to_read if isinstance(branches_to_read, list) else [branches_to_read]
    branches_to_read = list(set(branches_to_read))
    logger.info(f'Requested branches: {branches_to_read}')

    # ========================================
    # Get the branch names that are available in the tree
    # ========================================

    # Get the branch names that are available in the tree
    branches_exist_in_tree = get_branch_names(input_file_path[0], input_tree_name)

    # ========================================
    # Identify existing and missing branches
    # ========================================

    # Identify existing and missing branches
    existing_branches = [br for br in branches_to_read if br in branches_exist_in_tree]
    missing_branches = [br for br in branches_to_read if br not in branches_exist_in_tree]

    # If no branches are missing, create the RDataFrame directly with the requested branches
    # So, at the moment, we could not simply call 'RDataFrame(input_tree_name, input_file_path, branches_to_read)' to read only the requested branches.
    # Hopefully, this will be fixed in the future.
    if not missing_branches:
        rdf = RDataFrame(input_tree_name, input_file_path, branches_to_read)

    # Otherwise, create the RDataFrame with existing branches
    else:
        # There is a bug in RDataFrame. Even if only selected branches are requested, RDataFrame will read all branches.
        rdf = RDataFrame(input_tree_name, input_file_path, existing_branches)

        logger.warning(f'Missing required branches: [bold yellow]{missing_branches}[/]', extra={"markup": True})

        # Handle missing branches
        if fill_missing_branches:
            for branch in missing_branches:
                logger.warning(f'Filling missing branch: [bold yellow]{branch:<40}[/] with 0.0', extra={"markup": True})
                rdf = rdf.Define(branch, "0.0")

        else:
            logger.warning('Ignoring missing branches', extra={"markup": True})

    # Set the maximum number of entries to read
    n_candidates = rdf.Count().GetValue()
    if n_entries_max > 0:
        if n_entries_max < n_candidates:
            logger.info(f'Setting the maximum number of entries to read to {n_entries_max} (from {n_candidates})')
            rdf = rdf.Range(n_entries_max)
        else:
            logger.warning(
                f'The number of entries in the input file is {n_candidates}, but the maximum number of entries to read is {n_entries_max}, so we will read all entries that are available.',
                extra={"markup": True},
            )

    # Return the RDataFrame
    return rdf


def create_selected_dataframe(input_source: Union[str, list, RDataFrame], tree_name: str, cut_str: str = 'None') -> RDataFrame:
    """Create and prepare a RDataFrame from various input sources.

    Parameters:
        input_source: Input can be:
            - str: Single file path or comma-separated file paths
            - List[str]: List of file paths
            - RDataFrame: Existing RDataFrame (returned as-is)
        tree_name: Name of the tree to load from ROOT files
        cut_str: Selection criteria to apply (default: 'None')

    Returns:
        RDataFrame: Processed dataframe with cuts applied

    Raises:
        TypeError: If input_source type is invalid
        FileNotFoundError: If input files don't exist
        RuntimeError: If RDataFrame creation fails
    """
    # ========================================
    # Check input type
    # ========================================

    if isinstance(input_source, (str, list)):
        input_source = input_source if isinstance(input_source, list) else input_source.split(',')
        rdf = RDataFrame(tree_name, input_source)
        logger.info(f'Loading tree [bold green]"{tree_name}"[/] from [bold green]{input_source}[/]', extra={"markup": True})
    elif ('ROOT.RDF.RInterface' in str(type(input_source))) or ('ROOT.RDataFrame' in str(type(input_source))):
        rdf = input_source
    else:
        raise TypeError(f"Invalid input type: {type(input_source)}. Expected string, list, or RDataFrame.")

    # ========================================
    # Apply selection criteria
    # ========================================

    return apply_cut_to_rdf(rdf, cut_str)


def set_branch_status(
    ch: TChain,
    keep_all_branches: bool,
    branch_list: Union[List[str], str],
    status: bool,
) -> None:
    """set branch status helper
    Set branch status.
        ch: [TTree/TChain] tree/chain of the file.
        keep_all_branches: [bool] whether keep all branchs, this operation is on the top of all other status operation.
        branchList: [list] branch which status will be changed (wildcard is supported).
        status: [bool] set branch status, if True: set certain branch status to be true, vice versa.
    Return sum of the weights [float].
    """
    branch_list = [branch_list] if type(branch_list) != type([]) else branch_list

    ch.SetBranchStatus("*", 0) if keep_all_branches else None

    if branch_list:
        for b in branch_list:
            ch.SetBranchStatus(b, status)


def make_TChain(
    input_files: Union[List[str], str],
    input_tree_name: str = "DecayTree",
    cut_string: Optional[str] = None,
    max_run_events: int = -1,
    keep_all_branches: bool = True,
    branch_list: Optional[Union[List[str], str]] = None,
    branch_status: bool = True,
) -> TChain:
    """make TChain helper
    Helper function to make TChain.
        input_files: [list] input file list which will be cooperated togerther into chain.
        input_tree_name: [str] the name of input tree.
        cut_string: [str] add cuts to the tree if specified.
        max_run_events: [int] maximum of events to run.
        keep_all_branches: [bool] whether keep all branchs, this operation is on the top of all other status operation.
        branchList: [list] branch which status will be changed (wildcard is supported).
        branch_status: [bool] set branch status for the branches in branch_list, if True: set certain branch status to be true, vice versa.
    Return TChain
    """

    input_files = [input_files] if type(input_files) != type([]) else input_files
    ch = TChain(input_tree_name)
    for it in input_files:
        logger.info(f'Adding file: {it} to TChain')
        ch.Add(it)

    if branch_list:
        set_branch_status(
            ch=ch,
            keep_all_branches=keep_all_branches,
            branch_list=branch_list,
            status=branch_status,
        )

    if max_run_events != -1:
        MaxEntries = min(ch.GetEntries(), max_run_events)
        rprint(f"The input file has {ch.GetEntries()} events, and set the maximum of events to run is {max_run_events}.")
    else:
        MaxEntries = ch.GetEntries()

    # MaxEntries = ch.GetEntries() if max_run_events == -1 else max_run_events

    ch_selected = ch.CopyTree(cut_string, "", MaxEntries, 0) if cut_string else ch.CopyTree("1>0", "", MaxEntries, 0)
    if ch_selected.GetEntries() == 0:
        logger.warning('The selected chain has 0 entries.', extra={"markup": True})

    return ch_selected


# * ############################################################## #


# save plots from TCanvas
def save_pic_from_tcanvas(canvas: TCanvas, outpic: str, formats: Union[str, List[str]] = "") -> None:
    """Root helper
    Print picture as *.png, *.pdf, *.eps, *.C or customized format.
        canvas: [TCanvas] the prepared canvas to be drawn.
        outpic: [string] the output address of picture to be saved.
        format: [str | list] format of picture to be saved.
    """
    extSuffix = [".pdf", ".png", ".C"]

    outpic = Path(outpic).resolve().as_posix()
    Path(outpic).parent.mkdir(parents=True, exist_ok=True)

    if os.path.splitext(outpic)[1] in extSuffix:
        outpic_noExt = os.path.splitext(outpic)[0]
    else:
        outpic_noExt = outpic

    if not formats:
        formats = extSuffix

    formats = [formats] if type(formats) != type([]) else formats
    for _f in formats:
        _outpic = outpic_noExt + _f
        canvas.SaveAs(_outpic)


# * ############################################################## #
# * ##########      For testing purposes      ##################### #
# * ############################################################## #


def generate_test_root_file(
    output_file_path: str,
    tree_name: str = "DecayTree",
    num_entries: int = 1000,
    random_seed: int = 42,
) -> None:
    """
    Generate a ROOT file with various branch types for testing purposes.

    Creates branches with different data types:
    - random_integers_0_100: Random integers between 0-100
    - random_floats_normal: Random floats from normal distribution (mean=0, std=1)
    - gaussian_mean_1_std_1: Random floats from normal distribution (mean=1, std=1)
    - gaussian_mean_1_std_2: Random floats from normal distribution (mean=1, std=2)
    - exponential_scale_2: Random floats from exponential distribution (scale=2)
    - sequential_integers: Sequential integers from 0 to num_entries-1

    Args:
        output_file_path: Path where the ROOT file will be saved
        tree_name: Name of the tree to create (default: "DecayTree")
        num_entries: Number of entries/events to generate (default: 1000)
        random_seed: Seed for random number generation for reproducibility (default: 42)

    Example:
        >>> generate_test_root_file("test_data.root", num_entries=5000, random_seed=123)
        >>> # Creates test_data.root with 5000 entries using seed 123
    """
    logger.info(f"Generating test ROOT file: {output_file_path}")
    logger.info(f"  Tree name: {tree_name}")
    logger.info(f"  Number of entries: {num_entries}")
    logger.info(f"  Random seed: {random_seed}")

    # ========================================
    # Set random seeds for reproducible results
    # ========================================

    np.random.seed(random_seed)
    random.seed(random_seed)

    # ========================================
    # Generate various types of test data
    # ========================================

    test_data = {
        'random_integers_0_100': np.random.randint(0, 100, num_entries),
        'random_floats_normal': np.random.normal(0, 1, num_entries),
        'gaussian_mean_1_std_1': np.random.normal(1, 1, num_entries),
        'gaussian_mean_1_std_2': np.random.normal(1, 2, num_entries),
        'exponential_scale_2': np.random.exponential(2.0, num_entries),
        'sequential_integers': np.arange(num_entries, dtype=np.int32),
    }

    # ========================================
    # Create RDataFrame from the generated data
    # ========================================

    test_dataframe = r.RDF.FromNumpy(test_data)

    logger.info("Generated branches:")
    for branch_name in test_dataframe.GetColumnNames():
        logger.info(f"  - {branch_name}")

    # ========================================
    # Ensure output directory exists
    # ========================================

    output_path = Path(output_file_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save RDataFrame to ROOT file
    test_dataframe.Snapshot(tree_name, output_path.as_posix())
    logger.info(f"Saved ROOT file to: {output_path}")


# * ############################################################## #
