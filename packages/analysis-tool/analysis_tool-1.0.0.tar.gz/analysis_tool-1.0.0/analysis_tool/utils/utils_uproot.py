'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-06-19 16:25:34 +0200
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-10-16 06:17:44 +0200
FilePath     : utils_uproot.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

import re
from pathlib import Path
from typing import List, Optional, Union, Dict, Any, Tuple, Callable
import colorama

import uproot as ur
import pandas as pd
import numpy as np
import awkward as ak

import formulate


from rich import print as rprint

# Use rich backend for logging
import logging
from rich.logging import RichHandler

# Configure rich logging globally
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%x %X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)  # or "DEBUG"/"WARNING" as needed
logger = logging.getLogger(__name__)


from ..utils.utils_general import adapt_logic_syntax, check_contain_operator, disentangle_expression_ast


def list_supported_branches(input_file_path: str, input_tree_name: str, library: str = "pd"):
    """
    Determines which branches in a ROOT file can be read by uproot without throwing errors,
    indicating they don't contain unsupported data types.

    Parameters:
    input_file_path (str): Path to the ROOT file.
    decay_tree_name (str): Name of the tree in the ROOT file.

    Returns:
    list: A list of branch names that are supported.
    """

    # ========================================
    # List to store branches that can be read without errors
    # ========================================
    supported_branches = []

    # ========================================
    # Open the ROOT file using uproot
    # ========================================
    with ur.open(input_file_path) as f:
        # ========================================
        # Access the specified tree
        # ========================================
        tree = f[input_tree_name]

        # ========================================
        # Get all branch names
        # ========================================
        all_branches = tree.keys()

        # ========================================
        # Attempt to read each branch individually to filter out unsupported types
        # ========================================
        for branch in all_branches:
            try:
                # Try to read only the first few entries to test if the branch is supported
                df = tree.arrays([branch], entry_start=0, entry_stop=1, library=library)

                if library != "ak":
                    assert df[branch].dtype.name != 'awkward'

                    # Do operations on this branch if it can be read without errors
                    df[branch].astype(np.float64)

                # If no errors are thrown, add the branch to the list of supported branches
                supported_branches.append(branch)
            except Exception as e:
                # Log the branch name with markup
                logger.warning(f'skipping unsupported branch [bold yellow]{branch}[/]', extra={"markup": True})
                # Log the exception separately without markup to avoid any interpretation issues
                if str(e):
                    logger.warning(f'Reason: [plain]{str(e)}[/plain]', extra={"markup": False})
    return supported_branches


def evaluate_expression_and_assign(
    df: pd.DataFrame,
    expression: str,
    new_column: str,
    allowed_funcs: dict = None,
    return_only_new_column: bool = True,
) -> pd.Series | pd.DataFrame:
    """
    Assigns a new column to the DataFrame based on the given expression with generalized function mapping.

    Args:
        df (pd.DataFrame): The input DataFrame.
        expression (str): The expression string, e.g., "min(a, max(b, c))".
        new_column (str): The name of the new column to assign.
        allowed_funcs (dict, optional): A dictionary mapping allowed function names to their implementations.
        return_only_new_column (bool, optional): If True, return only the new column. If False, return the entire DataFrame.

    Returns:
        pd.Series or pd.DataFrame: The Series of the new column if return_only_new_column is True, else the entire DataFrame.
    """
    if allowed_funcs is None:
        allowed_funcs = {
            'min': np.minimum,
            'max': np.maximum,
            'sum': np.sum,
            'mean': np.mean,
            'median': np.median,
            'abs': np.abs,
            'sqrt': np.sqrt,
            'log': np.log,
            'exp': np.exp,
            'sin': np.sin,
            'cos': np.cos,
            'tan': np.tan,
            'arcsin': np.arcsin,
            'arccos': np.arccos,
            'arctan': np.arctan,
            'sinh': np.sinh,
            'cosh': np.cosh,
            'tanh': np.tanh,
            'arcsinh': np.arcsinh,
            'arccosh': np.arccosh,
            'arctanh': np.arctanh,
            'arctan2': np.arctan2,
            # Add more allowed functions as needed
        }

    # ========================================
    # Create a regex pattern to match all allowed functions
    # ========================================
    pattern = r'\b(' + '|'.join(map(re.escape, allowed_funcs.keys())) + r')\s*\('

    # ========================================
    # Replace allowed function names with their NumPy counterparts
    # ========================================
    def replace_func(match):
        func_name = match.group(1).lower()
        mapped_func = allowed_funcs.get(func_name)
        if not mapped_func:
            raise ValueError(f"Function '{func_name}' is not allowed.")
        return f'np.{mapped_func.__name__}('  # Ensures correct NumPy function is used

    processed_expr = re.sub(pattern, replace_func, expression, flags=re.IGNORECASE)

    # ========================================
    # Define the evaluation environment
    # ========================================
    allowed_names = {'np': np}

    # ========================================
    # Convert DataFrame columns to Series in the locals
    # ========================================
    locals_dict = allowed_names | df.to_dict(orient='series')

    # ========================================
    # Evaluate the expression
    # ========================================
    try:
        df_new = df.assign(**{new_column: eval(processed_expr, {"__builtins__": {}}, locals_dict)})
    except NameError as e:
        raise ValueError(f"Name error in expression '{expression}': {e}")
    except TypeError as e:
        raise ValueError(f"Type error in expression '{expression}': {e}")
    except Exception as e:
        raise ValueError(f"Error evaluating expression '{expression}': {e}")

    # ========================================
    # Corrected return statement
    # ========================================
    return df_new[new_column] if return_only_new_column else df_new


