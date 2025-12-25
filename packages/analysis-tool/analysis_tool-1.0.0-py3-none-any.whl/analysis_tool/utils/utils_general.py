'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-08-22 03:17:50 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-11-07 03:56:58 +0100
FilePath     : utils_general.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import os, sys
import re
import argparse
import ast
from pathlib import Path

import colorama
import warnings

from itertools import chain
from typing import Any, List, Union, Tuple
import glob
import shutil
from rich import print as rprint


# ----- ArgParse part -----
def print_args(parser: argparse.ArgumentParser, args=None, only_non_defaut: bool = False):
    """
    Print arguments and sorted by
    1) default args
    2) not default args
    """

    # Check if args is None
    args = parser.parse_args() if args is None else args

    default_str_list = ['=====default args=====']
    non_default_str_list = ['=====not default args=====']

    args_dict = vars(args)
    for k, v in args_dict.items():
        default = parser.get_default(k)
        if v == default:
            default_str_list.append(f'{k}: {v}')
        else:
            non_default_str_list.append(f'{k}: {v} (default: {default})')

    non_default_str = '\n'.join(non_default_str_list)

    rprint(non_default_str)
    if not only_non_defaut:
        default_str = '\n'.join(default_str_list)
        rprint(default_str)
    rprint('-' * 15)


# ----- Others part -----
def remove_files(path_dir, key_flag, iterative=False):
    if iterative:
        for root, dirs, files in os.walk(path_dir):
            for name in files:
                if key_flag in name:
                    rprint('removing ', name)
                    os.remove(os.path.join(root, name))

    else:
        for name in os.listdir(path_dir):
            if key_flag in name:
                rprint('removing ', name)
                os.remove(name)


def copy_matched_files(input_path: str, output_path: str, *, rename_dict: dict[str, str] = None) -> bool:
    """
    Copies files matched by the input_path pattern to the specified output_path.

    - If input_path is a glob pattern, all matched files are copied.
    - If output_path is a directory, all matched files are copied into it.
    - If output_path is a single file and multiple input files are matched, raises ValueError.
    - If output_path is a single file and already exists, only overwrite if the source is newer.
    - Similar logic applies when output_path is a directory and a file with the same name exists.
    - If no files match input_path, raises FileNotFoundError.
    - If rename_dict is provided and output_path is a directory, file names will be processed
      according to the dictionary, replacing occurrences of keys with their corresponding values.

    Parameters:
        input_path (str): The source path pattern (may include wildcards).
        output_path (str): The destination path (a directory or a file path).
        rename_dict (dict[str, str], optional): Dictionary for renaming files when copying to a directory.
                                     Keys are words to be replaced, values are replacement words.

    Returns:
        bool: True if copying was successful and no exceptions were raised, False otherwise.
    """

    rprint(f"Copying files from [bold green]{input_path}[/] to [bold green]{output_path}[/]")

    # Expand the input path using glob
    input_files = glob.glob(input_path)
    if not input_files:
        raise FileNotFoundError(f"No files matched the input path: {input_path}")

    # Resolve the output path
    output_path_obj = Path(output_path).resolve()

    # Determine if the output path is a directory
    # We consider it a directory if it ends with '/' or is actually a directory
    output_is_dir = output_path.endswith('/') or output_path_obj.is_dir()

    try:
        if output_is_dir:
            # Ensure the output directory exists
            output_path_obj.mkdir(parents=True, exist_ok=True)

            for file_str in input_files:
                src = Path(file_str).resolve()

                # Process the filename if rename_dict is provided
                dest_name = src.name
                if rename_dict:
                    for old, new in rename_dict.items():
                        dest_name = dest_name.replace(old, new)
                    if dest_name != src.name:
                        rprint(f"Renamed: [bold magenta]{src.name}[/] -> [bold magenta]{dest_name}[/]")

                dest = output_path_obj / dest_name

                if dest.exists():
                    # Compare modification times
                    src_mtime = src.stat().st_mtime
                    dest_mtime = dest.stat().st_mtime

                    if src_mtime > dest_mtime:
                        rprint(f"The source file [bold blue]{src}[/] is newer, overwriting [bold yellow]{dest}[/]")
                        shutil.copy2(src, dest)
                        rprint(f"Copied: \n\t[bold blue]{src}[/] \n\tto \n\t[bold yellow]{dest}[/]")
                    elif src_mtime == dest_mtime:
                        rprint(f"The source file [bold blue]{src}[/] is the same as [bold yellow]{dest}[/], no overwrite needed")
                    else:
                        warnings.warn(f"The source file {colorama.Fore.RED}{src}{colorama.Style.RESET_ALL} is older, not overwriting {colorama.Fore.YELLOW}{dest}{colorama.Style.RESET_ALL}")
                else:
                    shutil.copy2(src, dest)
                    rprint(f"Copied: \n\t[bold blue]{src}[/] \n\tto \n\t[bold yellow]{dest}[/]")

        else:
            # Output path is a single file
            if len(input_files) > 1:
                raise ValueError(f"Cannot copy multiple files to a single file: {output_path_obj}")

            # Ensure the parent directory of the output file exists
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            src = Path(input_files[0]).resolve()
            if output_path_obj.exists():
                src_mtime = src.stat().st_mtime
                dest_mtime = output_path_obj.stat().st_mtime

                if src_mtime > dest_mtime:
                    rprint(f"The source file [bold blue]{src}[/] is newer, overwriting [bold yellow]{output_path_obj}[/]")
                    shutil.copy2(src, output_path_obj)
                    rprint(f"Copied from: \n\t[bold blue]{src}[/] \nto \n\t[bold yellow]{output_path_obj}[/]")
                elif src_mtime == dest_mtime:
                    rprint(f"The source file [bold blue]{src}[/] is the same as [bold yellow]{output_path_obj}[/], no overwrite needed")
                else:
                    warnings.warn(f"The source file {colorama.Fore.RED}{src}{colorama.Style.RESET_ALL} is older, not overwriting {colorama.Fore.YELLOW}{output_path_obj}{colorama.Style.RESET_ALL}")

            else:
                # Destination file does not exist, copy it
                shutil.copy2(src, output_path_obj)
                rprint(f"Copied from: \n\t[bold blue]{src}[/] \nto \n\t[bold yellow]{output_path_obj}[/]")

        print("All files copied successfully.")
        return True
    except Exception as e:
        print(f"An error occurred during copying: {e}")
        return False


