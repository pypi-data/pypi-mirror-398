'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2024-12-06 13:57:58 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-05-18 10:21:57 +0200
FilePath     : utils.py
Description  :

Copyright (c) 2024 by everyone, All Rights Reserved.
'''

from math import floor, log, fabs, log10
from texttable import Texttable
import latextable  # https://github.com/JAEarly/latextable
import warnings
from rich import print as rprint


###############################################################################
# Helper functions for decimal-place logic, rounding vs. truncation, and LaTeX
###############################################################################


def countZeroAfterDot(num_str: str) -> int:
    """
    Counts the number of consecutive zeros immediately after the decimal point
    and before the first non-zero digit.

    Args:
        num_str (str): A string representing a floating-point number.

    Returns:
        int: The number of consecutive zeros after the decimal point and
             before the first non-zero digit.

    Example:
        "0.000123" -> returns 3
        "1.002" -> returns 0
    """
    zero_after_dot = 0
    if "." in num_str:
        part_after_dot = num_str.split(".")[1]
        for ch in part_after_dot:
            if ch == "0":
                zero_after_dot += 1
            else:
                break
    return zero_after_dot


def getSigDig(error: float, significant_figures: bool = False, sig_f_to_keep: int = 1) -> int:
    """
    Determine how many decimal places (or negative exponent) to keep,
    given an error value. This function is key to controlling the
    rounding in 'printValue'.

    If `significant_figures` is True, we interpret that we want
    `sig_f_to_keep` significant figures in the error. (Often 1 or 2
    is typical in physics.)

    Otherwise, we default to -2 (which your code interprets as 2 decimal places).

    Returns an integer that is used to build the final 'sig_d'
    in 'printValue', e.g.:
        sig_d = getSigDig(error, significant_figures) - (digit - 2)

    Args:
        error (float): The error value (must be > 0).
        significant_figures (bool, optional): If True, we compute an exponent
            that ensures the error is ~ 1 or 2 sig figs. Defaults to False.
        sig_f_to_keep (int, optional): The number of sig figs for the error, typical 1 or 2.
            Only used if significant_figures=True.

    Returns:
        int: A negative exponent or similar integer that your 'printValue' logic
             uses to control decimal places.

    Raises:
        ValueError: If error <= 0, we fallback or do a safe approach.
    """
    if error <= 0:
        # Fallback, e.g. default to -2
        return -2

    if not significant_figures:
        # If not using sig figs, just do the old default
        return -2

    # We want to base the exponent on log10 of the error
    abs_err = abs(error)
    exponent = floor(log10(abs_err))  # e.g. if error=0.012 => exponent=-2
    # If we want 'sig_f_to_keep' sig figs, typically we want the error
    # to look like X * 10^(exponent), where X has 'sig_f_to_keep' digits.
    #
    # The typical approach: if exponent=-2 and sig_f_to_keep=1, that's ~ 1.2e-2 => 0.01
    # We'll define:
    #   result = exponent - (sig_f_to_keep - 1)
    # This is returned to be combined with your next logic step.

    result = exponent - (sig_f_to_keep - 1)
    return int(result)


def checkForZero(num_str: str, digit: int, exponent: int = 0) -> str:
    """
    Adjust trailing or needed zeros in a numeric string to meet 'digit' specification,
    factoring in an exponent.

    This function is used by getNumStr to fine-tune the number of decimals or trailing zeros.

    Args:
        num_str (str): The numeric string (e.g. '0.0012345678').
        digit (int): The measure of how many decimals or significant digits to keep
                     (in your code's logic).
        exponent (int): The exponent for scientific notation shift.

    Returns:
        str: The adjusted numeric string with trailing zeros or cuts as needed.
    """
    sign_after_dot = 0
    before_dot = True

    # count how many digits occur after the decimal
    for ch in num_str:
        if ch == ".":
            before_dot = False
            continue
        if not before_dot:
            sign_after_dot += 1

    # If digit < 0 means we want extra decimals
    # We can add trailing zeros if needed
    while digit < -sign_after_dot:
        num_str += "0"
        sign_after_dot += 1

    # Possibly remove extra digits
    # If digit > -1 and exponent != 0 => remove digits from the end?
    if digit > -1 and exponent != 0:
        # Keep digit places for exponent notation?
        cut_pos = int(-sign_after_dot - 1 - digit)
        if cut_pos < len(num_str):
            num_str = num_str[:cut_pos]
    elif digit > -1 and exponent == 0:
        # If exponent = 0, might remove everything after certain place
        cut_pos = int(-sign_after_dot - 1)
        if cut_pos < len(num_str):
            num_str = num_str[:cut_pos]
    elif digit > -sign_after_dot:
        # Another logic branch to remove digits from the end
        cut_pos = int(-sign_after_dot - digit)
        if cut_pos < len(num_str):
            num_str = num_str[:cut_pos]
    return num_str


def doStandardRounding(value: float, decimals: int) -> float:
    """
    Standard rounding of 'value' to 'decimals' decimal places.
    Example: doStandardRounding(0.239, 2) -> 0.24
    """
    power = 10**decimals
    return round(value * power) / power


def doTruncation(value: float, decimals: int) -> float:
    """
    Truncate 'value' to 'decimals' decimal places.
    Example: doTruncation(0.239, 2) -> 0.23
    """
    power = 10**decimals
    truncated = int(value * power) / power
    rprint(f"Truncation: {value} -> {truncated}")
    rprint(f"Truncation: power={power}, value*power={value*power}, int={int(value*power)}, final={truncated}")
    return truncated


# def getNumStr(val: float, sig_dig: int, exponent: int, roundMethod: str = "round") -> str:
#     """
#     Formats 'val' into a string with 'sig_dig' controlling decimal places,
#     factoring in an exponent shift.

#     Now we also have 'roundMethod' to decide how we do the final decimal math:
#       - "round" => standard Python rounding
#       - "truncate" => direct truncation approach

#     Args:
#         val (float): The numeric value to format.
#         sig_dig (int): The measure of digits or decimal places.
#         exponent (int): The exponent for scientific notation shift.
#         roundMethod (str): "round" or "truncate".

#     Returns:
#         str: The adjusted numeric string.
#     """

#     # We'll scale 'val' by 10^-exponent
#     scaled = val / (10**exponent)

#     # 1) Either round or truncate to 10 decimal places as an intermediate step
#     # 2) Then convert to string
#     if roundMethod == "round":
#         scaled_intermediate = round(scaled, 10)
#     elif roundMethod == "truncate":
#         # E.g. to keep 10 decimals, we might do:
#         power_10 = 10**10
#         scaled_intermediate = int(scaled * power_10) / power_10
#     else:
#         warnings.warn(f"roundMethod must be 'round' or 'truncate', not '{roundMethod}'")
#         exit(1)
#         # raise ValueError(f"roundMethod must be 'round' or 'truncate', not '{roundMethod}'")

#     # We'll format 'scaled' with up to 10 decimal places
#     num_str = f"{scaled_intermediate:.10f}"
#     # Then pass to checkForZero to finalize trailing zeros or cut positions
#     return checkForZero(num_str, sig_dig, exponent)


def getNumStr(val: float, sig_dig: int, exponent: int, roundMethod: str = "round") -> str:
    """
    Formats 'val' into a string with 'sig_dig' controlling decimal places,
    factoring in an exponent shift.

    Now we also have 'roundMethod' to decide how we do the final decimal math:
      - "round" => standard Python rounding
      - "truncate" => direct truncation approach

    Args:
        val (float): The numeric value to format.
        sig_dig (int): The measure of digits or decimal places.
        exponent (int): The exponent for scientific notation shift.
        roundMethod (str): "round" or "truncate".

    Returns:
        str: The adjusted numeric string.
    """

    if roundMethod.lower() == "round":
        # rprint(f'CHECK~~~~~ val = {val}, sig_dig = {sig_dig}, exponent = {exponent}')
        val = doStandardRounding(val, abs(sig_dig) - abs(exponent))

        # val = doStandardRounding(val, abs(sig_dig))

        # rprint(f'val = {val}, sig_dig = {sig_dig}, exponent = {exponent}')
    elif roundMethod.lower() == "truncate":
        pass  # the default behavior
        # val = doTruncation(val, sig_dig)
    else:
        warnings.warn(f"roundMethod must be 'round' or 'truncate', not '{roundMethod}'")
        exit(1)

    # Round the value scaled by exponent
    scaled = round(
        (val / (10**exponent)),
        10,  # store intermediate up to 10 decimals
    )
    # Then we re-scale by exponent in the final string logic
    # your code does something like (val / 10^sig) * 10^sig / 10^exponent,
    # but let's keep it consistent:

    # We'll format 'scaled' with up to 10 decimal places
    num_str = f"{scaled:.10f}"
    # Then pass to checkForZero, which accounts for 'sig_dig - exponent'
    return checkForZero(num_str, sig_dig, exponent)


# print the value with error
def printValue(
    val: float,
    error: float = 0,
    useExpo: bool = False,
    significantFigures: bool = False,
    digit: int = 2,
    reference: bool = False,
    addPhantom: bool = False,
    sig_f_to_keep: int = 1,
    roundMethod: str = "round",
) -> str:
    """
    Print value ± error, optionally using scientific notation, significant figures, etc.

    If error=0, we interpret that as no error (or unknown error),
    so we won't print ± error (unless reference=False, but that wouldn't matter
    because error=0 => no error).

    If reference=True, we omit error from the output entirely.

    Negative near-zero fix: If 'val' was negative, we store was_negative,
    and if the final round => '0.0000', we still print '-0.0000'.

    significantFigures fix: We use getSigDig with a better approach for sig figs.
    If significantFigures=True, pass sig_f_to_keep to getSigDig to keep 1 or 2 sig figs in the error.

    The 'digit' param in your code further modifies the final rounding logic:
      final 'sig_d' => getSigDig(error, significantFigures, sig_f_to_keep) - (digit - 2).

    Args:
        val (float): The central value.
        error (float): The error, defaults to 0.
        useExpo (bool): Whether to use scientific notation for large or small numbers. Defaults to False.
        significantFigures (bool): If True, interpret 'digit' in a sig fig sense. Defaults to False.
        digit (int): Extra digit logic from your original code. Defaults to 2.
        reference (bool): If True, do not print the error portion. Defaults to False.
        addPhantom (bool): If True, add a phantom minus for alignment if val >=0. Defaults to False.
        sig_f_to_keep (int): If using significantFigures, how many sig figs for error. Typically 1 or 2.
        roundMethod (str): "round" or "truncate".

    Returns:
        str: A LaTeX-like string with value ± error or just the value, possibly with x10^ exponent.
    """
    sign_str = ""
    exponent = 0
    no_error = False
    was_negative = val < 0

    try:
        # If no error, fallback to 'val' for deciding decimal digit, but don't print ± error
        if error == 0:
            no_error = True
            error = abs(val) if val != 0 else 1.0  # fallback

        # Manage sign
        if was_negative:
            val = -val
        else:
            # If we want a phantom minus sign for alignment
            if addPhantom:
                sign_str = r"\phantom{-}"

        # Decide exponent if useExpo is True or if data is large/small enough
        max_val = max(val, error)
        if max_val >= 1000 or max_val < 0.01:
            exponent = floor(log10(max_val))
        if not useExpo:
            exponent = 0

        # Decide how many digits to keep
        # getSigDig => raw
        raw_sig_d = getSigDig(error, significantFigures, sig_f_to_keep=sig_f_to_keep)
        # Then combine with (digit - 2)
        sig_d = raw_sig_d - (digit - 2)

        # Convert to strings
        val_str = getNumStr(val, sig_d, exponent, roundMethod=roundMethod)
        error_str = getNumStr(error, sig_d, exponent, roundMethod=roundMethod)

        # If the final val_str is effectively 0.0, check negativity
        if float(val_str) == 0.0:
            # If original was negative, keep the minus sign
            if was_negative:
                sign_str = "-"
            else:
                sign_str = ""

        else:
            # If val_str is not 0, apply the minus sign if originally negative
            if was_negative:
                sign_str = "-"

        if no_error or reference:
            # Omit error
            if exponent != 0:
                return f"{sign_str}{val_str}\\times 10^{{{int(exponent)}}}"
            else:
                return f"{sign_str}{val_str}"

        # Otherwise, print ± error
        if exponent != 0:
            return f"({sign_str}{val_str}\\pm{error_str})\\times 10^{{{int(exponent)}}}"
        else:
            return f"{sign_str}{val_str}\\pm{error_str}"

    except Exception:
        # fallback if something goes wrong
        return "-" if no_error else "-\\pm-"


# def GetTruncNumbers(val, error, digit=4):
#     string = printValue(val, error, digit=digit)
#     value = float(string.split("\\pm")[0])
#     error = float(string.split("\\pm")[1])
#     return [value, error]


def GetTruncNumbers(val: float, error: float, digit: int = 4, roundMethod: str = "truncate") -> list:
    """
    Returns truncated or formatted numeric values after calling printValue,
    re-parsing the result. This can be error-prone if scientific notation or
    unusual formatting is used. It's just a helper function.

    Args:
        val (float): The central value.
        error (float): The error.
        digit (int, optional): The digit measure. Defaults to 4.
        roundMethod (str): "round" or "truncate"

    Returns:
        list: [value, error] as floats, extracted from the LaTeX-like output.

    Example:
        string = "1.234\\pm0.002"
        => [1.234, 0.002]
    """
    result_str = printValue(val, error, digit=digit, roundMethod=roundMethod)
    if "\\pm" in result_str:
        left, right = result_str.split("\\pm")
        try:
            # remove parentheses or x10^ notation
            left_clean = left.replace("(", "").replace(")", "")
            right_clean = right.replace("(", "").replace(")", "")
            # convert x 10^ if present
            left_clean = left_clean.replace("\\times 10^{", "e").replace("}", "")
            right_clean = right_clean.replace("\\times 10^{", "e").replace("}", "")
            new_val = float(left_clean)
            new_err = float(right_clean)
            return [new_val, new_err]
        except ValueError:
            return [None, None]
    else:
        # no ± => likely no error
        try:
            single_clean = result_str.replace("\\times 10^{", "e").replace("}", "")
            new_val = float(single_clean)
            return [new_val, 0.0]
        except ValueError:
            return [None, None]


def printYield(value: float) -> str:
    """
    Print yield with a suffix (k, M, etc.) based on exponent intervals of 3.

    If value=0, returns '0'. Otherwise:
      - exponent = floor(log10(abs(value))).
      - cat = floor(exponent / 3).
      - If cat=1 => 'k', cat=2 => 'M', etc.

    Args:
        value (float): The yield.

    Returns:
        str: A string with an optional suffix like k or M.
    """
    if value == 0:
        return "0"
    exponent = floor(log10(abs(value)))
    cat = exponent // 3
    prec = exponent % 3
    cat_name = ""
    if cat == 1:
        cat_name = "\\,\\text{k}"
    elif cat == 2:
        cat_name = "\\,\\text{M}"
    # You can extend if cat == 3 => "G", etc.

    # Round to (2-prec) digits
    yield_tr = round(value / (10 ** (cat * 3)), int(2 - prec))

    # Now we might want to pass yield_tr to checkForZero or just str it
    yield_str = str(yield_tr)

    # Heuristic to remove trailing zeros or handle decimal logic
    # e.g., if >= 100 => no decimal, if >=10 => 1 decimal, else 2 decimals
    if yield_tr >= 100:
        # integer
        yield_str = checkForZero(yield_str, 0)
    elif yield_tr >= 10:
        yield_str = checkForZero(yield_str, -1)
    else:
        yield_str = checkForZero(yield_str, -2)

    return yield_str + cat_name


###############################################################################
# Extra functions for table usage, etc.
###############################################################################


def construct_latexTable(latexTableList: list, caption: str = "caption", label: str = "label", cols_dtype: list = None, cols_align: list = None) -> str:
    """construct latex table

    Args:
        latexTableList (list): contents prepared for latex table
        caption (str, optional): caption. Defaults to 'caption'.
        label (str, optional): label. Defaults to 'label'.
        cols_dtype (list, optional): datatype for columns ('a','t','f','e','i'). Defaults to None(auto for each column).
        cols_align (list, optional): aline option for columns. Defaults to None.

    Returns:
        latextable: the latextable constructed, to be write to file
    """

    # construct latex table

    table = Texttable(max_width=200)

    if cols_dtype:  # 'a' --> automatic as default
        table.set_cols_dtype(cols_dtype)

    if cols_align:
        table.set_cols_align(cols_align)
    else:
        table.set_cols_align(["l"] + ["c"] * (len(latexTableList[0]) - 1))

    table.set_deco(Texttable.HEADER | Texttable.VLINES | Texttable.BORDER | Texttable.HLINES)
    table.add_rows(latexTableList)
    rprint("-- Texttable preview --")
    rprint(f"Caption: {caption}")
    rprint(f"Label: {label}")
    rprint(table.draw())
    return latextable.draw_latex(table, caption=caption, caption_above=True, label=label, position="!htb")


def formatWrapper(value: float, absOpt: bool = False, precision: int = 3) -> str:
    """format the value to be printed in latex table

    Args:
        value (_type_): _description_
        absOpt (bool, optional): _description_. Defaults to False.
        precision (int, optional): _description_. Defaults to 3.

    Returns:
        str: The formatted string
    """
    value = fabs(value) if absOpt else value

    # & \multirow{2}{*}{$0.003$}
    if precision == 3:
        if f"{value:.3f}".strip("-") == "0.000":
            return "& \\multirow{2}{*}{---}"
        else:
            return f"& \\multirow{{2}}{{*}}{{${value:.3f}$}}"
    elif precision == 4:
        if f"{value:.4f}".strip("-") == "0.0000":
            return "& \\multirow{2}{*}{---}"
        else:
            return f"& \\multirow{{2}}{{*}}{{${value:.4f}$}}"
    elif precision == 5:
        if f"{value:.5f}".strip("-") == "0.00000":
            return "& \\multirow{2}{*}{---}"
        else:
            return f"& \\multirow{{2}}{{*}}{{${value:.5f}$}}"


if __name__ == "__main__":

    # Test printValue
    rprint('\nTest printValue:')
    rprint(printValue(10000.23456789, 0.12345))
    rprint(printValue(10000.23456789, 0, useExpo=False, digit=4, reference=False))
    rprint(printValue(10000.23456789, 0.12345, useExpo=False, digit=4, reference=False))
    rprint(printValue(199999999.23456789, 0.12345, useExpo=True, digit=4, reference=False, roundMethod="round"))
    rprint(printValue(199999999.23456789, 0.12345, useExpo=True, digit=4, reference=False, roundMethod="truncate"))

    rprint(printValue(199999999.99999, 0.19999, useExpo=False, digit=4, reference=False, roundMethod="round"))
    rprint(printValue(199999999.99999, 0.19999, useExpo=False, digit=4, reference=False, roundMethod="truncate"))
    rprint('----------')

    rprint(printValue(0.0000023456789, 0.82345, useExpo=False, digit=5, reference=False, significantFigures=False))
    rprint(printValue(0.0000023456789, 0.82345, useExpo=True, digit=5, reference=False, significantFigures=False))

    rprint('----------')
    rprint(printValue(8000.00023456789, 12.82345, useExpo=False, digit=3, reference=False, significantFigures=True))
    rprint(printValue(8000.00023456789, 12.82345, useExpo=True, digit=3, reference=False, significantFigures=True))

    rprint(printValue(-0.00006789, -0.12345, useExpo=False, digit=4, reference=True))
    rprint(printValue(0.23456789, 0.12345, useExpo=False, digit=4, reference=True, addPhantom=True))
    rprint(printValue(0.23995, 0.12355, useExpo=False, digit=4, roundMethod="truncate"))
    rprint(printValue(0.23995, 0.12355, useExpo=False, digit=4, roundMethod="round"))

    exit(1)

    # Test GetTruncNumbers
    rprint('\nTest GetTruncNumbers:')
    rprint(GetTruncNumbers(10000.23456789, 0.12345))

    # Test printYield
    rprint('\nTest printYield:')
    rprint(printYield(100000.1234))

    # Test construct_latexTable
    rprint('\nTest construct_latexTable:')
    data = [
        ["A", "B", "C"],
        [1, 2, 3],
        [4, 5, 6],
    ]
    rprint(construct_latexTable(data))

    # Test formatWrapper
    rprint('\nTest formatWrapper:')
    rprint(formatWrapper(0.003, absOpt=False, precision=3))
    rprint(formatWrapper(-0.003, absOpt=True, precision=4))
    rprint(formatWrapper(0.0000001, absOpt=False, precision=5))