def evaluate_expression_and_add_column(
    df: pd.DataFrame,
    expression: str,
    new_column: str,
    return_only_new_column: bool = False,
    custom_evaluator=None,
) -> pd.Series | pd.DataFrame:
    """
    Evaluates a given expression on the DataFrame and assigns the result to a new column.

    The function first attempts to evaluate the expression using pandas.DataFrame.eval().
    If that fails, it falls back to a custom evaluation function provided by the user.

    Args:
        df (pd.DataFrame): The input DataFrame.
        expression (str): The expression string to evaluate, e.g., "min(a, max(b, c))".
        new_column (str): The name of the new column to assign the evaluated result.
        return_only_new_column (bool, optional): If True, return only the new column. If False, return the entire DataFrame.
        custom_evaluator (callable, optional): A custom function to evaluate the expression.
            It should take three arguments: the DataFrame, the expression, and the new column name.

    Returns:
        pd.Series or pd.DataFrame: The Series of the new column if return_only_new_column is True, else the entire DataFrame.

    Raises:
        ValueError: If both evaluation methods fail.
    """

    # ========================================
    # The dataframe to store the new columns
    # ========================================
    new_columns_pd = pd.DataFrame()

    # ========================================
    # Check if the new column already exists to prevent overwriting
    # ========================================
    if new_column in df.columns:
        logger.warning(f"Column [bold yellow]'{new_column}'[/] already exists in the DataFrame and will be overwritten.", extra={"markup": True})

    # ========================================
    # Attempt to evaluate the expression using DataFrame.eval()
    # ========================================
    try:
        # Evaluate the expression and assign it to the new column
        expression = formulate.from_auto(expression).to_numexpr()  # convert the expression to numexpr format, to be used in DataFrame.eval()
        # expression = adapt_logic_syntax(expression, compiler='python')
        new_columns_pd[new_column] = df.eval(expression)
    except Exception as ae:
        # Issue a warning and attempt to use the custom evaluator
        logger.warning(f"Failed to evaluate expression [bold yellow]'{expression}'[/] using DataFrame.eval(): {ae}. ", extra={"markup": True})
        logger.warning("Attempting to evaluate using custom function.", extra={"markup": True})

        # ========================================
        # Check if a custom evaluator is provided
        # ========================================
        if custom_evaluator is not None:
            try:
                # Use the custom evaluator to compute the result
                expression = adapt_logic_syntax(expression, compiler='python')
                computed_series = custom_evaluator(df, expression, new_column)

                # Assign the computed result to the new column
                new_columns_pd[new_column] = computed_series

                # Print a success message
                logger.info(f"Expression [bold green]'{expression}'[/] evaluated successfully using custom function.", extra={"markup": True})
            except Exception as e:
                # Raise a ValueError with a detailed error message if custom evaluation fails
                raise ValueError(f"{colorama.Fore.RED}Failed to evaluate '{expression}' using custom function: {e}{colorama.Style.RESET_ALL}") from e
        else:
            # Raise a ValueError if no custom evaluator is provided
            raise ValueError(f"{colorama.Fore.RED}Failed to evaluate '{expression}' using DataFrame.eval() and no custom evaluator provided.{colorama.Style.RESET_ALL}") from ae

    # return the computed DataFrame or Series based on the flag
    if return_only_new_column:
        return new_columns_pd[new_column]
    else:
        return df.assign(**new_columns_pd)