def linecount(filename):
    """Return the number of lines of given file.

    Args:
        filename (str): the path to the file
    """
    with open(filename) as f:
        return sum(1 for _ in f)


def flatten_list(nested_item: Any) -> list[Any]:
    """
    Recursively flattens an arbitrarily nested structure of lists and tuples.

    This function will "descend" into any item that is a list or a tuple,
    collecting all non-list/tuple elements into a single, flat list.
    Other iterables (like strings, bytes, sets, dicts) are treated
    as "atoms" and are not iterated over.

    Args:
        nested_item: The item to flatten. This can be a single item
                        (like a string or number) or a nested structure
                        of lists and tuples (e.g., [1, [2, ('a', 'b')], 3]).

    Returns:
        A flat list containing all the "atomic" elements from the
        nested structure, in the order they were encountered.

    Example:
        >>> nested_structure = ['a', ['b', ('c', 'd')], 'e', [1, [2]], 3]
        >>> flatten_list(nested_structure)
        ['a', 'b', 'c', 'd', 'e', 1, 2, 3]

        >>> flatten_list('a single string')
        ['a single string']

        >>> flatten_list(123)
        [123]
    """

    # --- Base Case ---
    # This is the "stop" condition for the recursion.
    # If the item is NOT a list or a tuple, we can't (or don't want to)
    # descend into it. We consider it an "atom".
    # We return it wrapped in a list, so the caller can always
    # expect a list to be returned.
    if not isinstance(nested_item, (list, tuple)):
        return [nested_item]

    # --- Recursive Case ---
    # If we're here, nested_item IS a list or a tuple.
    # We need to process each of its sub-items.

    # We will collect the flattened results of each sub-item here.
    # This will become a "list of lists".
    all_flattened_sublists = []

    for sub_item in nested_item:
        # This is the recursive call. We call the function on
        # the sub-item. This will *always* return a flat list,
        # (thanks to our base case).
        #
        # - If sub_item is 'a', this appends ['a']
        # - If sub_item is [1, 2], this appends [1, 2]
        flattened_sublist = flatten_list(sub_item)
        all_flattened_sublists.append(flattened_sublist)

    # At this point, all_flattened_sublists might look like:
    # [['a'], ['b', 'c', 'd'], ['e'], [1, 2], [3]]

    # We use chain.from_iterable to "stitch" all these sub-lists
    # together into one single, efficient iterator.
    flattened_iterator = chain.from_iterable(all_flattened_sublists)

    # Finally, we convert the iterator to a list and return it.
    return list(flattened_iterator)


