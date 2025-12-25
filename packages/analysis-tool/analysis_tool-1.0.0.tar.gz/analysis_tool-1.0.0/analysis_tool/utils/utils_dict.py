'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-06-19 15:31:32 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-11-04 10:47:42 +0100
FilePath     : utils_dict.py
Description  : Dictionary utility functions for configuration management, comparison, and manipulation

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

# ========================================
# Import statements and setup
# ========================================

import contextlib
import os, sys
import json
import random
import re
import inspect
import textwrap
from itertools import chain
from collections import Counter
from collections.abc import Mapping
import string
import copy
from pathlib import Path


from typing import TypedDict, Literal, Optional, Sequence, Union, TypeVar, NamedTuple, Dict, List, Any


from rich import print as rprint

import logging
from analysis_tool.utils.utils_logging import get_logger

# Check if running in Snakemake
is_snakemake = any('snakemake' in arg for arg in sys.argv)

if not is_snakemake:
    logger = get_logger(__name__, auto_setup_rich_logging=True)
else:
    logger = logging.getLogger(__name__)


# ========================================
# Environment variable expansion utilities
# ========================================


def dict_expand_env_vars(data: Union[dict, list, str, Any]) -> Union[dict, list, str, Any]:
    """
    Recursively expand environment variables in nested data structures.

    This function traverses dictionaries, lists, and strings to find and expand
    environment variables using the format $VAR or ${VAR}.

    Args:
        data: Input data structure (dict, list, str, or any other type)

    Returns:
        Same structure as input with environment variables expanded

    Examples:
        >>> data = {"path": "$HOME/data", "items": ["$USER", "static"]}
        >>> expanded = dict_expand_env_vars(data)
        >>> # Returns: {"path": "/home/user/data", "items": ["username", "static"]}
    """
    if isinstance(data, dict):
        # Recursively process all dictionary values
        return {k: dict_expand_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        # Recursively process all list items
        return [dict_expand_env_vars(v) for v in data]
    elif isinstance(data, str):
        # Expand environment variables in strings
        return os.path.expandvars(data)
    # Return unchanged for other data types
    return data


# ========================================
# Dictionary comparison and analysis tools
# ========================================


def compare_dicts(
    dict1: dict,
    dict2: dict,
    flag_dict1: str = 'Baseline',
    flag_dict2: str = 'Overwriting',
    *,
    ignore_keys_only_in_dict1: bool = False,
    ignore_keys_only_in_dict2: bool = False,
    max_depth: int = 50,
    _path: str = "",
    _is_root: bool = True,
    _current_depth: int = 0,
) -> dict:
    """
    Compare two dictionaries and return their differences with readable output.

    This function performs a deep comparison of two dictionaries, identifying:
    - Keys that exist only in the first dictionary
    - Keys that exist only in the second dictionary
    - Keys with different values between the dictionaries

    The comparison supports nested dictionaries and provides colored output
    for easy visualization of differences.

    Args:
        dict1: First dictionary for comparison (baseline)
        dict2: Second dictionary to be compared against first
        flag_dict1: Descriptive label for first dictionary in output
        flag_dict2: Descriptive label for second dictionary in output
        ignore_keys_only_in_dict1: Skip reporting keys unique to dict1
        ignore_keys_only_in_dict2: Skip reporting keys unique to dict2
        max_depth: Maximum recursion depth to prevent infinite loops
        _path: Internal parameter for tracking nested key paths
        _is_root: Internal parameter indicating if this is the root call
        _current_depth: Internal parameter tracking current recursion depth

    Returns:
        Dictionary with categorized differences:
        {
            'only_in_dict1': {path: value, ...},      # Keys unique to dict1
            'only_in_dict2': {path: value, ...},      # Keys unique to dict2
            'value_differences': {                     # Keys with different values
                path: {'dict1': value1, 'dict2': value2}, ...
            },
            'summary': {                               # Summary statistics
                'total_differences': int,
                'only_in_dict1': int,
                'only_in_dict2': int,
                'value_differences': int
            }
        }

    Examples:
        >>> d1 = {'a': 1, 'b': {'x': 10}}
        >>> d2 = {'a': 2, 'b': {'x': 10}, 'c': 3}
        >>> result = compare_dicts(d1, d2)
        # Prints colored diff and returns structured result
    """
    # Print header for root-level comparison
    if _is_root:
        rprint(f"\n[bold blue]═══ Comparing Dictionaries ═══[/bold blue]")
        rprint(f"[cyan]'{flag_dict1}'[/cyan] vs [cyan]'{flag_dict2}'[/cyan]\n")

    # Check depth limit to prevent infinite recursion
    if _current_depth >= max_depth:
        logger.warning(f"Max depth {max_depth} reached at path '{_path}' - stopping recursion")
        return {
            'only_in_dict1': {},
            'only_in_dict2': {},
            'value_differences': {},
            'summary': {'total_differences': 0, 'only_in_dict1': 0, 'only_in_dict2': 0, 'value_differences': 0},
            'max_depth_reached': _path,  # Track where recursion stopped
        }

    # Initialize counters for accurate statistics
    actual_only_dict1 = 0
    actual_only_dict2 = 0

    # Initialize result structure
    result = {
        'only_in_dict1': {},
        'only_in_dict2': {},
        'value_differences': {},
        'summary': {'total_differences': 0, 'only_in_dict1': 0, 'only_in_dict2': 0, 'value_differences': 0},
    }

    # Get all unique keys from both dictionaries
    all_keys = set(dict1.keys()) | set(dict2.keys())

    # Process each key in sorted order for consistent output
    for key in sorted(all_keys):
        # Build nested path string for reporting
        current_path = f"{_path}.{key}" if _path else key

        if key not in dict1:
            # Key exists only in dict2
            actual_only_dict2 += 1

            if ignore_keys_only_in_dict2:
                continue

            # Display the unique key with formatting
            rprint(f"[red]➤[/red] [bold]'{current_path}'[/bold] only in [cyan]{flag_dict2}[/cyan]")
            rprint(f"   [dim]Value:[/dim] {_format_value(dict2[key])}\n")

            result['only_in_dict2'][current_path] = dict2[key]

        elif key not in dict2:
            # Key exists only in dict1
            actual_only_dict1 += 1

            if ignore_keys_only_in_dict1:
                continue

            # Display the unique key with formatting
            rprint(f"[red]➤[/red] [bold]'{current_path}'[/bold] only in [cyan]{flag_dict1}[/cyan]")
            rprint(f"   [dim]Value:[/dim] {_format_value(dict1[key])}\n")

            result['only_in_dict1'][current_path] = dict1[key]

        elif isinstance(dict1[key], Mapping) and isinstance(dict2[key], Mapping):
            # Both values are dictionaries - recurse deeper
            nested_result = compare_dicts(
                dict1[key],
                dict2[key],
                flag_dict1,
                flag_dict2,
                ignore_keys_only_in_dict1=ignore_keys_only_in_dict1,
                ignore_keys_only_in_dict2=ignore_keys_only_in_dict2,
                max_depth=max_depth,
                _path=current_path,
                _is_root=False,
                _current_depth=_current_depth + 1,  # Increment depth counter
            )

            # Merge results from nested comparison
            for category in ['only_in_dict1', 'only_in_dict2', 'value_differences']:
                result[category].update(nested_result[category])
                result['summary'][category] += nested_result['summary'][category]

        elif dict1[key] != dict2[key]:
            # Values differ between dictionaries
            rprint(f"[yellow]⚠[/yellow] [bold]'{current_path}'[/bold] differs:")
            rprint(f"   [cyan]{flag_dict1}:[/cyan] {_format_value(dict1[key])}")
            rprint(f"   [cyan]{flag_dict2}:[/cyan] {_format_value(dict2[key])}\n")

            result['value_differences'][current_path] = {flag_dict1: dict1[key], flag_dict2: dict2[key]}
            result['summary']['value_differences'] += 1

    # Update final summary counts
    result['summary']['only_in_dict1'] = actual_only_dict1
    result['summary']['only_in_dict2'] = actual_only_dict2
    result['summary']['total_differences'] = result['summary']['only_in_dict1'] + result['summary']['only_in_dict2'] + result['summary']['value_differences']

    # Print summary only for root-level call
    if _is_root:
        _print_summary(result['summary'], flag_dict1, flag_dict2)

    return result


def _format_value(value: Any, max_length: int = 100) -> str:
    """
    Format a value for readable display in comparison output.

    Handles different data types appropriately:
    - Dictionaries: Show structure or summary for large ones
    - Lists/Tuples: Show content or summary for large ones
    - Other values: Convert to string with truncation if needed

    Args:
        value: The value to format for display
        max_length: Maximum length for string representation

    Returns:
        Formatted string representation of the value
    """
    if isinstance(value, dict):
        if len(value) == 0:
            return "{}"
        elif len(value) <= 10:
            return str(value)
        else:
            # Large dictionary - show summary
            return f"{{...}} ([dim]{len(value)} keys: {list(value.keys())}[/dim])"
    elif isinstance(value, (list, tuple)):
        if len(value) == 0:
            return "[]" if isinstance(value, list) else "()"
        elif len(value) <= 10:
            return str(value)
        else:
            # Large sequence - show summary
            type_name = "list" if isinstance(value, list) else "tuple"
            return f"[...] ([dim]{len(value)} items, {type_name}[/dim])"
    else:
        # Convert to string and truncate if necessary
        str_val = str(value)
        if len(str_val) > max_length:
            return f"{str_val[:max_length]}... ([dim]truncated[/dim])"
        return str_val


def _print_summary(summary: dict, flag_dict1: str, flag_dict2: str) -> None:
    """
    Print a formatted summary of dictionary comparison results.

    Args:
        summary: Summary dictionary with difference counts
        flag_dict1: Label for first dictionary
        flag_dict2: Label for second dictionary
    """
    total = summary['total_differences']

    rprint(f"[bold blue]═══ Summary ═══[/bold blue]")

    if total == 0:
        # No differences found
        rprint("[green]✓ No differences found - dictionaries are identical![/green]")
    else:
        # Display breakdown of differences
        rprint(f"[yellow]Found {total} total difference(s):[/yellow]")

        if summary['only_in_dict1'] > 0:
            rprint(f"  • [red]{summary['only_in_dict1']}[/red] key(s) only in [cyan]{flag_dict1}[/cyan]")

        if summary['only_in_dict2'] > 0:
            rprint(f"  • [red]{summary['only_in_dict2']}[/red] key(s) only in [cyan]{flag_dict2}[/cyan]")

        if summary['value_differences'] > 0:
            rprint(f"  • [yellow]{summary['value_differences']}[/yellow] value difference(s)")

    rprint()


# ========================================
# Configuration management utilities
# ========================================


def update_config(base_config: dict, overwrite_dict: dict) -> dict:
    """
    Recursively update a base configuration dictionary with values from an overwrite dictionary.

    This function performs a deep merge of two dictionaries, where:
    - New keys from overwrite_dict are added to the result
    - Existing keys are updated with values from overwrite_dict
    - Nested dictionaries are merged recursively
    - The original dictionaries remain unchanged (deep copy is used)

    See: http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth

    Args:
        base_config: The original configuration dictionary (remains unchanged)
        overwrite_dict: Dictionary whose values will override/extend base_config

    Returns:
        New dictionary with merged configuration

    Examples:
        >>> base = {'db': {'host': 'localhost', 'port': 5432}, 'debug': True}
        >>> override = {'db': {'port': 3306}, 'logging': {'level': 'INFO'}}
        >>> result = update_config(base, override)
        >>> # Returns: {'db': {'host': 'localhost', 'port': 3306}, 'debug': True, 'logging': {'level': 'INFO'}}

    Note:
        - Recursively merges nested dictionaries
        - Warns about type mismatches when overwriting
        - Creates deep copy to avoid modifying original inputs
    """

    # Create deep copy to avoid modifying the original base configuration
    merged_config = copy.deepcopy(base_config)

    def _recursive_update(orig_dict: dict, new_dict: dict) -> dict:
        """
        Helper function to recursively merge dictionary values.

        Args:
            orig_dict: Dictionary to be updated (modified in place)
            new_dict: Dictionary containing new/override values

        Returns:
            Updated dictionary reference
        """
        for key, value in new_dict.items():
            # Check for type mismatches and warn user
            if key in orig_dict and not isinstance(value, type(orig_dict.get(key))):
                logger.warning(f"Type mismatch for key '{key}': original type {type(orig_dict.get(key))} but new type {type(value)}. Overwriting with new value.")

            # If both values are dictionaries, merge them recursively
            if isinstance(value, Mapping) and isinstance(orig_dict.get(key), Mapping):
                orig_dict[key] = _recursive_update(orig_dict.get(key, {}), value)
            else:
                # Direct assignment for non-dict values or when key doesn't exist
                orig_dict[key] = value

        return orig_dict

    # Perform the recursive update
    _recursive_update(merged_config, overwrite_dict)

    return merged_config


# ========================================
# Dictionary manipulation utilities
# ========================================


def remove_keys(d: dict, keys_to_remove: Union[str, List[str]], inplace: bool = False) -> dict:
    """
    Remove specified keys from a dictionary recursively.

    This function traverses the entire dictionary structure and removes
    all occurrences of the specified keys at any nesting level.

    Args:
        d: Dictionary to remove keys from
        keys_to_remove: Single key name or list of key names to remove
        inplace: If True, modify the original dictionary; if False, create a copy

    Returns:
        Dictionary with specified keys removed

    Examples:
        >>> data = {'a': 1, 'secret': 'hidden', 'nested': {'secret': 'also_hidden', 'b': 2}}
        >>> clean = remove_keys(data, 'secret')
        >>> # Returns: {'a': 1, 'nested': {'b': 2}}
    """

    # Normalize input to list format
    if isinstance(keys_to_remove, str):
        keys_to_remove = [keys_to_remove]

    def _remove_keys_recursive(obj: Any) -> Any:
        """
        Recursively traverse and clean data structure.

        Args:
            obj: Current object being processed

        Returns:
            Cleaned object with specified keys removed
        """
        if isinstance(obj, dict):
            # Process dictionary: keep keys not in removal list and recurse on values
            return {k: _remove_keys_recursive(v) for k, v in obj.items() if k not in keys_to_remove}
        # Return non-dict objects unchanged
        return obj

    # Choose whether to modify original or work with copy
    _d = d if inplace else copy.deepcopy(d)

    return _remove_keys_recursive(_d)


def remove_duplicated_dict(list_of_dicts: list[dict], print_duplicated: bool = True, sequences_to_be_sorted: tuple[type] = (tuple, set)) -> list[dict]:
    """
    Remove duplicated dictionaries from a list and optionally display duplicates.

    This function identifies duplicate dictionaries by normalizing their content
    and computing JSON-based hashes. It can optionally sort sequences within
    dictionaries to treat order-independent sequences as equivalent.

    Args:
        list_of_dicts: List of dictionaries to deduplicate
        print_duplicated: Whether to print information about found duplicates
        sequences_to_be_sorted: Tuple types that should be sorted for comparison
                                (treats ('a','b') same as ('b','a'))
                                the order of the elements in these sequences is not important

    Returns:
        List containing only unique dictionaries (first occurrence kept)

    Examples:
        >>> dicts = [{'a': 1, 'tags': ('x', 'y')}, {'a': 1, 'tags': ('y', 'x')}, {'b': 2}]
        >>> unique = remove_duplicated_dict(dicts)
        >>> # Returns: [{'a': 1, 'tags': ('x', 'y')}, {'b': 2}]  # Second dict treated as duplicate
    """

    # Handle empty input
    if not list_of_dicts:
        return []

    def _normalize_for_comparison(obj):
        """
        Recursively normalize dictionary structure for comparison.

        This function ensures that dictionaries with equivalent content
        but different sequence ordering are treated as identical.

        Args:
            obj: Object to normalize

        Returns:
            Normalized version of the object
        """
        if isinstance(obj, dict):
            # Recursively normalize all dictionary values
            return {k: _normalize_for_comparison(v) for k, v in obj.items()}
        elif isinstance(obj, sequences_to_be_sorted):
            try:
                # Sort sequences for order-independent comparison
                return tuple(sorted(_normalize_for_comparison(item) for item in obj))
            except TypeError:
                # Handle cases where items aren't sortable (mixed types, etc.)
                return tuple(_normalize_for_comparison(item) for item in obj)
        else:
            # Return other types unchanged
            return obj

    # Track seen dictionaries and results
    seen_hashes = set()
    unique_dicts = []
    duplicate_indices = []

    # First pass: identify unique and duplicate dictionaries
    for i, original_dict in enumerate(list_of_dicts):
        # Normalize dictionary structure if sequence sorting is enabled
        normalized = _normalize_for_comparison(original_dict) if sequences_to_be_sorted else original_dict

        # Create consistent hash for comparison
        dict_hash = json.dumps(normalized, sort_keys=True)

        # rprint(dict_hash)  # Debug: show hash being processed

        if dict_hash in seen_hashes:
            # Duplicate found
            duplicate_indices.append(i)
        else:
            # New unique dictionary
            seen_hashes.add(dict_hash)
            unique_dicts.append(original_dict)

    # Display duplicate information if requested
    if print_duplicated and duplicate_indices:
        rprint(f'Found {len(duplicate_indices)} duplicate dictionaries:')
        for i in duplicate_indices:
            rprint(list_of_dicts[i])
            rprint(f"[italic dim](Treated as duplicate)[/italic dim]\n")

    return unique_dicts


# ========================================
# Basic file operations placeholder
# ========================================
# Note: This section is reserved for future file operation utilities


# ========================================
# Test functions and examples
# =======================================


def test_compare_dicts():
    """
    Test function demonstrating the compare_dicts functionality.

    This function creates two complex nested dictionaries representing
    analysis configurations and compares them to show the different
    types of differences that can be detected.
    """
    # Sample baseline configuration
    dict1 = {
        'analysis': {
            'name': 'ttH_analysis',
            'version': '1.2.0',
            'channels': ['ee', 'mm', 'em'],
            'systematics': {'JES': ['up', 'down'], 'JER': ['up', 'down'], 'luminosity': 0.025},
            'regions': {'SR1': {'cuts': 'njet >= 4', 'weight': 1.0}, 'SR2': {'cuts': 'njet >= 6', 'weight': 1.2}},
        },
        'analysis2': {
            'name': 'ttH_analysis',
            'version': '1.2.0',
            'channels': ['ee', 'mm', 'em'],
            'systematics': {'JES': ['up', 'down'], 'JER': ['up', 'down'], 'luminosity': 0.025},
            'regions': {'SR1': {'cuts': 'njet >= 4', 'weight': 1.0}, 'SR2': {'cuts': 'njet >= 6', 'weight': 1.2}},
        },
        'data': {'path': '/data/2022/', 'format': 'root', 'total_events': 1000000},
        'only_in_dict1': 'baseline_value',
        'type_mismatch': 42,
        'nested_only_dict1': {'special_config': True},
    }

    # Sample updated configuration with various differences
    dict2 = {
        'analysis': {
            'name': 'ttH_analysis',
            'version': '1.3.0',  # Different version
            'channels': ['ee', 'mm', 'em', 'tt'],  # Extra channel
            'systematics': {'JES': ['up', 'down'], 'JER': ['up'], 'luminosity': 0.027, 'PDF': ['up', 'down']},  # Missing 'down', different value, new systematic
            'regions': {'SR1': {'cuts': 'njet >= 4', 'weight': 1.1}, 'SR2': {'cuts': 'njet >= 6', 'weight': 1.2}, 'CR1': {'cuts': 'njet == 3', 'weight': 0.9}},  # Different weight, new region
        },
        'data': {'path': '/data/2023/', 'format': 'parquet', 'total_events': 1500000},  # All values different
        'only_in_dict2': 'overwrite_value',
        'type_mismatch': '42',  # String instead of int - demonstrates type mismatch
        'nested_only_dict2': {'new_feature': 'enabled'},
        'Unique_key': {'a': 1, 'b': 2, 'c': 3},
    }

    # Perform comparison with specific ignore flags
    result = compare_dicts(dict1, dict2, 'Baseline_Config', 'New_Config', ignore_keys_only_in_dict1=True, ignore_keys_only_in_dict2=True)


def test_remove_duplicated_dict():
    # Your original list of dictionaries, including duplicates and nested lists
    list_of_dicts = [
        {'region': 'SR1', 'systs': ['JES_up', 'JER_down']},
        {'region': 'SR2', 'systs': ['PDF_up']},
        {'region': 'SR2', 'systs': 'PDF_up'},
        {'systs': ['JES_up', 'JER_down'], 'region': 'SR1'},
        {'systs': ('JES_up', 'JER_down'), 'region': 'SR1', 'syst2': ['JES_up', 'JER_down']},
        {'systs': ('JES_up', 'JER_down'), 'region': 'SR1', 'syst2': ['JER_down', 'JES_up']},
        {'systs': ('JES_up', 'JER_down'), 'region': 'SR1', 'syst2': ('JER_up', 'JES_down')},
    ]  # Duplicate

    rprint('--------------------------------')
    rprint('Original list of dicts:')
    rprint(list_of_dicts)

    rprint('--------------------------------')
    # Remove duplicated dicts
    unique_list = remove_duplicated_dict(list_of_dicts, sequences_to_be_sorted=(tuple, set))

    rprint(unique_list)


# ========================================
# Main execution
# ========================================

if __name__ == "__main__":
    # Run test function when script is executed directly
    # test_compare_dicts()

    test_remove_duplicated_dict()
