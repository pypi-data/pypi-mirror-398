'''
Author       : Jie Wu j.wu@cern.ch
Date         : 2025-01-07 02:50:36 +0100
LastEditors  : Jie Wu j.wu@cern.ch
LastEditTime : 2025-01-07 03:20:01 +0100
FilePath     : test.py
Description  : 

Copyright (c) 2025 by everyone, All Rights Reserved. 
'''

from math import floor, log10
from texttable import Texttable
import latextable
from rich import print as rprint


def countZeroAfterDot(num_str: str) -> int:
    """
    Counts how many consecutive zeros after the decimal point before the first non-zero digit.
    Example:
      "0.000123" -> returns 3
      "1.002"    -> returns 0
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
    Returns a negative exponent for your old logic if not using sig figs,
    or a derived exponent if using sig figs.
    Typically returns -2 if no significant_figures.
    """
    if error <= 0:
        return -2  # fallback if no real error
    if not significant_figures:
        return -2  # old default => 2 decimals

    abs_err = abs(error)
    exponent = floor(log10(abs_err))  # e.g. error=0.012 => exponent=-2
    # If we want 'sig_f_to_keep'=2 => exponent-(2-1)=> exponent-1
    result = exponent - (sig_f_to_keep - 1)
    return int(result)


def checkForZero(num_str: str, digit: int, exponent: int = 0) -> str:
    """
    Your older snippet that can add trailing zeros or cut digits. Interprets
    'digit' as negative => keep that many decimals, etc. If you pass '-2' => 2 decimals, etc.
    """
    sign_after_dot = 0
    before_dot = True

    for ch in num_str:
        if ch == ".":
            before_dot = False
            continue
        if not before_dot:
            sign_after_dot += 1

    # Possibly add trailing zeros if digit < 0
    while digit < -sign_after_dot:
        num_str += "0"
        sign_after_dot += 1

    # Possibly remove extra digits
    # (some branches might not trigger if 'digit' is negative)
    if digit > -1 and exponent != 0:
        cut_pos = int(-sign_after_dot - 1 - digit)
        if 0 <= cut_pos < len(num_str):
            num_str = num_str[:cut_pos]
    elif digit > -1 and exponent == 0:
        cut_pos = int(-sign_after_dot - 1)
        if 0 <= cut_pos < len(num_str):
            num_str = num_str[:cut_pos]
    elif digit > -sign_after_dot:
        cut_pos = int(-sign_after_dot - digit)
        if 0 <= cut_pos < len(num_str):
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
    return truncated


def printValue(
    val: float,
    error: float = 0,
    useExpo: bool = False,
    significantFigures: bool = False,
    digit: int = 2,
    reference: bool = False,
    addPhantom: bool = False,
    sig_f_to_keep: int = 1,
    roundMethod: str = "round",  # default to "round"
) -> str:
    """
    Print value ± error. The parameter 'digit' is interpreted
    as the number of decimals to keep.

    If roundMethod=="round": we do standard rounding to 'digit' decimals.
    If roundMethod=="truncate": we do direct truncation to 'digit' decimals.

    Example usage:
      1) printValue(0.239, 0.12545, digit=2)
         => 0.24±0.13   (by default rounding)
      2) printValue(0.239, 0.12545, digit=2, roundMethod="truncate")
         => 0.23±0.12   (truncate approach)

    The rest of your original logic is retained for exponent shifting
    (useExpo=True => might do x10^... for large or small numbers).
    """
    was_negative = val < 0
    sign_str = ""
    exponent = 0
    no_error = error == 0

    if no_error:
        # fallback
        error = abs(val) if val != 0 else 1e-6

    if was_negative:
        val = -val
    else:
        if addPhantom:
            sign_str = r"\phantom{-}"

    # possibly decide exponent
    max_val = max(val, error)
    if useExpo and (max_val >= 1000 or max_val < 0.01):
        exponent = floor(log10(max_val))

    # scale
    scaled_val = val / (10**exponent)
    scaled_err = error / (10**exponent)

    if roundMethod == "round":
        # interpret 'digit' as how many decimals to standard-round
        new_val = doStandardRounding(scaled_val, digit)
        new_err = doStandardRounding(scaled_err, digit)

        # val_str = f"{new_val:.10f}"
        # err_str = f"{new_err:.10f}"

        val_str = str(new_val)
        err_str = str(new_err)

        # pass negative 'digit' to 'checkForZero' => keep 'digit' decimals
        # e.g. if digit=2 => pass '-2'
        val_str = checkForZero(val_str, -digit, exponent=0)
        err_str = checkForZero(err_str, -digit, exponent=0)

    elif roundMethod == "truncate":
        # interpret 'digit' as how many decimals to truncate
        new_val = doTruncation(scaled_val, digit)
        new_err = doTruncation(scaled_err, digit)

        # val_str = f"{new_val:.10f}"
        # err_str = f"{new_err:.10f}"

        val_str = str(new_val)
        err_str = str(new_err)

        # again pass '-digit' => keep exactly 'digit' decimals
        val_str = checkForZero(val_str, -digit, exponent=0)
        err_str = checkForZero(err_str, -digit, exponent=0)

    else:
        raise ValueError("roundMethod must be 'round' or 'truncate'")

    # If final val_str is effectively 0 => keep minus if originally negative
    if float(val_str) == 0.0:
        if was_negative:
            sign_str = "-"
    else:
        if was_negative:
            sign_str = "-"

    # if we skip error
    if reference or (error == 0):
        if exponent != 0:
            return f"{sign_str}{val_str}\\times 10^{{{int(exponent)}}}"
        return f"{sign_str}{val_str}"

    # otherwise
    if exponent != 0:
        return f"({sign_str}{val_str}\\pm{err_str})\\times 10^{{{int(exponent)}}}"
    else:
        return f"{sign_str}{val_str}\\pm{err_str}"