def apply_func_to_dataframe(
    df_data: pd.DataFrame,
    transform_func: Callable,
    output_branches: Optional[List[str]] = None,
    copy_data_frame: bool = True,
    **transform_kwargs,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Apply a function to a pandas DataFrame and return the modified DataFrame and the output branches.

    Args:
        df_data (pd.DataFrame): The input DataFrame to process.
        transform_func (Callable): The function to apply to the DataFrame.
        output_branches (Optional[List[str]]): The output branches to return. If None, return all branches.
        copy_data_frame (bool): Whether to copy the DataFrame before applying the function.
        **transform_kwargs: Additional keyword arguments to pass to the transform function.

    Returns:
        Tuple[pd.DataFrame, List[str]]: A tuple containing the modified DataFrame and the output branches.
    """
    # ========================================
    # Copy DataFrame if requested
    # ========================================
    if copy_data_frame:
        df_data = df_data.copy()

    # ========================================
    # Apply the transformation function
    # ========================================
    try:
        result = transform_func(df_data, **transform_kwargs)
        if result is not None:
            df_data = result
    except Exception as e:
        raise ValueError(f"Error applying function to DataFrame: {e}") from e

    # ========================================
    # Determine output branches
    # ========================================
    if output_branches:
        output_branches_set = set(output_branches)
        if missing_cols := output_branches_set - set(df_data.columns):
            raise KeyError(f"Missing output branches after processing DataFrame: {missing_cols}. Available: {list(df_data.columns)}")
    else:
        output_branches = list(df_data.columns)
        output_branches_set = set(output_branches)

    return df_data, list(output_branches_set)


# ----------------------uproot area----------------------------#
def check_root_file(input_file_name: str, tree_name: str) -> bool:
    """
    Checks if a ROOT file exists, contains a specified tree, and that the tree has non-zero entries.

    Parameters:
        input_file_name (str): The path to the input ROOT file.
        tree_name (str): The name of the tree to check in the ROOT file.

    Returns:
        bool: True if the file exists, contains the tree, and the tree has non-zero entries. False otherwise.
    """
    # ========================================
    # Step 1: Check if the file exists
    # ========================================
    if not Path(input_file_name).exists():
        logger.warning(f'File [bold yellow]{input_file_name}[/] does not exist.', extra={"markup": True})
        return False

    # ========================================
    # Step 2: Try to open the ROOT file
    # ========================================
    try:
        with ur.open(input_file_name) as f:
            # ========================================
            # Step 3: Check if the specified tree exists
            # ========================================
            if tree_name not in f:
                logger.warning(f'Tree [bold yellow]"{tree_name}"[/] not found in the file [bold yellow]"{input_file_name}"[/].', extra={"markup": True})
                return False

            # ========================================
            # Step 4: Access the tree
            # ========================================
            tree = f[tree_name]

            # ========================================
            # Step 5: Check if the tree has non-zero entries
            # ========================================
            num_entries = tree.num_entries
            if num_entries > 0:
                logger.info(f"Tree [bold green]{tree_name}[/] in file [bold green]{input_file_name}[/] has [bold green]{num_entries}[/] entries.", extra={"markup": True})
                return True
            else:
                logger.warning(f'Tree [bold yellow]"{tree_name}"[/] has zero entries in the file [bold yellow]"{input_file_name}"[/].', extra={"markup": True})
                return False

    except Exception as e:
        logger.error(f"Error opening file [bold yellow]'{input_file_name}'[/]: [bold red]'{e}'[/]", extra={"markup": True})
        if str(e):
            logger.error(f"Reason: [plain]{str(e)}[/plain]", extra={"markup": False})
        return False


def parse_input_paths(files: Union[str, List[str]]) -> List[str]:
    """
    Parse input file paths from string or list format.

    Args:
        files: File paths as semicolon-separated string or list of strings

    Returns:
        List of individual file paths

    Examples:
        >>> parse_input_paths("file1.root;file2.root")
        ['file1.root', 'file2.root']
        >>> parse_input_paths(["file1.root", "file2.root;file3.root"])
        ['file1.root', 'file2.root, 'file3.root']
    """
    # ========================================
    # Check if the input is empty
    # ========================================
    if not files:
        return []

    # ========================================
    # Handle string input
    # ========================================
    if isinstance(files, str):
        return [f.strip() for f in files.split(';') if f.strip()]

    # ========================================
    # Handle list input with potential semicolon-separated strings
    # ========================================
    result = []
    for f in files:
        if f and isinstance(f, str):
            result.extend(f.strip() for f in f.split(';') if f.strip())

    return result


def parse_tree_names(trees: Union[str, List[str]], num_files: int) -> List[str]:
    """
    Ensure input_tree_name is a list matching the number of input files.

    Args:
        trees (Union[str, List[str]]): The input tree names as a string or list.
        num_files (int): The number of input files.
    """
    # ========================================
    # Convert input to list
    # ========================================
    tree_list: list[str] = trees if isinstance(trees, list) else trees.split(";")
    tree_list = [t.strip() for t in tree_list if t.strip()]

    # ========================================
    # Check if the number of tree names matches the number of files
    # ========================================
    if len(tree_list) == 1:
        # Single tree name - repeat for all files
        return tree_list * num_files
    elif len(tree_list) == num_files:
        # Perfect match
        return tree_list
    else:
        raise ValueError(f"Number of tree names does not match the number of files or is not 1: {len(tree_list)} != {num_files} or {len(tree_list)} != 1")


def load_variables_to_pd_by_uproot(
    input_file_path: Union[str, List[str]],
    input_tree_name: Union[str, List[str]],
    variables: Optional[Union[str, List[str]]] = None,
    selection: str = "NONE",
    library: str = "pd",
    max_entries: Optional[int] = None,
    num_workers: int = 1,
    step_size: int = 50000,
    auto_evaluate_variables_as_expressions: bool = True,
) -> Union[pd.DataFrame, np.ndarray, ak.Array]:
    """
    Load variables from a tree in a ROOT file to a pandas DataFrame, NumPy array, or Awkward Array using uproot with multithreading.

    Args:
        input_file_path (Union[str, List[str]]): The input file path(s), separated by semicolons(;) or provided as a list.
        input_tree_name (Union[str, List[str]]): The name of the tree(s) corresponding to each input file.
        variables (Optional[Union[str, List[str]]], optional): Variables to load. Can be a comma-separated string or a list.
                                        If None, load all supported branches. Defaults to None.
                                        If an expression is provided, it is evaluated and disentangled to extract the variables needed.        selection (str, optional): The selection criteria to be applied. Defaults to "NONE".
        library (str, optional): The format of the output array ("pd", "np", or "ak"). Defaults to "pd".
        max_entries (Optional[int], optional): The maximum number of entries to read. If None, all entries are read.
        num_workers (int, optional): The number of worker threads to use for reading data. Defaults to 1.
        step_size (int, optional): The number of entries to read in each step. Defaults to 50000.
        auto_evaluate_variables_as_expressions (bool, optional): If True, evaluate the variables as expressions. Defaults to True.
                                                                If False, do not evaluate the variables as expressions, the variables are loaded as is.
    Returns:
        Union[pd.DataFrame, np.ndarray, ak.Array]: Data loaded from the ROOT file in the specified library format.
        - pd.DataFrame: pandas DataFrame
        - np.ndarray: NumPy array
        - ak.Array: Awkward Array
    """

    # ========================================
    # Helper Functions
    # ========================================

    def _extract_variables(vars_input: str | list[str] | None, file_path: str, tree_name: str) -> List[str]:
        """Determine which variables to load."""
        if not vars_input:
            loaded_vars = list_supported_branches(file_path, tree_name, library)
            logger.info(f"Loading all supported variables from [bold green]{file_path}[/]:[bold green]{tree_name}[/] using uproot.", extra={"markup": True})
            return loaded_vars
        else:
            vars_list = vars_input.split(",") if isinstance(vars_input, str) else vars_input
            if not isinstance(vars_list, list):
                vars_list = [vars_list]
            variables_to_load = []
            for var in vars_list:
                extracted_vars, operators = disentangle_expression_ast(var)
                if operators:
                    logger.info(f"Variable [bold yellow]'{var}'[/] contains operators. Extracted variables: [bold yellow]{extracted_vars}[/]", extra={"markup": True})
                variables_to_load.extend(extracted_vars)
            # Remove duplicates
            variables_to_load = list(set(variables_to_load))
            return variables_to_load

    def _adapt_selection(sel: str, compiler='numpy') -> Optional[str]:
        """Adapt selection syntax to the target library."""
        if not isinstance(sel, str):
            return None

        cleaned_sel = sel.strip().replace(" ", "").upper()
        if cleaned_sel in {"NONE", "1>0", "1", "(1>0)"}:
            return None

        return adapt_logic_syntax(sel.strip(), compiler=compiler)

    def _extend_variables_with_selection(vars_to_load: List[str], sel: str) -> List[str]:
        """Extract variables from selection and add to vars_to_load."""
        sel_vars, _ = disentangle_expression_ast(sel)
        if sel_vars:
            logger.info(f"Selection expression requires variables: {sel_vars}", extra={"markup": True})
            vars_to_load.extend(sel_vars)
            # Remove duplicates
            vars_to_load = list(set(vars_to_load))
        return vars_to_load

    # ========================================
    # Input Argument Processing
    # ========================================
    if max_entries is not None:
        max_entries = None if max_entries < 0 else max_entries

    # Parse input file paths and tree names
    input_files = parse_input_paths(input_file_path)
    input_trees = parse_tree_names(input_tree_name, len(input_files))

    # Initialize variables_to_load list
    variables_to_load = []

    # Extract variables based on input
    if auto_evaluate_variables_as_expressions:
        variables_to_load = _extract_variables(variables, input_files[0], input_trees[0])
    else:
        variables_to_load = variables

    # Adapt and process selection
    adapted_selection = _adapt_selection(selection)
    if adapted_selection:
        variables_to_load = _extend_variables_with_selection(variables_to_load, selection)

    # ========================================
    # Data Loading
    # ========================================
    # Prepare list of file:tree strings
    file_tree_pairs: list[str] = []
    for path, tree in zip(input_files, input_trees):
        if check_root_file(path, tree):
            file_tree_pairs.append(f"{path}:{tree}")
        else:
            raise ValueError(f"{colorama.Fore.RED}File {path} or tree {tree} does not exist.{colorama.Style.RESET_ALL}")

    # Determine if multiple files or wildcard is used
    is_multiple_files = len(input_files) > 1 or "*" in input_files[0]
    logger.info(f"Loading variables: {variables_to_load}")
    logger.info(f"from {input_file_path}:{input_tree_name} using uproot")

    # !-----------------------------------------------------------------------------------------
    # !---------------------------------- DEBUG ##################################
    # try:
    #     if is_multiple_files:
    #         # Attempt to concatenate multiple files with selection
    #         arrays = ur.concatenate(
    #             file_tree_pairs,
    #             library=library,
    #             expressions=variables_to_load,
    #             cut=adapted_selection,
    #             max_num_elements=max_entries,
    #             num_workers=num_workers,
    #         )
    #     else:
    #         # Single file processing
    #         entry_stop = None if (max_entries is None or max_entries == -1) else max_entries
    #         arrays = ur.open(file_tree_pairs[0]).arrays(
    #             library=library,
    #             expressions=variables_to_load,
    #             cut=adapted_selection,
    #             entry_start=None,
    #             entry_stop=entry_stop,
    #         )

    # ========================================
    # Adjust step size if needed
    # ========================================
    if (max_entries is not None) and (0 < max_entries <= step_size):
        step_size = max_entries
        logger.info(f"Adjusted chunk size to {step_size} based on max_entries")

    try:
        # Use iterate to read files in chunks
        logger.info(f"Reading files in chunks with {num_workers} workers")
        chunks: list[pd.DataFrame | np.ndarray | ak.Array] = []

        # Count total entries to calculate loading fraction
        total_entries = 0
        for file_tree in file_tree_pairs:
            file_path, tree_name = file_tree.split(':')
            with ur.open(file_path) as f:
                total_entries += f[tree_name].num_entries

        target_entries = min(max_entries, total_entries) if max_entries is not None else total_entries
        logger.info(f"Total entries to read: {target_entries}/{total_entries}")

        entries_read = 0
        for i, chunk in enumerate(
            ur.iterate(
                file_tree_pairs,
                expressions=variables_to_load,
                cut=adapted_selection,
                step_size=step_size,
                library=library,
                num_workers=num_workers,
                entry_stop=target_entries,  # Pass max_entries directly to uproot
            )
        ):

            chunk_size: int = len(chunk)
            entries_read += chunk_size

            # ========================================
            # Show progress periodically (every N chunks)
            # ========================================
            chunk_reporting_interval = 10  # Report every 10 chunks
            if i % chunk_reporting_interval == 0:
                progress_percent = (entries_read / target_entries * 100) if target_entries > 0 else 0
                logger.info(f"Chunk {i}: {chunk_size:,} entries, {progress_percent:.1f}% complete ({entries_read:,}/{target_entries:,})")

            # ========================================
            # Append the chunk to the list of chunks
            # ========================================
            chunks.append(chunk)

            # Check if we've reached max_entries
            if max_entries is not None and entries_read >= max_entries:
                logger.info(f"Reached max entries limit of {max_entries}, stopping reading.")
                break  # Exit the loop to avoid reading more data

        # ========================================
        # Combine chunks based on library type
        # ========================================
        if library == 'pd':
            arrays = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=variables_to_load)
        elif library == 'np':
            arrays = np.concatenate(chunks) if chunks else np.array([])
        elif library == 'ak':
            arrays = ak.concatenate(chunks) if chunks else ak.Array([])
        else:
            raise ValueError(f"{colorama.Fore.RED}Unsupported library type: {library}{colorama.Style.RESET_ALL}")

    # !---------------------------------- DEBUG ##################################
    # !-----------------------------------------------------------------------------------------

    # ! Temporary workaround for a bug in uproot when concatenating multiple files with selection ---------- below
    except AttributeError as ae:
        # Temporary workaround for uproot bug when concatenating with selection
        logger.warning(
            f"AttributeError encountered: [bold yellow]{ae}[/] (possible uproot bug). Attempting to read file(s) [bold yellow]{input_file_path}[/] with selection requirements [bold yellow]{adapted_selection}[/], and apply selection manually.",
            extra={"markup": True},
        )

        try:
            arrays = ur.concatenate(
                file_tree_pairs,
                library=library,
                expressions=variables_to_load,
                cut=None,
                max_num_elements=max_entries,
                num_workers=num_workers,
            )

            # apply the selection after concatenation
            if adapted_selection:
                if library == 'pd':
                    df = arrays
                elif library == 'np':
                    df = np.array(arrays)
                elif library == 'ak':
                    df = ak.Array(arrays)
                else:
                    raise ValueError(f"{colorama.Fore.RED}Unsupported library type: {library}{colorama.Style.RESET_ALL}")

                logger.info("[bold green]Applying selection manually on the DataFrame.[/]", extra={"markup": True})
                if library == 'pd':
                    df_filtered = df.query(adapted_selection)
                elif library == 'np':
                    # For NumPy, convert selection to a boolean mask
                    # Note: This assumes the selection can be interpreted by NumPy
                    # You may need to implement a parser or use pandas for complex selections
                    # Here, we raise an error for unsupported operations
                    raise NotImplementedError("Manual selection for NumPy arrays is not implemented.")
                elif library == 'ak':
                    # For Awkward Arrays, use Awkward's filtering
                    # This requires translating the selection string to Awkward's syntax
                    # For simplicity, this example does not implement it
                    raise NotImplementedError("Manual selection for Awkward Arrays is not implemented.")
                logger.info("[bold green]Manual selection applied successfully.[/]", extra={"markup": True})

                return df_filtered
        except Exception as e:
            raise ValueError(f"{colorama.Fore.RED}Failed to concatenate without selection and apply manual cut: {e}{colorama.Style.RESET_ALL}") from e
    # ! Temporary workaround for a bug in uproot when concatenating multiple files with selection ---------- above

    except Exception as e:
        raise ValueError(f"{colorama.Fore.RED}An unexpected error occurred during data loading, please check the input arguments: {e}{colorama.Style.RESET_ALL}") from e

    # ========================================
    # Convert arrays to the desired library format
    # ========================================
    if library == 'pd':
        df = arrays
    elif library == 'np':
        df = np.array(arrays)
    elif library == 'ak':
        df = ak.Array(arrays)
    else:
        raise ValueError(f"{colorama.Fore.RED}Unsupported library type: {library}{colorama.Style.RESET_ALL}")

    logger.info(f"Data successfully loaded into a {library.upper()} structure.")
    return df


# def load_variables_to_pd_by_uproot(
#     input_file_path: str | list[str],
#     input_tree_name: str | list[str],
#     variables: str | list[str] | None = None,
#     selection: str = "NONE",
#     library: str = "pd",  # "pd" for pandas, "np" for NumPy, "ak" for Awkward Array
#     max_entries: Optional[int] = None,
#     num_workers: int = 1,
# ) -> pd.DataFrame | np.ndarray | ak.Array:
#     """
#     Load variables from a tree in a ROOT file to a pandas DataFrame, NumPy array, or Awkward Array using uproot with multithreading.

#     Args:
#         input_file_path (str | list[str]): The input file path(s), separated by semicolons or provided as a list.
#         input_tree_name (str | list[str]): The name of the tree(s) corresponding to each input file.
#         variables (str | list[str] | None, optional): The branches to be read from the input file. If None, all supported branches are loaded.
#         selection (str, optional): The selection criteria to be applied. Defaults to "NONE".
#         library (str, optional): The format of the output array ("pd", "np", or "ak"). Defaults to "pd".
#         max_entries (int | None, optional): The maximum number of entries to read. If None, all entries are read.
#         num_workers (int, optional): The number of worker threads to use for reading data. Defaults to 1.

#     Returns:
#         pd.DataFrame | np.ndarray | ak.Array: Data loaded from the ROOT file in the specified library format.
#     """

# # ----- Check input arguments -----#
# # Check input files
# input_file_path_list = input_file_path if isinstance(input_file_path, list) else input_file_path.split(";")
# input_tree_name_list = input_tree_name if isinstance(input_tree_name, list) else input_tree_name.split(";")

# if len(input_file_path_list) != len(input_tree_name_list):
#     input_tree_name_list *= len(input_file_path_list)

# # 1) variables
# # Check whether variables contain any operators (assuming check_contain_operator is defined)
# if not variables:
#     variables_to_load = list_supported_branches(input_file_path_list[0], input_tree_name_list[0], 'pd')
#     print(f"INFO::load_variables_to_pd_by_uproot: Loading all pandas.dataframe recognisable variables from {input_file_path}:{input_tree_name} using uproot")
# else:
#     # Convert the variables to a list if it is a string
#     variables = variables.split(",") if isinstance(variables, str) else variables
#     variables = variables if isinstance(variables, list) else [variables]

#     # Disentangle the expression to get the variables
#     variables_to_load = []
#     for var in variables:
#         _variables_to_load, _operators = disentangle_expression_ast(var)

#         if bool(_operators):
#             print(
#                 f"INFO::load_variables_to_pd_by_uproot: The requested variable to be loaded is: {var:<40}, but the variable needed to be disentangled from the expression (operators) as: {_variables_to_load}"
#             )
#         variables_to_load.extend(_variables_to_load)

#     # Remove duplicates
#     variables_to_load = list(set(variables_to_load))

# # 2) selection
# if isinstance(selection, str):
#     selection = None if selection.upper() in {"NONE", "1>0", "1", '(1>0)'} else selection.strip()
#     selection = adapt_logic_syntax(selection, compiler='numpy') if selection else selection
# else:
#     selection = None

# # Disentangle the selection to get the variables and operators, append the variables to the variables_to_load
# if selection:
#     _variables_in_selection, _operators = disentangle_expression_ast(selection)

#     # Append the variables in the selection to the variables_to_load
#     print(
#         f"INFO::load_variables_to_pd_by_uproot: standardised selection expression = {selection}, variables required and disentangled from the selection expression are: {_variables_in_selection}"
#     )
#     variables_to_load.extend(_variables_in_selection)

#     # Remove duplicates
#     variables_to_load = list(set(variables_to_load))

# # If multiple files are given, use concatenate method to load them; otherwise, use uproot.open to speed up
# # multiple files: input_file_path looks like: "file1.root;file2.root;file3.root" or "file*.root"

# print(f"INFO::load_variables_to_pd_by_uproot: Loading variables {variables_to_load} from {input_file_path}:{input_tree_name} using uproot")
# if "*" in input_file_path or len(input_file_path_list) > 1:

#     try:  # Attempt concatenation with selection
#         arrays = ur.concatenate(
#             [f"{path}:{tree_name}" for path, tree_name in zip(input_file_path_list, input_tree_name_list)],
#             library=library,
#             expressions=variables_to_load,
#             cut=selection,
#             max_num_elements=max_entries,
#             num_workers=num_workers,  # Pass the number of workers
#         )

#     # ! Temporary workaround for a bug in uproot when concatenating multiple files with selection ---------- below
#     except AttributeError as ae:
#         warnings.warn(
#             f"{colorama.Fore.YELLOW}AttributeError encountered: {ae} (should be a bug in uproot, and supposed to be fixed in the next uproot version). Attempting to concatenate without selection and apply cut manually as a temporary workaround.{colorama.Style.RESET_ALL}"
#         )
#         try:  # Concatenate without selection (Bug in uproot, as a temporary workaround)
#             arrays = ur.concatenate(
#                 [f"{path}:{tree_name}" for path, tree_name in zip(input_file_path_list, input_tree_name_list)],
#                 library=library,
#                 expressions=variables_to_load,
#                 cut=None,
#                 max_num_elements=max_entries,
#                 num_workers=num_workers,  # Pass the number of workers
#             )

#             # apply the selection after concatenation
#             if selection:
#                 # Convert to pandas DataFrame if not already
#                 df = arrays if library == 'pd' else pd.DataFrame(arrays)

#                 print(f"{colorama.Fore.GREEN}Applying selection manually on the DataFrame.{colorama.Style.RESET_ALL}")
#                 df_filtered = df.query(selection)
#                 print(f"{colorama.Fore.GREEN}Manual selection applied successfully.{colorama.Style.RESET_ALL}")
#                 return df_filtered

#         except Exception as e:
#             raise ValueError(f"{colorama.Fore.RED}Failed to concatenate without selection and apply manual cut: {e}{colorama.Style.RESET_ALL}") from e

#     except Exception as e:
#         raise ValueError(f"{colorama.Fore.RED}An unexpected error occurred during concatenation with selection: {e}: {e}{colorama.Style.RESET_ALL}") from e
#     # ! Temporary workaround for a bug in uproot when concatenating multiple files with selection ---------- above
# else:
#     entry_stop = None if (max_entries is None or max_entries == -1) else max_entries

#     arrays = ur.open(f"{input_file_path_list[0]}:{input_tree_name_list[0]}").arrays(
#         library=library,
#         expressions=variables_to_load,
#         cut=selection,
#         entry_start=None,
#         entry_stop=entry_stop,
#     )

# # Convert the arrays to a pandas DataFrame
# df = arrays if library == 'pd' else pd.DataFrame(arrays)

# print("INFO::load_variables_to_pd_by_uproot: Data succesfully loaded with uproot, and converted to pandas DataFrame")
# # print(f"INFO::load_variables_to_pd_by_uproot: Loaded branches: {df.columns}")

# return df


#####################################


################# ! UNDER DEVELOPING ! #################
def get_variables_pd(
    input_file_path: str | list[str],
    input_tree_name: str | list[str],
    variables: str | list = None,
    selection: str = "NONE",
    max_entries: int = None,
    num_workers: int = 1,
    return_only_requested_vars: bool = False,  # return only the evaluated requested variables if the requested variables are expressions
    auto_evaluate_variables_as_expressions: bool = True,
) -> pd.DataFrame:
    """
    Load variables from a ROOT file using uproot and return them as a pandas DataFrame.
    If the variables include expressions not directly available in the ROOT file,
    they are evaluated using pandas' DataFrame.eval() method.

    Args:
        input_file_path (str | list[str]): The input file path(s), separated by semicolons(;) or provided as a list.
        input_tree_name (str | list[str]): The name of the tree(s) corresponding to each input file.
        variables (str or list, optional):  Variables to load. Can be a comma-separated string or a list.
                                            If None, load all supported branches. Defaults to None.
                                            If an expression is provided, it is evaluated and added as a new column to the DataFrame.
        selection (str, optional): Selection expression to filter the data. Defaults to "NONE".
        max_entries (int, optional): Maximum number of entries to load. If None, load all entries.
        num_workers (int, optional): Number of worker threads to use for loading data. Defaults to 1.
        return_only_requested_vars (bool, optional):    If True, return only the requested variables (including evaluated expressions).
                                                        If False, return all variables loaded plus any evaluated expressions.
        auto_evaluate_variables_as_expressions (bool, optional): If True, evaluate the variables as expressions. Defaults to True.
                                                                If False, do not evaluate the variables as expressions, the variables are loaded as is.

    Returns:
        pd.DataFrame: DataFrame containing the requested variables and any evaluated expressions.
    """

    # ========================================
    # Parse input paths and tree names
    # ========================================
    input_files = parse_input_paths(input_file_path)
    input_trees = parse_tree_names(input_tree_name, len(input_files))

    # ========================================
    # Check input arguments
    # ========================================
    if not variables:  # Read all supported branches if no variables are specified
        variables = list_supported_branches(input_files[0], input_tree_name, 'pd')
    elif isinstance(variables, str):
        variables = variables.split(",")
    else:
        variables = list(variables)

    if max_entries is not None:
        max_entries = None if max_entries < 0 else max_entries

    # ========================================
    # Load all the variables needed for comparison
    # ========================================
    variables_pd = load_variables_to_pd_by_uproot(
        input_file_path=input_files,
        input_tree_name=input_trees,
        variables=variables,
        selection=selection,
        library='pd',
        max_entries=max_entries,
        num_workers=num_workers,
        auto_evaluate_variables_as_expressions=auto_evaluate_variables_as_expressions,
    )

    # ========================================
    # Make a copy of the DataFrame to prevent fragmentation.
    # ========================================
    variables_pd = variables_pd.copy()

    # ========================================
    # Create an empty DataFrame to store new columns resulting from evaluating expressions.
    # ========================================
    new_columns_pd = pd.DataFrame()

    # ========================================
    # Loop over each variable expression in 'variables'.
    # ========================================
    for var_expr in variables:
        # If 'var_expr' is not already a column in 'variables_pd', attempt to evaluate it as an expression.
        try:
            if var_expr not in variables_pd.columns:

                # Evaluate the expression using DataFrame.eval() and store the result in 'new_columns_pd'.
                # new_columns_pd[var_expr] = variables_pd.eval(var_expr)
                new_columns_pd[var_expr] = evaluate_expression_and_add_column(
                    df=variables_pd, expression=var_expr, new_column=var_expr, return_only_new_column=True, custom_evaluator=evaluate_expression_and_assign
                )

        except Exception as e:
            # If evaluation fails, raise a ValueError with a detailed error message, preserving the original exception.
            raise ValueError(f"{colorama.Fore.RED}Failed to evaluate '{var_expr}': {e}{colorama.Style.RESET_ALL}") from e

    # ========================================
    # Decide which columns to return based on 'return_only_requested_vars'.
    # ========================================
    if return_only_requested_vars:
        # Identify variables that are already in 'variables_pd' but not in 'new_columns_pd'.
        existing_columns = [var_expr for var_expr in variables if var_expr in variables_pd.columns and var_expr not in new_columns_pd.columns]
        # Select these existing columns from 'variables_pd'.
        columns_from_original_pd = variables_pd[existing_columns]
        # Concatenate the evaluated expressions with the existing columns.
        # return pd.concat([new_columns_pd, columns_from_original_pd], axis=1)

        return new_columns_pd.join(columns_from_original_pd)

    else:
        # Return all loaded variables plus any new evaluated expressions.
        return variables_pd.assign(**new_columns_pd)


def get_weights_np(
    input_files: Union[str, List[str]],
    input_tree_names: Union[str, List[str]],
    weight_expr: Optional[str],
    selection: str = "NONE",
    auto_evaluate_variables_as_expressions: bool = True,
) -> np.ndarray:

    # ========================================
    # Check input arguments
    # ========================================
    input_files = parse_input_paths(input_files)
    input_tree_names = parse_tree_names(input_tree_names, len(input_files))

    weight_expr = weight_expr or 'NONE'

    if weight_expr and str(weight_expr).upper() in {'NONE', '1', 'ONE'}:
        num_entries = sum(ur.open(f"{fname}:{tree_name}").num_entries for fname, tree_name in zip(input_files, input_tree_names))

        result = np.ones(num_entries, dtype=np.float32)

    else:
        # ========================================
        # Load the weight variable
        # ========================================
        _df_weights = load_variables_to_pd_by_uproot(
            input_files,
            input_tree_names,
            weight_expr,
            selection=selection,
            library='pd',
            auto_evaluate_variables_as_expressions=auto_evaluate_variables_as_expressions,
        )

        if weight_expr in _df_weights.columns:
            result = _df_weights[weight_expr].values

        else:
            try:
                weight_expr = formulate.from_auto(weight_expr).to_numexpr()  # convert the expression to numexpr format, to be used in DataFrame.eval()
                result = _df_weights.eval(weight_expr).values

            except Exception as e:
                raise ValueError(f"{colorama.Fore.RED}failed to evaluate '{weight_expr}': {e}{colorama.Style.RESET_ALL}") from e

    return result


################# ! UNDER DEVELOPING ! #################


def dfMergeFriends(df_nominal: pd.DataFrame, df_friends: list):
    # ========================================
    # Check input arguments
    # ========================================
    df_friends = df_friends if isinstance(df_friends, list) else [df_friends]

    # ========================================
    # Start with the nominal DataFrame
    # ========================================
    result = df_nominal.copy()

    # ========================================
    # Merge the friends
    # ========================================
    for df_friend in df_friends:
        # Identify overlapping columns
        overlapping_cols = [col for col in df_friend.columns if col in df_nominal.columns]
        logger.info(f'Overlapping columns to be dropped from the df_friend:\n{overlapping_cols}')

        # Drop the overlapping columns from the second DataFrame
        df_friend = df_friend.drop(overlapping_cols, axis=1)

        # Perform the merge
        result = pd.merge(result, df_friend, how='left', left_index=True, right_index=True, suffixes=('', '_dupBranchR'))

    # Return the result within a chunk of continuous memory
    return result.copy()


def save_df_to_root(
    df: pd.DataFrame,
    output_file_path: str,
    output_tree_name: str,
    branches_to_save: Optional[List[str]] = None,
    chunk_size: int = 50000,
):
    """
    Save a pandas DataFrame to a ROOT file as a TTree using uproot.

    Args:
        df (pd.DataFrame): DataFrame to save to the ROOT file.
        output_file_path (str): Path to the output ROOT file.
        output_tree_name (str): Name of the TTree to create in the output ROOT file.
        branches_to_save (Optional[List[str]]): List of branches to save. If None, save all branches.
        chunk_size (int): Number of entries to write per chunk. Default: 50000.
    """

    # ========================================
    # Validate input arguments
    # ========================================
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")

    if df.empty:
        logger.warning("DataFrame is empty, creating empty ROOT file")
        # Create empty file with just the tree structure
        output_file_path = Path(output_file_path).resolve().as_posix()
        Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)
        with ur.recreate(output_file_path) as f:
            # ! Create empty tree with type specifications from DataFrame, required by uproot > 5.7.0
            f.mktree(output_tree_name, {})
            # f[output_tree_name] = {}
        logger.warning(f"Empty ROOT file created: '{output_file_path}' with tree '{output_tree_name}'")
        return

    # ========================================
    # Make sure the output file folder exists
    # ========================================
    output_file_path = Path(output_file_path).resolve().as_posix()
    Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)

    # ========================================
    # Select branches to save
    # ========================================
    if branches_to_save is not None:
        # Validate that all requested branches exist
        if missing_branches := [branch for branch in branches_to_save if branch not in df.columns]:
            raise KeyError(f"Requested branches not found in DataFrame: {missing_branches}. Available: {list(df.columns)}")
        df_to_save = df[branches_to_save]
        logger.info(f"Saving {len(branches_to_save)} selected branches: {branches_to_save}")
    else:
        df_to_save = df
        logger.info(f"Saving all {len(df_to_save.columns)} branches")

    # ========================================
    # Save data to ROOT file
    # ========================================
    with ur.recreate(output_file_path) as f:

        # ! Create empty tree with type specifications from DataFrame, required by uproot > 5.7.0
        branch_types = {col: df_to_save[col].dtype for col in df_to_save.columns}
        f.mktree(output_tree_name, branch_types)

        # Write data to tree
        if len(df_to_save) <= chunk_size:
            # Write all data at once
            data_to_write = df_to_save.to_dict('series')
            f[output_tree_name].extend(data_to_write)

            logger.info(f"Data saved to ROOT file '{output_file_path}' with tree '{output_tree_name}' ({len(df_to_save):,} entries)")
        else:
            # Write data in chunks
            total_entries = len(df_to_save)
            num_chunks = (total_entries + chunk_size - 1) // chunk_size  # Ceiling division

            logger.info(f"Writing {total_entries:,} entries in {num_chunks} chunks of {chunk_size:,}")

            for i, start_idx in enumerate(range(0, total_entries, chunk_size)):
                end_idx = min(start_idx + chunk_size, total_entries)
                chunk_df = df_to_save.iloc[start_idx:end_idx]

                # Convert the chunk to a dictionary of series, where the index is removed
                data_to_write = chunk_df.to_dict('series')

                # Extend tree with subsequent chunks
                f[output_tree_name].extend(data_to_write)

                # Log progress for large datasets
                if num_chunks > 10 and (i + 1) % max(1, num_chunks // 10) == 0:
                    progress = (i + 1) / num_chunks * 100
                    logger.info(f"Progress: {progress:.1f}% ({i + 1}/{num_chunks} chunks)")

            logger.info(f"Data saved to ROOT file '{output_file_path}' with tree '{output_tree_name}' ({total_entries:,} entries in {num_chunks} chunks)")


def save_dict_to_root(dict_data: dict[str, list | np.ndarray | pd.DataFrame], output_file_path: str, output_tree_name: str):
    """
    Save a dictionary to a ROOT file as a TTree using uproot.

    Args:
        dict_data (dict[str, list | np.ndarray | pd.DataFrame]): Dictionary to save to the ROOT file. The key is the branch name, and the value is the data to save.
        output_file_path (str): Path to the output ROOT file.
        output_tree_name (str): Name of the TTree to create in the output ROOT file.
    """

    # ========================================
    # Convert the dictionary to a DataFrame
    # ========================================
    df = pd.DataFrame(dict_data)

    # ========================================
    # Save the DataFrame to the ROOT file
    # ========================================
    save_df_to_root(df, output_file_path, output_tree_name)


def process_root_file_with_function(
    input_files: Union[str, List[str]],
    input_trees: Union[str, List[str]],
    output_file: str,
    output_tree: str,
    transform_func: Callable,
    input_branches: Optional[List[str]] = None,
    output_branches: Optional[List[str]] = None,
    aliases: Optional[Dict[str, str]] = None,
    selection: Optional[str] = None,
    library: str = "pd",
    max_entries: int = 0,
    chunk_size: int = 50000,
    copy_data_frame: bool = False,
    **transform_kwargs: Dict[str, Any],
) -> None:
    """
    Process ROOT files by applying a transformation function to each chunk and writing to a new file.

    Reads ROOT files in chunks, applies a user-defined transformation function to each chunk,
    and writes the processed data to a new ROOT file. Ideal for large-scale data processing
    where you need to transform data while maintaining memory efficiency.

    Args:
        input_files: Input ROOT file path(s). Single file or list of files.
        input_trees: Input tree name(s). Must match the number of input files.
        output_file: Output ROOT file path.
        output_tree: Output tree name.
        transform_func: Function to apply to each data chunk. Must accept DataFrame
                        as first argument and modify in-place or return new DataFrame.
        input_branches: Specific branches to read. If None, reads all supported branches.
        output_branches: Specific branches to write. If None, writes all processed branches.
        aliases: Branch aliases for input data (e.g., {'new_name': 'old_name'}).
        selection: Selection criteria to filter input data (e.g., 'pt > 10').
        library: Output library format ('pd', 'np', 'ak'). Default: 'pd'.
        max_entries: Maximum entries to read (0 = all entries). Default: 0.
        chunk_size: Number of entries to process per chunk. Default: 50000.
        copy_data_frame: Whether to copy each chunk before transformation. Default: False.
        **transform_kwargs: Additional arguments passed to transform_func.

    Raises:
        ValueError: If input arguments are invalid.
        FileNotFoundError: If input files don't exist.
        KeyError: If required output branches are missing after processing.

    Example:
        >>> def add_mass_column(df):
        ...     df['mass'] = np.sqrt(df['E']**2 - df['px']**2 - df['py']**2 - df['pz']**2)
        ...
        >>> process_root_file_with_function(
        ...     input_files='input.root',
        ...     input_trees='events',
        ...     output_file='output.root',
        ...     output_tree='processed_events',
        ...     transform_func=add_mass_column,
        ...     selection='pt > 10'
        ... )
    """

    # ========================================
    # Check input arguments
    # ========================================
    if not callable(transform_func):
        raise ValueError(f"transform_func must be callable, but got {type(transform_func)}")

    # ========================================
    # Initialize defaults and validate inputs
    # ========================================
    aliases = aliases or {}
    parsed_input_files = parse_input_paths(input_files)
    parsed_input_trees = parse_tree_names(input_trees, len(parsed_input_files))

    # ========================================
    # Validate input files exist and contain the specified trees
    # ========================================
    for file_path, tree_name in zip(parsed_input_files, parsed_input_trees):
        if not check_root_file(file_path, tree_name):
            raise FileNotFoundError(f"Invalid file or tree: {file_path}:{tree_name}")

    # ========================================
    # Prepare file:tree pairs for uproot.iterate
    # ========================================
    file_tree_pairs = [f"{file_path}:{tree_name}" for file_path, tree_name in zip(parsed_input_files, parsed_input_trees)]

    # ========================================
    # Validate selection syntax if provided
    # ========================================
    if selection:
        try:
            selection = selection.strip()
            if selection.upper() in {"NONE", "1>0", "1", "(1>0)"}:
                selection = None
            else:
                # Use existing function to adapt logic syntax
                selection = adapt_logic_syntax(selection, compiler='numpy')
        except Exception as e:
            raise ValueError(f"Invalid selection expression '{selection}': {e}") from e

    # ========================================
    # Prepare output file
    # ========================================
    output_path = Path(output_file).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ========================================
    # Adjust chunk size if needed
    # ========================================
    if 0 < max_entries <= chunk_size:
        chunk_size = max_entries
        logger.info(f"Adjusted chunk size to {chunk_size} based on max_entries")

    # ========================================
    # Log operation details
    # ========================================
    logger.info("Starting ROOT file processing:")
    logger.info(f"  Input: {len(parsed_input_files)} file(s) ({parsed_input_files}) -> {output_file}")
    logger.info(f"  Branches: {input_branches or 'all supported'}")
    logger.info(f"  Selection: {selection or 'none'}")
    logger.info(f"  Chunk size: {chunk_size:,}")
    logger.info(f"  Max entries: {max_entries if max_entries > 0 else 'all'}")

    # ========================================
    # Process data chunks
    # ========================================
    try:
        with ur.recreate(output_file) as root_file:
            events_processed = 0
            events_written = 0
            chunk_count = 0

            for chunk_data in ur.iterate(file_tree_pairs, expressions=input_branches, aliases=aliases, cut=selection, library=library, step_size=chunk_size, num_workers=1, num_fallback_workers=1):
                chunk_count += 1

                # ========================================
                # Process chunk
                # ========================================
                processed_chunk, final_output_branches = apply_func_to_dataframe(
                    chunk_data,
                    transform_func,
                    output_branches,
                    copy_data_frame,
                    **transform_kwargs,
                )

                # ========================================
                # Write to ROOT file
                # ========================================
                data_to_write = processed_chunk[final_output_branches].to_dict('series')

                # ! Create empty tree with type specifications from DataFrame, required by uproot > 5.7.0
                if chunk_count == 1:
                    branch_types = {col: processed_chunk[col].dtype for col in final_output_branches}
                    root_file.mktree(output_tree, branch_types)

                # Store data to tree
                root_file[output_tree].extend(data_to_write)

                # ========================================
                # Update progress, if there are selection requirements, the written events could be less than the processed events
                # ========================================
                events_written += len(processed_chunk)
                events_processed += chunk_size

                if events_processed % (chunk_size * 10) == 0:  # Report every 10 chunks
                    logger.info(f"Processed {events_processed:,} events ({chunk_count} chunks), written {events_written:,} events")

                # ========================================
                # Check entry limit
                # ========================================
                if max_entries > 0 and events_processed >= max_entries:
                    logger.info(f"Reached entry limit of {max_entries:,}, stopping")
                    break

    except Exception as e:
        # ========================================
        # Clean up partial output file on error
        # ========================================
        if output_path.exists():
            output_path.unlink()
        raise RuntimeError(f"Error during ROOT file processing: {e}") from e

    logger.info("ROOT file processing completed successfully:")
    logger.info(f"  Events processed: {events_processed:,}")
    logger.info(f"  Chunks processed: {chunk_count:}")
    logger.info(f"  Events written: {events_written:,}")
    logger.info(f"  Output file: {output_path}")
    logger.info(f"  Output branches: {len(final_output_branches)}")