def is_valid_cpp_var_name(name: str):
    # Regular expression for a valid C++ variable name
    pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    return bool(pattern.match(name))


def adapt_logic_syntax(cutStr: str, compiler: str = 'numpy') -> str:
    """
    Transforms logical operators in a given string to match the syntax of the specified compiler.

    Parameters:
        cutStr (str): The input string containing logical expressions.
        compiler (str): The target syntax for the logical operators.
                        Must be one of 'PYTHON', 'NUMPY', 'C', or 'C++'.

    Returns:
        str: The transformed string with adapted logical operators for the specified compiler.

    Raises:
        AssertionError: If the compiler argument is not one of the expected values.
    """
    # Normalize the compiler argument
    compiler = compiler.upper()
    valid_compilers = {'PYTHON', 'NUMPY', 'C', 'C++'}
    if compiler not in valid_compilers:
        raise AssertionError(f"Invalid compiler specified. Must be one of: {', '.join(valid_compilers)}")

    # Do not modify the input string
    result = cutStr.strip().replace("  ", " ")

    # Special handling to preserve '!=' as a valid operator
    # We will replace it temporarily with a unique placeholder
    placeholder = "≠"  # a character not likely to appear in the input
    result = result.replace("!=", placeholder)

    # Define replacements for logical operators
    # Default replacements use Python/Numpy-style operators
    replacements = {
        '&&': ' & ',  # Replace logical AND
        '||': ' | ',  # Replace logical OR
    }

    # Adjust replacements based on compiler selection
    if compiler == 'PYTHON':
        # Use Python's logical operators
        replacements |= {
            '!': ' not ',  # Negation
            '&&': ' and ',  # Logical AND
            '||': ' or ',  # Logical OR
        }
    elif compiler == 'NUMPY':
        # Use Numpy's bitwise operators for element-wise operations
        replacements |= {
            '!': '~',  # Bitwise NOT
            '&&': '&',  # Bitwise AND
            '||': '|',  # Bitwise OR
        }
    elif compiler in {'C', 'C++'}:
        # For C or C++, ensure operators are double symbols
        replacements |= {
            '!': '!',  # Negation remains the same
            '&': '&&',  # Replace single & with logical &&
            '|': '||',  # Replace single | with logical ||
        }

    # Apply replacements to the string
    for old, new in replacements.items():
        result = result.replace(old, new)

    # Handle edge cases specific to C/C++
    if compiler in {'C', 'C++'}:
        # Avoid triple symbols if any replacements resulted in duplications
        result = result.replace('&&&', '&&').replace('|||', '||')

    # Revert placeholder for '!=' back to '!='
    result = result.replace(placeholder, "!=")

    if cutStr != result:
        rprint(f"INFO::adapt_logic_syntax::The expression has been adapted to {compiler} syntax: [green]\n{cutStr} \n-> \n{result}[/green]")
    return result.strip()


OPERATOR_SYMBOLS = {
    'Add': '+',
    'Sub': '-',
    'Mult': '*',
    'Div': '/',
    'FloorDiv': '//',
    'Mod': '%',
    'Pow': '**',
    'LShift': '<<',
    'RShift': '>>',
    'BitOr': '|',
    'BitXor': '^',
    'BitAnd': '&',
    'And': 'and',
    'Or': 'or',
    'Not': 'not',
    'Invert': '~',
    'Eq': '==',
    'NotEq': '!=',
    'Lt': '<',
    'LtE': '<=',
    'Gt': '>',
    'GtE': '>=',
    'Is': 'is',
    'IsNot': 'is not',
    'In': 'in',
    'NotIn': 'not in',
}