def GetTruncNumbers(val: float, error: float, digit: int = 2, roundMethod: str = "round"):
    """
    Re-parse the output of printValue -> [val, error].
    If roundMethod="round", we do standard rounding.
    If roundMethod="truncate", we do truncation.
    """
    result_str = printValue(val, error, digit=digit, roundMethod=roundMethod)
    if "\\pm" in result_str:
        left, right = result_str.split("\\pm")
        try:
            left_clean = left.replace("(", "").replace(")", "")
            right_clean = right.replace("(", "").replace(")", "")
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


###############################################################################
# Additional snippet for yields, latex table, etc. (unchanged from before)
###############################################################################


def printYield(value: float) -> str:
    if value == 0:
        return "0"
    from math import floor, log10, round

    exponent = floor(log10(abs(value)))
    cat = exponent // 3
    prec = exponent % 3
    cat_name = ""
    if cat == 1:
        cat_name = "\\,\\text{k}"
    elif cat == 2:
        cat_name = "\\,\\text{M}"

    yield_tr = round(value / (10 ** (cat * 3)), int(2 - prec))
    yield_str = str(yield_tr)
    if yield_tr >= 100:
        yield_str = checkForZero(yield_str, 0)
    elif yield_tr >= 10:
        yield_str = checkForZero(yield_str, -1)
    else:
        yield_str = checkForZero(yield_str, -2)
    return yield_str + cat_name


def construct_latexTable(latexTableList, caption="caption", label="label", cols_dtype=None, cols_align=None):
    table = Texttable(max_width=200)
    if cols_dtype:
        table.set_cols_dtype(cols_dtype)
    if cols_align:
        table.set_cols_align(cols_align)
    else:
        table.set_cols_align(["l"] + ["c"] * (len(latexTableList[0]) - 1))

    table.set_deco(Texttable.HEADER | Texttable.VLINES | Texttable.BORDER | Texttable.HLINES)
    table.add_rows(latexTableList)

    rprint("-- Table output: Basic --")
    rprint("Texttable Output:")
    rprint(table.draw())

    return latextable.draw_latex(table, caption=caption, caption_above=True, label=label, position="!htb")


def formatWrapper(value, absOpt=False, precision=3):
    from math import fabs

    if absOpt:
        value = fabs(value)

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
    else:
        if f"{value:.3f}".strip("-") == "0.000":
            return "& \\multirow{2}{*}{---}"
        else:
            return f"& \\multirow{{2}}{{*}}{{${value:.3f}$}}"


if __name__ == "__main__":

    # # Test printValue
    # print('\nTest printValue:')
    # rprint(printValue(10000.23456789, 0.12345))
    # rprint(printValue(10000.23456789, 0, useExpo=False, digit=4, reference=False))
    # rprint(printValue(10000.23456789, 0.12345, useExpo=False, digit=4, reference=False))
    # rprint(printValue(10000.23456789, 0.12345, useExpo=True, digit=4, reference=False))
    # rprint(printValue(10000.23456789, 0.12345, useExpo=False, digit=4, reference=True))

    # rprint(printValue(0.0000023456789, 0.82345, useExpo=False, digit=5, reference=False, significantFigures=False))
    # rprint(printValue(0.0000023456789, 0.82345, useExpo=True, digit=5, reference=False, significantFigures=False))

    # print('----------')
    # rprint(printValue(8000.00023456789, 12.82345, useExpo=False, digit=3, reference=False, significantFigures=True))
    # rprint(printValue(8000.00023456789, 12.82345, useExpo=True, digit=3, reference=False, significantFigures=True))

    # rprint(printValue(-0.00006789, -0.12345, useExpo=False, digit=4, reference=True))
    # rprint(printValue(0.23456789, 0.12345, useExpo=False, digit=4, reference=True, addPhantom=True))
    # rprint(printValue(0.239, 0.12345, useExpo=False, digit=2, roundMethod="round"))
    print(printValue(0.239, 0.12345, useExpo=False, digit=2, roundMethod="truncate"))

    print(printValue(0.239, 0.12545, digit=2))
    print(printValue(0.239, 0.12345, digit=2, roundMethod="truncate"))

    exit(1)