def disentangle_expression_ast(expr_str: str) -> Tuple[List[str], List[str]]:
    """
    Disentangles variable names and operators from an expression string using the ast module.

    Args:
        expr_str (str): The expression string to parse.

    Returns:
        A tuple containing a list in the format of [variable_name, operator]
        Tuple[List[str], List[str]]:
        [0] variable_names
        [1] operators
    """
    variable_names = set()
    operators = set()

    # Make sure the expression is pythonic
    expr_str_pythonic = adapt_logic_syntax(expr_str, compiler='Python')
    if expr_str != expr_str_pythonic:
        # Let the print colour to be in orange
        rprint(f'INFO::disentangle_expression_ast::the expression has been adapted to Pythonic syntax: [blue]\n{expr_str}[/] \n-> \n[yellow]{expr_str_pythonic}[/]')
    # Parse the expression into an AST
    tree = ast.parse(expr_str_pythonic, mode='eval')

    class ExpressionVisitor(ast.NodeVisitor):
        def visit_Name(self, node):
            # Variable names (identifiers)
            variable_names.add(node.id)
            self.generic_visit(node)

        def visit_BinOp(self, node):
            # Binary operators (e.g., +, -, *, /)
            op_name = type(node.op).__name__
            operators.add(OPERATOR_SYMBOLS.get(op_name, op_name))
            self.generic_visit(node)

        def visit_UnaryOp(self, node):
            # Unary operators (e.g., -, +)
            op_name = type(node.op).__name__
            operators.add(OPERATOR_SYMBOLS.get(op_name, op_name))
            self.generic_visit(node)

        def visit_BoolOp(self, node):
            # Boolean operators (e.g., and, or)
            op_name = type(node.op).__name__
            operators.add(OPERATOR_SYMBOLS.get(op_name, op_name))
            self.generic_visit(node)

        def visit_Compare(self, node):
            # Comparison operators (e.g., ==, !=, >, <)
            for op in node.ops:
                op_name = type(op).__name__
                operators.add(OPERATOR_SYMBOLS.get(op_name, op_name))
            self.generic_visit(node)

        def visit_Call(self, node):
            # Treat function names as operators
            if isinstance(node.func, ast.Name):
                # Add the function name to operators
                operators.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                # Handle attribute access (e.g., np.log)
                # Can include the module name if needed
                # operators.add(f"{node.func.value.id}.{node.func.attr}")
                operators.add(node.func.attr)
            self.generic_visit(node)

    # Create an instance of the visitor and traverse the tree
    visitor = ExpressionVisitor()
    visitor.visit(tree)

    # Remove operator names from variable names
    variable_names -= operators

    return sorted(variable_names), sorted(operators)


def check_contain_operator(expr: str) -> bool:

    variable_names, operators = disentangle_expression_ast(expr)

    if bool(operators):
        print(f'INFO::check_contain_operator: The expression contains operators: {operators}')

    return bool(operators)


# def check_contain_operator(expr: str) -> bool:

#     operator_pattern = r'[+\-*/%=><!&|]|log'

#     return bool(re.search(operator_pattern, expr))


if __name__ == '__main__':

    # Do some tests
    # expr_str = "log(col1 + col2) / (col3 >= col4 & (col5 < col6)) and not exp(col7) == 'value' && col8"
    # expr_str = "1>0"
    expr_str = "( col1)"
    variables, ops = disentangle_expression_ast(expr_str)
    print("Variables:", variables)
    print("Operators:", ops)

    # Example usage:
    nested_list = [[['Polarity', 'eventNumber'], ['Lb_L0Global_Dec', 'Lb_L0Global_TIS']], ['bdt', ['isoBDTcut']], 'other_element']

    try:
        flattened = flatten_list(nested_list)
        print(flattened)
    except TypeError as e:
        print(f"Failed to flatten list: {e}")
